from __future__ import annotations

from pathlib import Path
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path = "config.yaml") -> dict:
    """加载配置。

    兼容从任意工作目录运行：相对路径会以项目根目录为基准解析。
    """
    p = Path(path)
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()

    with p.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_project_root"] = str(PROJECT_ROOT)
    return cfg
