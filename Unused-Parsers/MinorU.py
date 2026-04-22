"""
Run MinerU (OpenDataLab ``mineru``) on a PDF and collect Markdown output under an output folder.

MinerU 3.x does **not** expose ``mineru.partition``; parsing is done via the ``mineru`` CLI
(``python -m mineru.cli.client``), same as ``mineru -p … -o …``.

Environment:
  MINERU_SOURCE           — path to PDF (or image dir); default: Holiday 2026.pdf or first *.pdf in cwd
  MINERU_OUTPUT_DIR       — optional output parent directory; default: ``{stem}_extracted_mineru`` under the process cwd
  MINERU_BACKEND          — pipeline | vlm-http-client | hybrid-http-client | vlm-auto-engine | hybrid-auto-engine
                            (default: hybrid-auto-engine)
  MINERU_METHOD           — auto | txt | ocr (default: auto)
  MINERU_LANG             — e.g. ch, en (default: ch)
  MINERU_START            — start page index (0-based), passed as -s
  MINERU_END              — end page index (0-based), passed as -e
  MINERU_API_URL          — optional MinerU FastAPI base URL (else CLI may start a local API)
  MINERU_SERVER_URL       — for *-http-client backends, passed as -u
  MINERU_FORMULA          — 0 to disable formula parsing (-f false)
  MINERU_TABLE            — 0 to disable table parsing (-t false)
  MINERU_EXTRA_ARGS       — extra CLI tokens (space-separated, quoted carefully in shell)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

_BACKENDS = frozenset(
    {
        "pipeline",
        "vlm-http-client",
        "hybrid-http-client",
        "vlm-auto-engine",
        "hybrid-auto-engine",
    }
)
_METHODS = frozenset({"auto", "txt", "ocr"})


def _pick_pdf(cwd: Path) -> Path:
    pdf = cwd / "meta.pdf"
    if pdf.exists():
        return pdf
    matches = sorted(cwd.glob("*.pdf"))
    if not matches:
        raise FileNotFoundError(
            "No PDF found. Set MINERU_SOURCE or add a .pdf in the current working directory."
        )
    return matches[0]


def _resolve_source(runtime_cwd: Path) -> Path:
    raw = os.environ.get("MINERU_SOURCE", "").strip()
    if raw:
        p = Path(raw).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"MINERU_SOURCE not found: {p}")
        return p
    return _pick_pdf(runtime_cwd)


def _env_choice(name: str, default: str, allowed: frozenset[str]) -> str:
    raw = os.environ.get(name, default).strip()
    if raw not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}; got {raw!r}")
    return raw


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw not in ("0", "false", "no")


def _extra_cli_args() -> list[str]:
    raw = os.environ.get("MINERU_EXTRA_ARGS", "").strip()
    if not raw:
        return []
    return re.split(r"\s+", raw)


def _find_markdown_files(root: Path) -> list[Path]:
    return sorted(root.glob("**/*.md"))


def main() -> None:
    # Use process cwd so FastAPI/subprocess callers (cwd=temp dir) read/write there,
    # not next to this script. Matches MINERU_SOURCE / docstring ("*.pdf in cwd").
    runtime_cwd = Path.cwd()
    source = _resolve_source(runtime_cwd)
    stem = source.stem

    out_raw = os.environ.get("MINERU_OUTPUT_DIR", "").strip()
    out_root = (
        Path(out_raw).expanduser()
        if out_raw
        else (runtime_cwd / f"{stem}_extracted_mineru")
    )
    out_root.mkdir(parents=True, exist_ok=True)

    backend = _env_choice("MINERU_BACKEND", "hybrid-auto-engine", _BACKENDS)
    method = _env_choice("MINERU_METHOD", "auto", _METHODS)
    lang = os.environ.get("MINERU_LANG", "ch").strip() or "ch"

    cmd: list[str] = [
        sys.executable,
        "-m",
        "mineru.cli.client",
        "-p",
        str(source),
        "-o",
        str(out_root),
        "-b",
        backend,
        "-m",
        method,
        "-l",
        lang,
        "-f",
        str(_env_bool("MINERU_FORMULA", True)),
        "-t",
        str(_env_bool("MINERU_TABLE", True)),
    ]

    start_s = os.environ.get("MINERU_START", "").strip()
    if start_s:
        cmd.extend(["-s", start_s])
    end_s = os.environ.get("MINERU_END", "").strip()
    if end_s:
        cmd.extend(["-e", end_s])

    api_url = os.environ.get("MINERU_API_URL", "").strip()
    if api_url:
        cmd.extend(["--api-url", api_url])
    server_url = os.environ.get("MINERU_SERVER_URL", "").strip()
    if server_url:
        cmd.extend(["-u", server_url])

    cmd.extend(_extra_cli_args())

    print(
        f"MinerU: {source.name} → {out_root} (backend={backend}, method={method}) …",
        file=sys.stderr,
    )
    print(f"[DEBUG] source={source}", file=sys.stderr)
    print(f"[DEBUG] out_root={out_root}", file=sys.stderr)
    print(f"[DEBUG] backend={backend} method={method} lang={lang}", file=sys.stderr)
    print(f"[DEBUG] api_url={api_url or '(none)'}", file=sys.stderr)
    print(f"[DEBUG] server_url={server_url or '(none)'}", file=sys.stderr)
    print(f"[DEBUG] cmd={' '.join(cmd)}", file=sys.stderr)

    t0 = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    assert proc.stdout is not None
    for line in proc.stdout:
        stdout_lines.append(line)
        print(f"[mineru][stdout] {line.rstrip()}", file=sys.stderr)

    assert proc.stderr is not None
    for line in proc.stderr:
        stderr_lines.append(line)
        print(f"[mineru][stderr] {line.rstrip()}", file=sys.stderr)

    returncode = proc.wait()
    elapsed = time.perf_counter() - t0
    stdout_text = "".join(stdout_lines)
    stderr_text = "".join(stderr_lines)
    print(
        f"[DEBUG] returncode={returncode} elapsed={elapsed:.2f}s",
        file=sys.stderr,
    )

    md_files = _find_markdown_files(out_root)
    combined = "\n\n".join(
        f"<!-- {p.relative_to(out_root)} -->\n\n{p.read_text(encoding='utf-8', errors='replace')}"
        for p in md_files
    )
    extracted = out_root / "extracted.md"
    if combined.strip():
        extracted.write_text(combined, encoding="utf-8")
    else:
        extracted.write_text(
            "(No .md files found under output tree; see mineru stderr.)\n",
            encoding="utf-8",
        )

    result_json = out_root / "result.json"
    payload = {
        "source": str(source),
        "output_dir": str(out_root),
        "command": cmd,
        "returncode": returncode,
        "seconds": round(elapsed, 3),
        "markdown_files": [str(p.relative_to(out_root)) for p in md_files],
        "stdout_tail": stdout_text[-8000:],
        "stderr_tail": stderr_text[-8000:],
    }
    result_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = out_root / "summary.txt"
    summary.write_text(
        "\n".join(
            [
                "--- MinerU (mineru CLI) summary ---",
                f"Source: {source}",
                f"Output: {out_root}",
                f"Backend: {backend} (MINERU_BACKEND)",
                f"Method: {method} | Lang: {lang}",
                f"Return code: {proc.returncode}",
                f"Time: {elapsed:.2f} s",
                f"Markdown files found: {len(md_files)}",
                f"Aggregated MD: {extracted.name}",
                f"Run metadata: {result_json.name}",
                "",
                "CLI: python -m mineru.cli.client (see `mineru --help`).",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Wrote: {extracted}")
    print(f"Wrote: {result_json}")
    print(f"Wrote: {summary}")

    if returncode != 0:
        print(
            stderr_text or stdout_text or "(no output)",
            file=sys.stderr,
        )
        raise SystemExit(returncode)


if __name__ == "__main__":
    main()
