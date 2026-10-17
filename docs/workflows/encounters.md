# Staff encounter workflow

1. Find the patient and confirm identity/contact context and the visible allergy banner.
2. Choose Register and start visit for a new patient, or Visit workspace → Start visit for an existing
   patient. Enter actual local date/time, chief complaint / visit reason and consent context.
3. Enter history/examination/provisional diagnosis / assessment/plan in that same form. Record allergy
   and medication review explicitly, then Create draft visit. The note is saved with the new visit.
4. Add optional observations with date, kg/cm units, position, technique, equipment and source.
5. Save draft with a reason. Unsaved entries are held in memory only.
6. Submit for review with a reason. Return to draft for further changes.
7. Sign after review. Server requires complete sections/review acknowledgments; signing preserves
   the authenticated actor and immutable encounter snapshot.
8. Correct signed text by signing an addendum with a reason. Cancel only unsigned visits.
9. Reopen visits from the timeline. Reload after a concurrency conflict and reconcile before editing.

See [Unit 02](../units/02-encounters.md) for storage, modification and recovery details.
No medication orders, clinical calculations or verified consent administration exists. Attachments and
investigations are available in their patient sections. Registration and visit creation are separate saves;
discarding an unsaved visit does not remove the registered patient.
