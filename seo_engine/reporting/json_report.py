import json
from pathlib import Path


def write_json_report(result: dict, path: str):
    Path(path).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
