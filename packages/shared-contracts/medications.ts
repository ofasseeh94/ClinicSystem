export interface CatalogEntry {
  request_id:string; id:string; catalog_id:string; version:number; revision:number; state:string;
  product_name:string; generic_name:string; formulation:string; strength_text:string; route_text:string;
  source_kind:string; source_title:string; source_publisher:string; source_version:string; source_url:string;
  source_country:string; source_checked_on:string; created_by:string; created_at:string;
  reviewed_by:string|null; reviewed_at:string|null; review_reason:string|null;
}
export interface MedicationStatement {
  request_id:string; id:string; patient_id:string; encounter_id:string|null; catalog_version_id:string|null;
  supersedes_id:string|null; corrected_by_id:string|null; medication_name:string;
  reported_instructions:string; use_status:string; recorded_for:string; source:string; reason:string;
  created_by:string; created_at:string;
}
export interface MedicationCapabilities {
  dose_calculation_enabled:boolean; prescribing_enabled:boolean; verification_scope:string; prerequisites:string[];
}
export interface CatalogPage {items:CatalogEntry[];total:number;page:number}
export interface MedicationPage {items:MedicationStatement[];total:number;page:number}
