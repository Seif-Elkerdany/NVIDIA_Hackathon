"""Real PostgreSQL catalog identity, provenance and immutable publication checks."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import insert, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from tests.integration import test_identity as identity

from benefitbridge.db.sources import (
    OpportunityMetadata,
    OpportunityRecord,
    OpportunityVersionRecord,
    ProviderPolicy,
    ProviderRecord,
    SourceFetchRecord,
    SourceRecord,
    SourceSnapshotRecord,
    SourceSpanRecord,
    VersionSourceRecord,
)
from benefitbridge.domain.dto import Deadline
from benefitbridge.domain.enums import Authority, Availability, Completeness, Lane
from benefitbridge.sources.contracts import normalize_document, normalize_pages

identity_database = identity.database


@pytest.fixture
def database(identity_database):
    try:
        yield identity_database
    finally:
        identity_database[1].dispose()


@pytest.fixture
def catalog(database, fake_clock):
    engine = database[0]
    provider, source, snapshot = uuid4(), uuid4(), uuid4()
    normalized = normalize_document("Applicants must be enrolled.\nNo exceptions.")
    with Session(engine) as session, session.begin():
        session.add(
            ProviderRecord(
                id=provider,
                name="Fictional Institute",
                domains=["example.invalid"],
                policies=ProviderPolicy(
                    version=1, affiliation_evidence=(), notes="Synthetic fixture only"
                ),
                created_at=fake_clock.now(),
            )
        )
        session.flush()
        session.add(
            SourceRecord(
                id=source,
                provider_id=provider,
                canonical_url="https://example.invalid/policy",
                created_at=fake_clock.now(),
            )
        )
        session.flush()
        session.add(
            SourceSnapshotRecord(
                id=snapshot,
                source_id=source,
                raw_hash="a" * 64,
                normalized_hash=normalized.normalized_text_hash,
                normalized=normalized,
                text_object_key="synthetic/key",
                retrieved_at=fake_clock.now(),
                authority=Authority.OFFICIAL,
                completeness=Completeness.COMPLETE,
            )
        )
    return engine, provider, source, snapshot, normalized, fake_clock


def metadata():
    return OpportunityMetadata(
        title="Synthetic Placement",
        lane=Lane.INTERNSHIP_RESEARCH,
        remote=False,
        official_url="https://example.invalid/policy",
        authority=Authority.OFFICIAL,
        availability=Availability.UNKNOWN,
        deadline=Deadline(
            raw_text="Not specified",
            precision="UNKNOWN",
            date=None,
            at=None,
            timezone=None,
            ambiguity="Missing",
        ),
    )


def publish(
    catalog,
    *,
    intake="2027",
    location="EG",
    external="placement-1",
    number=1,
    opportunity=None,
    version=None,
):
    engine, provider, _, snapshot, _, clock = catalog
    opportunity, version = opportunity or uuid4(), version or uuid4()
    with Session(engine) as session, session.begin():
        if number == 1:
            session.add(
                OpportunityRecord(
                    id=opportunity,
                    provider_id=provider,
                    external_id=external,
                    intake=intake,
                    location_scope=location,
                    current_version_id=version,
                    created_at=clock.now(),
                )
            )
            session.flush()
        session.add(
            OpportunityVersionRecord(
                id=version,
                opportunity_id=opportunity,
                version_number=number,
                cycle=intake,
                location=location,
                public_metadata=metadata(),
                created_at=clock.now(),
            )
        )
        session.flush()
        session.add(VersionSourceRecord(version_id=version, snapshot_id=snapshot))
        if number > 1:
            session.execute(
                text(
                    "UPDATE opportunities SET current_version_id=:version, revision=revision+1 "
                    "WHERE id=:opportunity"
                ),
                {"version": version, "opportunity": opportunity},
            )
    return opportunity, version


def test_distinct_intakes_and_locations(catalog):
    first, _ = publish(catalog)
    second, _ = publish(catalog, intake="2028")
    third, _ = publish(catalog, location="US")
    with catalog[0].connect() as connection:
        keys = connection.execute(select(OpportunityRecord.canonical_key)).scalars().all()
        assert len(set(keys)) == 3
    assert len({first, second, third}) == 3
    with pytest.raises(IntegrityError):
        publish(catalog)


def test_concurrent_canonical_publication_has_one_winner(catalog):
    barrier = Barrier(2)

    def competing_insert():
        barrier.wait(timeout=10)
        try:
            publish(catalog)
            return "committed"
        except IntegrityError:
            return "duplicate"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: competing_insert(), range(2)))
    assert sorted(results) == ["committed", "duplicate"]


def test_length_delimited_identity_avoids_separator_collisions(catalog):
    publish(catalog, external="a:b", intake="c")
    publish(catalog, external="a", intake="b:c")
    with catalog[0].connect() as connection:
        assert len(set(connection.execute(select(OpportunityRecord.canonical_key)).scalars())) == 2


def test_hash_reuse_keeps_fetches_and_citations(catalog):
    engine, _, source, snapshot, normalized, clock = catalog
    span_id = uuid4()
    with Session(engine) as session, session.begin():
        session.add(
            SourceSpanRecord(
                id=span_id,
                snapshot_id=snapshot,
                page=None,
                start=0,
                end=28,
                quote="Applicants must be enrolled.",
            )
        )
        for raw_hash in ("a" * 64, "b" * 64):
            statement = (
                pg_insert(SourceSnapshotRecord)
                .values(
                    id=uuid4(),
                    source_id=source,
                    raw_hash=raw_hash,
                    normalized_hash=normalized.normalized_text_hash,
                    normalized=normalized,
                    text_object_key="another/key",
                    retrieved_at=clock.now(),
                    authority=Authority.OFFICIAL,
                    completeness=Completeness.COMPLETE,
                )
                .on_conflict_do_nothing(constraint="uq_source_snapshots_source_hash")
            )
            session.execute(statement)
            reused = session.scalar(
                select(SourceSnapshotRecord.id).where(
                    SourceSnapshotRecord.source_id == source,
                    SourceSnapshotRecord.normalized_hash == normalized.normalized_text_hash,
                )
            )
            assert reused == snapshot
            session.add(
                SourceFetchRecord(
                    id=uuid4(),
                    source_id=source,
                    snapshot_id=reused,
                    raw_hash=raw_hash,
                    http_status=200,
                    checked_at=clock.now(),
                )
            )
    with Session(engine) as session:
        assert len(session.scalars(select(SourceSnapshotRecord)).all()) == 1
        assert [
            f.raw_hash
            for f in session.scalars(select(SourceFetchRecord).order_by(SourceFetchRecord.raw_hash))
        ] == ["a" * 64, "b" * 64]
        assert session.get(SourceSpanRecord, span_id).quote == "Applicants must be enrolled."


def test_changed_content_creates_new_snapshot(catalog):
    engine, _, source, original, _, clock = catalog
    changed = normalize_document("New policy: enrollment is optional.")
    new = uuid4()
    with Session(engine) as session, session.begin():
        session.add(
            SourceSnapshotRecord(
                id=new,
                source_id=source,
                raw_hash="c" * 64,
                normalized_hash=changed.normalized_text_hash,
                normalized=changed,
                text_object_key="new/key",
                retrieved_at=clock.now(),
                authority=Authority.OFFICIAL,
                completeness=Completeness.COMPLETE,
            )
        )
    with Session(engine) as session:
        assert len(session.scalars(select(SourceSnapshotRecord)).all()) == 2
        assert session.get(SourceSnapshotRecord, original).normalized.text.startswith(
            "Applicants must"
        )


@pytest.mark.parametrize(
    "page,start,end,quote", [(None, 0, 3, "XYZ"), (2, 0, 3, "ABC"), (None, 99, 102, "ABC")]
)
def test_forged_citations_rejected_by_database(catalog, page, start, end, quote):
    with pytest.raises(IntegrityError):
        with catalog[0].begin() as connection:
            connection.execute(
                insert(SourceSpanRecord).values(
                    id=uuid4(), snapshot_id=catalog[3], page=page, start=start, end=end, quote=quote
                )
            )


def test_unicode_page_coordinates(catalog):
    engine, _, source, _, _, clock = catalog
    normalized = normalize_pages(["First.", "é😀 no."])
    snapshot = uuid4()
    with Session(engine) as session, session.begin():
        session.add(
            SourceSnapshotRecord(
                id=snapshot,
                source_id=source,
                raw_hash="d" * 64,
                normalized_hash=normalized.normalized_text_hash,
                normalized=normalized,
                text_object_key="paged/key",
                retrieved_at=clock.now(),
                authority=Authority.OFFICIAL,
                completeness=Completeness.COMPLETE,
            )
        )
        session.flush()
        session.add(
            SourceSpanRecord(id=uuid4(), snapshot_id=snapshot, page=2, start=0, end=2, quote="é😀")
        )
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                insert(SourceSpanRecord).values(
                    id=uuid4(), snapshot_id=snapshot, page=None, start=0, end=2, quote="Fi"
                )
            )


def test_forged_normalized_hash_rejected_by_database(catalog):
    normalized = catalog[4].model_dump(mode="json")
    normalized["text"] = "Fabricated text"
    with pytest.raises(IntegrityError):
        with catalog[0].begin() as connection:
            connection.execute(
                text("""INSERT INTO source_snapshots
                (id,source_id,raw_hash,normalized_hash,text_object_key,normalized,
                 retrieved_at,authority,completeness)
                SELECT :new,source_id,raw_hash,normalized_hash,'forged/key',
                       jsonb_set(normalized,'{text}','"Fabricated text"'),
                       retrieved_at,authority,completeness FROM source_snapshots WHERE id=:old"""),
                {"new": uuid4(), "old": catalog[3]},
            )


@pytest.mark.parametrize(
    "table",
    [
        "source_snapshots",
        "source_spans",
        "source_fetches",
        "opportunity_versions",
        "version_sources",
    ],
)
def test_public_history_is_immutable_even_for_admin(catalog, table):
    engine, _, source, snapshot, _, clock = catalog
    publish(catalog)
    with engine.begin() as connection:
        connection.execute(
            insert(SourceSpanRecord).values(
                id=uuid4(),
                snapshot_id=snapshot,
                start=0,
                end=28,
                quote="Applicants must be enrolled.",
            )
        )
        connection.execute(
            insert(SourceFetchRecord).values(
                id=uuid4(),
                source_id=source,
                snapshot_id=snapshot,
                raw_hash="a" * 64,
                checked_at=clock.now(),
            )
        )
    for operation in (
        f"DELETE FROM {table}",
        f"UPDATE {table} SET "
        + ("version_id=version_id" if table == "version_sources" else "id=id"),
    ):
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(text(operation))


def test_version_membership_is_sealed(catalog):
    _, version = publish(catalog)
    with pytest.raises(IntegrityError, match="sealed"):
        with catalog[0].begin() as connection:
            connection.execute(
                insert(VersionSourceRecord).values(version_id=version, snapshot_id=catalog[3])
            )


def test_current_pointer_must_belong_and_advance(catalog):
    engine = catalog[0]
    opportunity, first = publish(catalog)
    other, other_version = publish(catalog, intake="2028")
    for version in (uuid4(), other_version):
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE opportunities SET current_version_id=:v, revision=revision+1 "
                        "WHERE id=:o"
                    ),
                    {"v": version, "o": opportunity},
                )
    _, second = publish(catalog, opportunity=opportunity, number=2)
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE opportunities SET current_version_id=:v, revision=revision+1 "
                    "WHERE id=:o"
                ),
                {"v": first, "o": opportunity},
            )
    with engine.connect() as connection:
        assert (
            connection.scalar(
                select(OpportunityRecord.current_version_id).where(
                    OpportunityRecord.id == opportunity
                )
            )
            == second
        )
    assert other != opportunity


def test_nonexistent_initial_pointer_and_wrong_scope_fail(catalog):
    engine, provider, _, _, _, clock = catalog
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                insert(OpportunityRecord).values(
                    id=uuid4(),
                    provider_id=provider,
                    external_id="invalid",
                    intake="2027",
                    location_scope="EG",
                    current_version_id=uuid4(),
                    created_at=clock.now(),
                )
            )
    opportunity, _ = publish(catalog)
    with pytest.raises(IntegrityError):
        publish(catalog, opportunity=opportunity, number=2, intake="2028")


def test_identity_and_revision_updates_are_guarded(catalog):
    opportunity, _ = publish(catalog)
    for statement in (
        "UPDATE opportunities SET intake='2028', revision=revision+1 WHERE id=:id",
        "UPDATE opportunities SET revision=revision WHERE id=:id",
    ):
        with pytest.raises(IntegrityError):
            with catalog[0].begin() as connection:
                connection.execute(text(statement), {"id": opportunity})


def test_fetch_cannot_reference_another_source(catalog):
    engine, provider, _, snapshot, _, clock = catalog
    other = uuid4()
    with engine.begin() as connection:
        connection.execute(
            insert(SourceRecord).values(
                id=other,
                provider_id=provider,
                canonical_url="https://example.invalid/other",
                created_at=clock.now(),
            )
        )
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                insert(SourceFetchRecord).values(
                    id=uuid4(),
                    source_id=other,
                    snapshot_id=snapshot,
                    raw_hash="a" * 64,
                    checked_at=clock.now(),
                )
            )


def test_app_is_read_only_and_catalog_writer_is_separate(database, catalog):
    _, app, _, _ = database
    with app.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM sources")) == 1
    with pytest.raises(DBAPIError):
        with app.begin() as connection:
            connection.execute(text("UPDATE providers SET revision=revision+1"))
    with catalog[0].begin() as connection:
        connection.execute(text("SET LOCAL ROLE benefitbridge_catalog_writer"))
        connection.execute(text("UPDATE providers SET revision=revision+1"))
        with pytest.raises(DBAPIError):
            with connection.begin_nested():
                connection.execute(text("SELECT * FROM accounts"))


def test_sources_migration_downgrade_and_reupgrade(database):
    with database[0].begin() as connection:
        config = Config(str(identity.ROOT / "alembic.ini"))
        config.attributes["connection"] = connection
        command.downgrade(config, "0001_identity")
        assert connection.scalar(text("SELECT to_regclass('public.sources')")) is None
        command.upgrade(config, "head")
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == "0004_documents"
        )
