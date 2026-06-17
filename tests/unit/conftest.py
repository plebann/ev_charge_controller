from __future__ import annotations

from datetime import UTC, datetime

import pytest

from custom_components.ev_charge_controller.domain.models import TelemetrySnapshot


@pytest.fixture
def empty_snapshot() -> TelemetrySnapshot:
    return TelemetrySnapshot(timestamp=datetime.now(UTC))


@pytest.fixture(autouse=True)
def _allow_local_sockets(socket_enabled: None) -> None:
    return None
