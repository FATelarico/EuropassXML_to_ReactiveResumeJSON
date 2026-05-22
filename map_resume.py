"""
Map parsed Europass Candidate content into app-compatible resume JSON.

This module is the first layer that knows both sides:
- ParsedCandidate from parse_candidate.py
- app-compatible Reactive Resume-style JSON based on sample.json

It does not parse XML and does not write files.
"""

from __future__ import annotations

import copy
import html
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None  # type: ignore[assignment]

try:
    from .contacts import (
        ContactSelection,
        WebsiteCandidate,
        label_from_url,
        normalise_url_for_link,
        select_contacts,
    )
    from .languages import compress_language_level
    from .parse_candidate import (
        Address,
        AttachmentData,
        CodeLabel,
        ConferenceSeminar,
        Course,
        DateRange,
        EducationExperience,
        LanguageCompetency,
        OtherBlock,
        ParsedCandidate,
        ParsedDate,
        PublicationGroup,
        UnhandledBlock,
        WorkExperience,
    )
    from .sanitize_html import sanitize_html
    from .template import (
        custom_section_base,
        empty_website,
        prepare_resume_template,
        set_layout_pages,
    )
except ImportError:  # pragma: no cover - useful when running as flat scripts
    from contacts import (
        ContactSelection,
        WebsiteCandidate,
        label_from_url,
        normalise_url_for_link,
        select_contacts,
    )
    from languages import compress_language_level
    from parse_candidate import (
        Address,
        AttachmentData,
        CodeLabel,
        ConferenceSeminar,
        Course,
        DateRange,
        EducationExperience,
        LanguageCompetency,
        OtherBlock,
        ParsedCandidate,
        ParsedDate,
        PublicationGroup,
        UnhandledBlock,
        WorkExperience,
    )
    from sanitize_html import sanitize_html
    from template import (
        custom_section_base,
        empty_website,
        prepare_resume_template,
        set_layout_pages,
    )


@dataclass(frozen=True)
class MappingResult:
    """
    Result of mapping a parsed Europass Candidate into resume JSON.
    """

    resume: dict[str, Any]
    diagnostics: list[str] = field(default_factory=list)


def map_candidate_to_resume(
    parsed: ParsedCandidate,
    template: Mapping[str, Any],
    *,
    preferred_email: str | None = None,
    preferred_phone: str | None = None,
    preferred_website: str | None = None,
    split_pages: bool = True,
) -> MappingResult:
    """
    Convert ParsedCandidate into app-compatible resume JSON.

    Args:
        parsed:
            Parsed Europass Candidate object from parse_candidate.py.

        template:
            Raw sample/app-compatible resume JSON template. This function calls
            prepare_resume_template() internally.

        preferred_email:
            Optional future CLI/UI-selected primary email.

        preferred_phone:
            Optional future CLI/UI-selected primary phone.

        preferred_website:
            Optional future CLI/UI-selected primary website.

    Returns:
        MappingResult containing the resume dict and diagnostics.
    """

    resume = prepare_resume_template(template)
    diagnostics: list[str] = list(parsed.diagnostics)

    contacts = select_contacts(
        parsed.contacts,
        preferred_email=preferred_email,
        preferred_phone=preferred_phone,
        preferred_website=preferred_website,
    )
    diagnostics.extend(contacts.diagnostics)

    map_picture(resume, parsed.attachments)
    map_basics(resume, parsed, contacts)
    map_summary(resume, parsed)
    map_profiles(resume, contacts)
    map_experience(resume, parsed.work_experiences)
    map_education(resume, parsed.education)
    map_certifications(resume, parsed.courses)
    map_publications_and_custom_sections(resume, parsed.publication_groups)
    map_conferences(resume, parsed.conferences_seminars)
    map_other_blocks(resume, parsed.other_blocks)
    map_languages(resume, parsed.languages)
    map_references_placeholder(resume)
    map_unhandled_blocks(resume, parsed.unhandled_blocks)

    rebuild_layout(resume, split_pages=split_pages)

    return MappingResult(resume=resume, diagnostics=diagnostics)


def new_id() -> str:
    return str(uuid.uuid4())


def map_picture(resume: dict[str, Any], attachments: list[AttachmentData]) -> None:
    picture = resume.setdefault("picture", {})

    if not isinstance(picture, dict):
        resume["picture"] = picture = {}

    photo_url = ""

    for attachment in attachments:
        if not is_photo_attachment(attachment):
            continue

        if attachment.data_uri:
            photo_url = attachment.data_uri
            break

        if attachment.mime_type and attachment.payload_base64:
            photo_url = f"data:{attachment.mime_type};base64,{attachment.payload_base64}"
            break

    if photo_url:
        picture["url"] = photo_url
        picture["hidden"] = False
    else:
        picture["url"] = ""
        picture["hidden"] = True


def is_photo_attachment(attachment: AttachmentData) -> bool:
    markers = " ".join(
        [
            attachment.file_type,
            attachment.instructions,
            attachment.mime_type,
        ]
    ).lower()

    return (
        "photo" in markers
        or "picture" in markers
        or attachment.mime_type.startswith("image/")
        or attachment.data_uri.startswith("data:image/")
    )


def map_basics(
    resume: dict[str, Any],
    parsed: ParsedCandidate,
    contacts: ContactSelection,
) -> None:
    basics = resume.setdefault("basics", {})

    if not isinstance(basics, dict):
        resume["basics"] = basics = {}

    basics["name"] = choose_name(parsed)
    basics["headline"] = choose_headline(parsed)
    basics["email"] = contacts.primary_email
    basics["phone"] = contacts.primary_phone
    basics["location"] = choose_location(parsed)

    if contacts.primary_website is not None:
        basics["website"] = website_object(
            contacts.primary_website.url,
            contacts.primary_website.label,
        )
    else:
        basics["website"] = empty_website()

    custom_fields: list[dict[str, Any]] = []

    for field in contacts.custom_fields:
        custom_fields.append(
            {
                "id": new_id(),
                "icon": field.icon,
                "text": field.text,
                "link": field.link,
            }
        )

    for sensitive_field in sensitive_personal_fields(parsed):
        custom_fields.append(sensitive_field)

    basics["customFields"] = custom_fields


def choose_name(parsed: ParsedCandidate) -> str:
    identity = parsed.identity

    if identity.full_name:
        return identity.full_name

    return " ".join(
        part for part in [identity.given_name, identity.family_name] if part
    ).strip()


def choose_headline(parsed: ParsedCandidate) -> str:
    for item in parsed.work_experiences:
        position = item.position.strip()
        organisation = item.organisation.strip()

        if position and organisation:
            return f"{position} at {organisation}"

        if position:
            return position

        if organisation:
            return organisation

    return ""


def choose_location(parsed: ParsedCandidate) -> str:
    if not parsed.addresses:
        return ""

    address = parsed.addresses[0]
    country = code_label_display(address.country)

    parts = [part for part in [address.city, country] if part]
    return ", ".join(parts)


def sensitive_personal_fields(parsed: ParsedCandidate) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []

    nationality = parsed.identity.nationality
    if nationality is not None:
        value = code_label_display(nationality)
        if value:
            fields.append(
                {
                    "id": new_id(),
                    "icon": "",
                    "text": f"Nationality: {value}",
                    "link": "",
                }
            )

    birth_date = parsed.identity.birth_date
    if birth_date is not None:
        label = format_birth_date_label(birth_date)
        if label:
            fields.append(
                {
                    "id": new_id(),
                    "icon": "",
                    "text": label,
                    "link": "",
                }
            )

    return fields


def format_birth_date_label(date: ParsedDate) -> str:
    if not date.raw:
        return ""

    if date.precision == "day" and date.year and date.month and date.day:
        return f"Birth date: {date.year:04d}-{date.month:02d}-{date.day:02d}"

    if date.precision == "month" and date.year and date.month:
        return f"Birth date: {date.year:04d}-{date.month:02d}"

    if date.precision == "year" and date.year:
        return f"Birth year: {date.year:04d}"

    return f"Birth date: {date.raw}"


def map_summary(resume: dict[str, Any], parsed: ParsedCandidate) -> None:
    resume["summary"]["content"] = sanitize_html(parsed.summary)


def map_profiles(resume: dict[str, Any], contacts: ContactSelection) -> None:
    items: list[dict[str, Any]] = []

    for profile in contacts.profiles:
        items.append(
            {
                "id": new_id(),
                "hidden": False,
                "icon": profile.icon,
                "iconColor": "",
                "network": profile.network,
                "username": profile.username,
                "website": website_object(
                    profile.website.url,
                    profile.website.label,
                ),
            }
        )

    resume["sections"]["profiles"]["items"] = items


def map_experience(
    resume: dict[str, Any],
    work_experiences: list[WorkExperience],
) -> None:
    items: list[dict[str, Any]] = []

    for work in work_experiences:
        if not work.organisation and not work.position:
            continue

        items.append(
            {
                "id": new_id(),
                "hidden": False,
                "company": work.organisation,
                "position": work.position,
                "location": work_location(work),
                "period": format_date_range(work.date_range),
                "website": first_link_website(work.links),
                "description": sanitize_html(work.description),
                "roles": [],
            }
        )

    resume["sections"]["experience"]["items"] = items


def work_location(work: WorkExperience) -> str:
    country = code_label_display(work.country)

    if work.city or country:
        return ", ".join(part for part in [work.city, country] if part)

    if work.address is not None:
        address_country = code_label_display(work.address.country)
        return ", ".join(
            part for part in [work.address.city, address_country] if part
        )

    return ""


def map_education(
    resume: dict[str, Any],
    education_items: list[EducationExperience],
) -> None:
    items: list[dict[str, Any]] = []

    for education in education_items:
        if not education.organisation and not education.degree:
            continue

        items.append(
            {
                "id": new_id(),
                "hidden": False,
                "school": education.organisation,
                "degree": education.degree,
                "area": "",
                "grade": education.grade,
                "location": education_location(education),
                "period": format_date_range(education.date_range),
                "website": first_link_website(education.links),
                "description": build_education_description(education),
            }
        )

    resume["sections"]["education"]["items"] = items


def education_location(education: EducationExperience) -> str:
    if education.address is None:
        return ""

    country = code_label_display(education.address.country)
    return ", ".join(part for part in [education.address.city, country] if part)


def build_education_description(education: EducationExperience) -> str:
    parts: list[str] = []

    description = sanitize_html(education.description)
    if description:
        parts.append(description)

    if education.thesis:
        parts.append(sanitize_html(f"Thesis: {education.thesis}"))

    credits = format_credits(education)
    if credits:
        parts.append(sanitize_html(f"Credits: {credits}"))

    return "".join(parts)


def format_credits(education: EducationExperience) -> str:
    if not education.credits and not education.credit_type:
        return ""

    return " ".join(
        part for part in [education.credits, education.credit_type] if part
    ).strip()


def map_certifications(resume: dict[str, Any], courses: list[Course]) -> None:
    items: list[dict[str, Any]] = []

    for course in courses:
        if not course.title:
            continue

        items.append(
            {
                "id": new_id(),
                "hidden": False,
                "title": course.title,
                "issuer": "",
                "date": format_date_range(course.date_range),
                "website": first_link_website(course.links),
                "description": sanitize_html(course.description),
            }
        )

    resume["sections"]["certifications"]["items"] = items


def map_publications_and_custom_sections(
    resume: dict[str, Any],
    publication_groups: list[PublicationGroup],
) -> None:
    publication_items: list[dict[str, Any]] = []
    grouped_items: list[dict[str, Any]] = []

    for group in publication_groups:
        if not group.group_title and not group.description:
            continue

        split_items = split_publication_group(group)

        if split_items:
            publication_items.extend(split_items)
            continue

        content = build_grouped_publication_content(group)
        if content:
            grouped_items.append(
                {
                    "id": new_id(),
                    "hidden": False,
                    "content": content,
                }
            )

    resume["sections"]["publications"]["items"] = publication_items

    if grouped_items:
        section = custom_section_base(
            "Publications",
            "summary",
            section_id=new_id(),
        )
        section["items"] = grouped_items
        resume["customSections"].append(section)


def split_publication_group(group: PublicationGroup) -> list[dict[str, Any]]:
    """
    Split only obvious HTML list items into publication records.

    This deliberately avoids citation parsing. If no clear <li> structure is
    present, grouped publication content is preserved as a custom summary
    section instead.
    """

    if BeautifulSoup is None:
        return []

    description = sanitize_html(group.description)
    if not description:
        return []

    soup = BeautifulSoup(description, "html.parser")
    list_items = soup.find_all("li")

    if not list_items:
        return []

    result: list[dict[str, Any]] = []

    for list_item in list_items:
        text = list_item.get_text(" ", strip=True)
        if not text:
            continue

        item_html = sanitize_html(str(list_item))
        title = truncate_title(text)

        result.append(
            {
                "id": new_id(),
                "hidden": False,
                "title": title,
                "publisher": "",
                "date": "",
                "website": empty_website(),
                "description": item_html,
            }
        )

    return result


def build_grouped_publication_content(group: PublicationGroup) -> str:
    parts: list[str] = []

    if group.group_title:
        parts.append(f"<p><strong>{escape_text(group.group_title)}</strong></p>")

    description = sanitize_html(group.description)
    if description:
        parts.append(description)

    if group.links:
        parts.append(links_as_html(group.links))

    return "".join(parts)


def map_conferences(
    resume: dict[str, Any],
    conferences: list[ConferenceSeminar],
) -> None:
    items: list[dict[str, Any]] = []

    for conference in conferences:
        if not conference.title:
            continue

        description_parts: list[str] = []

        if conference.description:
            description_parts.append(sanitize_html(conference.description))

        if conference.location:
            description_parts.append(sanitize_html(f"Location: {conference.location}"))

        items.append(
            {
                "id": new_id(),
                "hidden": False,
                "name": conference.title,
                "period": format_date_range(conference.date_range),
                "website": first_link_website(conference.links or [conference.link]),
                "description": "".join(description_parts),
            }
        )

    if not items:
        return

    section = custom_section_base(
        "Conferences and seminars",
        "projects",
        section_id=new_id(),
    )
    section["items"] = items
    resume["customSections"].append(section)


def map_other_blocks(
    resume: dict[str, Any],
    other_blocks: list[OtherBlock],
) -> None:
    items: list[dict[str, Any]] = []

    for block in other_blocks:
        content = build_other_block_content(block)
        if not content:
            continue

        items.append(
            {
                "id": new_id(),
                "hidden": False,
                "content": content,
            }
        )

    if not items:
        return

    section = custom_section_base(
        "Additional information",
        "summary",
        section_id=new_id(),
    )
    section["items"] = items
    resume["customSections"].append(section)


def build_other_block_content(block: OtherBlock) -> str:
    parts: list[str] = []

    title_parts = [part for part in [block.section_title, block.item_title] if part]
    if title_parts:
        parts.append(
            f"<p><strong>{escape_text(' - '.join(title_parts))}</strong></p>"
        )

    period = format_date_range(block.date_range)
    if period:
        parts.append(sanitize_html(period))

    description = sanitize_html(block.description)
    if description:
        parts.append(description)

    if block.links:
        parts.append(links_as_html(block.links))

    return "".join(parts)


def map_languages(
    resume: dict[str, Any],
    languages: list[LanguageCompetency],
) -> None:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    for language in languages:
        name = language_name(language)
        if not name:
            continue

        key = name.casefold()

        if key in seen:
            # Native languages are parsed before foreign languages, so native
            # entries naturally win.
            continue

        seen.add(key)

        compressed = compress_language_level(
            language.scores,
            native=language.is_native,
            declared_fluency="Native" if language.is_native else None,
        )

        items.append(
            {
                "id": new_id(),
                "hidden": False,
                "language": name,
                "fluency": compressed.fluency,
                "level": compressed.level,
            }
        )

    resume["sections"]["languages"]["items"] = items


def language_name(language: LanguageCompetency) -> str:
    value = code_label_display(language.language)
    return value


def map_references_placeholder(resume: dict[str, Any]) -> None:
    resume["sections"]["references"]["items"] = [
        {
            "id": new_id(),
            "hidden": False,
            "name": "Available upon request",
            "position": "",
            "website": empty_website(),
            "phone": "",
            "description": "",
        }
    ]


def map_unhandled_blocks(
    resume: dict[str, Any],
    unhandled_blocks: list[UnhandledBlock],
) -> None:
    items: list[dict[str, Any]] = []

    for block in unhandled_blocks:
        content = build_unhandled_block_content(block)
        if not content:
            continue

        items.append(
            {
                "id": new_id(),
                "hidden": False,
                "content": content,
            }
        )

    if not items:
        return

    section = custom_section_base(
        "Unhandled Europass content",
        "summary",
        section_id=new_id(),
    )
    section["items"] = items
    resume["customSections"].append(section)


def build_unhandled_block_content(block: UnhandledBlock) -> str:
    parts: list[str] = []

    title = block.title or block.path
    if title:
        parts.append(f"<p><strong>{escape_text(title)}</strong></p>")

    if block.text:
        parts.append(sanitize_html(block.text))

    return "".join(parts)


def rebuild_layout(
    resume: dict[str, Any],
    *,
    split_pages: bool = True,
) -> None:
    """
    Rebuild metadata.layout.pages using standard order and only contentful
    sections/custom sections.

    If split_pages is False, put all content on a single layout page.
    """

    standard_main_order = [
        "summary",
        "experience",
        "education",
        "certifications",
        "publications",
        "projects",
        "awards",
        "volunteer",
    ]

    standard_sidebar_order = [
        "profiles",
        "skills",
        "languages",
        "references",
        "interests",
    ]

    main_ids = [
        section_id
        for section_id in standard_main_order
        if section_has_content(resume, section_id)
    ]

    custom_ids = [
        section["id"]
        for section in resume.get("customSections", [])
        if isinstance(section, dict)
        and section.get("id")
        and custom_section_has_content(section)
    ]

    insert_after = max(
        [
            main_ids.index(section_id)
            for section_id in ["certifications", "publications"]
            if section_id in main_ids
        ],
        default=len(main_ids) - 1,
    )

    if main_ids:
        main_ids = (
            main_ids[: insert_after + 1]
            + custom_ids
            + main_ids[insert_after + 1 :]
        )
    else:
        main_ids = custom_ids

    sidebar_ids = [
        section_id
        for section_id in standard_sidebar_order
        if section_has_content(resume, section_id)
    ]

    if split_pages:
        pages = build_pages(main_ids, sidebar_ids)
    else:
        pages = build_single_page(main_ids, sidebar_ids)

    set_layout_pages(resume, pages)


def build_pages(main_ids: list[str], sidebar_ids: list[str]) -> list[dict[str, Any]]:
    """
    Build compact app-compatible layout pages.

    Page 1 favours the canonical CV spine:
    summary, experience, education / profiles, skills, languages.

    Page 2 receives remaining content. Empty pages are omitted.
    """

    first_main_priority = ["summary", "experience", "education"]
    first_sidebar_priority = ["profiles", "skills", "languages"]

    page1_main = [section_id for section_id in first_main_priority if section_id in main_ids]
    page1_sidebar = [
        section_id for section_id in first_sidebar_priority if section_id in sidebar_ids
    ]

    remaining_main = [section_id for section_id in main_ids if section_id not in page1_main]
    remaining_sidebar = [
        section_id for section_id in sidebar_ids if section_id not in page1_sidebar
    ]

    raw_pages: list[tuple[list[str], list[str]]] = []

    if page1_main or page1_sidebar:
        raw_pages.append((page1_main, page1_sidebar))

    if remaining_main or remaining_sidebar:
        raw_pages.append((remaining_main, remaining_sidebar))

    pages: list[dict[str, Any]] = []

    for main, sidebar in raw_pages:
        if not main and sidebar:
            pages.append(
                {
                    "fullWidth": True,
                    "main": sidebar,
                    "sidebar": [],
                }
            )
            continue

        pages.append(
            {
                "fullWidth": not bool(sidebar),
                "main": main,
                "sidebar": sidebar,
            }
        )

    return pages

def build_single_page(
    main_ids: list[str],
    sidebar_ids: list[str],
) -> list[dict[str, Any]]:
    """
    Build a single app-compatible layout page.

    This prevents the converter from splitting metadata.layout.pages into
    multiple pages. It does not prevent the rendering app from visually
    paginating overflowing content.
    """

    if not main_ids and not sidebar_ids:
        return []

    if not main_ids and sidebar_ids:
        return [
            {
                "fullWidth": True,
                "main": sidebar_ids,
                "sidebar": [],
            }
        ]

    return [
        {
            "fullWidth": not bool(sidebar_ids),
            "main": main_ids,
            "sidebar": sidebar_ids,
        }
    ]

def section_has_content(resume: dict[str, Any], section_id: str) -> bool:
    if section_id == "summary":
        summary = resume.get("summary", {})
        return isinstance(summary, dict) and bool(summary.get("content"))

    section = resume.get("sections", {}).get(section_id)
    if not isinstance(section, dict):
        return False

    items = section.get("items", [])
    return isinstance(items, list) and len(items) > 0


def custom_section_has_content(section: Mapping[str, Any]) -> bool:
    items = section.get("items", [])
    return isinstance(items, list) and len(items) > 0


def website_object(url: str, label: str = "") -> dict[str, str]:
    if not url:
        return empty_website()

    normalised_url = normalise_url_for_link(url)
    if not normalised_url:
        return {
            "url": "",
            "label": label or url,
        }

    return {
        "url": normalised_url,
        "label": label or label_from_url(normalised_url),
    }


def first_link_website(links: list[str]) -> dict[str, str]:
    for link in links:
        if not link:
            continue

        normalised = normalise_url_for_link(link)
        if normalised:
            return website_object(normalised, label_from_url(normalised))

    return empty_website()


def format_date_range(date_range: DateRange) -> str:
    start = format_date(date_range.start)
    end = format_date(date_range.end)

    if start and date_range.ongoing:
        return f"{start} - Present"

    if start and end:
        return f"{start} - {end}"

    if start:
        return start

    if end:
        return end

    if date_range.raw:
        return date_range.raw

    return ""


def format_date(date: ParsedDate | None) -> str:
    if date is None:
        return ""

    if date.precision == "year" and date.year:
        return f"{date.year:04d}"

    if date.precision == "month" and date.year and date.month:
        return f"{MONTH_NAMES[date.month]} {date.year:04d}"

    if date.precision == "day" and date.year and date.month and date.day:
        return f"{date.day} {MONTH_NAMES[date.month]} {date.year:04d}"

    return date.raw


MONTH_NAMES: dict[int, str] = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


def code_label_display(value: CodeLabel | None) -> str:
    if value is None:
        return ""

    if value.label:
        return value.label

    if value.code:
        return value.code.upper()

    return ""


def truncate_title(value: str, *, max_length: int = 120) -> str:
    text = re.sub(r"\s+", " ", value).strip()

    if len(text) <= max_length:
        return text

    return text[: max_length - 1].rstrip() + "…"


def links_as_html(links: list[str]) -> str:
    safe_links: list[str] = []

    for link in links:
        url = normalise_url_for_link(link)
        if not url:
            continue

        label = label_from_url(url)
        safe_links.append(
            f'<li><a href="{escape_attribute(url)}">{escape_text(label)}</a></li>'
        )

    if not safe_links:
        return ""

    return "<ul>" + "".join(safe_links) + "</ul>"


def escape_text(value: Any) -> str:
    return html.escape(str(value or ""), quote=False)


def escape_attribute(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


__all__ = [
    "MappingResult",
    "map_candidate_to_resume",
    "new_id",
    "map_picture",
    "map_basics",
    "map_summary",
    "map_profiles",
    "map_experience",
    "map_education",
    "map_certifications",
    "map_publications_and_custom_sections",
    "map_conferences",
    "map_other_blocks",
    "map_languages",
    "map_references_placeholder",
    "map_unhandled_blocks",
    "rebuild_layout",
    "format_date",
    "format_date_range",
    "website_object",
    "first_link_website",
    "code_label_display",
    "build_single_page",
]