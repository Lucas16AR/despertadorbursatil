"""Snapshots locales del dólar, para calcular variaciones (dolarapi.com no expone histórico).

- `last_snapshot`: la corrida anterior — da la variación contra la tanda previa (cada envío).
- `inicio_dia`: la primera tanda del día (pre-apertura) — permite que la tanda de cierre muestre
  además la variación del día completo (pedido de Capi, 2026-07-09)."""
from __future__ import annotations

import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"
SNAPSHOT_PATH = _DATA_DIR / "last_snapshot.json"
INICIO_DIA_PATH = _DATA_DIR / "inicio_dia.json"


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_previous() -> dict | None:
    return _load(SNAPSHOT_PATH)


def save_current(data: dict) -> None:
    _save(SNAPSHOT_PATH, data)


def load_inicio_dia() -> dict | None:
    return _load(INICIO_DIA_PATH)


def save_inicio_dia(data: dict) -> None:
    _save(INICIO_DIA_PATH, data)
