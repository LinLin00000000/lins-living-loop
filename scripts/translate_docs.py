#!/usr/bin/env python3
"""Translate Lin's Living Loop Chinese Markdown docs to English using an OpenAI-compatible API.

Secrets are read from environment variables. For legacy/private compatibility,
--secret-file may load an env file explicitly, but no project-specific env file
is read by default. The script never prints API key values.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SECRET_FILE: Path | None = None
DEFAULT_TARGET_LANG = "English"
DEFAULT_TARGET_CODE = "en"
# Match the aios-kit default scope: README plus public docs/ pages.
# SKILL.md, CHANGELOG.md, references/, and templates/ are not Chinese source
# docs in this repo and should not be auto-translated as public zh->en docs.
SOURCE_FILES = [Path("README.md")]
SOURCE_GLOBS = ["docs/*.md"]
GENERATED_MARKER = "<!-- AUTO-GENERATED FILE. DO NOT EDIT. -->"

SYSTEM_PROMPT = """You are a careful technical documentation translator.
Translate Simplified Chinese Markdown documentation for Lin's Living Loop into natural, concise English.
Preserve Markdown structure, frontmatter keys, code fences, inline code, links, HTML comments, tables, and command examples.
Do not add new sections. Do not remove content. Translate prose only.
Keep product names (Lin's Living Loop, LLL, DOP), file paths, command names, JSON keys, and code identifiers unchanged unless they are natural-language labels.
""".strip()


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
            value = value[1:-1]
        value = value.replace("'\\''", "'")
        os.environ.setdefault(key, value)


def require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def api_config() -> dict[str, str]:
    return {
        "base_url": require_env("TRANSLATE_BASE_URL").rstrip("/"),
        "api_key": require_env("TRANSLATE_API_KEY"),
        "model": require_env("TRANSLATE_MODEL"),
        "api_mode": os.environ.get("TRANSLATE_API_MODE", "chat_completions").strip().lower() or "chat_completions",
    }


def request_json(url: str, api_key: str, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            return json.loads(text)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"API HTTP {exc.code} from {url}: {detail}") from exc


def extract_response_text(data: dict[str, Any]) -> str:
    if isinstance(data.get("output_text"), str):
        return data["output_text"].strip()
    output = data.get("output")
    if isinstance(output, list):
        parts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, dict):
                        text = c.get("text") or c.get("content")
                        if isinstance(text, str):
                            parts.append(text)
            elif isinstance(content, str):
                parts.append(content)
        if parts:
            return "\n".join(parts).strip()
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        msg = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = msg.get("content")
        if isinstance(content, str):
            return content.strip()
    raise RuntimeError(f"Could not extract text from API response keys: {sorted(data.keys())}")


def call_model(prompt: str, user_text: str, cfg: dict[str, str]) -> str:
    mode = cfg["api_mode"]
    if mode in {"responses", "codex_responses", "openai_responses"}:
        url = cfg["base_url"] + "/responses"
        payload = {
            "model": cfg["model"],
            "input": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_text},
            ],
        }
    else:
        url = cfg["base_url"] + "/chat/completions"
        payload = {
            "model": cfg["model"],
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_text},
            ],
            "temperature": 0.2,
        }
    return extract_response_text(request_json(url, cfg["api_key"], payload))


def source_files() -> list[Path]:
    files = [ROOT / p for p in SOURCE_FILES if (ROOT / p).exists()]
    for pattern in SOURCE_GLOBS:
        files.extend(sorted(ROOT.glob(pattern)))
    return [p for p in files if p.is_file() and not any(part in {"en", "translations"} for part in p.relative_to(ROOT).parts)]


def resolve_only_sources(values: list[str]) -> list[Path]:
    allowed = {p.relative_to(ROOT) for p in source_files()}
    resolved: list[Path] = []
    errors: list[str] = []
    for raw in values:
        rel = Path(raw)
        if rel.is_absolute() or ".." in rel.parts:
            errors.append(f"unsafe path: {raw}")
            continue
        if rel not in allowed:
            errors.append(f"not a translatable source doc: {raw}")
            continue
        resolved.append(ROOT / rel)
    if errors:
        raise SystemExit("Invalid --only values:\n- " + "\n- ".join(errors))
    # Keep deterministic source order and drop duplicates.
    requested = set(resolved)
    return [p for p in source_files() if p in requested]


def target_path(source: Path, target_code: str) -> Path:
    rel = source.relative_to(ROOT)
    if rel == Path("README.md"):
        return ROOT / "translations" / target_code / "README.md"
    return ROOT / "translations" / target_code / rel


def source_link_for(source: Path, target_code: str) -> str:
    """Return the source-side link to the generated translation."""
    rel = os.path.relpath(target_path(source, target_code), source.parent).replace(os.sep, "/")
    if source.parent == ROOT and not rel.startswith(("./", "../")):
        return "./" + rel
    return rel


def chinese_link_for(target: Path, target_code: str) -> str:
    rel = target.relative_to(ROOT)
    if rel == Path("translations") / target_code / "README.md":
        return "../../README.md"
    if len(rel.parts) >= 2 and rel.parts[:2] == ("translations", target_code):
        source_rel = Path(*rel.parts[2:])
        return os.path.relpath(ROOT / source_rel, target.parent).replace(os.sep, "/")
    return "../../README.md"


def generated_header(target: Path, target_code: str, target_lang: str) -> str:
    zh = chinese_link_for(target, target_code)
    return f"{GENERATED_MARKER}\n\n[简体中文]({zh}) | **{target_lang}**\n\n> This file is automatically generated from the Chinese source. Please edit the Chinese source file instead.\n\n"


SOURCE_SWITCH_RE = re.compile(
    r"\n?(?:"
    r"\*\*简体中文\*\*\s*\|\s*\[English\]\([^)]*\)"
    r"|\[(?:中文|简体中文)\]\([^)]*\)\s*\|\s*\[English\]\([^)]*\)"
    r")\n+",
    re.I,
)


def strip_source_language_switch(text: str) -> str:
    # Source files may have a language switch near the top. Generated files get
    # their own header, so translating the source switch would create duplicates.
    return SOURCE_SWITCH_RE.sub("\n", text, count=1)


def source_language_switch(source: Path, target_code: str, target_lang: str) -> str:
    return f"**简体中文** | [{target_lang}]({source_link_for(source, target_code)})"


def add_or_update_source_language_switch(text: str, source: Path, target_code: str, target_lang: str) -> str:
    """Place the aios-kit-style source language switch after the first H1."""
    stripped = strip_source_language_switch(text).strip() + "\n"
    lines = stripped.splitlines()
    insert_at = 0

    # Preserve YAML frontmatter at the top if a future public doc uses it.
    if lines and lines[0] == "---":
        for idx in range(1, len(lines)):
            if lines[idx] == "---":
                insert_at = idx + 1
                break

    for idx in range(insert_at, len(lines)):
        if lines[idx].startswith("# "):
            insert_at = idx + 1
            break

    switch = source_language_switch(source, target_code, target_lang)
    lines[insert_at:insert_at] = ["", switch]
    return "\n".join(lines).strip() + "\n"


def strip_translated_language_switch(text: str) -> str:
    text = re.sub(r"\n?\[Chinese\]\([^)]*\)\s*\|\s*\[English\]\([^)]*\)\n+", "\n", text, count=1, flags=re.I)
    return re.sub(r"\n?\*\*(?:Simplified Chinese|Chinese|简体中文)\*\*\s*\|\s*\[English\]\([^)]*\)\n+", "\n", text, count=1, flags=re.I)


def rewrite_markdown_links(translated: str, source: Path, target: Path, target_code: str) -> str:
    """Rewrite links to source Markdown files so generated English docs stay in translations/en.

    Each generated file header already links back to the Simplified Chinese source.
    Body links between docs should point to generated English counterparts when available.
    """
    known_sources = {p.resolve(): target_path(p, target_code) for p in source_files()}

    def repl(match: re.Match[str]) -> str:
        label, url = match.group(1), match.group(2)
        if re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I) or url.startswith(("#", "/")):
            return match.group(0)
        path_part, sep, fragment = url.partition("#")
        if not path_part.endswith(".md"):
            return match.group(0)
        source_target = (source.parent / path_part).resolve()
        generated = known_sources.get(source_target)
        if not generated:
            return match.group(0)
        rel = os.path.relpath(generated, target.parent).replace(os.sep, "/")
        if sep:
            rel = rel + "#" + fragment
        return f"[{label}]({rel})"

    return re.sub(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)", repl, translated)


def strip_existing_generated_header(text: str) -> str:
    if not text.startswith(GENERATED_MARKER):
        return text
    # Remove marker plus the small generated notice block up to the first blank line after blockquote.
    lines = text.splitlines()
    idx = 1
    while idx < len(lines) and idx < 8:
        idx += 1
        if idx >= 4 and idx < len(lines) and lines[idx - 1] == "" and not lines[idx:idx+1]:
            break
    # Simpler robust path: remove fixed notice if present.
    joined = "\n".join(lines)
    m = re.search(r"^<!-- AUTO-GENERATED FILE\. DO NOT EDIT\. -->\n\n.*?edit the Chinese source file instead\.\n\n", joined, re.S)
    return joined[m.end():] if m else text


def translate_file(source: Path, cfg: dict[str, str], target_code: str, target_lang: str) -> tuple[Path, str]:
    original = strip_source_language_switch(source.read_text(encoding="utf-8"))
    rel = source.relative_to(ROOT).as_posix()
    user = f"Translate this Markdown file to {target_lang}. File path: {rel}\n\n{original}"
    translated = call_model(SYSTEM_PROMPT, user, cfg)
    target = target_path(source, target_code)
    translated = strip_existing_generated_header(translated).strip() + "\n"
    translated = strip_translated_language_switch(translated).strip() + "\n"
    translated = rewrite_markdown_links(translated, source, target, target_code).strip() + "\n"
    return target, generated_header(target, target_code, target_lang) + translated


def write_if_changed(path: Path, content: str) -> bool:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def check_api(cfg: dict[str, str]) -> None:
    text = call_model(
        "You are a health-check endpoint for a documentation translation workflow. Reply with exactly: ok",
        "Reply with exactly: ok",
        cfg,
    )
    normalized = re.sub(r"[^a-z]", "", text.lower())
    if "ok" not in normalized:
        raise RuntimeError(f"Unexpected API health-check response shape: {text[:80]!r}")
    host_hint = re.sub(r"//([^/@:]+)(:[0-9]+)?", r"//<host>\2", cfg["base_url"])
    print("API check passed")
    print(f"- base_url_host_hint: {host_hint}")
    print(f"- model: {cfg['model']}")
    print(f"- api_mode: {cfg['api_mode']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--secret-file", type=Path, default=DEFAULT_SECRET_FILE, help="optional legacy/private env file to load before reading TRANSLATE_* from the environment")
    parser.add_argument("--target-code", default=DEFAULT_TARGET_CODE)
    parser.add_argument("--target-language", default=DEFAULT_TARGET_LANG)
    parser.add_argument("--check-api", action="store_true")
    parser.add_argument("--write", action="store_true", help="write translated files")
    parser.add_argument("--dry-run", action="store_true", help="show planned files without calling translation for all files")
    parser.add_argument("--sync-source-switches", action="store_true", help="add or update source-side language switches for planned docs without calling the API")
    parser.add_argument("--limit", type=int, default=0, help="limit number of files translated; useful for smoke tests")
    parser.add_argument("--only", action="append", default=[], help="relative source path to translate; may be repeated")
    args = parser.parse_args()

    if args.secret_file:
        load_env_file(args.secret_file)

    files = source_files()
    if args.only:
        files = resolve_only_sources(args.only)
    if args.limit:
        files = files[: args.limit]

    planned = [(p, target_path(p, args.target_code)) for p in files]
    print(f"Translation source files: {len(planned)}")
    for src, dst in planned:
        print(f"- {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")

    if args.dry_run and not args.write and not args.sync_source_switches:
        if args.check_api:
            cfg = api_config()
            check_api(cfg)
        return 0

    if args.sync_source_switches:
        changed = 0
        for src in files:
            content = add_or_update_source_language_switch(src.read_text(encoding="utf-8"), src, args.target_code, args.target_language)
            if write_if_changed(src, content):
                changed += 1
                print(f"  updated source switch {src.relative_to(ROOT)}")
            else:
                print(f"  source switch unchanged {src.relative_to(ROOT)}")
        print(f"Source language switch sync complete: changed_files={changed}")
        if not args.write:
            if args.check_api:
                cfg = api_config()
                check_api(cfg)
            return 0

    cfg = api_config()
    if args.check_api:
        check_api(cfg)
    if not args.write:
        print("No files written. Pass --write to generate translations.")
        return 0

    changed = 0
    started = time.time()
    for idx, src in enumerate(files, 1):
        print(f"Translating {idx}/{len(files)}: {src.relative_to(ROOT)}")
        dst, content = translate_file(src, cfg, args.target_code, args.target_language)
        if write_if_changed(dst, content):
            changed += 1
            print(f"  wrote {dst.relative_to(ROOT)}")
        else:
            print(f"  unchanged {dst.relative_to(ROOT)}")
    print(f"Translation complete: changed_files={changed}, elapsed_seconds={time.time() - started:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
