"""
Command-line interface for the Europass-to-resume converter.

Usage:

    python -m europass_converter.cli input.xml --template sample.json --output resume.json

or, when running as a flat script:

    python cli.py input.xml --template sample.json --output resume.json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import traceback
from pathlib import Path
from typing import Any

from .version import __version__
from .converter import ConversionError, convert_files, resume_to_json


EXIT_SUCCESS = 0
EXIT_CONVERSION_ERROR = 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="europass-convert",
        description=(
            "Convert a Europass Candidate XML file into app-compatible "
            "Reactive Resume-style JSON."
        ),
    )

    parser.add_argument(
        "xml_path",
        help="Path to the Europass Candidate XML file.",
    )

    parser.add_argument(
        "--no-split-pages",
        action="store_true",
        help=(
            "Put all content into a single metadata.layout.pages entry. "
            "This prevents converter-level page splitting, but the rendering app "
            "may still paginate visually if content overflows."
        ),
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--template",
        required=True,
        help="Path to the app-compatible sample/template JSON file.",
    )

    parser.add_argument(
        "--output",
        help=(
            "Path to write the converted JSON. If omitted, JSON is written "
            "to stdout."
        ),
    )

    parser.add_argument(
        "--preferred-email",
        help="Preferred primary email address, if several are found.",
    )

    parser.add_argument(
        "--preferred-phone",
        help="Preferred primary phone number, if several are found.",
    )

    parser.add_argument(
        "--preferred-website",
        help="Preferred primary website, if several are found.",
    )

    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level. Default: 2.",
    )

    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write compact single-line JSON. Overrides --indent.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        type=int,
        choices=(0, 1, 2),
        default=0,
        help=(
            "Verbosity level: 0 suppresses diagnostics, 1 prints diagnostics "
            "when present, 2 also prints a success summary. Default: 0."
        ),
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print a full traceback on conversion errors.",
    )

    parser.add_argument(
        "--debug-parsed",
        action="store_true",
        help=(
            "Print the parsed intermediate representation to stderr. "
            "Development/debugging option."
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = convert_files(
            args.xml_path,
            args.template,
            preferred_email=args.preferred_email,
            preferred_phone=args.preferred_phone,
            preferred_website=args.preferred_website,
            include_parsed=args.debug_parsed,
            split_pages=not args.no_split_pages,
        )

        output = serialise_resume(
            result.resume,
            compact=args.compact,
            indent=args.indent,
        )

        write_output(output, args.output)

        if args.debug_parsed and result.parsed is not None:
            print_debug_parsed(result.parsed)

        print_diagnostics(
            diagnostics=result.diagnostics,
            verbose=args.verbose,
            output_path=args.output,
        )

        return EXIT_SUCCESS

    except ConversionError as exc:
        print_error(exc, debug=args.debug)
        return EXIT_CONVERSION_ERROR

    except OSError as exc:
        print_error(exc, debug=args.debug)
        return EXIT_CONVERSION_ERROR


def serialise_resume(
    resume: dict[str, Any],
    *,
    compact: bool,
    indent: int,
) -> str:
    if compact:
        return json.dumps(
            resume,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    return resume_to_json(resume, indent=indent)


def write_output(output: str, output_path: str | None) -> None:
    if not output_path:
        sys.stdout.write(output)
        sys.stdout.write("\n")
        return

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output + "\n", encoding="utf-8")


def print_diagnostics(
    *,
    diagnostics: list[str],
    verbose: int,
    output_path: str | None,
) -> None:
    if verbose <= 0:
        return

    if diagnostics:
        print("Diagnostics:", file=sys.stderr)
        for diagnostic in diagnostics:
            print(f"- {diagnostic}", file=sys.stderr)

    if verbose >= 2:
        if output_path:
            print(f"Conversion completed: {output_path}", file=sys.stderr)
        else:
            print("Conversion completed: JSON written to stdout.", file=sys.stderr)


def print_error(exc: BaseException, *, debug: bool) -> None:
    if debug:
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
        return

    print(f"Error: {exc}", file=sys.stderr)


def print_debug_parsed(parsed: Any) -> None:
    print("Parsed intermediate representation:", file=sys.stderr)
    print(
        json.dumps(
            make_json_safe(parsed),
            ensure_ascii=False,
            indent=2,
        ),
        file=sys.stderr,
    )


def make_json_safe(value: Any) -> Any:
    """
    Convert dataclasses and common non-JSON values into a debug-printable form.

    This is intentionally for diagnostics only. It is not part of the conversion
    output format.
    """

    if dataclasses.is_dataclass(value):
        return {
            field.name: make_json_safe(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set, frozenset)):
        return [make_json_safe(item) for item in value]

    if isinstance(value, bytes):
        return f"<bytes {len(value)}>"

    if isinstance(value, Path):
        return str(value)

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    return repr(value)


if __name__ == "__main__":
    raise SystemExit(main())
