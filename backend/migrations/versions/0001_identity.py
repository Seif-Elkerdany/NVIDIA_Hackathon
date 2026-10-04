"""Identity, immutable profiles and owner isolation (MS-007).

Application/identity administrator login roles must be granted the corresponding
NOLOGIN group. Migration credentials are never used by private repositories.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0001_identity"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'benefitbridge_app') THEN
            CREATE ROLE benefitbridge_app NOLOGIN NOSUPERUSER NOBYPASSRLS;
          END IF;
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'benefitbridge_identity_admin') THEN
            CREATE ROLE benefitbridge_identity_admin NOLOGIN NOSUPERUSER NOBYPASSRLS;
          END IF;
        END $$
    """)
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("timezone", sa.String(100), nullable=False),
        sa.Column("consent_version", sa.String(100)),
        sa.Column("consent_at", sa.DateTime(timezone=True)),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deletion_epoch", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE', 'DELETING')", name="ck_accounts_status"),
        sa.CheckConstraint("deletion_epoch >= 0", name="ck_accounts_deletion_epoch"),
        sa.CheckConstraint(
            "char_length(display_name) BETWEEN 1 AND 120", name="ck_accounts_display_name"
        ),
        sa.CheckConstraint(
            "(consent_version IS NULL) = (consent_at IS NULL)", name="ck_accounts_consent_pair"
        ),
    )
    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_id", sa.Uuid(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("current_version_id", sa.Uuid(), nullable=False),
        sa.UniqueConstraint("owner_id", name="uq_profiles_owner_id"),
        sa.UniqueConstraint("owner_id", "id", name="uq_profiles_owner_id_id"),
    )
    op.create_table(
        "profile_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Uuid(),
            sa.ForeignKey("profiles.owner_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_txid",
            sa.Text(),
            nullable=False,
            server_default=sa.text("pg_current_xact_id()::text"),
        ),
        sa.UniqueConstraint("owner_id", "id", name="uq_profile_versions_owner_id_id"),
        sa.UniqueConstraint(
            "owner_id", "version_number", name="uq_profile_versions_owner_id_version_number"
        ),
        sa.CheckConstraint("version_number > 0", name="ck_profile_versions_positive_version"),
    )
    op.create_foreign_key(
        "fk_profiles_current_version",
        "profiles",
        "profile_versions",
        ["owner_id", "current_version_id"],
        ["owner_id", "id"],
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_table(
        "facts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_id", sa.Uuid(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("attribute", sa.String(100), nullable=False),
        sa.Column("typed_value", pg.JSONB(), nullable=False),
        sa.Column("provenance", sa.String(32), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_from", sa.Date()),
        sa.Column("valid_until", sa.Date()),
        sa.Column("conflict", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("owner_id", "id", name="uq_facts_owner_id_id"),
        sa.UniqueConstraint("owner_id", "id", "attribute", name="uq_facts_owner_id_id_attribute"),
        sa.CheckConstraint("jsonb_typeof(typed_value) = 'object'", name="ck_facts_value_object"),
        sa.CheckConstraint(
            "provenance IN ('USER_CONFIRMED', 'USER_CONFIRMED_DOCUMENT', 'CONFLICTING')",
            name="ck_facts_provenance",
        ),
        sa.CheckConstraint("conflict = (provenance = 'CONFLICTING')", name="ck_facts_conflict"),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from",
            name="ck_facts_validity",
        ),
    )
    op.create_table(
        "profile_version_facts",
        sa.Column("owner_id", sa.Uuid(), primary_key=True),
        sa.Column("version_id", sa.Uuid(), primary_key=True),
        sa.Column("fact_id", sa.Uuid(), primary_key=True),
        sa.Column("attribute", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id", "version_id"],
            ["profile_versions.owner_id", "profile_versions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "fact_id", "attribute"],
            ["facts.owner_id", "facts.id", "facts.attribute"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "owner_id",
            "version_id",
            "attribute",
            name="uq_profile_version_facts_owner_version_attribute",
        ),
    )
    op.create_table(
        "deleted_subjects",
        sa.Column("subject_hmac", sa.LargeBinary(), primary_key=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retain_until", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "octet_length(subject_hmac) = 32", name="ck_deleted_subjects_hmac_length"
        ),
        sa.CheckConstraint("retain_until > deleted_at", name="ck_deleted_subjects_retention"),
    )
    op.create_index("ix_deleted_subjects_retain_until", "deleted_subjects", ["retain_until"])
    # No self-recursive account policy: account status is checked directly there.
    owner = "nullif(current_setting('app.owner_id', true), '')::uuid"
    epoch = "nullif(current_setting('app.deletion_epoch', true), '')::integer"
    for table in ("accounts", "profiles", "profile_versions", "facts", "profile_version_facts"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        predicate = (
            f"id = {owner} AND status = 'ACTIVE' AND deletion_epoch = {epoch}"
            if table == "accounts"
            else (
                f"owner_id = {owner} AND EXISTS (SELECT 1 FROM public.accounts a "
                f"WHERE a.id = {owner} AND a.status = 'ACTIVE' AND a.deletion_epoch = {epoch})"
            )
        )
        op.execute(
            f"CREATE POLICY owner_access ON {table} TO benefitbridge_app "
            f"USING ({predicate}) WITH CHECK ({predicate})"
        )
        op.execute(
            f"CREATE POLICY identity_admin ON {table} TO benefitbridge_identity_admin "
            "USING (true) WITH CHECK (true)"
        )
        op.execute(f"REVOKE ALL ON {table} FROM PUBLIC")
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO benefitbridge_identity_admin"
        )
    op.execute("GRANT SELECT, INSERT, UPDATE ON accounts, profiles TO benefitbridge_app")
    op.execute(
        "GRANT SELECT, INSERT ON profile_versions, facts, profile_version_facts "
        "TO benefitbridge_app"
    )
    op.execute("ALTER TABLE deleted_subjects ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE deleted_subjects FORCE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON deleted_subjects FROM PUBLIC, benefitbridge_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON deleted_subjects TO benefitbridge_identity_admin"
    )
    op.execute(
        "CREATE POLICY identity_admin ON deleted_subjects TO benefitbridge_identity_admin "
        "USING (true) WITH CHECK (true)"
    )
    op.execute("""
        DO $$ BEGIN
          EXECUTE format('CREATE POLICY deny_lookup ON public.deleted_subjects '
                         'FOR SELECT TO %I USING (true)', current_user);
        END $$
    """)
    # Fixed-search-path, boolean-only lookup; no ledger content reaches the app.
    op.execute("""
        CREATE FUNCTION public.benefitbridge_subject_denied(digest bytea, at_time timestamptz)
        RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public AS $$
          SELECT EXISTS (SELECT 1 FROM public.deleted_subjects
                         WHERE subject_hmac = digest AND retain_until > at_time)
        $$;
        REVOKE ALL ON FUNCTION public.benefitbridge_subject_denied(bytea, timestamptz) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION public.benefitbridge_subject_denied(bytea, timestamptz)
          TO benefitbridge_app, benefitbridge_identity_admin;
    """)
    op.execute("""
        CREATE FUNCTION public.benefitbridge_immutable() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
          IF TG_OP = 'DELETE'
             AND pg_has_role(current_user, 'benefitbridge_identity_admin', 'member') THEN
            RETURN OLD;
          END IF;
          RAISE EXCEPTION 'Immutable profile input' USING ERRCODE = '23514';
        END $$;
        CREATE FUNCTION public.benefitbridge_membership_insert() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM public.profile_versions
            WHERE owner_id = NEW.owner_id AND id = NEW.version_id
              AND created_txid = pg_current_xact_id()::text) THEN
            RAISE EXCEPTION 'Version membership is sealed' USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$;
        REVOKE ALL ON FUNCTION public.benefitbridge_immutable() FROM PUBLIC;
        REVOKE ALL ON FUNCTION public.benefitbridge_membership_insert() FROM PUBLIC;
    """)
    op.execute("""
        CREATE FUNCTION public.benefitbridge_version_insert() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
          NEW.created_txid := pg_current_xact_id()::text;
          RETURN NEW;
        END $$;
        REVOKE ALL ON FUNCTION public.benefitbridge_version_insert() FROM PUBLIC;
        CREATE TRIGGER stamp_version BEFORE INSERT ON profile_versions
          FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_version_insert();
    """)
    for table in ("profile_versions", "facts", "profile_version_facts"):
        op.execute(
            f"CREATE TRIGGER immutable_input BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_immutable()"
        )
    op.execute(
        "CREATE TRIGGER seal_membership BEFORE INSERT ON profile_version_facts "
        "FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_membership_insert()"
    )


def downgrade() -> None:
    op.drop_constraint("fk_profiles_current_version", "profiles", type_="foreignkey")
    for table in (
        "profile_version_facts",
        "facts",
        "profile_versions",
        "profiles",
        "accounts",
        "deleted_subjects",
    ):
        op.drop_table(table)
    op.execute("DROP FUNCTION public.benefitbridge_subject_denied(bytea, timestamptz)")
    op.execute("DROP FUNCTION public.benefitbridge_membership_insert()")
    op.execute("DROP FUNCTION public.benefitbridge_immutable()")
    op.execute("DROP FUNCTION public.benefitbridge_version_insert()")
    # Group roles can be shared with other databases; downgrade must retain them.
