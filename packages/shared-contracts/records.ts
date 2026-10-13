export interface DocumentRecord {
  id: string; patient_id: string; encounter_id: string | null; title: string;
  category: string; captured_at: string; source: string; state: string;
  mime_type: string | null; byte_size: number | null; sha256: string | null;
  scan_detail: string; version: number; created_by: string; created_at: string;
  withdrawal_reason: string | null;
}
export interface DocumentPage { items: DocumentRecord[]; total: number; page: number; scan_mode: string }
export interface InvestigationOrder {
  id: string; patient_id: string; encounter_id: string; test_name: string; indication: string;
  priority: string; status: string; version: number; created_by: string; created_at: string;
  updated_by: string; updated_at: string; cancellation_reason: string | null;
}
export interface InvestigationResult {
  id: string; patient_id: string; order_id: string | null; document_id: string | null;
  supersedes_id: string | null; corrected_by_id: string | null;
  test_name: string; collected_at: string; value: string; unit: string;
  reference_range: string; interpretation: string; source: string; reason: string;
  created_by: string; created_at: string;
}
export interface InvestigationPage {
  orders: InvestigationOrder[]; results: InvestigationResult[];
  orders_total: number; results_total: number; page: number;
}
