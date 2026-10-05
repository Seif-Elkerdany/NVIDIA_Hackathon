"""M1 handoff: purge-safe accounting and constrained atomic budget operations."""

from alembic import op

revision = "0005_budget"
down_revision = "0004_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE budget_locks (
          kind varchar(6) NOT NULL, key uuid NOT NULL, owner_id uuid, run_id uuid,
          CONSTRAINT pk_budget_locks PRIMARY KEY (kind,key),
          CONSTRAINT fk_budget_locks_owner_id_accounts FOREIGN KEY(owner_id)
            REFERENCES accounts(id) ON DELETE CASCADE,
          CONSTRAINT fk_budget_locks_owner_id_runs FOREIGN KEY(owner_id,run_id)
            REFERENCES runs(owner_id,id) ON DELETE CASCADE,
          CONSTRAINT ck_budget_locks_scope CHECK (
            (kind='GLOBAL' AND key='00000000-0000-0000-0000-000000000000'::uuid
             AND owner_id IS NULL AND run_id IS NULL) OR
            (kind='OWNER' AND key=owner_id AND owner_id IS NOT NULL AND run_id IS NULL) OR
            (kind='RUN' AND key=run_id AND owner_id IS NOT NULL AND run_id IS NOT NULL))
        );
        CREATE TABLE budget_charges (
          id uuid NOT NULL, amount bigint NOT NULL, cost bigint, active boolean NOT NULL,
          quote jsonb NOT NULL, created_at timestamptz NOT NULL, expires_at timestamptz NOT NULL,
          settled_at timestamptz,
          CONSTRAINT pk_budget_charges PRIMARY KEY(id),
          CONSTRAINT ck_budget_charges_money CHECK(amount>=0 AND (cost IS NULL OR cost>=0)),
          CONSTRAINT ck_budget_charges_expiry CHECK(expires_at>created_at),
          CONSTRAINT ck_budget_charges_settlement CHECK((cost IS NULL)=(settled_at IS NULL)),
          CONSTRAINT ck_budget_charges_active CHECK(NOT active OR cost IS NULL),
          CONSTRAINT ck_budget_charges_quote CHECK(jsonb_typeof(quote)='object')
        );
        INSERT INTO budget_locks VALUES
          ('GLOBAL','00000000-0000-0000-0000-000000000000',NULL,NULL);
        INSERT INTO budget_charges
          SELECT r.id,r.amount,e.cost,r.status='RESERVED' AND e.reservation_id IS NULL,
            jsonb_build_object('registry_version',r.registry_version,'price_version',r.price_version),
            r.created_at,r.expires_at,CASE WHEN e.cost IS NOT NULL THEN e.created_at END
          FROM usage_reservations r LEFT JOIN usage_entries e ON e.reservation_id=r.id;
    """)
    for table in ("budget_locks", "budget_charges"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON {table} FROM PUBLIC")
        op.execute(
            f"CREATE POLICY budget_admin ON {table} TO benefitbridge_budget_admin "
            "USING (true) WITH CHECK (true)"
        )
        op.execute(f"GRANT SELECT,INSERT,UPDATE ON {table} TO benefitbridge_budget_admin")
    # Deletion only cascades private lock keys; the billing journal has no private FK.
    op.execute("GRANT DELETE ON budget_locks TO benefitbridge_identity_admin")
    op.execute(
        "CREATE POLICY purge_locks ON budget_locks TO benefitbridge_identity_admin USING (true)"
    )
    op.execute("""
        CREATE FUNCTION public.benefitbridge_budget_mirror() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
        BEGIN
          IF TG_TABLE_NAME='usage_reservations' THEN
            INSERT INTO public.budget_charges
              VALUES(NEW.id,NEW.amount,NULL,NEW.status='RESERVED',
                jsonb_build_object('registry_version',NEW.registry_version,
                                   'price_version',NEW.price_version),
                NEW.created_at,NEW.expires_at,NULL)
              ON CONFLICT(id) DO UPDATE SET active=CASE WHEN budget_charges.cost IS NULL
                THEN NEW.status='RESERVED' ELSE false END;
          ELSE
            UPDATE public.budget_charges SET cost=NEW.cost, active=false,
              settled_at=CASE WHEN NEW.cost IS NOT NULL THEN
                coalesce(nullif(current_setting('app.budget_at',true),'')::timestamptz,
                         NEW.created_at) END
              WHERE id=NEW.reservation_id;
          END IF;
          RETURN NEW;
        END $$;

        CREATE FUNCTION public.benefitbridge_budget_lock(p_owner uuid,p_run uuid) RETURNS void
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
        BEGIN
          PERFORM 1 FROM public.budget_locks WHERE kind='GLOBAL' FOR UPDATE;
          IF p_owner IS NOT NULL THEN
            INSERT INTO public.budget_locks VALUES('OWNER',p_owner,p_owner,NULL)
              ON CONFLICT DO NOTHING;
            PERFORM 1 FROM public.budget_locks WHERE kind='OWNER' AND key=p_owner FOR UPDATE;
            INSERT INTO public.budget_locks VALUES('RUN',p_run,p_owner,p_run)
              ON CONFLICT DO NOTHING;
            PERFORM 1 FROM public.budget_locks WHERE kind='RUN' AND key=p_run FOR UPDATE;
          END IF;
        END $$;

        CREATE FUNCTION public.benefitbridge_budget_authorized(p_owner uuid,p_run uuid)
          RETURNS boolean LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
          SELECT CASE WHEN p_owner IS NULL THEN
            p_run IS NULL AND pg_has_role(session_user,'benefitbridge_public_worker','member')
          ELSE p_owner=nullif(current_setting('app.owner_id',true),'')::uuid
            AND pg_has_role(session_user,'benefitbridge_app','member')
            AND EXISTS(SELECT 1 FROM public.accounts WHERE id=p_owner AND status='ACTIVE'
              AND deletion_epoch=nullif(current_setting('app.deletion_epoch',true),'')::bigint)
            AND EXISTS(SELECT 1 FROM public.runs WHERE owner_id=p_owner AND id=p_run
              AND deletion_epoch=nullif(current_setting('app.deletion_epoch',true),'')::bigint)
          END
        $$;

        CREATE FUNCTION public.benefitbridge_budget_available(p_run uuid,p_expires timestamptz)
          RETURNS boolean LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
          SELECT EXISTS(SELECT 1 FROM public.runs WHERE id=p_run AND NOT cancel_requested
            AND status IN ('QUEUED','RUNNING') AND deadline_at>=p_expires)
        $$;

        CREATE FUNCTION public.benefitbridge_budget_reserve(
          p_id uuid,p_owner uuid,p_run uuid,p_amount bigint,p_quote jsonb,p_limits jsonb,
          p_now timestamptz,p_expires timestamptz) RETURNS text
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
        DECLARE global_money numeric; owner_money numeric; run_money numeric;
          global_active bigint; owner_active bigint; run_active bigint;
          day_start timestamptz; limit_entry record;
        BEGIN
          IF NOT public.benefitbridge_budget_authorized(p_owner,p_run) THEN
            RETURN 'NOT_FOUND'; END IF;
          IF p_owner IS NOT NULL AND NOT public.benefitbridge_budget_available(p_run,p_expires)
            THEN RETURN 'RUN_UNAVAILABLE'; END IF;
          IF p_amount<0 OR p_expires<=p_now OR jsonb_typeof(p_quote)<>'object'
             OR p_quote-ARRAY['registry_version','price_version','registry_fingerprint',
                'provider','model_id','input_token_limit','output_token_limit']<>'{}'::jsonb
             OR coalesce(length(p_quote->>'registry_version'),0)=0
             OR coalesce(length(p_quote->>'price_version'),0)=0
          THEN RAISE EXCEPTION 'Invalid reservation metadata' USING ERRCODE='23514'; END IF;
          IF jsonb_typeof(p_limits)<>'object' OR NOT p_limits ?& ARRAY[
              'run_microusd','owner_daily_microusd','global_daily_microusd',
              'run_concurrency','owner_concurrency','global_concurrency']
            OR p_limits-ARRAY['run_microusd','owner_daily_microusd','global_daily_microusd',
              'run_concurrency','owner_concurrency','global_concurrency']<>'{}'::jsonb
          THEN RAISE EXCEPTION 'Explicit budget limits required' USING ERRCODE='23514'; END IF;
          FOR limit_entry IN SELECT key,value FROM jsonb_each(p_limits) LOOP
            IF jsonb_typeof(limit_entry.value)<>'number' THEN
              RAISE EXCEPTION 'Invalid budget limit' USING ERRCODE='23514'; END IF;
            IF limit_entry.value::numeric<>trunc(limit_entry.value::numeric)
              OR limit_entry.value::numeric<0 OR limit_entry.value::numeric>9223372036854775807
              OR (limit_entry.key LIKE '%concurrency' AND
                limit_entry.value::numeric NOT BETWEEN 1 AND 2147483647)
            THEN RAISE EXCEPTION 'Invalid budget limit' USING ERRCODE='23514'; END IF;
          END LOOP;
          PERFORM public.benefitbridge_budget_lock(p_owner,p_run);
          -- A dead worker releases its concurrency slot, never its uncertain cost hold.
          UPDATE public.budget_charges SET active=false WHERE active AND expires_at<=p_now;
          day_start=date_trunc('day',p_now AT TIME ZONE 'UTC') AT TIME ZONE 'UTC';
          SELECT coalesce(sum(CASE WHEN cost IS NULL THEN amount
            WHEN settled_at>=day_start AND settled_at<day_start+interval '24 hours' THEN cost
            ELSE 0 END),0),count(*) FILTER(WHERE active)
            INTO global_money,global_active FROM public.budget_charges;
          SELECT coalesce(sum(CASE WHEN c.cost IS NULL THEN c.amount
            WHEN c.settled_at>=day_start AND c.settled_at<day_start+interval '24 hours' THEN c.cost
            ELSE 0 END),0),count(*) FILTER(WHERE c.active)
            INTO owner_money,owner_active FROM public.budget_charges c
            JOIN public.usage_reservations r ON r.id=c.id WHERE r.owner_id=p_owner;
          SELECT coalesce(sum(coalesce(c.cost,c.amount)),0),count(*) FILTER(WHERE c.active)
            INTO run_money,run_active FROM public.budget_charges c
            JOIN public.usage_reservations r ON r.id=c.id WHERE r.run_id=p_run;
          IF global_money+p_amount>(p_limits->>'global_daily_microusd')::bigint
            OR (p_owner IS NOT NULL AND
              (owner_money+p_amount>(p_limits->>'owner_daily_microusd')::bigint
               OR run_money+p_amount>(p_limits->>'run_microusd')::bigint))
          THEN RETURN 'BUDGET_EXCEEDED'; END IF;
          IF global_active>=(p_limits->>'global_concurrency')::bigint
            OR (p_owner IS NOT NULL AND
              (owner_active>=(p_limits->>'owner_concurrency')::bigint
               OR run_active>=(p_limits->>'run_concurrency')::bigint))
          THEN RETURN 'CONCURRENCY_LIMIT'; END IF;
          INSERT INTO public.usage_reservations
            (id,scope,owner_id,run_id,amount,status,registry_version,price_version,
             created_at,expires_at)
            VALUES(p_id,CASE WHEN p_owner IS NULL THEN 'PUBLIC' ELSE 'PRIVATE' END,
              p_owner,p_run,p_amount,'RESERVED',p_quote->>'registry_version',
              p_quote->>'price_version',p_now,p_expires);
          UPDATE public.budget_charges SET quote=p_quote WHERE id=p_id;
          RETURN 'RESERVED';
        END $$;

        CREATE FUNCTION public.benefitbridge_budget_reconcile(
          p_id uuid,p_cost bigint,p_usage jsonb,p_now timestamptz) RETURNS text
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
        DECLARE r public.usage_reservations; e public.usage_entries;
        BEGIN
          SELECT * INTO r FROM public.usage_reservations WHERE id=p_id;
          IF NOT FOUND OR NOT public.benefitbridge_budget_authorized(r.owner_id,r.run_id)
            THEN RETURN 'NOT_FOUND'; END IF;
          PERFORM public.benefitbridge_budget_lock(r.owner_id,r.run_id);
          SELECT * INTO e FROM public.usage_entries WHERE reservation_id=p_id FOR UPDATE;
          IF FOUND AND e.status='KNOWN' THEN
            IF p_cost IS NOT DISTINCT FROM e.cost AND p_usage=e.provider_usage
              THEN RETURN 'RECONCILED'; END IF;
            RETURN 'RECONCILIATION_CONFLICT';
          END IF;
          IF p_cost<0 THEN RAISE EXCEPTION 'Negative charge' USING ERRCODE='23514'; END IF;
          PERFORM set_config('app.budget_at',p_now::text,true);
          UPDATE public.usage_reservations SET status=CASE WHEN p_cost IS NULL
              THEN 'BILLING_UNKNOWN' ELSE 'RECONCILED' END,revision=revision+1 WHERE id=p_id;
          IF e.id IS NULL THEN
            INSERT INTO public.usage_entries
              (id,scope,owner_id,run_id,reservation_id,provider_usage,cost,status,
               registry_version,price_version,created_at)
              VALUES(p_id,r.scope,r.owner_id,r.run_id,p_id,p_usage,p_cost,
                CASE WHEN p_cost IS NULL THEN 'UNKNOWN' ELSE 'KNOWN' END,
                r.registry_version,r.price_version,p_now);
          ELSE
            UPDATE public.usage_entries SET cost=p_cost,provider_usage=p_usage,
              status=CASE WHEN p_cost IS NULL THEN 'UNKNOWN' ELSE 'KNOWN' END,
              revision=revision+1 WHERE id=e.id;
          END IF;
          RETURN CASE WHEN p_cost IS NULL THEN 'BILLING_UNKNOWN' ELSE 'RECONCILED' END;
        END $$;
    """)
    functions = (
        "benefitbridge_budget_mirror()",
        "benefitbridge_budget_lock(uuid,uuid)",
        "benefitbridge_budget_authorized(uuid,uuid)",
        "benefitbridge_budget_reserve(uuid,uuid,uuid,bigint,jsonb,jsonb,timestamptz,timestamptz)",
        "benefitbridge_budget_reconcile(uuid,bigint,jsonb,timestamptz)",
    )
    for signature in functions:
        # Boolean owner checks run under ordinary app RLS. The accounting role
        # receives no SELECT privilege on accounts, runs or their private inputs.
        owner = (
            "benefitbridge_app"
            if signature.startswith("benefitbridge_budget_authorized")
            else "benefitbridge_budget_admin"
        )
        op.execute(f"ALTER FUNCTION public.{signature} OWNER TO {owner}")
        op.execute(f"REVOKE ALL ON FUNCTION public.{signature} FROM PUBLIC")
    op.execute(
        "ALTER FUNCTION public.benefitbridge_budget_available(uuid,timestamptz) "
        "OWNER TO benefitbridge_app"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION public.benefitbridge_budget_available(uuid,timestamptz) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION public.benefitbridge_budget_available(uuid,timestamptz), "
        "public.benefitbridge_budget_authorized(uuid,uuid) TO benefitbridge_budget_admin"
    )
    for signature in functions[-2:]:
        op.execute(
            f"GRANT EXECUTE ON FUNCTION public.{signature} "
            "TO benefitbridge_app,benefitbridge_public_worker"
        )
    for table in ("usage_reservations", "usage_entries"):
        op.execute(
            f"CREATE TRIGGER budget_mirror AFTER INSERT OR UPDATE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION public.benefitbridge_budget_mirror()"
        )


def downgrade() -> None:
    for table in ("usage_entries", "usage_reservations"):
        op.execute(f"DROP TRIGGER budget_mirror ON {table}")
    for signature in (
        "benefitbridge_budget_reconcile(uuid,bigint,jsonb,timestamptz)",
        "benefitbridge_budget_reserve(uuid,uuid,uuid,bigint,jsonb,jsonb,timestamptz,timestamptz)",
        "benefitbridge_budget_authorized(uuid,uuid)",
        "benefitbridge_budget_available(uuid,timestamptz)",
        "benefitbridge_budget_lock(uuid,uuid)",
        "benefitbridge_budget_mirror()",
    ):
        op.execute(f"DROP FUNCTION public.{signature}")
    op.drop_table("budget_charges")
    op.drop_table("budget_locks")
