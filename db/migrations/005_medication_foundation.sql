CREATE TABLE medication_catalog (
 id uuid PRIMARY KEY, clinic_id uuid NOT NULL, catalog_id uuid NOT NULL, version integer NOT NULL,
 product_name text NOT NULL, generic_name text NOT NULL, formulation text NOT NULL,
 strength_text text NOT NULL, route_text text NOT NULL,
 source_kind text NOT NULL CHECK(source_kind IN ('synthetic','regulatory_label','formulary')),
 source_title text NOT NULL, source_publisher text NOT NULL, source_version text NOT NULL,
 source_url text NOT NULL, source_country text NOT NULL, source_checked_on date NOT NULL,
 state text NOT NULL DEFAULT 'draft' CHECK(state IN ('draft','in_review','verified_identity','retired')),
 revision integer NOT NULL DEFAULT 1, created_by text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 reviewed_by text, reviewed_at timestamptz, review_reason text, request_hash text NOT NULL,
 UNIQUE(clinic_id,id), UNIQUE(clinic_id,catalog_id,version)
);
CREATE INDEX catalog_clinic ON medication_catalog(clinic_id,created_at DESC,id);
CREATE FUNCTION protect_medication_catalog() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Catalog history cannot be deleted'; END IF;
 IF (to_jsonb(NEW)-ARRAY['state','revision','reviewed_by','reviewed_at','review_reason'])
   IS DISTINCT FROM (to_jsonb(OLD)-ARRAY['state','revision','reviewed_by','reviewed_at','review_reason'])
   THEN RAISE EXCEPTION 'Catalog content is immutable; create a new version'; END IF;
 IF NEW.revision<>OLD.revision+1 THEN RAISE EXCEPTION 'Catalog revision must advance'; END IF;
 IF NOT ((OLD.state='draft' AND NEW.state IN ('in_review','retired'))
   OR (OLD.state='in_review' AND NEW.state IN ('draft','verified_identity','retired'))
   OR (OLD.state='verified_identity' AND NEW.state='retired'))
   THEN RAISE EXCEPTION 'Invalid catalog transition'; END IF;
 IF NEW.state='verified_identity' AND (NEW.source_kind='synthetic' OR NEW.reviewed_by=NEW.created_by
   OR NEW.reviewed_by IS NULL OR NEW.reviewed_at IS NULL OR length(NEW.review_reason)<5)
   THEN RAISE EXCEPTION 'Independent sourced identity review required'; END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER catalog_history BEFORE UPDATE OR DELETE ON medication_catalog
 FOR EACH ROW EXECUTE FUNCTION protect_medication_catalog();
CREATE TABLE medication_statements (
 id uuid PRIMARY KEY, clinic_id uuid NOT NULL, patient_id uuid NOT NULL, encounter_id uuid,
 catalog_version_id uuid, supersedes_id uuid, medication_name text NOT NULL,
 reported_instructions text NOT NULL, use_status text NOT NULL CHECK(use_status IN ('active','stopped','completed','unknown')),
 recorded_for timestamptz NOT NULL, source text NOT NULL, reason text NOT NULL,
 created_by text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), request_hash text NOT NULL,
 UNIQUE(clinic_id,id), FOREIGN KEY(clinic_id,patient_id) REFERENCES patients(clinic_id,id),
 FOREIGN KEY(clinic_id,encounter_id) REFERENCES encounters(clinic_id,id),
 FOREIGN KEY(clinic_id,catalog_version_id) REFERENCES medication_catalog(clinic_id,id),
 FOREIGN KEY(clinic_id,supersedes_id) REFERENCES medication_statements(clinic_id,id)
);
CREATE UNIQUE INDEX statement_correction ON medication_statements(clinic_id,supersedes_id) WHERE supersedes_id IS NOT NULL;
CREATE INDEX medication_patient ON medication_statements(clinic_id,patient_id,recorded_for DESC,id);
CREATE TRIGGER immutable_medication_statements BEFORE UPDATE OR DELETE ON medication_statements
 FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();
