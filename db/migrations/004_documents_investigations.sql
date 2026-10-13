CREATE TABLE documents (
  id uuid PRIMARY KEY, clinic_id uuid NOT NULL, patient_id uuid NOT NULL, encounter_id uuid,
  title text NOT NULL, category text NOT NULL CHECK(category IN ('lab','imaging','letter','other')),
  captured_at timestamptz NOT NULL, source text NOT NULL,
  state text NOT NULL DEFAULT 'pending_upload' CHECK(state IN ('pending_upload','quarantined','ready','synthetic_ready','rejected','withdrawn')),
  mime_type text, byte_size integer, sha256 text, encrypted_content bytea,
  scan_detail text NOT NULL DEFAULT 'Not uploaded', version integer NOT NULL DEFAULT 1,
  created_by text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  request_hash text NOT NULL, withdrawal_reason text,
  UNIQUE(clinic_id,id), FOREIGN KEY(clinic_id,patient_id) REFERENCES patients(clinic_id,id),
  FOREIGN KEY(clinic_id,encounter_id) REFERENCES encounters(clinic_id,id),
  CHECK(byte_size IS NULL OR byte_size BETWEEN 1 AND 10485760)
);
CREATE INDEX documents_patient ON documents(clinic_id,patient_id,captured_at DESC,id);
CREATE FUNCTION protect_document() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Document deletion is prohibited'; END IF;
  IF OLD.state='withdrawn' THEN RAISE EXCEPTION 'Withdrawn document is immutable'; END IF;
  IF NEW.id<>OLD.id OR NEW.clinic_id<>OLD.clinic_id OR NEW.patient_id<>OLD.patient_id
    OR NEW.encounter_id IS DISTINCT FROM OLD.encounter_id OR NEW.title<>OLD.title
    OR NEW.category<>OLD.category OR NEW.captured_at<>OLD.captured_at OR NEW.source<>OLD.source
    OR NEW.created_by<>OLD.created_by OR NEW.created_at<>OLD.created_at OR NEW.request_hash<>OLD.request_hash
    THEN RAISE EXCEPTION 'Document metadata is immutable'; END IF;
  IF OLD.encrypted_content IS NOT NULL AND (NEW.encrypted_content IS DISTINCT FROM OLD.encrypted_content
    OR NEW.sha256 IS DISTINCT FROM OLD.sha256 OR NEW.mime_type IS DISTINCT FROM OLD.mime_type
    OR NEW.byte_size IS DISTINCT FROM OLD.byte_size) THEN RAISE EXCEPTION 'Document content is immutable'; END IF;
  IF NEW.version<>OLD.version+1 THEN RAISE EXCEPTION 'Document version must advance'; END IF;
  RETURN NEW;
END; $$;
CREATE TRIGGER document_history BEFORE UPDATE OR DELETE ON documents
  FOR EACH ROW EXECUTE FUNCTION protect_document();
CREATE TABLE document_scans (
  id uuid PRIMARY KEY, clinic_id uuid NOT NULL, document_id uuid NOT NULL, state text NOT NULL,
  detail text NOT NULL, actor text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY(clinic_id,document_id) REFERENCES documents(clinic_id,id)
);
CREATE TRIGGER immutable_scans BEFORE UPDATE OR DELETE ON document_scans
  FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();
CREATE TABLE investigation_orders (
  id uuid PRIMARY KEY, clinic_id uuid NOT NULL, patient_id uuid NOT NULL, encounter_id uuid NOT NULL,
  test_name text NOT NULL, indication text NOT NULL,
  priority text NOT NULL CHECK(priority IN ('routine','urgent')),
  status text NOT NULL DEFAULT 'requested' CHECK(status IN ('requested','in_progress','completed','cancelled')),
  version integer NOT NULL DEFAULT 1, created_by text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  updated_by text NOT NULL, updated_at timestamptz NOT NULL DEFAULT now(), request_hash text NOT NULL,
  cancellation_reason text, UNIQUE(clinic_id,id),
  FOREIGN KEY(clinic_id,patient_id) REFERENCES patients(clinic_id,id),
  FOREIGN KEY(clinic_id,encounter_id) REFERENCES encounters(clinic_id,id)
);
CREATE FUNCTION protect_order() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Order deletion is prohibited'; END IF;
  IF OLD.status IN ('completed','cancelled') THEN RAISE EXCEPTION 'Final order is immutable'; END IF;
  IF NEW.id<>OLD.id OR NEW.clinic_id<>OLD.clinic_id OR NEW.patient_id<>OLD.patient_id
    OR NEW.encounter_id<>OLD.encounter_id OR NEW.test_name<>OLD.test_name OR NEW.indication<>OLD.indication
    OR NEW.priority<>OLD.priority OR NEW.created_by<>OLD.created_by OR NEW.created_at<>OLD.created_at
    OR NEW.request_hash<>OLD.request_hash THEN RAISE EXCEPTION 'Order identity is immutable'; END IF;
  IF NEW.version<>OLD.version+1 THEN RAISE EXCEPTION 'Order version must advance'; END IF;
  RETURN NEW;
END; $$;
CREATE TRIGGER order_history BEFORE UPDATE OR DELETE ON investigation_orders
  FOR EACH ROW EXECUTE FUNCTION protect_order();
CREATE TABLE investigation_results (
  id uuid PRIMARY KEY, clinic_id uuid NOT NULL, patient_id uuid NOT NULL, order_id uuid,
  document_id uuid, supersedes_id uuid, test_name text NOT NULL, collected_at timestamptz NOT NULL,
  value text NOT NULL, unit text NOT NULL, reference_range text NOT NULL, interpretation text NOT NULL,
  source text NOT NULL, reason text NOT NULL, created_by text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  request_hash text NOT NULL, UNIQUE(clinic_id,id),
  FOREIGN KEY(clinic_id,patient_id) REFERENCES patients(clinic_id,id),
  FOREIGN KEY(clinic_id,order_id) REFERENCES investigation_orders(clinic_id,id),
  FOREIGN KEY(clinic_id,document_id) REFERENCES documents(clinic_id,id),
  FOREIGN KEY(clinic_id,supersedes_id) REFERENCES investigation_results(clinic_id,id)
);
CREATE UNIQUE INDEX result_correction ON investigation_results(clinic_id,supersedes_id) WHERE supersedes_id IS NOT NULL;
CREATE INDEX results_patient ON investigation_results(clinic_id,patient_id,collected_at DESC,id);
CREATE TRIGGER immutable_results BEFORE UPDATE OR DELETE ON investigation_results
  FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();
