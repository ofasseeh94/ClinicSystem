# Documents and investigations workflow

## Attach a source report

1. Open the patient and confirm identity; select Documents.
2. Upload a PDF/PNG/JPEG with title, category, source and actual date; optionally select an encounter.
3. Wait for the recorded state: production-style ClamAV mode quarantines unavailable scans;
   development synthetic mode explicitly labels files as unscanned. Only released states can be viewed.
4. View/download through the authenticated controls. Review source and hash/attribution as needed.
5. Withdraw an incorrect document with a reason; upload a replacement as a new record. Do not overwrite history.

The sample attachment link contains only fictional demonstration text. Use it to try this unit.
Metadata remains visible for pending/rejected/withdrawn files. A failed upload may leave a pending
metadata slot; retry with unchanged fields/file or withdraw the slot.

## Track an investigation

1. Create an encounter first. In Investigations, request a test with indication and routine/urgent priority.
2. Mark it in progress if appropriate. This is internal tracking and does not send anything to a lab.
3. Record reported findings, optional units/reference range, actual collection time, source and reason.
   Link the order and released source attachment when available. External results may have no order.
4. Enter a staff interpretation only if appropriate; the system supplies no clinical interpretation.
5. Review the source and complete the order. At least one recorded result is required.
6. Correct transcription by appending a correction with a reason; the previous result stays visible as superseded.
7. Cancel an unfinished order with a reason when needed. Completed/cancelled orders remain immutable.

Registrar can handle attachments and read investigations; clinician/admin can write investigations.
The backend enforces these roles and patient/clinic link checks independently of the UI.
See [Unit 03 modification guide](../units/03-documents-investigations.md).
