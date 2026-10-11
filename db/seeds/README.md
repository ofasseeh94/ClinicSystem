# Synthetic data only

No automatic data is loaded into a new registry. Pytest's `tests/conftest.py` creates fictional
patient inputs and unique clinic scopes. Playwright creates a clearly named synthetic patient
through the real API. Integration tests require a separate PostgreSQL database ending in `_test`.
Never place real patient data in fixtures, screenshots, repository files or logs.
