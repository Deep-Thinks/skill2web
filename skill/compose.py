#!/usr/bin/env python3
"""
skill2web composer (v0.3)

三步组装:
  1. 取 templates/skeleton.html 为骨架
  2. 按 ir.ir_kind 选 templates/blocks/<kind>.html, 替换 BLOCK:* 标记
  3. 按 ir.browser_runtime.{llm,image}_adapter 选 templates/adapters/*.js,
     inline 到 ADAPTER:LLM / ADAPTER:IMAGE 段
  4. 替换所有 {{IR.X.Y|filter}} placeholder

用法:
  python3 skill/compose.py <ir.json> <out.html>

实现遵守 KISS / YAGNI: 不做 schema 校验(那是 agent 的事),仅做机械组装。
"""
import json
import re
import sys
import html as html_mod
import urllib.parse as urlquote
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"


# ===== Filters =====================================================

def f_raw(v: Any) -> str:
    return "" if v is None else str(v)

def f_html(v: Any) -> str:
    return html_mod.escape("" if v is None else str(v), quote=True)

def f_attr(v: Any) -> str:
    # Same as html-escape for attribute use; caller wraps in quotes.
    return html_mod.escape("" if v is None else str(v), quote=True)

def f_url(v: Any) -> str:
    return html_mod.escape(urlquote.quote("" if v is None else str(v), safe=":/?#[]@!$&'()*+,;=%"), quote=True)

def f_js_string(v: Any) -> str:
    """Emit as JS template literal (backtick-wrapped). Escape backticks and ${}."""
    s = "" if v is None else str(v)
    s = s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    return "`" + s + "`"

def f_js_number(v: Any) -> str:
    if v is None:
        return "0"
    if isinstance(v, bool):
        return "1" if v else "0"
    return str(v)

def f_js_bool(v: Any) -> str:
    return "true" if bool(v) else "false"

def f_js_bool_non_null(v: Any) -> str:
    return "true" if v is not None and v != "" else "false"

def f_js_object(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, indent=2)

def f_js_array(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"))


# ===== Path lookup ==================================================

def lookup(ir: dict, path: str) -> Any:
    """path = 'IR.skill_meta.display_name' -> walk."""
    parts = path.split(".")
    assert parts[0] == "IR", f"internal: regex should ensure IR. prefix (got {path})"
    cur: Any = ir
    for p in parts[1:]:
        if cur is None:
            return None
        if isinstance(cur, list):
            try:
                cur = cur[int(p)]
            except (ValueError, IndexError):
                return None
        else:
            cur = cur.get(p)
    return cur


# ===== Special filters: render-form-fields, js-spec, js-pipeline ====

def render_form_fields(input_schema: list) -> str:
    rows = []
    for f in input_schema:
        key   = f["key"]
        ftype = f.get("type", "text")
        label = f.get("label", key)
        req   = bool(f.get("required"))
        ph    = f.get("placeholder", "")
        default = f.get("default", "")
        label_html = html_mod.escape(label) + (" *" if req else "")
        if ftype == "textarea":
            rows.append(
                f'<div class="form-row"><label>{label_html}</label>'
                f'<textarea id="input-{key}" placeholder="{html_mod.escape(ph)}">{html_mod.escape(str(default))}</textarea>'
                f'</div>'
            )
        elif ftype == "select":
            opts = []
            for opt in f.get("options", []):
                v = opt["value"]; lbl = opt.get("label", str(v))
                sel = " selected" if str(v) == str(default) else ""
                opts.append(f'<option value="{html_mod.escape(str(v))}"{sel}>{html_mod.escape(lbl)}</option>')
            rows.append(
                f'<div class="form-row"><label>{label_html}</label>'
                f'<select id="input-{key}">{"".join(opts)}</select></div>'
            )
        elif ftype == "number":
            rows.append(
                f'<div class="form-row"><label>{label_html}</label>'
                f'<input type="number" id="input-{key}" value="{html_mod.escape(str(default))}" placeholder="{html_mod.escape(ph)}">'
                f'</div>'
            )
        elif ftype.startswith("file:"):
            accept = ftype[len("file:"):]
            rows.append(
                f'<div class="form-row"><label>{label_html}</label>'
                f'<input type="file" id="input-{key}" accept="{html_mod.escape(accept)}">'
                f'</div>'
            )
        else:  # text
            rows.append(
                f'<div class="form-row"><label>{label_html}</label>'
                f'<input type="text" id="input-{key}" value="{html_mod.escape(str(default))}" placeholder="{html_mod.escape(ph)}">'
                f'</div>'
            )
    return "\n    ".join(rows)


def js_spec(input_schema: list) -> str:
    """Emit a compact JS array describing fields by key/required/type/label."""
    spec = [
        {
            "key": f["key"],
            "type": f.get("type", "text"),
            "label": f.get("label", f["key"]),
            "required": bool(f.get("required")),
        }
        for f in input_schema
    ]
    return json.dumps(spec, ensure_ascii=False)


def js_pipeline(pipeline: list) -> str:
    """Emit JS const for llm_pipeline.

    Each step's prompt template fields are kept as JS template literals so
    they render with Mustache-lite at run-time.

    v0.3: an optional `when` (structured branch condition) is emitted verbatim
    as a JS object. `uses` may carry multiple parents (static DAG fan-in).
    """
    parts = []
    for step in pipeline:
        sys_t = step.get("system_prompt_template", "")
        usr_t = step.get("user_prompt_template", "")
        obj_lines = [
            "  {",
            f'    id: {f_js_string(step["id"])},',
            f'    model_hint: {f_js_string(step.get("model_hint", ""))},',
            f'    temperature: {f_js_number(step.get("temperature", 0.4))},',
            f'    json_mode: {f_js_string(step.get("json_mode", "prompt-only"))},',
            f'    system_prompt_template: {f_js_string(sys_t)},',
            f'    user_prompt_template: {f_js_string(usr_t)},',
            f'    uses: {f_js_array(step.get("uses", []))},',
        ]
        if step.get("when") is not None:
            obj_lines.append(f'    when: {f_js_array(step["when"])},')
        obj_lines.append("  }")
        parts.append("\n".join(obj_lines))
    return "[\n" + ",\n".join(parts) + "\n]"


# ===== Block substitution ===========================================

BLOCK_RE = re.compile(r"<!--\s*(BLOCK:[A-Z_]+|ADAPTER:[A-Z_]+)\s*-->\s*(?:.*?)\s*<!--\s*\1_END\s*-->",
                      re.DOTALL)


def load_block_segments(block_path: Path) -> dict:
    """Parse a blocks/<kind>.html file into a {marker: content} dict."""
    if not block_path.exists():
        return {}
    text = block_path.read_text(encoding="utf-8")
    out = {}
    pattern = re.compile(r"<!--\s*(BLOCK:[A-Z_]+)\s*-->\s*\n?(.*?)\n?\s*<!--\s*\1_END\s*-->", re.DOTALL)
    for m in pattern.finditer(text):
        out[m.group(1)] = m.group(2)
    return out


def inject_blocks(html: str, segments: dict) -> str:
    def repl(m):
        marker = m.group(1)
        content = segments.get(marker, "")
        return f"<!-- {marker} -->\n{content}\n<!-- {marker}_END -->"
    pattern = re.compile(r"<!--\s*(BLOCK:[A-Z_]+)\s*-->\s*(?:.*?)\s*<!--\s*\1_END\s*-->", re.DOTALL)
    return pattern.sub(repl, html)


def inject_adapters(html: str, llm_adapter: str, image_adapter: str | None) -> str:
    llm_path = TEMPLATES / "adapters" / f"{llm_adapter}.js"
    if not llm_path.exists():
        raise FileNotFoundError(f"llm adapter not found: {llm_path}")
    llm_js = llm_path.read_text(encoding="utf-8")
    image_js = ""
    if image_adapter:
        img_path = TEMPLATES / "adapters" / f"{image_adapter}.js"
        if not img_path.exists():
            raise FileNotFoundError(f"image adapter not found: {img_path}")
        image_js = img_path.read_text(encoding="utf-8")

    def repl(m):
        marker = m.group(1)
        if marker == "ADAPTER:LLM":
            content = llm_js
        elif marker == "ADAPTER:IMAGE":
            content = image_js
        else:
            content = ""
        return f"<!-- {marker} -->\n{content}\n<!-- {marker}_END -->"
    pattern = re.compile(r"<!--\s*(ADAPTER:[A-Z_]+)\s*-->\s*(?:.*?)\s*<!--\s*\1_END\s*-->", re.DOTALL)
    return pattern.sub(repl, html)


# ===== Placeholder substitution =====================================

# Only match build-time placeholders: must start with `IR.`.
# Run-time {{key}} / {{steps.X.output.Y}} mustache-lite is left alone.
PLACEHOLDER_RE = re.compile(r"\{\{\s*(IR(?:\.[A-Za-z0-9_]+)+)(?:\|([a-z0-9-]+))?\s*\}\}")

FILTERS = {
    "raw": f_raw,
    "html": f_html,
    "attr": f_attr,
    "url": f_url,
    "js-string": f_js_string,
    "js-number": f_js_number,
    "js-bool": f_js_bool,
    "js-bool-non-null": f_js_bool_non_null,
    "js-object": f_js_object,
    "js-array": f_js_array,
}

SPECIAL_FILTERS = {
    "render-form-fields": lambda v: render_form_fields(v),
    "js-spec":            lambda v: js_spec(v),
    "js-pipeline":        lambda v: js_pipeline(v),
}


def substitute_placeholders(html: str, ir: dict) -> tuple[str, list]:
    warnings = []
    def repl(m):
        path = m.group(1); flt = m.group(2) or "html"
        val = lookup(ir, path)
        if val is None and flt not in ("js-bool-non-null", "js-bool", "raw"):
            warnings.append(f"placeholder unresolved: {path}|{flt}")
        if flt in SPECIAL_FILTERS:
            return SPECIAL_FILTERS[flt](val if val is not None else [])
        if flt not in FILTERS:
            warnings.append(f"unknown filter: {flt} (path={path})")
            return f_html(val)
        return FILTERS[flt](val)
    out = PLACEHOLDER_RE.sub(repl, html)
    return out, warnings


# ===== Main =========================================================

def compose(ir_path: Path, out_path: Path) -> None:
    ir = json.loads(ir_path.read_text(encoding="utf-8"))

    if ir.get("ir_version") not in ("0.2", "0.3"):
        raise ValueError(f"ir_version must be 0.2 or 0.3 (got {ir.get('ir_version')})")
    kind = ir.get("ir_kind")
    if not kind:
        raise ValueError("ir_kind missing")

    skel_path  = TEMPLATES / "skeleton.html"
    block_path = TEMPLATES / "blocks" / f"{kind}.html"

    html = skel_path.read_text(encoding="utf-8")
    segments = load_block_segments(block_path)
    if not segments:
        raise FileNotFoundError(f"no block segments found for ir_kind={kind} at {block_path}")

    html = inject_blocks(html, segments)

    br = ir.get("browser_runtime", {})
    html = inject_adapters(html, br.get("llm_adapter", "openai-chat-compat"),
                                 br.get("image_adapter"))

    html, warns = substitute_placeholders(html, ir)

    if warns:
        print("== composer warnings ==", file=sys.stderr)
        for w in warns:
            print("  - " + w, file=sys.stderr)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"composed {len(html)} bytes -> {out_path}")


def cli():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    compose(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    cli()
