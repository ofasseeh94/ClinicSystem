-- Append a new version; existing definitions and responses remain unchanged.
INSERT INTO form_definitions(form_key,version,schema)
SELECT form_key,2,jsonb_set(schema,'{fields}',schema->'fields' || '[
 {"key":"birth.ventilation","label":"Neonatal ventilation","type":"enum","options":["yes","no","unknown","not_recorded"]}
]'::jsonb) FROM form_definitions WHERE form_key='background' AND version=1;
