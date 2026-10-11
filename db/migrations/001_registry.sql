CREATE SEQUENCE patient_code_sequence;
CREATE TABLE patients (
  id uuid PRIMARY KEY, clinic_id uuid NOT NULL, clinic_code text NOT NULL UNIQUE,
  name_ar text NOT NULL DEFAULT '', name_en text NOT NULL DEFAULT '', normalized_names text NOT NULL,
  dob date NOT NULL CHECK (dob >= DATE '1900-01-01'),
  dob_precision text NOT NULL CHECK (dob_precision IN ('exact','estimated','month','year')),
  dob_source text NOT NULL CHECK (dob_source IN ('guardian','document','imported','unknown')),
  growth_reference_sex text NOT NULL CHECK (growth_reference_sex IN ('female','male','unknown')),
  allergy_review_status text NOT NULL CHECK (allergy_review_status IN ('unknown','not_assessed','no_known','known')),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','archived')),
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  created_by text NOT NULL, updated_by text NOT NULL,
  UNIQUE (clinic_id,id), CHECK (length(name_ar) > 0 OR length(name_en) > 0)
);
CREATE INDEX patients_clinic ON patients(clinic_id,created_at DESC);
CREATE TABLE contacts (
  id uuid PRIMARY KEY, clinic_id uuid NOT NULL, name text NOT NULL, normalized_name text NOT NULL,
  phone_e164 text NOT NULL CHECK (phone_e164 ~ '^\+[1-9][0-9]{7,14}$'),
  verified_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  created_by text NOT NULL, updated_by text NOT NULL, UNIQUE(clinic_id,id)
);
CREATE INDEX contacts_phone ON contacts(clinic_id,phone_e164);
CREATE TABLE patient_contacts (
  clinic_id uuid NOT NULL, patient_id uuid NOT NULL, contact_id uuid NOT NULL,
  relation text NOT NULL CHECK (relation IN ('mother','father','guardian','other','unknown')),
  authority_status text NOT NULL DEFAULT 'unverified' CHECK (authority_status IN ('unverified','verified','revoked')),
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  created_by text NOT NULL, updated_by text NOT NULL,
  PRIMARY KEY(patient_id,contact_id),
  FOREIGN KEY(clinic_id,patient_id) REFERENCES patients(clinic_id,id),
  FOREIGN KEY(clinic_id,contact_id) REFERENCES contacts(clinic_id,id)
);
CREATE TABLE patient_aliases (
  id uuid PRIMARY KEY, clinic_id uuid NOT NULL, patient_id uuid NOT NULL,
  alias text NOT NULL, normalized_alias text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  created_by text NOT NULL, FOREIGN KEY(clinic_id,patient_id) REFERENCES patients(clinic_id,id)
);
CREATE INDEX aliases_patient ON patient_aliases(clinic_id,patient_id);
CREATE TABLE allergies (
  id uuid PRIMARY KEY, clinic_id uuid NOT NULL, patient_id uuid NOT NULL,
  substance text NOT NULL, reaction text NOT NULL, state text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(), created_by text NOT NULL,
  FOREIGN KEY(clinic_id,patient_id) REFERENCES patients(clinic_id,id)
);
CREATE TABLE form_definitions (
  form_key text NOT NULL, version integer NOT NULL CHECK(version > 0), schema jsonb NOT NULL,
  published_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(form_key,version)
);
CREATE TABLE form_responses (
  id uuid PRIMARY KEY, clinic_id uuid NOT NULL, patient_id uuid NOT NULL,
  form_key text NOT NULL, form_version integer NOT NULL, answers jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(), created_by text NOT NULL,
  FOREIGN KEY(clinic_id,patient_id) REFERENCES patients(clinic_id,id),
  FOREIGN KEY(form_key,form_version) REFERENCES form_definitions(form_key,version)
);
CREATE TABLE audit_events (
  sequence bigint GENERATED ALWAYS AS IDENTITY UNIQUE, id uuid PRIMARY KEY, clinic_id uuid NOT NULL,
  actor text NOT NULL, action text NOT NULL, record_id uuid, payload jsonb NOT NULL,
  previous_hash text NOT NULL, event_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_clinic ON audit_events(clinic_id,sequence DESC);
CREATE TABLE idempotency_keys (
  clinic_id uuid NOT NULL, actor text NOT NULL, key uuid NOT NULL, request_hash text NOT NULL,
  patient_id uuid NOT NULL, response jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(clinic_id,actor,key), FOREIGN KEY(clinic_id,patient_id) REFERENCES patients(clinic_id,id)
);
CREATE FUNCTION reject_immutable_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Immutable record: append a new version or event'; END;
$$;
CREATE TRIGGER immutable_audit BEFORE UPDATE OR DELETE ON audit_events
  FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();
CREATE TRIGGER immutable_form_definitions BEFORE UPDATE OR DELETE ON form_definitions
  FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();
CREATE TRIGGER immutable_form_responses BEFORE UPDATE OR DELETE ON form_responses
  FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();
INSERT INTO form_definitions(form_key,version,schema) VALUES ('background',1,'{
 "title":"Medical and birth background","fields":[
 {"key":"medical.chronic_conditions","label":"Chronic conditions","type":"text","max_length":2000},
 {"key":"medical.current_medications","label":"Reported current medications","type":"text","max_length":2000},
 {"key":"medical.prior_admissions","label":"Prior admissions","type":"text","max_length":2000},
 {"key":"birth.ga_weeks","label":"Gestational age (weeks)","type":"integer","min":20,"max":45},
 {"key":"birth.ga_days","label":"Additional gestational days","type":"integer","min":0,"max":6},
 {"key":"birth.weight_kg","label":"Birth weight (kg)","type":"number","min":0.1,"max":8},
 {"key":"birth.nicu","label":"NICU admission","type":"enum","options":["yes","no","unknown","not_recorded"]}
 ]}'::jsonb);
