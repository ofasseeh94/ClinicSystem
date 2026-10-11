export type DobPrecision = 'exact' | 'estimated' | 'month' | 'year';
export type GrowthSex = 'female' | 'male' | 'unknown';
export type AllergyStatus = 'unknown' | 'not_assessed' | 'no_known' | 'known';
export interface Guardian { name: string; phone_e164: string; relation: 'mother' | 'father' | 'guardian' | 'other' | 'unknown' }
export interface Allergy { substance: string; reaction: string }
export interface PatientInput {
  name_ar: string; name_en: string; dob: string; dob_precision: DobPrecision;
  dob_source: 'guardian' | 'document' | 'imported' | 'unknown'; growth_reference_sex: GrowthSex;
  guardian: Guardian; aliases: string[]; allergy_review_status: AllergyStatus; allergies: Allergy[];
}
export interface FormSubmission { form_key: string; version: number; answers: Record<string, unknown> }
export interface FormResponse extends FormSubmission { id: string; created_at: string; created_by: string; schema_definition: { title: string; fields: FormField[] } }
export interface PatientRecord extends PatientInput {
  patient_id: string; clinic_code: string; version: number; created_at: string; updated_at: string;
  created_by: string; updated_by: string; status: string; contact_authority: string;
  background_responses: FormResponse[]; warnings: string[];
}
export interface PatientSummary {
  patient_id: string; clinic_code: string; name_ar: string; name_en: string; dob: string;
  dob_precision: DobPrecision; growth_reference_sex: GrowthSex; allergy_review_status: AllergyStatus;
  guardian_name: string; masked_phone: string; version: number;
}
export interface SearchResponse { items: PatientSummary[]; total: number; page: number; page_size: number }
export interface FormField {
  key: string; label: string; type: 'text' | 'enum' | 'integer' | 'number';
  options?: string[]; min?: number; max?: number; max_length?: number; required?: boolean;
}
export interface FormDefinition { form_key: string; version: number; schema: { title: string; fields: FormField[] } }
export interface Session { actor_id: string; clinic_id: string; roles: string[]; environment: string }
export interface ApiProblem { title: string; detail: string; status: number; fields?: string[]; candidates?: PatientSummary[] }
