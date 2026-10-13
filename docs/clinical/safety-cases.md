# Clinical safety cases

No clinical decisions are supported by this scaffold. Future hazard cases must cover unknown allergy states, stale weights, uncertain age, rule provenance, immutable signed records and clinician review.

Unit 04A checks: unauthenticated/unauthorized/cross-clinic access; self-review; synthetic-source approval;
local development-key approval; source URL credentials/schemes; overwritten catalog/history; branched
corrections; stale review revisions; and clinical operations remaining blocked after identity review.
Calculation/prescribing attempts return an explicit audited unavailable state and create no order.
These are software workflow checks, not clinical dose, maximum, allergy or interaction validation.
