"""Snapshot local del último envío, para calcular variación día a día del dólar
(dolarapi.com no expone histórico)."""
from __future__ import annotations

import json
from pathlib import Path

SNAPSHOT_PATH = Path(__file__).parent / "data" / "last_snapshot.json"


def load_previous() -> dict | None:
    if not SNAPSHOT_PATH.exists():
        return None
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def save_current(data: dict) -> None:
    SNAPSHOT_PATH.parent.mkdir(exist_ok=True)
    SNAPSHOT_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
