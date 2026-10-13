# ADR-005 — source/version foundation before clinical drug calculations

Accepted for synthetic development, 2026-10-13. M4 remains partial.

No approved pediatric dose reference or independently validated clinical rules are present.
Build medication identity/source review and reported history now, while keeping calculation and
prescribing unavailable at the API as well as the UI. No medication recommendation or dose is invented.

Catalog records hold immutable source identity/formulation/strength/route text and reference title,
publisher, edition, jurisdiction, checked date and optional HTTPS citation. Changes append a catalog
version, rather than altering historical content. Review state uses an independent optimistic revision.
Qualified managed `clinical_reviewer` role plus a different author are required to verify identity;
synthetic sources and local development-key identities cannot approve. That state is explicitly
`verified_identity`, never approval of pediatric dosing, interactions or safety.

Reported medication use is a separate immutable statement with source, observation date/status and
optional reviewed catalog/encounter links. Corrections append, preserving previous values. Free-text
reported instructions are copied history, not an order, computation or clinician recommendation.

Capabilities return calculation/prescribing disabled. Authenticated attempts are blocked and audited
without storing clinical calculation inputs. There is no prescription table or dose rule seed in this step.
Later clinical engines need vetted licensed sources, pharmacist/clinical verification, concentration/unit
normalization, age/weight/allergy/renal/interaction rules, source versions and independently verified fixtures.

Public regulatory references have provenance limits: current DailyMed labeling can differ from the
last FDA-approved labeling; U.S. labeling does not establish Egyptian product availability or pediatric
off-label guidance. Source selection and jurisdiction review must precede import/clinical use.
References: [NLM DailyMed description](https://dailymed.nlm.nih.gov/dailymed/about-dailymed.cfm),
[FDA labeling resources](https://www.fda.gov/drugs/drug-approvals-and-databases/resources-information-approved-drugs).
No real product label or dose was imported in this step; source preference was requested from the user.
