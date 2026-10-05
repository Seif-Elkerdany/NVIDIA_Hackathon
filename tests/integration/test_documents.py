"""MS-025 owner FKs, immutable citations, quota races and tombstone visibility."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import insert, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from tests.integration import test_identity as identity
from tests.integration import test_jobs as jobs

from benefitbridge.db.documents import (
    DocumentRecord,
    DocumentVersionRecord,
    EvidenceSpanRecord,
    FactCandidateRecord,
    FactEvidenceRecord,
)
from benefitbridge.domain.facts import FactCandidate
from benefitbridge.sources.contracts import normalize_pages

identity_database = identity.database
database = jobs.database


def document(clock, owner=identity.OWNER_A, **changes):
    return dict(
        id=uuid4(),
        owner_id=owner,
        filename="synthetic.pdf",
        kind="CV",
        status="UPLOADING",
        bytes_reserved=1024,
        created_at=clock.now(),
        updated_at=clock.now(),
        upload_expires_at=clock.now() + timedelta(hours=1),
        **changes,
    )


@pytest.fixture
def evidence(database, fake_clock):
    doc = document(fake_clock)
    version, span, candidate = uuid4(), uuid4(), uuid4()
    normalized = normalize_pages(["Enrolled at Synthetic Institute."])
    value = {"type": "BOOLEAN", "value": True}
    with database[0].begin() as connection:
        connection.execute(insert(DocumentRecord).values(**doc))
        connection.execute(
            insert(DocumentVersionRecord).values(
                id=version,
                owner_id=doc["owner_id"],
                document_id=doc["id"],
                version_number=1,
                object_key="synthetic/document/1",
                content_hash="a" * 64,
                normalized=normalized,
                page_count=1,
                quality="READABLE",
                created_at=fake_clock.now(),
            )
        )
        connection.execute(
            insert(EvidenceSpanRecord).values(
                id=span,
                owner_id=doc["owner_id"],
                document_id=doc["id"],
                document_version_id=version,
                page=1,
                start=0,
                end=8,
                quote="Enrolled",
                normalized_hash=normalized.pages[0].normalized_text_hash,
            )
        )
        connection.execute(
            insert(FactCandidateRecord).values(
                id=candidate,
                owner_id=doc["owner_id"],
                document_id=doc["id"],
                candidate=FactCandidate(
                    id=candidate,
                    document_id=doc["id"],
                    attribute="education.enrolled",
                    value=value,
                    evidence_ids=(span,),
                    state="PENDING",
                    issues=(),
                ),
                created_at=fake_clock.now(),
            )
        )
        connection.execute(
            insert(FactEvidenceRecord).values(
                owner_id=doc["owner_id"],
                fact_id=identity.FACT_A,
                evidence_id=span,
                supported_value=value,
            )
        )
    return doc, version, span, candidate


def test_owner_visibility_and_tombstone_hide_all_evidence(database, evidence, fake_clock):
    doc, version, span, candidate = evidence
    with database[1].begin() as connection:
        identity.context(connection)
        assert connection.scalar(select(EvidenceSpanRecord.id)) == span
        assert connection.scalar(select(FactCandidateRecord.id)) == candidate
        assert connection.scalar(select(FactEvidenceRecord.evidence_id)) == span
    with database[1].begin() as connection:
        identity.context(connection, identity.OWNER_B)
        assert connection.scalar(select(EvidenceSpanRecord.id)) is None
    with database[1].begin() as connection:
        identity.context(connection)
        connection.execute(
            update(DocumentRecord)
            .where(DocumentRecord.id == doc["id"])
            .values(deleted_at=fake_clock.now(), status="DELETING", revision=2)
        )
        for table in (
            DocumentVersionRecord,
            EvidenceSpanRecord,
            FactCandidateRecord,
            FactEvidenceRecord,
        ):
            assert connection.execute(select(table)).all() == []


def test_foreign_owner_support_fails_database_fk(database, evidence):
    with pytest.raises(IntegrityError):
        with database[0].begin() as connection:
            connection.execute(
                insert(FactEvidenceRecord).values(
                    owner_id=identity.OWNER_B,
                    fact_id=identity.FACT_B,
                    evidence_id=evidence[2],
                    supported_value={"type": "BOOLEAN", "value": True},
                )
            )


def test_wrong_quote_and_hash_fail_and_spans_are_immutable(database, evidence):
    doc, version, span, _ = evidence
    with pytest.raises(IntegrityError):
        with database[0].begin() as connection:
            connection.execute(
                insert(EvidenceSpanRecord).values(
                    id=uuid4(),
                    owner_id=doc["owner_id"],
                    document_id=doc["id"],
                    document_version_id=version,
                    page=1,
                    start=0,
                    end=8,
                    quote="Invented",
                    normalized_hash="b" * 64,
                )
            )
    with pytest.raises(DBAPIError):
        with database[1].begin() as connection:
            identity.context(connection)
            connection.execute(
                update(EvidenceSpanRecord)
                .where(EvidenceSpanRecord.id == span)
                .values(quote="Invented")
            )


def test_concurrent_uploads_enforce_shared_byte_quota(database, fake_clock):
    def reserve(_):
        try:
            with database[1].begin() as connection:
                identity.context(connection)
                values = document(fake_clock)
                values["bytes_reserved"] = 10485760
                connection.execute(insert(DocumentRecord).values(**values))
            return True
        except IntegrityError:
            return False

    with ThreadPoolExecutor(max_workers=6) as workers:
        assert sum(workers.map(reserve, range(6))) == 5


def test_expired_intents_release_quota_but_cannot_finish_late(database, fake_clock):
    values = document(fake_clock)
    with database[0].begin() as connection:
        connection.execute(insert(DocumentRecord).values(**values))
    fake_clock.advance(3601)
    with pytest.raises(IntegrityError):
        with database[0].begin() as connection:
            connection.execute(
                update(DocumentRecord)
                .where(DocumentRecord.id == values["id"])
                .values(status="UPLOADED", revision=2, updated_at=fake_clock.now())
            )
