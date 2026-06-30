from __future__ import annotations

import pytest


@pytest.fixture
def integration_placeholder() -> dict[str, str]:
    return {"status": "placeholder"}