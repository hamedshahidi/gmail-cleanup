from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from gmail_cleanup.gmail import _app_data_dir


@dataclass(frozen=True)
class AppConfig:
    default_target_label: str = "cleanup/candidates"
    max_trash_without_force: int = 5000
    default_export_limit: int = 200
    default_scan_limit: int = 500
    default_sample: int = 10


def config_path() -> Path:
    return _app_data_dir() / "config.yaml"


def load_config() -> AppConfig:
    path = config_path()
    if not path.exists():
        return AppConfig()

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return AppConfig()

    return AppConfig(
        default_target_label=str(raw.get("default_target_label", "cleanup/candidates")),
        max_trash_without_force=int(raw.get("max_trash_without_force", 5000)),
        default_export_limit=int(raw.get("default_export_limit", 200)),
        default_scan_limit=int(raw.get("default_scan_limit", 500)),
        default_sample=int(raw.get("default_sample", 10)),
    )


def write_template(overwrite: bool = False) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return path

    data = {
        "default_target_label": "cleanup/candidates",
        "max_trash_without_force": 5000,
        "default_export_limit": 200,
        "default_scan_limit": 500,
        "default_sample": 10,
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path
