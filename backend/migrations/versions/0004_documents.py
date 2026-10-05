"""Private evidence and immutable support (MS-025). Frozen PostgreSQL DDL."""

from alembic import op

revision = "0004_documents"
down_revision = "0003_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(r"""
        CREATE TABLE documents (
        id UUID NOT NULL,
        owner_id UUID NOT NULL,
        filename VARCHAR(120) NOT NULL,
        kind VARCHAR(10) NOT NULL,
        status VARCHAR(9) NOT NULL,
        bytes_reserved INTEGER NOT NULL,
        size_bytes INTEGER DEFAULT 0 NOT NULL,
        sha256 VARCHAR(64),
        current_version_id UUID,
        deleted_at TIMESTAMP WITH TIME ZONE,
        revision INTEGER DEFAULT 1 NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        upload_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_documents PRIMARY KEY (id),
        CONSTRAINT uq_documents_owner_id_id UNIQUE (owner_id, id),
        CONSTRAINT ck_documents_quota_bytes CHECK (bytes_reserved BETWEEN 1 AND 10485760 AND
        size_bytes >= 0 AND size_bytes <= bytes_reserved),
        CONSTRAINT ck_documents_revision_times CHECK (revision > 0 AND updated_at >= created_at AND
        upload_expires_at > created_at),
        CONSTRAINT ck_documents_filename CHECK (char_length(filename) BETWEEN 1 AND 120),
        CONSTRAINT ck_documents_hash CHECK (sha256 IS NULL OR sha256 ~ '^[0-9a-f]{64}$'),
        CONSTRAINT ck_documents_tombstone CHECK (deleted_at IS NULL OR status = 'DELETING'),
        CONSTRAINT fk_documents_owner_id_accounts FOREIGN KEY(owner_id) REFERENCES accounts (id) ON
        DELETE CASCADE,
        CONSTRAINT ck_documents_documentkind CHECK (kind IN ('CV', 'TRANSCRIPT', 'ENROLLMENT')),
        CONSTRAINT ck_documents_documentstatus CHECK (status IN ('UPLOADING', 'UPLOADED', 'QUEUED',
        'PARSING', 'READY', 'FAILED', 'DELETING'))
        );
        
        CREATE INDEX ix_documents_owner_created ON documents (owner_id, created_at);
        
        CREATE TABLE document_versions (
        id UUID NOT NULL,
        owner_id UUID NOT NULL,
        document_id UUID NOT NULL,
        version_number INTEGER NOT NULL,
        object_key VARCHAR(512) NOT NULL,
        content_hash VARCHAR(64) NOT NULL,
        normalized JSONB NOT NULL,
        page_count INTEGER NOT NULL,
        quality VARCHAR(21) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_document_versions PRIMARY KEY (id),
        CONSTRAINT uq_document_versions_owner_id_id UNIQUE (owner_id, id),
        CONSTRAINT uq_document_versions_document UNIQUE (owner_id, id, document_id),
        CONSTRAINT uq_document_versions_number UNIQUE (owner_id, document_id, version_number),
        CONSTRAINT fk_document_versions_owner_id_documents FOREIGN KEY(owner_id, document_id)
        REFERENCES documents (owner_id, id) ON DELETE CASCADE,
        CONSTRAINT ck_document_versions_bounds CHECK (version_number > 0 AND page_count BETWEEN 1
        AND 20),
        CONSTRAINT ck_document_versions_hash CHECK (content_hash ~ '^[0-9a-f]{64}$'),
        CONSTRAINT ck_document_versions_object_key CHECK (char_length(object_key) BETWEEN 1 AND 512
        AND object_key !~ '(^/|\.\.)'),
        CONSTRAINT ck_document_versions_documentquality CHECK (quality IN ('READABLE',
        'MANUAL_ENTRY_REQUIRED'))
        );
        
        CREATE TABLE evidence_spans (
        id UUID NOT NULL,
        owner_id UUID NOT NULL,
        document_id UUID NOT NULL,
        document_version_id UUID NOT NULL,
        page INTEGER NOT NULL,
        start INTEGER NOT NULL,
        "end" INTEGER NOT NULL,
        quote TEXT NOT NULL,
        normalized_hash VARCHAR(64) NOT NULL,
        CONSTRAINT pk_evidence_spans PRIMARY KEY (id),
        CONSTRAINT uq_evidence_spans_owner_id_id UNIQUE (owner_id, id),
        CONSTRAINT fk_evidence_spans_owner_id_document_versions FOREIGN KEY(owner_id,
        document_version_id, document_id) REFERENCES document_versions (owner_id, id, document_id)
        ON DELETE CASCADE,
        CONSTRAINT ck_evidence_spans_span CHECK (page BETWEEN 1 AND 20 AND start >= 0 AND "end" >
        start AND char_length(quote) = "end" - start),
        CONSTRAINT ck_evidence_spans_hash CHECK (normalized_hash ~ '^[0-9a-f]{64}$')
        );
        
        CREATE INDEX ix_evidence_spans_owner_document ON evidence_spans (owner_id,
        document_version_id);
        
        CREATE TABLE fact_candidates (
        id UUID NOT NULL,
        owner_id UUID NOT NULL,
        document_id UUID NOT NULL,
        candidate JSONB NOT NULL,
        revision INTEGER DEFAULT 1 NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_fact_candidates PRIMARY KEY (id),
        CONSTRAINT uq_fact_candidates_owner_id_id UNIQUE (owner_id, id),
        CONSTRAINT fk_fact_candidates_owner_id_documents FOREIGN KEY(owner_id, document_id)
        REFERENCES documents (owner_id, id) ON DELETE CASCADE,
        CONSTRAINT ck_fact_candidates_revision CHECK (revision > 0)
        );
        
        CREATE INDEX ix_fact_candidates_owner_document ON fact_candidates (owner_id, document_id);
        
        CREATE TABLE fact_evidence (
        owner_id UUID NOT NULL,
        fact_id UUID NOT NULL,
        evidence_id UUID NOT NULL,
        supported_value JSONB NOT NULL,
        independently_confirmed BOOLEAN DEFAULT false NOT NULL,
        CONSTRAINT pk_fact_evidence PRIMARY KEY (owner_id, fact_id, evidence_id),
        CONSTRAINT fk_fact_evidence_owner_id_facts FOREIGN KEY(owner_id, fact_id) REFERENCES facts
        (owner_id, id) ON DELETE CASCADE,
        CONSTRAINT fk_fact_evidence_owner_id_evidence_spans FOREIGN KEY(owner_id, evidence_id)
        REFERENCES evidence_spans (owner_id, id) ON DELETE CASCADE
        );
        
        ALTER TABLE documents ADD CONSTRAINT fk_documents_current_version FOREIGN KEY(owner_id,
        current_version_id, id) REFERENCES document_versions (owner_id, id, document_id) DEFERRABLE
        INITIALLY DEFERRED;
    """)
    install_guards()


def install_guards() -> None:
    owner = "nullif(current_setting('app.owner_id', true), '')::uuid"
    epoch = "nullif(current_setting('app.deletion_epoch', true), '')::integer"
    for table in (
        "documents",
        "document_versions",
        "evidence_spans",
        "fact_candidates",
        "fact_evidence",
    ):
        predicate = (
            f"owner_id = {owner} AND EXISTS (SELECT 1 FROM public.accounts a "
            f"WHERE a.id = {owner} AND a.status = 'ACTIVE' AND a.deletion_epoch = {epoch})"
        )
        if table in {"document_versions", "evidence_spans", "fact_candidates"}:
            predicate += (
                f" AND EXISTS (SELECT 1 FROM public.documents d WHERE d.id = {table}.document_id "
                f"AND d.owner_id = {owner} AND d.deleted_at IS NULL AND d.status <> 'DELETING')"
            )
        if table == "fact_evidence":
            predicate += (
                " AND EXISTS (SELECT 1 FROM public.evidence_spans e "
                f"WHERE e.id = fact_evidence.evidence_id AND e.owner_id = {owner})"
            )
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON {table} FROM PUBLIC")
        op.execute(
            f"CREATE POLICY owner_access ON {table} TO benefitbridge_app "
            f"USING ({predicate}) WITH CHECK ({predicate})"
        )
        op.execute(
            f"CREATE POLICY identity_admin ON {table} TO benefitbridge_identity_admin "
            "USING (true) WITH CHECK (true)"
        )
        op.execute(f"GRANT SELECT, INSERT ON {table} TO benefitbridge_app")
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO benefitbridge_identity_admin"
        )
    op.execute("GRANT UPDATE ON documents, fact_candidates TO benefitbridge_app")
    for table in ("document_versions", "evidence_spans", "fact_evidence"):
        op.execute(
            f"CREATE TRIGGER immutable_input BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_immutable()"
        )
    op.execute(r"""
    CREATE FUNCTION public.benefitbridge_document_guard() RETURNS trigger
    LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
    DECLARE held bigint; files integer;
    BEGIN
      PERFORM 1 FROM public.accounts WHERE id = NEW.owner_id FOR UPDATE;
      IF TG_OP = 'UPDATE' AND (
          NEW.id <> OLD.id OR NEW.owner_id <> OLD.owner_id OR NEW.created_at <> OLD.created_at
          OR NEW.revision <> OLD.revision + 1 OR NEW.updated_at < OLD.updated_at
          OR (OLD.deleted_at IS NOT NULL AND NEW.deleted_at IS DISTINCT FROM OLD.deleted_at)) THEN
        RAISE EXCEPTION 'Invalid document revision' USING ERRCODE = '23514';
      END IF;
      IF TG_OP = 'UPDATE' AND OLD.status = 'UPLOADING' AND NEW.status <> 'UPLOADING'
        AND NEW.deleted_at IS NULL AND OLD.upload_expires_at <= NEW.updated_at THEN
        RAISE EXCEPTION 'Upload intent expired' USING ERRCODE = '23514';
      END IF;
      IF NEW.deleted_at IS NULL THEN
        SELECT coalesce(sum(bytes_reserved),0), count(*) INTO held, files
          FROM public.documents WHERE owner_id = NEW.owner_id AND id <> NEW.id
          AND deleted_at IS NULL AND (status <> 'UPLOADING' OR upload_expires_at > NEW.updated_at);
        IF held + NEW.bytes_reserved > 52428800 OR files + 1 > 10 THEN
          RAISE EXCEPTION 'Document quota exceeded' USING ERRCODE = '23514';
        END IF;
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER document_guard BEFORE INSERT OR UPDATE ON documents
      FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_document_guard();

    CREATE FUNCTION public.benefitbridge_evidence_guard() RETURNS trigger
    LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
    DECLARE n jsonb; marker jsonb; page_text text;
    BEGIN
      SELECT normalized INTO n FROM public.document_versions
        WHERE id = NEW.document_version_id AND owner_id = NEW.owner_id
        AND document_id = NEW.document_id;
      marker := n->'pages'->(NEW.page - 1);
      page_text := substring(n->>'text' FROM (marker->>'start')::integer + 1
                             FOR (marker->>'end')::integer - (marker->>'start')::integer);
      IF marker IS NULL OR NEW."end" > char_length(page_text)
        OR NEW.quote IS DISTINCT FROM
          substring(page_text FROM NEW.start + 1 FOR NEW."end" - NEW.start)
        OR NEW.normalized_hash IS DISTINCT FROM
          encode(sha256(convert_to(page_text,'UTF8')),'hex') THEN
        RAISE EXCEPTION 'Evidence does not match page text' USING ERRCODE = '23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER evidence_guard BEFORE INSERT ON evidence_spans
      FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_evidence_guard();

    CREATE FUNCTION public.benefitbridge_candidate_guard() RETURNS trigger
    LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
    DECLARE target text;
    BEGIN
      IF NEW.candidate->>'id' IS DISTINCT FROM NEW.id::text
        OR NEW.candidate->>'document_id' IS DISTINCT FROM NEW.document_id::text THEN
        RAISE EXCEPTION 'Candidate identity mismatch' USING ERRCODE = '23514';
      END IF;
      IF TG_OP = 'UPDATE' AND (NEW.id <> OLD.id OR NEW.owner_id <> OLD.owner_id
        OR NEW.document_id <> OLD.document_id OR NEW.revision <> OLD.revision + 1
        OR NEW.created_at <> OLD.created_at) THEN
        RAISE EXCEPTION 'Invalid candidate revision' USING ERRCODE = '23514';
      END IF;
      FOR target IN SELECT jsonb_array_elements_text(NEW.candidate->'evidence_ids') LOOP
        IF NOT EXISTS (SELECT 1 FROM public.evidence_spans WHERE id = target::uuid
                         AND owner_id = NEW.owner_id AND document_id = NEW.document_id) THEN
          RAISE EXCEPTION 'Evidence unavailable' USING ERRCODE = '23514';
        END IF;
      END LOOP;
      RETURN NEW;
    END $$;
    CREATE TRIGGER candidate_guard BEFORE INSERT OR UPDATE ON fact_candidates
      FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_candidate_guard();

    CREATE FUNCTION public.benefitbridge_fact_support_guard() RETURNS trigger
    LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM public.facts WHERE id = NEW.fact_id AND owner_id = NEW.owner_id
                     AND typed_value = NEW.supported_value) THEN
        RAISE EXCEPTION 'Fact support value differs' USING ERRCODE = '23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER fact_support_guard BEFORE INSERT ON fact_evidence
      FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_fact_support_guard();

    CREATE FUNCTION public.benefitbridge_document_version_guard() RETURNS trigger
    LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
    DECLARE marker jsonb; txt text; page_text text; cursor_pos integer := 0; ordinal integer := 0;
    BEGIN
      txt := NEW.normalized->>'text';
      IF NEW.normalized->>'normalization_version' IS DISTINCT FROM 'nfc-lf-v1'
        OR jsonb_typeof(NEW.normalized->'pages') IS DISTINCT FROM 'array'
        OR jsonb_array_length(NEW.normalized->'pages') <> NEW.page_count
        OR txt IS NULL OR txt <> normalize(txt, NFC) OR position(E'\r' in txt) > 0
        OR NEW.normalized->>'normalized_text_hash' IS DISTINCT FROM
           encode(sha256(convert_to(txt,'UTF8')),'hex') THEN
        RAISE EXCEPTION 'Invalid document normalization' USING ERRCODE = '23514';
      END IF;
      FOR marker IN SELECT value FROM jsonb_array_elements(NEW.normalized->'pages') LOOP
        ordinal := ordinal + 1;
        IF (marker->>'page')::integer IS DISTINCT FROM ordinal
          OR (marker->>'start')::integer IS DISTINCT FROM cursor_pos
          OR (marker->>'end')::integer < cursor_pos
          OR (marker->>'end')::integer > char_length(txt) THEN
          RAISE EXCEPTION 'Invalid document page' USING ERRCODE = '23514';
        END IF;
        page_text := substring(txt FROM cursor_pos + 1
                               FOR (marker->>'end')::integer - cursor_pos);
        IF marker->>'normalized_text_hash' IS DISTINCT FROM
           encode(sha256(convert_to(page_text,'UTF8')),'hex') THEN
          RAISE EXCEPTION 'Invalid document page hash' USING ERRCODE = '23514';
        END IF;
        cursor_pos := (marker->>'end')::integer;
        IF ordinal < NEW.page_count THEN
          IF substring(txt FROM cursor_pos + 1 FOR 3) <> E'\n\f\n' THEN
            RAISE EXCEPTION 'Invalid page separator' USING ERRCODE = '23514';
          END IF;
          cursor_pos := cursor_pos + 3;
        END IF;
      END LOOP;
      IF cursor_pos <> char_length(txt) THEN
        RAISE EXCEPTION 'Incomplete document pages' USING ERRCODE = '23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER document_version_guard BEFORE INSERT ON document_versions
      FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_document_version_guard();
    """)
    for name in (
        "document_guard",
        "evidence_guard",
        "candidate_guard",
        "fact_support_guard",
        "document_version_guard",
    ):
        op.execute(f"REVOKE ALL ON FUNCTION public.benefitbridge_{name}() FROM PUBLIC")


def downgrade() -> None:
    op.execute("ALTER TABLE documents DROP CONSTRAINT fk_documents_current_version")
    for table in (
        "fact_evidence",
        "fact_candidates",
        "evidence_spans",
        "document_versions",
        "documents",
    ):
        op.drop_table(table)
    for name in (
        "document_guard",
        "evidence_guard",
        "candidate_guard",
        "fact_support_guard",
        "document_version_guard",
    ):
        op.execute(f"DROP FUNCTION public.benefitbridge_{name}()")
