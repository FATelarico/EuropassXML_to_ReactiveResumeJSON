"""
Template handling for the Europass-to-resume converter.

This module prepares an app-compatible Reactive Resume-style JSON object by
cloning a sample/template JSON file, clearing existing CV content, and
preserving non-content rendering/default fields.

It does not:
- parse XML;
- map Europass content;
- generate item IDs;
- write final JSON output.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping


class TemplateError(ValueError):
    """Raised when the resume template is not usable."""


STANDARD_SECTIONS: tuple[str, ...] = (
    "profiles",
    "experience",
    "education",
    "projects",
    "skills",
    "languages",
    "interests",
    "awards",
    "certifications",
    "publications",
    "volunteer",
    "references",
)

DEFAULT_TEMPLATE = "rhyhorn"

DEFAULT_METADATA: dict[str, Any] = {
    "template": DEFAULT_TEMPLATE,
    "layout": {
        "sidebarWidth": 30,
        "pages": [],
    },
    "css": {
        "enabled": False,
        "value": "",
    },
    "page": {
        "gapX": 4,
        "gapY": 8,
        "marginX": 16,
        "marginY": 14,
        "format": "a4",
        "locale": "en-US",
        "hideIcons": False,
    },
    "design": {
        "level": {
            "icon": "acorn",
            "type": "circle",
        },
        "colors": {
            "primary": "rgba(0, 132, 209, 1)",
            "text": "rgba(0, 0, 0, 1)",
            "background": "rgba(255, 255, 255, 1)",
        },
    },
    "typography": {
        "body": {
            "fontFamily": "IBM Plex Serif",
            "fontWeights": ["400", "600"],
            "fontSize": 11,
            "lineHeight": 1.5,
        },
        "heading": {
            "fontFamily": "Fira Sans Condensed",
            "fontWeights": ["500"],
            "fontSize": 18,
            "lineHeight": 1.5,
        },
    },
    "notes": "",
}


def load_template(path: str | Path) -> dict[str, Any]:
    """
    Load a resume template JSON file.

    Args:
        path:
            Path to a sample/app-compatible JSON template.

    Returns:
        Template dictionary.

    Raises:
        TemplateError:
            If the file cannot be decoded as a JSON object.
    """

    template_path = Path(path)

    try:
        with template_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise TemplateError(f"Template is not valid JSON: {template_path}") from exc
    except OSError as exc:
        raise TemplateError(f"Could not read template file: {template_path}") from exc

    if not isinstance(data, dict):
        raise TemplateError("Template root must be a JSON object.")

    return data


def prepare_resume_template(template: Mapping[str, Any]) -> dict[str, Any]:
    """
    Return a deep-copied, content-cleared app-compatible resume template.

    The input object is never mutated.
    """

    if not isinstance(template, Mapping):
        raise TemplateError("Template root must be a JSON object.")

    resume = copy.deepcopy(dict(template))

    ensure_root_shape(resume)
    clear_picture_content(resume)
    clear_basics_content(resume)
    clear_summary_content(resume)
    clear_sections_content(resume)
    clear_custom_sections(resume)
    ensure_metadata_defaults(resume)
    clear_layout_pages(resume)

    return resume


def ensure_root_shape(resume: dict[str, Any]) -> None:
    """
    Ensure the minimum app-compatible root structure exists.

    Unknown root-level keys are preserved.
    """

    resume.setdefault("picture", {})
    resume.setdefault("basics", {})
    resume.setdefault("summary", {})
    resume.setdefault("sections", {})
    resume.setdefault("customSections", [])
    resume.setdefault("metadata", {})

    if not isinstance(resume["picture"], dict):
        resume["picture"] = {}

    if not isinstance(resume["basics"], dict):
        resume["basics"] = {}

    if not isinstance(resume["summary"], dict):
        resume["summary"] = {}

    if not isinstance(resume["sections"], dict):
        resume["sections"] = {}

    if not isinstance(resume["customSections"], list):
        resume["customSections"] = []

    if not isinstance(resume["metadata"], dict):
        resume["metadata"] = {}


def clear_picture_content(resume: dict[str, Any]) -> None:
    """
    Clear picture content while preserving picture styling.

    The sample's picture.hidden value is preserved.
    """

    picture = resume.setdefault("picture", {})

    if not isinstance(picture, dict):
        resume["picture"] = picture = {}

    picture.setdefault("hidden", False)
    picture.setdefault("size", 100)
    picture.setdefault("rotation", 0)
    picture.setdefault("aspectRatio", 1)
    picture.setdefault("borderRadius", 0)
    picture.setdefault("borderColor", "rgba(0, 0, 0, 0.5)")
    picture.setdefault("borderWidth", 0)
    picture.setdefault("shadowColor", "rgba(0, 0, 0, 0.5)")
    picture.setdefault("shadowWidth", 0)

    picture["url"] = ""


def clear_basics_content(resume: dict[str, Any]) -> None:
    """
    Clear content-bearing basics fields.

    The basics.website shape is kept as the sample/app-compatible form:
    {"url": "", "label": ""}.
    """

    basics = resume.setdefault("basics", {})

    if not isinstance(basics, dict):
        resume["basics"] = basics = {}

    basics["name"] = ""
    basics["headline"] = ""
    basics["email"] = ""
    basics["phone"] = ""
    basics["location"] = ""
    basics["website"] = empty_website()
    basics["customFields"] = []


def clear_summary_content(resume: dict[str, Any]) -> None:
    """
    Clear summary content while preserving wrapper defaults.
    """

    summary = resume.setdefault("summary", {})

    if not isinstance(summary, dict):
        resume["summary"] = summary = {}

    summary.setdefault("title", "")
    summary.setdefault("columns", 1)
    summary.setdefault("hidden", False)
    summary["content"] = ""


def clear_sections_content(resume: dict[str, Any]) -> None:
    """
    Ensure standard sections exist and clear all section item arrays.

    Unknown sections are preserved, but if they contain an items array, it is
    cleared because it is content-bearing.
    """

    sections = resume.setdefault("sections", {})

    if not isinstance(sections, dict):
        resume["sections"] = sections = {}

    for section_id in STANDARD_SECTIONS:
        existing = sections.get(section_id)

        if not isinstance(existing, dict):
            sections[section_id] = empty_section()
        else:
            sections[section_id] = normalise_section_wrapper(existing)

        sections[section_id]["items"] = []

    for section_id, section in list(sections.items()):
        if section_id in STANDARD_SECTIONS:
            continue

        if isinstance(section, dict) and isinstance(section.get("items"), list):
            section["items"] = []


def clear_custom_sections(resume: dict[str, Any]) -> None:
    """
    Remove content-bearing custom sections from the sample/template.
    """

    resume["customSections"] = []


def ensure_metadata_defaults(resume: dict[str, Any]) -> None:
    """
    Ensure app-compatible metadata exists.

    Existing metadata is preserved wherever present. Missing fields are filled
    from app-compatible defaults.
    """

    metadata = resume.setdefault("metadata", {})

    if not isinstance(metadata, dict):
        resume["metadata"] = metadata = {}

    merge_missing(metadata, DEFAULT_METADATA)

    layout = metadata.setdefault("layout", {})
    if not isinstance(layout, dict):
        metadata["layout"] = layout = {}

    layout.setdefault("sidebarWidth", DEFAULT_METADATA["layout"]["sidebarWidth"])
    layout.setdefault("pages", [])


def clear_layout_pages(resume: dict[str, Any]) -> None:
    """
    Clear metadata.layout.pages while preserving metadata.layout.sidebarWidth.
    """

    metadata = resume.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        resume["metadata"] = metadata = {}

    layout = metadata.setdefault("layout", {})
    if not isinstance(layout, dict):
        metadata["layout"] = layout = {}

    layout.setdefault("sidebarWidth", DEFAULT_METADATA["layout"]["sidebarWidth"])
    layout["pages"] = []


def set_layout_pages(
    resume: dict[str, Any],
    pages: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Set metadata.layout.pages and return the modified resume.

    This helper mutates the supplied resume object intentionally. It is intended
    for use after prepare_resume_template().
    """

    if not isinstance(resume, dict):
        raise TemplateError("Resume must be a JSON object.")

    metadata = resume.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        resume["metadata"] = metadata = {}

    layout = metadata.setdefault("layout", {})
    if not isinstance(layout, dict):
        metadata["layout"] = layout = {}

    layout.setdefault("sidebarWidth", DEFAULT_METADATA["layout"]["sidebarWidth"])
    layout["pages"] = copy.deepcopy(pages)

    return resume


def empty_website() -> dict[str, str]:
    """
    Return the sample/app-compatible empty website shape.

    Do not add inlineLink here; the selected target is sample/app-compatible,
    not strict-schema-compatible.
    """

    return {
        "url": "",
        "label": "",
    }


def empty_section(
    title: str = "",
    columns: int = 1,
    hidden: bool = False,
) -> dict[str, Any]:
    """
    Return an empty predefined section wrapper.
    """

    return {
        "title": title,
        "columns": columns,
        "hidden": hidden,
        "items": [],
    }


def normalise_section_wrapper(section: Mapping[str, Any]) -> dict[str, Any]:
    """
    Preserve title/columns/hidden where present, and clear items separately.
    """

    return {
        "title": section.get("title", ""),
        "columns": section.get("columns", 1),
        "hidden": section.get("hidden", False),
        "items": [],
    }


def empty_picture_from_template(template: Mapping[str, Any]) -> dict[str, Any]:
    """
    Return a picture object with the template styling but no image URL.
    """

    if not isinstance(template, Mapping):
        return {
            "hidden": False,
            "url": "",
            "size": 100,
            "rotation": 0,
            "aspectRatio": 1,
            "borderRadius": 0,
            "borderColor": "rgba(0, 0, 0, 0.5)",
            "borderWidth": 0,
            "shadowColor": "rgba(0, 0, 0, 0.5)",
            "shadowWidth": 0,
        }

    source = template.get("picture", {})
    if not isinstance(source, Mapping):
        source = {}

    picture = copy.deepcopy(dict(source))
    picture.setdefault("hidden", False)
    picture.setdefault("size", 100)
    picture.setdefault("rotation", 0)
    picture.setdefault("aspectRatio", 1)
    picture.setdefault("borderRadius", 0)
    picture.setdefault("borderColor", "rgba(0, 0, 0, 0.5)")
    picture.setdefault("borderWidth", 0)
    picture.setdefault("shadowColor", "rgba(0, 0, 0, 0.5)")
    picture.setdefault("shadowWidth", 0)
    picture["url"] = ""

    return picture


def custom_section_base(
    title: str,
    section_type: str,
    *,
    section_id: str = "",
    columns: int = 1,
    hidden: bool = False,
) -> dict[str, Any]:
    """
    Return an app-compatible custom section wrapper.

    The caller may supply section_id after generating it in map_resume.py.
    """

    return {
        "title": title,
        "columns": columns,
        "hidden": hidden,
        "id": section_id,
        "type": section_type,
        "items": [],
    }


def merge_missing(target: dict[str, Any], defaults: Mapping[str, Any]) -> None:
    """
    Recursively copy missing keys from defaults into target.

    Existing values are preserved. If an existing value has the wrong type for a
    nested dictionary, it is left unchanged except where later normalisation
    functions require a dictionary.
    """

    for key, default_value in defaults.items():
        if key not in target:
            target[key] = copy.deepcopy(default_value)
            continue

        current_value = target[key]

        if isinstance(current_value, dict) and isinstance(default_value, Mapping):
            merge_missing(current_value, default_value)


__all__ = [
    "TemplateError",
    "STANDARD_SECTIONS",
    "DEFAULT_TEMPLATE",
    "DEFAULT_METADATA",
    "load_template",
    "prepare_resume_template",
    "ensure_root_shape",
    "clear_picture_content",
    "clear_basics_content",
    "clear_summary_content",
    "clear_sections_content",
    "clear_custom_sections",
    "ensure_metadata_defaults",
    "clear_layout_pages",
    "set_layout_pages",
    "empty_website",
    "empty_section",
    "normalise_section_wrapper",
    "empty_picture_from_template",
    "custom_section_base",
    "merge_missing",
]