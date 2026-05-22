"""
High-level orchestration for the Europass-to-resume converter.

This module wires together:
- parse_candidate.py
- template.py
- map_resume.py

It does not:
- implement mapping rules directly;
- write output files;
- expose a CLI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .map_resume import MappingResult, map_candidate_to_resume
from .parse_candidate import (
    CandidateParseError,
    ParsedCandidate,
    parse_candidate_file,
    parse_candidate_xml,
)
from .template import TemplateError, load_template



class ConversionError(RuntimeError):
    """
    Raised when a conversion cannot be completed.

    The original exception is preserved as __cause__.
    """


@dataclass(frozen=True)
class ConversionResult:
    """
    Result of a complete conversion.

    parsed is optional and defaults to None because most callers only need the
    final resume and diagnostics. Development/test callers may opt into keeping
    the parsed representation.
    """

    resume: dict[str, Any]
    diagnostics: list[str] = field(default_factory=list)
    parsed: ParsedCandidate | None = None


def convert_files(
    xml_path: str | Path,
    template_path: str | Path,
    *,
    preferred_email: str | None = None,
    preferred_phone: str | None = None,
    preferred_website: str | None = None,
    include_parsed: bool = False,
    split_pages: bool = True,
) -> ConversionResult:
    """
    Convert a Europass Candidate XML file into app-compatible resume JSON.

    Args:
        xml_path:
            Path to the Europass Candidate XML file.

        template_path:
            Path to the app-compatible sample/template JSON file.

        preferred_email:
            Optional selected primary email.

        preferred_phone:
            Optional selected primary phone.

        preferred_website:
            Optional selected primary website.

        include_parsed:
            If true, include the ParsedCandidate object in the result.

    Returns:
        ConversionResult.
    """

    try:
        parsed = parse_candidate_file(xml_path)
        template = load_template(template_path)

        return convert_parsed(
            parsed,
            template,
            preferred_email=preferred_email,
            preferred_phone=preferred_phone,
            preferred_website=preferred_website,
            include_parsed=include_parsed,
            split_pages=split_pages,
        )
    except (CandidateParseError, TemplateError, OSError, ValueError) as exc:
        raise ConversionError(f"Could not convert files: {exc}") from exc


def convert_xml_string(
    xml: str | bytes,
    template: Mapping[str, Any],
    *,
    preferred_email: str | None = None,
    preferred_phone: str | None = None,
    preferred_website: str | None = None,
    include_parsed: bool = False,
    split_pages: bool = True,
) -> ConversionResult:
    """
    Convert an XML string/bytes object using an already-loaded template mapping.

    This is useful for tests, GUIs, and web backends.
    """

    try:
        parsed = parse_candidate_xml(xml)

        return convert_parsed(
            parsed,
            template,
            preferred_email=preferred_email,
            preferred_phone=preferred_phone,
            preferred_website=preferred_website,
            include_parsed=include_parsed,
            split_pages=split_pages,
        )
    except (CandidateParseError, TemplateError, ValueError) as exc:
        raise ConversionError(f"Could not convert XML string: {exc}") from exc


def convert_parsed(
    parsed: ParsedCandidate,
    template: Mapping[str, Any],
    *,
    preferred_email: str | None = None,
    preferred_phone: str | None = None,
    preferred_website: str | None = None,
    include_parsed: bool = False,
    split_pages: bool = True,
) -> ConversionResult:
    """
    Convert a ParsedCandidate using an already-loaded template mapping.
    """

    try:
        mapping_result: MappingResult = map_candidate_to_resume(
            parsed,
            template,
            preferred_email=preferred_email,
            preferred_phone=preferred_phone,
            preferred_website=preferred_website,
            split_pages=split_pages,
        )

        sanity_check_resume(mapping_result.resume)

        return ConversionResult(
            resume=mapping_result.resume,
            diagnostics=list(mapping_result.diagnostics),
            parsed=parsed if include_parsed else None,
        )
    except (TemplateError, ValueError, TypeError, KeyError) as exc:
        raise ConversionError(f"Could not map parsed candidate: {exc}") from exc


def sanity_check_resume(resume: Any) -> None:
    """
    Lightweight output sanity check.

    This is deliberately not strict JSON-schema validation. The target is
    sample/app-compatible output.
    """

    if not isinstance(resume, dict):
        raise ConversionError("Converted resume must be a JSON object.")

    missing = [
        key
        for key in ("basics", "sections", "metadata")
        if key not in resume
    ]

    if missing:
        raise ConversionError(
            "Converted resume is missing required root keys: "
            + ", ".join(missing)
        )

    if not isinstance(resume["basics"], dict):
        raise ConversionError("Converted resume key 'basics' must be an object.")

    if not isinstance(resume["sections"], dict):
        raise ConversionError("Converted resume key 'sections' must be an object.")

    if not isinstance(resume["metadata"], dict):
        raise ConversionError("Converted resume key 'metadata' must be an object.")


def resume_to_json(
    resume: Mapping[str, Any],
    *,
    indent: int = 2,
) -> str:
    """
    Serialise a converted resume to formatted JSON.

    This does not write files.
    """

    if not isinstance(resume, Mapping):
        raise ConversionError("Resume must be a JSON object before serialisation.")

    return json.dumps(
        resume,
        ensure_ascii=False,
        indent=indent,
    )


__all__ = [
    "ConversionError",
    "ConversionResult",
    "convert_files",
    "convert_xml_string",
    "convert_parsed",
    "sanity_check_resume",
    "resume_to_json",
]
