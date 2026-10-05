"""Durable private/public work and replay custody (MS-015)."""

from alembic import op

from benefitbridge.db import jobs  # noqa: F401 -- register work metadata

revision = "0003_jobs"
down_revision = "0002_sources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE deletion_receipts (
        id UUID NOT NULL,
        token_hash BYTEA NOT NULL,
        status VARCHAR(8) NOT NULL,
        requested_at TIMESTAMP WITH TIME ZONE NOT NULL,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        active_store_deleted_at TIMESTAMP WITH TIME ZONE,
        backup_retention_until TIMESTAMP WITH TIME ZONE,
        revision INTEGER DEFAULT 1 NOT NULL,
        CONSTRAINT pk_deletion_receipts PRIMARY KEY (id),
        CONSTRAINT uq_deletion_receipts_token_hash UNIQUE (token_hash),
        CONSTRAINT ck_deletion_receipts_token_hash CHECK (octet_length(token_hash) = 32),
        CONSTRAINT ck_deletion_receipts_retention_revision CHECK (expires_at = requested_at
          + interval '168 hours' AND revision > 0),
        CONSTRAINT ck_deletion_receipts_completion CHECK (status <> 'COMPLETE' OR
          active_store_deleted_at IS NOT NULL),
        CONSTRAINT ck_deletion_receipts_deletionstatus CHECK (status IN ('PENDING',
          'COMPLETE', 'FAILED'))
        )
    """)
    op.execute("""
        CREATE INDEX ix_deletion_receipts_expires ON deletion_receipts (expires_at)
    """)
    op.execute("""
        CREATE TABLE idempotency_records (
        owner_id UUID NOT NULL,
        operation VARCHAR(100) NOT NULL,
        key VARCHAR(128) NOT NULL,
        request_hash VARCHAR(64) NOT NULL,
        response_ciphertext BYTEA NOT NULL,
        response_status INTEGER NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_idempotency_records PRIMARY KEY (owner_id, operation, key),
        CONSTRAINT ck_idempotency_records_identity CHECK (char_length(operation) BETWEEN 1
          AND 100 AND char_length(key) BETWEEN 16 AND 128),
        CONSTRAINT ck_idempotency_records_request_hash CHECK (request_hash ~
          '^[0-9a-f]{64}$'),
        CONSTRAINT ck_idempotency_records_encrypted_replay CHECK
          (octet_length(response_ciphertext) BETWEEN 38 AND 262181 AND
          substring(response_ciphertext FROM 1 FOR 9) = decode('42425245504c415931',
          'hex')),
        CONSTRAINT ck_idempotency_records_response_status CHECK (response_status BETWEEN 200
          AND 599),
        CONSTRAINT ck_idempotency_records_retention CHECK (expires_at = created_at +
          interval '24 hours')
        )
    """)
    op.execute("""
        CREATE INDEX ix_idempotency_records_expires ON idempotency_records (expires_at)
    """)
    op.execute("""
        CREATE TABLE runs (
        id UUID NOT NULL,
        owner_id UUID NOT NULL,
        kind VARCHAR(15) NOT NULL,
        status VARCHAR(12) NOT NULL,
        inputs JSONB NOT NULL,
        progress JSONB DEFAULT jsonb_build_object('completed_units', 0, 'total_units', NULL)
          NOT NULL,
        funnel JSONB DEFAULT jsonb_build_object('raw_hits', 0, 'canonical', 0, 'official',
          0, 'parsed', 0, 'evaluated', 0) NOT NULL,
        result_refs JSONB DEFAULT jsonb_build_object('opportunity_ids', jsonb_build_array(),
          'evaluation_ids', jsonb_build_array(), 'draft_ids', jsonb_build_array()) NOT NULL,
        warnings JSONB DEFAULT '[]'::jsonb NOT NULL,
        failure_code VARCHAR(100),
        profile_version_id UUID,
        deletion_epoch INTEGER NOT NULL,
        stage VARCHAR(100) NOT NULL,
        cancel_requested BOOLEAN DEFAULT false NOT NULL,
        revision INTEGER DEFAULT 1 NOT NULL,
        deadline_at TIMESTAMP WITH TIME ZONE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_runs PRIMARY KEY (id),
        CONSTRAINT uq_runs_owner_id_id UNIQUE (owner_id, id),
        CONSTRAINT fk_runs_owner_id_profile_versions FOREIGN KEY(owner_id,
          profile_version_id) REFERENCES profile_versions (owner_id, id),
        CONSTRAINT ck_runs_version CHECK (deletion_epoch >= 0 AND revision > 0),
        CONSTRAINT ck_runs_inputs_object CHECK (jsonb_typeof(inputs) = 'object'),
        CONSTRAINT ck_runs_result_shapes CHECK (jsonb_typeof(progress) = 'object' AND
          jsonb_typeof(funnel) = 'object' AND jsonb_typeof(result_refs) = 'object' AND
          jsonb_typeof(warnings) = 'array'),
        CONSTRAINT ck_runs_stage CHECK (char_length(stage) BETWEEN 1 AND 100),
        CONSTRAINT ck_runs_times CHECK (deadline_at > created_at AND updated_at >=
          created_at),
        CONSTRAINT fk_runs_owner_id_accounts FOREIGN KEY(owner_id) REFERENCES accounts (id)
          ON DELETE CASCADE,
        CONSTRAINT ck_runs_runkind CHECK (kind IN ('DOCUMENT_PARSE', 'DISCOVERY', 'IMPORT',
          'EVALUATE', 'DRAFT_GENERATE', 'DRAFT_VALIDATE', 'REFRESH', 'DOCUMENT_DELETE',
          'ACCOUNT_DELETE', 'DEMO_RESET')),
        CONSTRAINT ck_runs_runstatus CHECK (status IN ('QUEUED', 'RUNNING', 'WAITING_USER',
          'SUCCEEDED', 'PARTIAL', 'FAILED', 'CANCELLED'))
        )
    """)
    op.execute("""
        CREATE INDEX ix_runs_owner_created ON runs (owner_id, created_at)
    """)
    op.execute("""
        CREATE TABLE jobs (
        id UUID NOT NULL,
        scope VARCHAR(7) NOT NULL,
        owner_id UUID,
        run_id UUID,
        source_id UUID,
        opportunity_id UUID,
        snapshot_id UUID,
        stage VARCHAR(100) NOT NULL,
        stage_key VARCHAR(256) NOT NULL,
        status VARCHAR(9) NOT NULL,
        due_at TIMESTAMP WITH TIME ZONE NOT NULL,
        deadline_at TIMESTAMP WITH TIME ZONE NOT NULL,
        attempt INTEGER DEFAULT 0 NOT NULL,
        max_attempts INTEGER DEFAULT 3 NOT NULL,
        lease_until TIMESTAMP WITH TIME ZONE,
        lease_owner UUID,
        fencing_token BIGINT DEFAULT 0 NOT NULL,
        revision INTEGER DEFAULT 1 NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_jobs PRIMARY KEY (id),
        CONSTRAINT uq_jobs_owner_id_id UNIQUE (owner_id, id),
        CONSTRAINT uq_jobs_stage_identity UNIQUE (owner_id, run_id, stage_key, id),
        CONSTRAINT uq_jobs_run_stage UNIQUE (run_id, stage_key),
        CONSTRAINT fk_jobs_owner_id_runs FOREIGN KEY(owner_id, run_id) REFERENCES runs
          (owner_id, id) ON DELETE CASCADE,
        CONSTRAINT ck_jobs_scope CHECK ((scope = 'PRIVATE' AND owner_id IS NOT NULL AND
          run_id IS NOT NULL) OR (scope = 'PUBLIC' AND owner_id IS NULL AND run_id IS
          NULL)),
        CONSTRAINT ck_jobs_stage CHECK (char_length(stage_key) BETWEEN 1 AND 256 AND
          char_length(stage) BETWEEN 1 AND 100),
        CONSTRAINT ck_jobs_counters CHECK (attempt >= 0 AND max_attempts > 0 AND attempt <=
          max_attempts AND fencing_token >= 0 AND revision > 0),
        CONSTRAINT ck_jobs_deadline CHECK (deadline_at > created_at AND due_at <=
          deadline_at),
        CONSTRAINT ck_jobs_lease CHECK ((status = 'RUNNING' AND lease_owner IS NOT NULL AND
          lease_until IS NOT NULL AND fencing_token > 0 AND lease_until <= deadline_at) OR
          (status <> 'RUNNING' AND lease_owner IS NULL AND lease_until IS NULL)),
        CONSTRAINT ck_jobs_public_target CHECK (scope <> 'PUBLIC' OR source_id IS NOT NULL
          OR opportunity_id IS NOT NULL OR snapshot_id IS NOT NULL),
        CONSTRAINT fk_jobs_owner_id_accounts FOREIGN KEY(owner_id) REFERENCES accounts (id)
          ON DELETE CASCADE,
        CONSTRAINT fk_jobs_source_id_sources FOREIGN KEY(source_id) REFERENCES sources (id),
        CONSTRAINT fk_jobs_opportunity_id_opportunities FOREIGN KEY(opportunity_id)
          REFERENCES opportunities (id),
        CONSTRAINT fk_jobs_snapshot_id_source_snapshots FOREIGN KEY(snapshot_id) REFERENCES
          source_snapshots (id),
        CONSTRAINT ck_jobs_jobstatus CHECK (status IN ('QUEUED', 'RUNNING', 'SUCCEEDED',
          'FAILED', 'CANCELLED'))
        )
    """)
    op.execute("""
        CREATE INDEX ix_jobs_due ON jobs (scope, due_at) WHERE status = 'QUEUED'
    """)
    op.execute("""
        CREATE UNIQUE INDEX ix_jobs_public_stage ON jobs (stage_key) WHERE scope = 'PUBLIC'
    """)
    op.execute("""
        CREATE TABLE outbox (
        id UUID NOT NULL,
        scope VARCHAR(7) NOT NULL,
        owner_id UUID,
        run_id UUID,
        event_key VARCHAR(256) NOT NULL,
        event_type VARCHAR(100) NOT NULL,
        payload JSONB NOT NULL,
        status VARCHAR(9) NOT NULL,
        revision INTEGER DEFAULT 1 NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_outbox PRIMARY KEY (id),
        CONSTRAINT uq_outbox_owner_id_id UNIQUE (owner_id, id),
        CONSTRAINT uq_outbox_run_event UNIQUE (run_id, event_key),
        CONSTRAINT fk_outbox_owner_id_runs FOREIGN KEY(owner_id, run_id) REFERENCES runs
          (owner_id, id) ON DELETE CASCADE,
        CONSTRAINT ck_outbox_scope CHECK ((scope = 'PRIVATE' AND owner_id IS NOT NULL AND
          run_id IS NOT NULL) OR (scope = 'PUBLIC' AND owner_id IS NULL AND run_id IS
          NULL)),
        CONSTRAINT ck_outbox_payload_object CHECK (jsonb_typeof(payload) = 'object'),
        CONSTRAINT ck_outbox_event CHECK (char_length(event_key) BETWEEN 1 AND 256 AND
          char_length(event_type) BETWEEN 1 AND 100),
        CONSTRAINT ck_outbox_revision CHECK (revision > 0),
        CONSTRAINT fk_outbox_owner_id_accounts FOREIGN KEY(owner_id) REFERENCES accounts
          (id) ON DELETE CASCADE,
        CONSTRAINT ck_outbox_outboxstatus CHECK (status IN ('PENDING', 'DELIVERED'))
        )
    """)
    op.execute("""
        CREATE INDEX ix_outbox_pending ON outbox (scope, created_at) WHERE status =
          'PENDING'
    """)
    op.execute("""
        CREATE UNIQUE INDEX ix_outbox_public_event ON outbox (event_key) WHERE scope =
          'PUBLIC'
    """)
    op.execute("""
        CREATE TABLE run_events (
        owner_id UUID NOT NULL,
        run_id UUID NOT NULL,
        seq BIGINT NOT NULL,
        event_type VARCHAR(100) NOT NULL,
        payload JSONB NOT NULL,
        at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_run_events PRIMARY KEY (owner_id, run_id, seq),
        CONSTRAINT fk_run_events_owner_id_runs FOREIGN KEY(owner_id, run_id) REFERENCES runs
          (owner_id, id) ON DELETE CASCADE,
        CONSTRAINT ck_run_events_seq CHECK (seq >= 0),
        CONSTRAINT ck_run_events_event_type CHECK (char_length(event_type) BETWEEN 1 AND
          100)
        )
    """)
    op.execute("""
        CREATE TABLE usage_reservations (
        id UUID NOT NULL,
        scope VARCHAR(7) NOT NULL,
        owner_id UUID,
        run_id UUID,
        amount BIGINT NOT NULL,
        status VARCHAR(15) NOT NULL,
        registry_version VARCHAR(100) NOT NULL,
        price_version VARCHAR(100) NOT NULL,
        revision INTEGER DEFAULT 1 NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_usage_reservations PRIMARY KEY (id),
        CONSTRAINT uq_usage_reservations_scope_id UNIQUE (scope, id),
        CONSTRAINT uq_usage_reservations_price_context UNIQUE (id, registry_version,
          price_version),
        CONSTRAINT uq_usage_reservations_private_id UNIQUE (owner_id, run_id, id),
        CONSTRAINT fk_usage_reservations_owner_id_runs FOREIGN KEY(owner_id, run_id)
          REFERENCES runs (owner_id, id) ON DELETE CASCADE,
        CONSTRAINT ck_usage_reservations_scope CHECK ((scope = 'PRIVATE' AND owner_id IS NOT
          NULL AND run_id IS NOT NULL) OR (scope = 'PUBLIC' AND owner_id IS NULL AND run_id
          IS NULL)),
        CONSTRAINT ck_usage_reservations_amount_revision CHECK (amount >= 0 AND revision >
          0),
        CONSTRAINT ck_usage_reservations_provenance CHECK (expires_at > created_at AND
          char_length(registry_version) > 0 AND char_length(price_version) > 0),
        CONSTRAINT fk_usage_reservations_owner_id_accounts FOREIGN KEY(owner_id) REFERENCES
          accounts (id) ON DELETE CASCADE,
        CONSTRAINT ck_usage_reservations_reservationstatus CHECK (status IN ('RESERVED',
          'BILLING_UNKNOWN', 'RECONCILED', 'RELEASED'))
        )
    """)
    op.execute("""
        CREATE INDEX ix_usage_reservations_owner_created ON usage_reservations (owner_id,
          created_at)
    """)
    op.execute("""
        CREATE INDEX ix_usage_reservations_scope_created ON usage_reservations (scope,
          created_at)
    """)
    op.execute("""
        CREATE TABLE stage_outputs (
        owner_id UUID NOT NULL,
        run_id UUID NOT NULL,
        stage_key VARCHAR(256) NOT NULL,
        job_id UUID NOT NULL,
        fencing_token BIGINT NOT NULL,
        artifact_ref JSONB NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_stage_outputs PRIMARY KEY (owner_id, run_id, stage_key),
        CONSTRAINT fk_stage_outputs_owner_id_runs FOREIGN KEY(owner_id, run_id) REFERENCES
          runs (owner_id, id) ON DELETE CASCADE,
        CONSTRAINT fk_stage_outputs_owner_id_jobs FOREIGN KEY(owner_id, run_id, stage_key,
          job_id) REFERENCES jobs (owner_id, run_id, stage_key, id) ON DELETE CASCADE,
        CONSTRAINT ck_stage_outputs_fencing_token CHECK (fencing_token > 0)
        )
    """)
    op.execute("""
        CREATE TABLE usage_entries (
        id UUID NOT NULL,
        scope VARCHAR(7) NOT NULL,
        owner_id UUID,
        run_id UUID,
        reservation_id UUID NOT NULL,
        provider_usage JSONB NOT NULL,
        cost BIGINT,
        status VARCHAR(7) NOT NULL,
        registry_version VARCHAR(100) NOT NULL,
        price_version VARCHAR(100) NOT NULL,
        revision INTEGER DEFAULT 1 NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_usage_entries PRIMARY KEY (id),
        CONSTRAINT uq_usage_entries_reservation UNIQUE (reservation_id),
        CONSTRAINT fk_usage_entries_price_context FOREIGN KEY(reservation_id,
          registry_version, price_version) REFERENCES usage_reservations (id,
          registry_version, price_version),
        CONSTRAINT fk_usage_entries_scope_usage_reservations FOREIGN KEY(scope,
          reservation_id) REFERENCES usage_reservations (scope, id),
        CONSTRAINT fk_usage_entries_owner_id_usage_reservations FOREIGN KEY(owner_id,
          run_id, reservation_id) REFERENCES usage_reservations (owner_id, run_id, id) ON
          DELETE CASCADE,
        CONSTRAINT ck_usage_entries_scope CHECK ((scope = 'PRIVATE' AND owner_id IS NOT NULL
          AND run_id IS NOT NULL) OR (scope = 'PUBLIC' AND owner_id IS NULL AND run_id IS
          NULL)),
        CONSTRAINT ck_usage_entries_billing CHECK ((status = 'KNOWN' AND cost IS NOT NULL
          AND cost >= 0) OR (status = 'UNKNOWN' AND cost IS NULL)),
        CONSTRAINT ck_usage_entries_usage_payload CHECK (jsonb_typeof(provider_usage) =
          'object' AND provider_usage -
          ARRAY['input_tokens','output_tokens','provider_request_id'] = '{}'::jsonb),
        CONSTRAINT ck_usage_entries_usage_values CHECK ((NOT provider_usage ? 'input_tokens'
          OR (jsonb_typeof(provider_usage->'input_tokens') = 'number' AND
          (provider_usage->>'input_tokens')::numeric >= 0 AND
          trunc((provider_usage->>'input_tokens')::numeric) =
          (provider_usage->>'input_tokens')::numeric)) AND (NOT provider_usage ?
          'output_tokens' OR (jsonb_typeof(provider_usage->'output_tokens') = 'number' AND
          (provider_usage->>'output_tokens')::numeric >= 0 AND
          trunc((provider_usage->>'output_tokens')::numeric) =
          (provider_usage->>'output_tokens')::numeric)) AND (NOT provider_usage ?
          'provider_request_id' OR (jsonb_typeof(provider_usage->'provider_request_id') =
          'string' AND provider_usage->>'provider_request_id' ~
          '^[A-Za-z0-9_.:-]{1,128}$'))),
        CONSTRAINT ck_usage_entries_provenance CHECK (char_length(registry_version) > 0 AND
          char_length(price_version) > 0),
        CONSTRAINT ck_usage_entries_revision CHECK (revision > 0),
        CONSTRAINT fk_usage_entries_owner_id_accounts FOREIGN KEY(owner_id) REFERENCES
          accounts (id) ON DELETE CASCADE
        )
    """)
    op.execute("""
        CREATE INDEX ix_usage_entries_owner_created ON usage_entries (owner_id, created_at)
    """)
    op.execute("""
        CREATE INDEX ix_usage_entries_scope_created ON usage_entries (scope, created_at)
    """)
    op.execute("""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'benefitbridge_public_worker') THEN
            CREATE ROLE benefitbridge_public_worker NOLOGIN NOSUPERUSER NOBYPASSRLS;
          END IF;
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'benefitbridge_budget_admin') THEN
            CREATE ROLE benefitbridge_budget_admin NOLOGIN NOSUPERUSER NOBYPASSRLS;
          END IF;
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'benefitbridge_receipt_admin') THEN
            CREATE ROLE benefitbridge_receipt_admin NOLOGIN NOSUPERUSER NOBYPASSRLS;
          END IF;
        END $$;
    """)
    owner = "nullif(current_setting('app.owner_id', true), '')::uuid"
    epoch = "nullif(current_setting('app.deletion_epoch', true), '')::integer"
    active = (
        f"EXISTS (SELECT 1 FROM public.accounts a WHERE a.id = {owner} "
        f"AND a.status = 'ACTIVE' AND a.deletion_epoch = {epoch})"
    )
    private = ("runs", "run_events", "stage_outputs", "idempotency_records")
    mixed = ("jobs", "outbox", "usage_reservations", "usage_entries")
    for table in (*private, *mixed):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON {table} FROM PUBLIC")
        predicate = f"owner_id = {owner} AND {active}"
        if table == "runs":
            predicate += f" AND deletion_epoch = {epoch}"
        if table in mixed:
            predicate += " AND scope = 'PRIVATE'"
        if table not in ("runs", "idempotency_records"):
            predicate += (
                " AND EXISTS (SELECT 1 FROM public.runs r "
                f"WHERE r.id = {table}.run_id AND r.owner_id = {owner} "
                f"AND r.deletion_epoch = {epoch})"
            )
        op.execute(
            f"CREATE POLICY owner_access ON {table} TO benefitbridge_app "
            f"USING ({predicate}) WITH CHECK ({predicate})"
        )
        op.execute(
            f"CREATE POLICY identity_admin ON {table} TO benefitbridge_identity_admin "
            "USING (true) WITH CHECK (true)"
        )
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO benefitbridge_identity_admin"
        )
        op.execute(f"GRANT SELECT, INSERT ON {table} TO benefitbridge_app")
        if table in mixed:
            op.execute(
                f"CREATE POLICY public_work ON {table} TO benefitbridge_public_worker "
                "USING (scope = 'PUBLIC' AND owner_id IS NULL AND run_id IS NULL) "
                "WITH CHECK (scope = 'PUBLIC' AND owner_id IS NULL AND run_id IS NULL)"
            )
            op.execute(f"GRANT SELECT, INSERT, UPDATE ON {table} TO benefitbridge_public_worker")
    op.execute(
        "GRANT UPDATE ON runs, jobs, outbox, usage_reservations, usage_entries TO benefitbridge_app"
    )
    for table in ("usage_reservations", "usage_entries"):
        op.execute(
            f"CREATE POLICY budget_admin ON {table} TO benefitbridge_budget_admin "
            "USING (true) WITH CHECK (true)"
        )
        op.execute(f"GRANT SELECT, INSERT, UPDATE ON {table} TO benefitbridge_budget_admin")
    op.execute(
        "GRANT SELECT ON providers, sources, source_snapshots, source_spans, "
        "opportunities, opportunity_versions, version_sources TO benefitbridge_public_worker"
    )
    op.execute("ALTER TABLE deletion_receipts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE deletion_receipts FORCE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON deletion_receipts FROM PUBLIC, benefitbridge_app")
    op.execute(
        "CREATE POLICY receipt_admin ON deletion_receipts "
        "TO benefitbridge_receipt_admin, benefitbridge_identity_admin "
        "USING (true) WITH CHECK (true)"
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON deletion_receipts "
        "TO benefitbridge_receipt_admin, benefitbridge_identity_admin"
    )
    op.execute("""
        CREATE FUNCTION public.benefitbridge_job_update() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
          IF (NEW.id, NEW.scope, NEW.owner_id, NEW.run_id, NEW.stage, NEW.stage_key,
              NEW.source_id, NEW.opportunity_id, NEW.snapshot_id, NEW.created_at)
             IS DISTINCT FROM
             (OLD.id, OLD.scope, OLD.owner_id, OLD.run_id, OLD.stage, OLD.stage_key,
              OLD.source_id, OLD.opportunity_id, OLD.snapshot_id, OLD.created_at)
             OR NEW.revision <> OLD.revision + 1 OR NEW.fencing_token < OLD.fencing_token
             OR NEW.attempt < OLD.attempt THEN
            RAISE EXCEPTION 'Job identity or revision conflict' USING ERRCODE = '23514';
          END IF;
          IF NEW.status = 'RUNNING' AND
             (OLD.status <> 'RUNNING' OR NEW.lease_owner IS DISTINCT FROM OLD.lease_owner)
             AND (NEW.fencing_token <= OLD.fencing_token OR NEW.attempt <> OLD.attempt + 1) THEN
            RAISE EXCEPTION 'A claim requires a new fence and attempt' USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$;
        CREATE FUNCTION public.benefitbridge_public_payload() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        DECLARE entry record; target uuid; present boolean;
        BEGIN
          IF NEW.scope = 'PUBLIC' THEN
            IF NEW.payload = '{}'::jsonb OR NEW.payload -
               ARRAY['source_id','snapshot_id','opportunity_id','job_id'] <> '{}'::jsonb THEN
              RAISE EXCEPTION 'Public work requires only public identifiers'
                USING ERRCODE = '23514';
            END IF;
            FOR entry IN SELECT key, value FROM jsonb_each_text(NEW.payload) LOOP
              target := entry.value::uuid;
              IF entry.key = 'source_id' THEN
                SELECT EXISTS (SELECT 1 FROM public.sources WHERE id = target) INTO present;
              ELSIF entry.key = 'snapshot_id' THEN
                SELECT EXISTS (SELECT 1 FROM public.source_snapshots WHERE id = target)
                  INTO present;
              ELSIF entry.key = 'opportunity_id' THEN
                SELECT EXISTS (SELECT 1 FROM public.opportunities WHERE id = target) INTO present;
              ELSE
                SELECT EXISTS (SELECT 1 FROM public.jobs WHERE id = target AND scope = 'PUBLIC')
                  INTO present;
              END IF;
              IF NOT present THEN
                RAISE EXCEPTION 'Missing public target' USING ERRCODE = '23503';
              END IF;
            END LOOP;
          END IF;
          RETURN NEW;
        END $$;
        CREATE FUNCTION public.benefitbridge_event_validate() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
          IF (NEW.payload->>'run_id')::uuid IS DISTINCT FROM NEW.run_id
             OR (NEW.payload->>'seq')::bigint IS DISTINCT FROM NEW.seq
             OR (NEW.payload->>'at')::timestamptz IS DISTINCT FROM NEW.at THEN
            RAISE EXCEPTION 'Event identity mismatch' USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$;
        CREATE FUNCTION public.benefitbridge_work_immutable() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
          IF TG_OP = 'DELETE'
             AND pg_has_role(current_user, 'benefitbridge_identity_admin', 'member') THEN
            RETURN OLD;
          END IF;
          RAISE EXCEPTION 'Immutable durable record' USING ERRCODE = '23514';
        END $$;
    """)
    op.execute("""
        CREATE FUNCTION public.benefitbridge_work_revision() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        DECLARE mutable text[];
        BEGIN
          IF TG_TABLE_NAME = 'runs' THEN
            mutable := ARRAY['status','stage','cancel_requested','updated_at','revision',
                             'progress','funnel','result_refs','warnings','failure_code'];
          ELSIF TG_TABLE_NAME = 'outbox' THEN
            mutable := ARRAY['status','revision'];
          ELSIF TG_TABLE_NAME = 'usage_reservations' THEN
            mutable := ARRAY['status','revision'];
          ELSIF TG_TABLE_NAME = 'usage_entries' THEN
            mutable := ARRAY['status','provider_usage','cost','revision'];
          ELSE
            mutable := ARRAY['status','active_store_deleted_at',
                             'backup_retention_until','revision'];
          END IF;
          IF to_jsonb(NEW) - mutable IS DISTINCT FROM to_jsonb(OLD) - mutable
             OR NEW.revision <> OLD.revision + 1 THEN
            RAISE EXCEPTION 'Durable identity or revision conflict' USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$;
    """)
    op.execute("""
        CREATE FUNCTION public.benefitbridge_replay_owner() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM public.accounts WHERE id = NEW.owner_id) THEN
            RAISE EXCEPTION 'Replay owner is unavailable' USING ERRCODE = '23503';
          END IF;
          RETURN NEW;
        END $$;
        CREATE FUNCTION public.benefitbridge_replay_purge() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
          DELETE FROM public.idempotency_records
            WHERE owner_id = OLD.id AND operation <> 'delete_account';
          RETURN OLD;
        END $$;
        REVOKE ALL ON FUNCTION public.benefitbridge_replay_owner() FROM PUBLIC;
        REVOKE ALL ON FUNCTION public.benefitbridge_replay_purge() FROM PUBLIC;
        CREATE TRIGGER replay_owner BEFORE INSERT ON idempotency_records
          FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_replay_owner();
        CREATE TRIGGER purge_replays BEFORE DELETE ON accounts
          FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_replay_purge();
    """)
    for function in (
        "job_update",
        "public_payload",
        "event_validate",
        "work_immutable",
        "work_revision",
    ):
        op.execute(f"REVOKE ALL ON FUNCTION public.benefitbridge_{function}() FROM PUBLIC")
    op.execute(
        "CREATE TRIGGER job_revision BEFORE UPDATE ON jobs "
        "FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_job_update()"
    )
    op.execute(
        "CREATE TRIGGER public_payload BEFORE INSERT OR UPDATE ON outbox "
        "FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_public_payload()"
    )
    op.execute(
        "CREATE TRIGGER validate_event BEFORE INSERT ON run_events "
        "FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_event_validate()"
    )
    for table in ("run_events", "stage_outputs", "idempotency_records"):
        op.execute(
            f"CREATE TRIGGER work_immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_work_immutable()"
        )
    for table in ("runs", "outbox", "usage_reservations", "usage_entries", "deletion_receipts"):
        op.execute(
            f"CREATE TRIGGER work_revision BEFORE UPDATE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_work_revision()"
        )


def downgrade() -> None:
    op.execute("DROP TRIGGER purge_replays ON accounts")
    for table in (
        "stage_outputs",
        "run_events",
        "idempotency_records",
        "usage_entries",
        "usage_reservations",
        "outbox",
        "jobs",
        "runs",
        "deletion_receipts",
    ):
        op.drop_table(table)
    for function in (
        "job_update",
        "public_payload",
        "event_validate",
        "work_immutable",
        "work_revision",
        "replay_owner",
        "replay_purge",
    ):
        op.execute(f"DROP FUNCTION public.benefitbridge_{function}()")
    # Roles are shared across databases and are retained, as in prior migrations.
