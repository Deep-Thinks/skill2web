#!/usr/bin/env python3
"""
v0.1 → v0.2 IR migration (DESIGN-v0.2.md 附录 A)

用法:
  python3 skill/migrate_v01_to_v02.py <v0.1.json> <v0.2.json>

转换规则:
  ir_version 0.1 -> 0.2
  ir_kind 不变
  skill_meta / input_schema / browser_runtime / error_ux / attribution 不变
  static_assets.*  (top-level)               ->  render.static_assets.*
  llm_phase: { ... }                          ->  llm_pipeline: [ { id: "plan",
                                                                    uses: [],
                                                                    ...llm_phase } ]
  render_phase: { kind, iterator, per_item } ->  render: { iterator, per_item }
                                                  (kind 升 top-level ir_kind)
  render_phase.iterator "$.slides"           ->  render.iterator
                                                  "$.steps.plan.output.slides"
  其它 $.xxx 引用同上前缀
  llm_phase.user_prompt_template 中 Mustache {{key}} (input refs)
                                              ->  {{input.<key>}}
"""
import json
import re
import sys
from pathlib import Path
from typing import Any


def add_input_prefix(template: str, input_keys: set) -> str:
    """Rewrite {{<key>}} -> {{input.<key>}} for keys in input_keys.
    Leaves Mustache section blocks ({{#x}} {{/x}}) and dotted paths alone.
    """
    pattern = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
    def repl(m):
        k = m.group(1)
        if k in input_keys:
            return "{{input." + k + "}}"
        return m.group(0)
    return pattern.sub(repl, template)


def migrate(v01: dict) -> dict:
    if v01.get("ir_version") != "0.1":
        raise ValueError(f"expected ir_version=0.1, got {v01.get('ir_version')}")

    out: dict = {}
    out["_comment"] = (v01.get("_comment", "") +
        " | Migrated to v0.2 by skill/migrate_v01_to_v02.py per DESIGN-v0.2.md 附录 A.")
    out["ir_version"] = "0.2"
    out["ir_kind"] = v01["ir_kind"]

    # Untouched top-level fields
    for k in ("skill_meta", "input_schema", "browser_runtime", "error_ux", "attribution"):
        if k in v01:
            out[k] = v01[k]

    input_keys = {f["key"] for f in v01.get("input_schema", [])}

    # llm_phase -> llm_pipeline (single 'plan' step)
    lp = v01.get("llm_phase")
    if not lp:
        raise ValueError("llm_phase missing in v0.1 IR")
    plan = {
        "id": "plan",
        "uses": [],
        "model_hint": lp.get("model_hint"),
        "temperature": lp.get("temperature", 0.4),
        "json_mode": lp.get("json_mode", "prompt-only"),
        "system_prompt_template": lp.get("system_prompt_template", ""),
        "user_prompt_template": add_input_prefix(lp.get("user_prompt_template", ""), input_keys),
        "expected_output_schema": lp.get("expected_output_schema", {}),
    }
    out["llm_pipeline"] = [plan]

    # render_phase -> render (drop kind; rewrite iterator path)
    rp = v01.get("render_phase", {})
    new_render: dict = {}

    # static_assets moves under render
    if "static_assets" in v01:
        new_render["static_assets"] = v01["static_assets"]

    if "iterator" in rp:
        it = rp["iterator"]
        if it.startswith("$.") and not it.startswith("$.steps."):
            it = "$.steps.plan.output." + it[2:]
        new_render["iterator"] = it
    if "per_item" in rp:
        new_render["per_item"] = rp["per_item"]

    out["render"] = new_render
    return out


def cli():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    src = Path(sys.argv[1]); dst = Path(sys.argv[2])
    v01 = json.loads(src.read_text(encoding="utf-8"))
    v02 = migrate(v01)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(v02, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"migrated {src} -> {dst}")


if __name__ == "__main__":
    cli()
