# Registry contracts

`registry.ts` supplies explicit frontend data types. `openapi.json` is generated alongside
`docs/api/openapi.yaml` by `python scripts/export-openapi.py` from the application schema.
The contract test verifies both generated files match the backend. When changing a field,
update the shared TypeScript model and typecheck the frontend; do not assume this handwritten
TypeScript file is automatically regenerated from OpenAPI.
