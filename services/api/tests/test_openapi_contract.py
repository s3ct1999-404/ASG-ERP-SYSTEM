"""The committed OpenAPI contract must match the code (no silent drift)."""

from pathlib import Path

from django.core.management import call_command

CONTRACT = Path(__file__).resolve().parents[3] / "docs" / "api" / "openapi.yaml"


def test_committed_openapi_matches_generated_schema(tmp_path: Path) -> None:
    generated = tmp_path / "openapi.yaml"
    call_command("spectacular", file=str(generated), validate=True)
    assert CONTRACT.exists(), (
        "docs/api/openapi.yaml is missing. Generate it with: "
        "python manage.py spectacular --validate --file ../../docs/api/openapi.yaml"
    )
    assert generated.read_text() == CONTRACT.read_text(), (
        "OpenAPI drift: regenerate with "
        "`python manage.py spectacular --validate --file ../../docs/api/openapi.yaml` "
        "and review the diff as an API contract change."
    )
