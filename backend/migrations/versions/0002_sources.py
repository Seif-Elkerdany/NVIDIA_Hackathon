"""Public source history and immutable opportunity versions (MS-014)."""

from alembic import op

from benefitbridge.db import sources  # noqa: F401 -- register catalog metadata

revision = "0002_sources"
down_revision = "0001_identity"
branch_labels = None
depends_on = None

# Immutable source inputs are shared history, not subject to private-account purge.
CATALOG_TABLES = (
    "providers",
    "sources",
    "source_snapshots",
    "source_spans",
    "source_fetches",
    "opportunities",
    "opportunity_versions",
    "version_sources",
)


def upgrade() -> None:
    op.execute("""
CREATE TABLE providers (
    id UUID NOT NULL,
    name TEXT NOT NULL,
    domains TEXT[] NOT NULL,
    policies JSONB NOT NULL,
    revision INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_providers PRIMARY KEY (id),
    CONSTRAINT ck_providers_name CHECK (char_length(name) > 0),
    CONSTRAINT ck_providers_domains CHECK (cardinality(domains) > 0 AND
      array_position(domains, NULL) IS NULL),
    CONSTRAINT ck_providers_policies_object CHECK (jsonb_typeof(policies) = 'object'),
    CONSTRAINT ck_providers_revision CHECK (revision > 0)
)
    """)
    op.execute("""
CREATE TABLE opportunities (
    id UUID NOT NULL,
    provider_id UUID NOT NULL,
    external_id TEXT NOT NULL,
    intake TEXT NOT NULL,
    location_scope TEXT NOT NULL,
    canonical_key TEXT GENERATED ALWAYS AS (provider_id::text || ':' ||
      char_length(external_id)::text || ':' || external_id || ':' ||
      char_length(intake)::text || ':' || intake || ':' || char_length(location_scope)::text
      || ':' || location_scope) STORED NOT NULL,
    current_version_id UUID NOT NULL,
    revision INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_opportunities PRIMARY KEY (id),
    CONSTRAINT uq_opportunities_canonical_key UNIQUE (canonical_key),
    CONSTRAINT uq_opportunities_identity UNIQUE (provider_id, external_id, intake, location_scope),
    CONSTRAINT uq_opportunities_scope UNIQUE (id, intake, location_scope),
    CONSTRAINT ck_opportunities_identity CHECK (char_length(external_id) > 0 AND
      char_length(intake) > 0 AND char_length(location_scope) > 0),
    CONSTRAINT ck_opportunities_revision CHECK (revision > 0),
    CONSTRAINT fk_opportunities_provider_id_providers FOREIGN KEY(provider_id) REFERENCES
      providers (id)
)
    """)
    op.execute("""
CREATE INDEX ix_opportunities_provider_intake ON opportunities (provider_id, intake)
    """)
    op.execute("""
CREATE TABLE sources (
    id UUID NOT NULL,
    canonical_url TEXT NOT NULL,
    provider_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_sources PRIMARY KEY (id),
    CONSTRAINT uq_sources_canonical_url UNIQUE (canonical_url),
    CONSTRAINT ck_sources_https_url CHECK (canonical_url ~ '^https://[^[:space:]]+$'),
    CONSTRAINT fk_sources_provider_id_providers FOREIGN KEY(provider_id) REFERENCES providers (id)
)
    """)
    op.execute("""
CREATE INDEX ix_sources_provider_id ON sources (provider_id)
    """)
    op.execute("""
CREATE TABLE opportunity_versions (
    id UUID NOT NULL,
    opportunity_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    cycle TEXT NOT NULL,
    location TEXT NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_txid TEXT DEFAULT pg_current_xact_id()::text NOT NULL,
    CONSTRAINT pk_opportunity_versions PRIMARY KEY (id),
    CONSTRAINT uq_opportunity_versions_opportunity_id_id UNIQUE (opportunity_id, id),
    CONSTRAINT uq_opportunity_versions_number UNIQUE (opportunity_id, version_number),
    CONSTRAINT fk_opportunity_versions_scope FOREIGN KEY(opportunity_id, cycle, location)
      REFERENCES opportunities (id, intake, location_scope),
    CONSTRAINT ck_opportunity_versions_version_number CHECK (version_number > 0),
    CONSTRAINT ck_opportunity_versions_metadata_object CHECK (jsonb_typeof(metadata) = 'object'),
    CONSTRAINT fk_opportunity_versions_opportunity_id_opportunities FOREIGN
      KEY(opportunity_id) REFERENCES opportunities (id)
)
    """)
    op.execute("""
CREATE TABLE source_snapshots (
    id UUID NOT NULL,
    source_id UUID NOT NULL,
    raw_hash VARCHAR(64) NOT NULL,
    normalized_hash VARCHAR(64) NOT NULL,
    text_object_key TEXT NOT NULL,
    normalized JSONB NOT NULL,
    retrieved_at TIMESTAMP WITH TIME ZONE NOT NULL,
    authority VARCHAR(32) NOT NULL,
    completeness VARCHAR(16) NOT NULL,
    CONSTRAINT pk_source_snapshots PRIMARY KEY (id),
    CONSTRAINT uq_source_snapshots_source_hash UNIQUE (source_id, normalized_hash),
    CONSTRAINT uq_source_snapshots_source_id_id UNIQUE (source_id, id),
    CONSTRAINT ck_source_snapshots_raw_hash CHECK (raw_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_source_snapshots_normalized_hash CHECK (normalized_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_source_snapshots_object_key CHECK (char_length(text_object_key) > 0),
    CONSTRAINT ck_source_snapshots_normalized_object CHECK (jsonb_typeof(normalized) = 'object'),
    CONSTRAINT ck_source_snapshots_authority CHECK (authority IN
      ('OFFICIAL','CORROBORATED','DISCOVERY_ONLY','UNRESOLVED')),
    CONSTRAINT ck_source_snapshots_completeness CHECK (completeness IN
      ('COMPLETE','INCOMPLETE','CONFLICTED')),
    CONSTRAINT fk_source_snapshots_source_id_sources FOREIGN KEY(source_id) REFERENCES sources (id)
)
    """)
    op.execute("""
CREATE INDEX ix_source_snapshots_normalized_hash ON source_snapshots (normalized_hash)
    """)
    op.execute("""
CREATE TABLE source_fetches (
    id UUID NOT NULL,
    source_id UUID NOT NULL,
    snapshot_id UUID,
    raw_hash VARCHAR(64),
    http_status INTEGER,
    checked_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_source_fetches PRIMARY KEY (id),
    CONSTRAINT fk_source_fetches_source_id_source_snapshots FOREIGN KEY(source_id,
      snapshot_id) REFERENCES source_snapshots (source_id, id),
    CONSTRAINT ck_source_fetches_http_status CHECK (http_status IS NULL OR http_status
      BETWEEN 100 AND 599),
    CONSTRAINT ck_source_fetches_raw_hash CHECK (raw_hash IS NULL OR raw_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_source_fetches_snapshot_hash CHECK (snapshot_id IS NULL OR raw_hash IS NOT NULL),
    CONSTRAINT fk_source_fetches_source_id_sources FOREIGN KEY(source_id) REFERENCES sources (id)
)
    """)
    op.execute("""
CREATE INDEX ix_source_fetches_source_checked ON source_fetches (source_id, checked_at)
    """)
    op.execute("""
CREATE TABLE source_spans (
    id UUID NOT NULL,
    snapshot_id UUID NOT NULL,
    page INTEGER,
    start INTEGER NOT NULL,
    "end" INTEGER NOT NULL,
    quote TEXT NOT NULL,
    CONSTRAINT pk_source_spans PRIMARY KEY (id),
    CONSTRAINT uq_source_spans_snapshot_id_id UNIQUE (snapshot_id, id),
    CONSTRAINT ck_source_spans_page CHECK (page IS NULL OR page > 0),
    CONSTRAINT ck_source_spans_offsets CHECK ("start" >= 0 AND "end" > "start" AND
      char_length(quote) = "end" - "start"),
    CONSTRAINT fk_source_spans_snapshot_id_source_snapshots FOREIGN KEY(snapshot_id)
      REFERENCES source_snapshots (id)
)
    """)
    op.execute("""
CREATE INDEX ix_source_spans_snapshot_id ON source_spans (snapshot_id)
    """)
    op.execute("""
CREATE TABLE version_sources (
    version_id UUID NOT NULL,
    snapshot_id UUID NOT NULL,
    CONSTRAINT pk_version_sources PRIMARY KEY (version_id, snapshot_id),
    CONSTRAINT fk_version_sources_version_id_opportunity_versions FOREIGN KEY(version_id)
      REFERENCES opportunity_versions (id),
    CONSTRAINT fk_version_sources_snapshot_id_source_snapshots FOREIGN KEY(snapshot_id)
      REFERENCES source_snapshots (id)
)
    """)
    op.execute("""
CREATE INDEX ix_version_sources_snapshot_id ON version_sources (snapshot_id)
    """)
    op.execute("""
    ALTER TABLE opportunities ADD CONSTRAINT fk_opportunities_current_version FOREIGN
      KEY(id, current_version_id) REFERENCES opportunity_versions (opportunity_id, id)
      DEFERRABLE INITIALLY DEFERRED
    """)

    op.execute("""
        CREATE FUNCTION public.benefitbridge_public_immutable() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
          RAISE EXCEPTION 'Immutable public input' USING ERRCODE = '23514';
        END $$;
        CREATE FUNCTION public.benefitbridge_snapshot_validate() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        DECLARE
          txt text; marker jsonb; page_text text; cursor_pos integer := 0;
          ordinal integer := 0; page_end integer;
        BEGIN
          txt := NEW.normalized->>'text';
          IF txt IS NULL OR NEW.normalized->>'normalization_version' IS DISTINCT FROM 'nfc-lf-v1'
             OR NEW.normalized->>'normalized_text_hash' IS DISTINCT FROM NEW.normalized_hash
             OR jsonb_typeof(NEW.normalized->'pages') IS DISTINCT FROM 'array'
             OR jsonb_typeof(NEW.normalized->'text') IS DISTINCT FROM 'string'
             OR encode(sha256(convert_to(txt, 'UTF8')), 'hex') <> NEW.normalized_hash
             OR normalize(txt, NFC) <> txt OR position(chr(13) IN txt) > 0 THEN
            RAISE EXCEPTION 'Invalid normalized source' USING ERRCODE = '23514';
          END IF;
          FOR marker IN SELECT value FROM jsonb_array_elements(NEW.normalized->'pages') LOOP
            ordinal := ordinal + 1;
            page_end := (marker->>'end')::integer;
            IF (marker->>'page')::integer IS DISTINCT FROM ordinal
               OR (marker->>'start')::integer IS DISTINCT FROM cursor_pos
               OR page_end IS NULL OR page_end < cursor_pos OR page_end > char_length(txt) THEN
              RAISE EXCEPTION 'Invalid source page' USING ERRCODE = '23514';
            END IF;
            page_text := substring(txt FROM cursor_pos + 1 FOR page_end - cursor_pos);
            IF marker->>'normalized_text_hash' IS DISTINCT FROM
               encode(sha256(convert_to(page_text, 'UTF8')), 'hex') THEN
              RAISE EXCEPTION 'Invalid page hash' USING ERRCODE = '23514';
            END IF;
            cursor_pos := page_end;
            IF ordinal < jsonb_array_length(NEW.normalized->'pages') THEN
              IF substring(txt FROM cursor_pos + 1 FOR 3) <> chr(10)||chr(12)||chr(10) THEN
                RAISE EXCEPTION 'Invalid page separator' USING ERRCODE = '23514';
              END IF;
              cursor_pos := cursor_pos + 3;
            END IF;
          END LOOP;
          IF ordinal > 0 AND cursor_pos <> char_length(txt) THEN
            RAISE EXCEPTION 'Incomplete page coordinates' USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$;
        CREATE FUNCTION public.benefitbridge_span_validate() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        DECLARE normalized jsonb; txt text; marker jsonb;
        BEGIN
          SELECT s.normalized INTO normalized FROM public.source_snapshots s
            WHERE s.id = NEW.snapshot_id;
          IF normalized IS NULL THEN
            RAISE EXCEPTION 'Missing source snapshot' USING ERRCODE = '23503';
          END IF;
          txt := normalized->>'text';
          IF NEW.page IS NULL THEN
            IF jsonb_array_length(normalized->'pages') <> 0 THEN
              RAISE EXCEPTION 'Page-local citation required' USING ERRCODE = '23514';
            END IF;
          ELSE
            marker := normalized->'pages'->(NEW.page - 1);
            IF marker IS NULL OR NEW.page < 1 THEN
              RAISE EXCEPTION 'Unknown source page' USING ERRCODE = '23514';
            END IF;
            txt := substring(txt FROM (marker->>'start')::integer + 1
                             FOR (marker->>'end')::integer - (marker->>'start')::integer);
          END IF;
          IF NEW."start" < 0 OR NEW."end" <= NEW."start" OR NEW."end" > char_length(txt)
             OR substring(txt FROM NEW."start" + 1 FOR NEW."end" - NEW."start") <> NEW.quote THEN
            RAISE EXCEPTION 'Citation does not match source' USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$;
        CREATE FUNCTION public.benefitbridge_version_source_insert() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM public.opportunity_versions
            WHERE id = NEW.version_id AND created_txid = pg_current_xact_id()::text) THEN
            RAISE EXCEPTION 'Version sources are sealed' USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$;
        CREATE FUNCTION public.benefitbridge_opportunity_update() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
          IF (NEW.id, NEW.provider_id, NEW.external_id, NEW.intake, NEW.location_scope,
              NEW.created_at) IS DISTINCT FROM
             (OLD.id, OLD.provider_id, OLD.external_id, OLD.intake, OLD.location_scope,
              OLD.created_at) OR NEW.revision <> OLD.revision + 1 THEN
            RAISE EXCEPTION 'Opportunity identity or revision conflict' USING ERRCODE = '23514';
          END IF;
          IF NEW.current_version_id <> OLD.current_version_id AND NOT EXISTS (
            SELECT 1 FROM public.opportunity_versions newer
            JOIN public.opportunity_versions older ON older.id = OLD.current_version_id
            WHERE newer.id = NEW.current_version_id AND newer.opportunity_id = NEW.id
              AND newer.version_number > older.version_number) THEN
            RAISE EXCEPTION 'Current version must advance' USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$;
        CREATE FUNCTION public.benefitbridge_provider_update() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
          IF NEW.id <> OLD.id OR NEW.created_at <> OLD.created_at
             OR NEW.revision <> OLD.revision + 1 THEN
            RAISE EXCEPTION 'Provider revision conflict' USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$;
    """)
    for function in (
        "public_immutable",
        "snapshot_validate",
        "span_validate",
        "version_source_insert",
        "opportunity_update",
        "provider_update",
    ):
        op.execute(f"REVOKE ALL ON FUNCTION public.benefitbridge_{function}() FROM PUBLIC")
    for table in (
        "sources",
        "source_snapshots",
        "source_spans",
        "source_fetches",
        "opportunity_versions",
        "version_sources",
    ):
        op.execute(
            f"CREATE TRIGGER immutable_public BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_public_immutable()"
        )
    op.execute("""
        CREATE TRIGGER validate_snapshot BEFORE INSERT ON source_snapshots
          FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_snapshot_validate();
        CREATE TRIGGER validate_span BEFORE INSERT ON source_spans
          FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_span_validate();
        CREATE TRIGGER stamp_version BEFORE INSERT ON opportunity_versions
          FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_version_insert();
        CREATE TRIGGER seal_sources BEFORE INSERT ON version_sources
          FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_version_source_insert();
        CREATE TRIGGER check_opportunity_update BEFORE UPDATE ON opportunities
          FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_opportunity_update();
        CREATE TRIGGER check_provider_update BEFORE UPDATE ON providers
          FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_provider_update();
    """)
    # Applicants read shared catalog history. Public maintenance has a separate
    # NOLOGIN group; the private app and identity administrator cannot write it.
    op.execute("""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'benefitbridge_catalog_writer') THEN
            CREATE ROLE benefitbridge_catalog_writer NOLOGIN NOSUPERUSER NOBYPASSRLS;
          END IF;
        END $$
    """)
    for table in CATALOG_TABLES:
        op.execute(f"REVOKE ALL ON {table} FROM PUBLIC")
        op.execute(f"GRANT SELECT ON {table} TO benefitbridge_app")
        op.execute(f"GRANT SELECT, INSERT ON {table} TO benefitbridge_catalog_writer")
    op.execute("GRANT UPDATE ON providers, opportunities TO benefitbridge_catalog_writer")


def downgrade() -> None:
    op.drop_constraint("fk_opportunities_current_version", "opportunities", type_="foreignkey")
    for table in (
        "version_sources",
        "source_fetches",
        "source_spans",
        "source_snapshots",
        "opportunity_versions",
        "opportunities",
        "sources",
        "providers",
    ):
        op.drop_table(table)
    for function in (
        "public_immutable",
        "snapshot_validate",
        "span_validate",
        "version_source_insert",
        "opportunity_update",
        "provider_update",
    ):
        op.execute(f"DROP FUNCTION public.benefitbridge_{function}()")
    # Retain shared NOLOGIN group roles on downgrade, matching MS-007.
