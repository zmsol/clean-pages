"""Command-line interface for leanmd."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from leanmd import converter

OUTPUT_DIR_NAME = "~/Documents/Books"


def _expand_inputs(paths: list[str]) -> list[Path]:
    supported = {".epub", ".pdf"}
    files: list[Path] = []
    for raw in paths:
        p = Path(raw).expanduser().resolve()
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.suffix.lower() in supported:
                    files.append(f)
        elif p.is_file():
            if p.suffix.lower() in supported:
                files.append(p)
            else:
                print(f"! Skipping unsupported file: {p}", file=sys.stderr)
        else:
            print(f"! Not found, skipping: {p}", file=sys.stderr)
    return files


def _output_path(input_path: Path, output_root: Path) -> Path:
    return output_root / (input_path.stem + ".md")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="leanmd", description="Convert EPUB and PDF files to Markdown.")
    parser.add_argument("inputs", nargs="+", help="EPUB/PDF files or directories (recursive).")
    parser.add_argument("-o", "--output", default=OUTPUT_DIR_NAME,
                        help="Output directory (default: ~/Documents/Books). Created if missing.")
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing .md files.")
    parser.add_argument("--keep-all", action="store_true",
                        help="Keep front/back matter. Default is MEAT-ONLY.")
    parser.add_argument("--keep-links", action="store_true", help="Keep hyperlinks/footnote refs.")
    args = parser.parse_args(argv)

    output_root = Path(args.output).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    files = _expand_inputs(args.inputs)
    if not files:
        print("No .epub or .pdf files found to convert.", file=sys.stderr)
        return 1

    print(f"Found {len(files)} file(s) to convert.")
    print(f"Output directory: {output_root}")
    print(f"Mode: {'meat-only' if not args.keep_all else 'keep-all'}"
          f"{' (links kept)' if args.keep_links else ''}\n")

    ok = skipped = failed = 0
    for f in files:
        out = _output_path(f, output_root)
        if out.exists() and not args.force:
            print(f"- Skip (exists): {f.name} -> {out.name}")
            skipped += 1
            continue
        try:
            md = converter.convert_to_markdown(f, meat=not args.keep_all, keep_links=args.keep_links)
        except Exception as exc:
            print(f"! Fail: {f.name} ({exc})", file=sys.stderr)
            failed += 1
            continue
        out.write_text(md, encoding="utf-8")
        words = len(md.split())
        print(f"+ Done: {out.name} ({len(md)} chars, {words} words)")
        ok += 1

    print("\nSummary:\n  converted: %d\n  skipped:   %d\n  failed:    %d" % (ok, skipped, failed))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
