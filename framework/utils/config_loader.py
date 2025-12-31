from __future__ import annotations

from pathlib import Path
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path = "config.yaml") -> dict:
    """Author: taobo.zhou
    中文：加载 YAML 配置文件并返回字典。
    参数:
        path: 配置文件路径，支持相对路径。
    """

    p = Path(path)
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()

    with p.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_project_root"] = str(PROJECT_ROOT)
    return cfg
