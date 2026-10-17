export interface EncounterNote {
  history: string; examination: string; assessment: string; plan: string;
  allergy_review: 'not_reviewed' | 'reviewed'; medication_review: 'not_reviewed' | 'reviewed';
}
export interface Measurement {
  measured_at: string; weight_kg: number | null; length_cm: number | null; head_cm: number | null;
  position: 'recumbent' | 'standing' | 'unknown'; technique: string; equipment: string;
  source: 'clinic' | 'guardian_report' | 'external_record';
}
export interface Encounter {
  id: string; patient_id: string; occurred_at: string; reason: string; consent_context: string;
  birth_context: { dob: string; precision: string; source: string; patient_version: number; age_days: number | null };
  note: EncounterNote; measurements: Measurement[]; status: 'draft' | 'in_review' | 'signed' | 'cancelled';
  version: number; created_by: string; updated_by: string; created_at: string; updated_at: string;
  signed_by: string | null; signed_at: string | null; cancellation_reason: string | null;
  addenda: { id: string; reason: string; content: string; signed_by: string; signed_at: string }[];
}
export interface EncounterPage { items: Encounter[]; total: number; page: number }

/** POST encounters: initial note is committed with the draft; measurements use the revision endpoint. */
export interface EncounterCreate {
  request_id: string; occurred_at: string; reason: string; consent_context: string;
  note?: EncounterNote;
}
