"""Check the repository foundation without third-party dependencies."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "docs/units/01-patient-registry.md",
    "db/migrations/001_registry.sql",
    "db/migrations/002_background_v2.sql",
    "services/api/src/clinic_api/registry/routes.py",
    "apps/web/src/PatientForm.tsx",
    "tests/e2e/registry.spec.ts",
    "packages/shared-contracts/openapi.json",
    "README.md",
    "AGENTS.md",
    "docs/build-journal.md",
    "docs/design/README.md",
    "docs/design/Pediatric_Clinic_Engineering_Master_Spec_v1.md",
    ".env.example",
    "docs/00-index.md",
    "docs/architecture/adr/001-stack.md",
    "docs/api/openapi.yaml",
    "apps/web/package.json",
    "services/api/pyproject.toml",
    "packages/shared-contracts",
    "packages/clinical-rules",
    "db/migrations",
    "db/seeds",
    "tests/unit",
    "tests/integration",
    "tests/e2e",
    "tests/security",
    "tests/clinical",
    "infrastructure/compose.yaml",
    ".github/workflows/ci.yml",
)


def missing_paths():
    return [path for path in REQUIRED if not (ROOT / path).exists()]


if __name__ == "__main__":
    missing = missing_paths()
    if missing:
        raise SystemExit("Missing paths: " + ", ".join(missing))
    print("Repository structure check passed.")
