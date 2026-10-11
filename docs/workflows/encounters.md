# Staff encounter workflow

1. Find the patient and confirm identity/contact context and the visible allergy banner.
2. Open Encounters, start a visit, enter actual local date/time, reason and consent context.
3. Enter history/examination/assessment/plan. Record allergy and medication review explicitly.
4. Add optional observations with date, kg/cm units, position, technique, equipment and source.
5. Save draft with a reason. Unsaved entries are held in memory only.
6. Submit for review with a reason. Return to draft for further changes.
7. Sign after review. Server requires complete sections/review acknowledgments; signing preserves
   the authenticated actor and immutable encounter snapshot.
8. Correct signed text by signing an addendum with a reason. Cancel only unsigned visits.
9. Reopen visits from the timeline. Reload after a concurrency conflict and reconcile before editing.

See [Unit 02](../units/02-encounters.md) for storage, modification and recovery details.
No medication orders, clinical calculations, attachment handling or verified consent administration exists.
