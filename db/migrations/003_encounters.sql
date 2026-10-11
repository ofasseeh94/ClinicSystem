CREATE TABLE encounters (
  id uuid PRIMARY KEY, clinic_id uuid NOT NULL, patient_id uuid NOT NULL,
  occurred_at timestamptz NOT NULL, reason text NOT NULL, consent_context text NOT NULL,
  birth_context jsonb NOT NULL, note jsonb NOT NULL, measurements jsonb NOT NULL DEFAULT '[]',
  status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','in_review','signed','cancelled')),
  version integer NOT NULL DEFAULT 1 CHECK(version>0),
  created_by text NOT NULL, updated_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  signed_by text, signed_at timestamptz, cancellation_reason text,
  create_actor text NOT NULL, create_hash text NOT NULL, create_response jsonb NOT NULL,
  UNIQUE(clinic_id,id), FOREIGN KEY(clinic_id,patient_id) REFERENCES patients(clinic_id,id),
  CHECK ((status='signed') = (signed_by IS NOT NULL AND signed_at IS NOT NULL)),
  CHECK (status!='cancelled' OR length(cancellation_reason)>=5)
);
CREATE INDEX encounters_timeline ON encounters(clinic_id,patient_id,occurred_at DESC,id);
CREATE FUNCTION protect_encounter() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Encounter deletion is prohibited'; END IF;
  IF OLD.status IN ('signed','cancelled') THEN RAISE EXCEPTION 'Final encounter is immutable'; END IF;
  IF NEW.id<>OLD.id OR NEW.clinic_id<>OLD.clinic_id OR NEW.patient_id<>OLD.patient_id
     OR NEW.birth_context<>OLD.birth_context OR NEW.occurred_at<>OLD.occurred_at
     OR NEW.create_hash<>OLD.create_hash OR NEW.create_response<>OLD.create_response
     OR NEW.create_actor<>OLD.create_actor OR NEW.created_by<>OLD.created_by
     OR NEW.created_at<>OLD.created_at THEN RAISE EXCEPTION 'Encounter identity is immutable'; END IF;
  IF NEW.version<>OLD.version+1 THEN RAISE EXCEPTION 'Encounter version must advance'; END IF;
  IF NOT ((OLD.status='draft' AND NEW.status IN ('draft','in_review','cancelled'))
      OR (OLD.status='in_review' AND NEW.status IN ('draft','signed','cancelled')))
    THEN RAISE EXCEPTION 'Invalid encounter transition'; END IF;
  RETURN NEW;
END; $$;
CREATE TRIGGER encounter_history BEFORE UPDATE OR DELETE ON encounters
  FOR EACH ROW EXECUTE FUNCTION protect_encounter();
CREATE TABLE encounter_addenda (
  id uuid PRIMARY KEY, clinic_id uuid NOT NULL, encounter_id uuid NOT NULL,
  reason text NOT NULL, content text NOT NULL, signed_by text NOT NULL,
  signed_at timestamptz NOT NULL DEFAULT now(), request_hash text NOT NULL,
  FOREIGN KEY(clinic_id,encounter_id) REFERENCES encounters(clinic_id,id)
);
CREATE FUNCTION require_signed_parent() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS(SELECT 1 FROM encounters WHERE clinic_id=NEW.clinic_id
    AND id=NEW.encounter_id AND status='signed') THEN RAISE EXCEPTION 'Signed encounter required'; END IF;
  RETURN NEW;
END; $$;
CREATE TRIGGER addendum_parent BEFORE INSERT ON encounter_addenda
  FOR EACH ROW EXECUTE FUNCTION require_signed_parent();
CREATE TRIGGER immutable_addenda BEFORE UPDATE OR DELETE ON encounter_addenda
  FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();
