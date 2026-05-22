"""
Parser for the Europass Candidate XML dialect used by the uploaded sample.

This module is deliberately neutral:
- it does not sanitise HTML;
- it does not format dates for final display;
- it does not choose preferred contacts;
- it does not build app-compatible resume JSON.

It extracts structured content from the XML and leaves mapping decisions to
map_resume.py.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from lxml import etree

try:
    from .contacts import ContactChannel
except ImportError:  # pragma: no cover - useful when running as a flat script
    from contacts import ContactChannel


class CandidateParseError(ValueError):
    """Raised when the XML is not a supported Europass Candidate document."""


@dataclass(frozen=True)
class CodeLabel:
    code: str = ""
    label: str = ""
    source: str = ""


@dataclass(frozen=True)
class ParsedDate:
    raw: str = ""
    year: int | None = None
    month: int | None = None
    day: int | None = None
    precision: str = ""  # "year", "month", "day", or ""


@dataclass(frozen=True)
class DateRange:
    start: ParsedDate | None = None
    end: ParsedDate | None = None
    ongoing: bool | None = None
    raw: str = ""


@dataclass(frozen=True)
class Address:
    lines: list[str] = field(default_factory=list)
    city: str = ""
    postal_code: str = ""
    country: CodeLabel = field(default_factory=CodeLabel)
    raw: str = ""

    def display(self) -> str:
        parts: list[str] = []
        parts.extend(line for line in self.lines if line)
        locality = " ".join(part for part in [self.postal_code, self.city] if part)
        if locality:
            parts.append(locality)
        country = self.country.label or self.country.code
        if country:
            parts.append(country)
        return ", ".join(parts)


@dataclass(frozen=True)
class PersonIdentity:
    given_name: str = ""
    family_name: str = ""
    full_name: str = ""
    birth_date: ParsedDate | None = None
    nationality: CodeLabel | None = None


@dataclass(frozen=True)
class LanguageCompetency:
    language: CodeLabel
    is_native: bool = False
    source: str = ""
    scores: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AttachmentData:
    file_type: str = ""
    instructions: str = ""
    mime_type: str = ""
    embedded_base64: str = ""
    payload_base64: str = ""
    data_uri: str = ""
    raw_bytes: bytes | None = None


@dataclass(frozen=True)
class WorkExperience:
    organisation: str = ""
    position: str = ""
    date_range: DateRange = field(default_factory=DateRange)
    description: str = ""
    city: str = ""
    country: CodeLabel = field(default_factory=CodeLabel)
    address: Address | None = None
    links: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EducationExperience:
    organisation: str = ""
    degree: str = ""
    level: CodeLabel = field(default_factory=CodeLabel)
    date_range: DateRange = field(default_factory=DateRange)
    description: str = ""
    grade: str = ""
    thesis: str = ""
    credit_type: str = ""
    credits: str = ""
    address: Address | None = None
    links: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Course:
    title: str = ""
    date_range: DateRange = field(default_factory=DateRange)
    description: str = ""
    links: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PublicationGroup:
    group_title: str = ""
    description: str = ""
    links: list[str] = field(default_factory=list)
    source_title: str = ""


@dataclass(frozen=True)
class ConferenceSeminar:
    title: str = ""
    date_range: DateRange = field(default_factory=DateRange)
    location: str = ""
    link: str = ""
    links: list[str] = field(default_factory=list)
    description: str = ""


@dataclass(frozen=True)
class OtherBlock:
    section_title: str = ""
    item_title: str = ""
    date_range: DateRange = field(default_factory=DateRange)
    description: str = ""
    links: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RenderingSection:
    title: str = ""
    custom: bool = False


@dataclass(frozen=True)
class RenderingMetadata:
    template: str = ""
    colour: str = ""
    font_size: str = ""
    logo: str = ""
    page_numbers: bool | None = None
    sections_order: list[RenderingSection] = field(default_factory=list)


@dataclass(frozen=True)
class UnhandledBlock:
    path: str = ""
    title: str = ""
    text: str = ""
    xml: str = ""


@dataclass(frozen=True)
class ParsedCandidate:
    identity: PersonIdentity = field(default_factory=PersonIdentity)
    contacts: list[ContactChannel] = field(default_factory=list)
    addresses: list[Address] = field(default_factory=list)
    summary: str = ""
    languages: list[LanguageCompetency] = field(default_factory=list)
    work_experiences: list[WorkExperience] = field(default_factory=list)
    education: list[EducationExperience] = field(default_factory=list)
    courses: list[Course] = field(default_factory=list)
    publication_groups: list[PublicationGroup] = field(default_factory=list)
    conferences_seminars: list[ConferenceSeminar] = field(default_factory=list)
    other_blocks: list[OtherBlock] = field(default_factory=list)
    attachments: list[AttachmentData] = field(default_factory=list)
    rendering: RenderingMetadata | None = None
    unhandled_blocks: list[UnhandledBlock] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)


LANGUAGE_LABELS: dict[str, str] = {
    "eng": "English",
    "en": "English",
    "fre": "French",
    "fra": "French",
    "fr": "French",
    "ita": "Italian",
    "it": "Italian",
    "slv": "Slovenian",
    "sl": "Slovenian",
    "bul": "Bulgarian",
    "bg": "Bulgarian",
    "deu": "German",
    "ger": "German",
    "de": "German",
    "spa": "Spanish",
    "es": "Spanish",
    "por": "Portuguese",
    "pt": "Portuguese",
}


CEFR_DIMENSION_KEYS: dict[str, str] = {
    "CEF-Understanding-Listening": "listening",
    "CEF-Understanding-Reading": "reading",
    "CEF-Speaking-Interaction": "spoken_interaction",
    "CEF-Speaking-Production": "spoken_production",
    "CEF-Writing-Production": "writing",
}


def parse_candidate_file(path: str | Path) -> ParsedCandidate:
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        recover=False,
        remove_blank_text=False,
    )
    document = etree.parse(str(path), parser)
    return parse_candidate_root(document.getroot())


def parse_candidate_xml(xml: str | bytes) -> ParsedCandidate:
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        recover=False,
        remove_blank_text=False,
    )
    data = xml.encode("utf-8") if isinstance(xml, str) else xml
    root = etree.fromstring(data, parser)
    return parse_candidate_root(root)


def parse_candidate_root(root: etree._Element) -> ParsedCandidate:
    if local_name(root) != "Candidate":
        raise CandidateParseError(
            f"Unsupported XML root '{local_name(root)}'. Expected 'Candidate'."
        )

    diagnostics: list[str] = []

    candidate_person = first_child(root, "CandidatePerson")
    supplier_person = first_descendant(first_child(root, "CandidateSupplier"), "PersonContact")
    profile = first_child(root, "CandidateProfile")

    if candidate_person is None and supplier_person is None:
        diagnostics.append("No CandidatePerson or CandidateSupplier/PersonContact found.")

    identity = parse_person_identity(candidate_person or supplier_person)
    contacts, addresses, native_languages = parse_person_contacts(candidate_person)

    if not contacts and supplier_person is not None:
        fallback_contacts, fallback_addresses, _ = parse_person_contacts(supplier_person)
        contacts = fallback_contacts
        if not addresses:
            addresses = fallback_addresses
        diagnostics.append(
            "CandidatePerson contained no contact channels; used CandidateSupplier contacts."
        )

    summary = child_text(profile, "ExecutiveSummary") if profile is not None else ""

    work_experiences = (
        parse_employment_history(first_child(profile, "EmploymentHistory"))
        if profile is not None
        else []
    )

    education = (
        parse_education_history(first_child(profile, "EducationHistory"))
        if profile is not None
        else []
    )

    foreign_languages = (
        parse_language_qualifications(first_child(profile, "PersonQualifications"))
        if profile is not None
        else []
    )

    courses: list[Course] = []
    publication_groups: list[PublicationGroup] = []
    other_blocks: list[OtherBlock] = []

    if profile is not None:
        for others in children(profile, "Others"):
            parsed_courses, parsed_publications, parsed_other = parse_others(others)
            courses.extend(parsed_courses)
            publication_groups.extend(parsed_publications)
            other_blocks.extend(parsed_other)

    conferences_seminars = (
        parse_conferences(first_child(profile, "ConferencesAndSeminars"))
        if profile is not None
        else []
    )

    attachments = (
        [parse_attachment(element) for element in children(profile, "Attachment")]
        if profile is not None
        else []
    )

    rendering = parse_rendering(first_child(root, "RenderingInformation"))

    unhandled_blocks = (
        parse_unhandled_profile_blocks(profile) if profile is not None else []
    )

    return ParsedCandidate(
        identity=identity,
        contacts=contacts,
        addresses=addresses,
        summary=summary,
        languages=native_languages + foreign_languages,
        work_experiences=work_experiences,
        education=education,
        courses=courses,
        publication_groups=publication_groups,
        conferences_seminars=conferences_seminars,
        other_blocks=other_blocks,
        attachments=attachments,
        rendering=rendering,
        unhandled_blocks=unhandled_blocks,
        diagnostics=diagnostics,
    )


def parse_person_identity(person: etree._Element | None) -> PersonIdentity:
    if person is None:
        return PersonIdentity()

    name = first_child(person, "PersonName")
    given_name = child_text(name, "GivenName")
    family_name = child_text(name, "FamilyName")
    full_name = " ".join(part for part in [given_name, family_name] if part).strip()

    birth_raw = child_text(person, "BirthDate")
    birth_date = parse_date_value(birth_raw) if birth_raw else None

    nationality_raw = child_text(person, "NationalityCode")
    nationality = (
        CodeLabel(code=nationality_raw, label="", source="NationalityCode")
        if nationality_raw
        else None
    )

    return PersonIdentity(
        given_name=given_name,
        family_name=family_name,
        full_name=full_name,
        birth_date=birth_date,
        nationality=nationality,
    )


def parse_person_contacts(
    person: etree._Element | None,
) -> tuple[list[ContactChannel], list[Address], list[LanguageCompetency]]:
    if person is None:
        return [], [], []

    contacts: list[ContactChannel] = []
    addresses: list[Address] = []
    native_languages: list[LanguageCompetency] = []

    for communication in children(person, "Communication"):
        address = first_child(communication, "Address")
        if address is not None:
            addresses.append(parse_address(address))

        channel = parse_communication_channel(communication)
        if channel is not None:
            contacts.append(channel)

    for language in children(person, "PrimaryLanguageCode"):
        value = text_content(language)
        if not value:
            continue

        native_languages.append(
            LanguageCompetency(
                language=CodeLabel(code="", label=value, source="PrimaryLanguageCode"),
                is_native=True,
                source="PrimaryLanguageCode",
                scores={},
            )
        )

    return contacts, addresses, native_languages


def parse_communication_channel(element: etree._Element) -> ContactChannel | None:
    channel_code = child_text(element, "ChannelCode")
    use_code = child_text(element, "UseCode")
    other_title = child_text(element, "OtherTitle")
    uri = child_text(element, "URI")

    country_dialling = child_text(element, "CountryDialing")
    dial_number = child_text(element, "DialNumber")

    if uri:
        value = uri
    elif dial_number:
        value = format_phone(country_dialling, dial_number)
    else:
        return None

    network = other_title or use_code
    label = other_title or use_code

    return ContactChannel(
        kind=channel_code or use_code or other_title,
        value=value,
        label=label,
        url=uri if looks_urlish(uri) else "",
        network=network,
        use=use_code,
        source=element_path(element),
    )


def format_phone(country_dialling: str, dial_number: str) -> str:
    country = country_dialling.strip().lstrip("+")
    number = dial_number.strip()

    if country and number:
        return f"+{country} {number}"

    return number or country


def parse_address(element: etree._Element) -> Address:
    lines = [text_content(line) for line in children(element, "AddressLine")]
    lines = [line for line in lines if line]

    city = child_text(element, "CityName")
    postal_code = child_text(element, "PostalCode")
    country_code = child_text(element, "CountryCode") or child_text(element, "Country")

    return Address(
        lines=lines,
        city=city,
        postal_code=postal_code,
        country=CodeLabel(code=country_code, label="", source="CountryCode"),
        raw=text_content(element),
    )


def parse_employment_history(element: etree._Element | None) -> list[WorkExperience]:
    if element is None:
        return []

    items: list[WorkExperience] = []

    for employer in children(element, "EmployerHistory"):
        organisation = child_text(employer, "OrganizationName")
        address, links = parse_organisation_contact(first_child(employer, "OrganizationContact"))

        direct_links = [text_content(link) for link in children(employer, "Link")]
        links = dedupe_preserve_order(links + direct_links)

        positions = children(employer, "PositionHistory")
        if not positions:
            items.append(
                WorkExperience(
                    organisation=organisation,
                    address=address,
                    links=links,
                )
            )
            continue

        for position in positions:
            period = parse_date_range(first_child(position, "EmploymentPeriod"))
            city = child_text(position, "City")
            country = child_text(position, "Country")

            items.append(
                WorkExperience(
                    organisation=organisation,
                    position=child_text(position, "PositionTitle"),
                    date_range=period,
                    description=child_text(position, "Description"),
                    city=city,
                    country=CodeLabel(code=country, label="", source="Country"),
                    address=address,
                    links=links,
                )
            )

    return items


def parse_organisation_contact(
    element: etree._Element | None,
) -> tuple[Address | None, list[str]]:
    if element is None:
        return None, []

    address: Address | None = None
    links: list[str] = []

    for communication in children(element, "Communication"):
        address_element = first_child(communication, "Address")
        if address_element is not None and address is None:
            address = parse_address(address_element)

        channel_code = child_text(communication, "ChannelCode").lower()
        uri = child_text(communication, "URI")

        if channel_code == "web" and uri:
            links.append(uri)

    return address, dedupe_preserve_order(links)


def parse_education_history(element: etree._Element | None) -> list[EducationExperience]:
    if element is None:
        return []

    items: list[EducationExperience] = []

    for attendance in children(element, "EducationOrganizationAttendance"):
        organisation = child_text(attendance, "OrganizationName")
        address, links = parse_organisation_contact(
            first_child(attendance, "OrganizationContact")
        )

        degree_element = first_child(attendance, "EducationDegree")

        level_code = child_text(attendance, "EducationLevelCode")
        level = CodeLabel(code=level_code, label="", source="EducationLevelCode")

        date_range = parse_date_range(first_child(attendance, "AttendancePeriod"))

        degree = child_text(degree_element, "DegreeName")
        description = child_text(degree_element, "OccupationalSkillsCovered")
        grade = first_descendant_text(first_child(degree_element, "FinalGrade"), "ScoreText")
        thesis = child_text(degree_element, "Thesis")
        credit_type = child_text(degree_element, "CreditType")
        credits = child_text(degree_element, "NumberOfCredit")

        items.append(
            EducationExperience(
                organisation=organisation,
                degree=degree,
                level=level,
                date_range=date_range,
                description=description,
                grade=grade,
                thesis=thesis,
                credit_type=credit_type,
                credits=credits,
                address=address,
                links=links,
            )
        )

    return items


def parse_language_qualifications(
    element: etree._Element | None,
) -> list[LanguageCompetency]:
    if element is None:
        return []

    languages: list[LanguageCompetency] = []

    for competency in children(element, "PersonCompetency"):
        taxonomy = first_descendant_text(competency, "TaxonomyID").lower()
        if taxonomy != "language":
            continue

        code = child_text(competency, "CompetencyID")
        language = CodeLabel(
            code=code,
            label=LANGUAGE_LABELS.get(code.lower(), ""),
            source="CompetencyID",
        )

        scores: dict[str, str] = {}

        for dimension in children(competency, "CompetencyDimension"):
            dimension_code = first_descendant_text(
                dimension,
                "CompetencyDimensionTypeCode",
            )
            key = CEFR_DIMENSION_KEYS.get(dimension_code, normalise_dimension_key(dimension_code))
            score = first_descendant_text(dimension, "ScoreText")
            if key:
                scores[key] = score

        languages.append(
            LanguageCompetency(
                language=language,
                is_native=False,
                source="PersonQualifications",
                scores=scores,
            )
        )

    return languages


def parse_others(
    element: etree._Element,
) -> tuple[list[Course], list[PublicationGroup], list[OtherBlock]]:
    section_title = child_text(element, "Title")
    normalised_section = normalise_title(section_title)

    courses: list[Course] = []
    publication_groups: list[PublicationGroup] = []
    other_blocks: list[OtherBlock] = []

    for other in children(element, "Other"):
        title = child_text(other, "Title")
        date_range = parse_date_range(first_child(other, "Date"))
        description = child_text(other, "Description")
        links = [text_content(link) for link in children(other, "Link")]
        links = dedupe_preserve_order(links)

        if normalised_section == "course":
            courses.append(
                Course(
                    title=title,
                    date_range=date_range,
                    description=description,
                    links=links,
                )
            )
            continue

        if normalised_section in {"publications", "pubblications"}:
            publication_groups.append(
                PublicationGroup(
                    group_title=title,
                    description=description,
                    links=links,
                    source_title=section_title,
                )
            )
            continue

        other_blocks.append(
            OtherBlock(
                section_title=section_title,
                item_title=title,
                date_range=date_range,
                description=description,
                links=links,
            )
        )

    return courses, publication_groups, other_blocks


def parse_conferences(element: etree._Element | None) -> list[ConferenceSeminar]:
    if element is None:
        return []

    items: list[ConferenceSeminar] = []

    for conference in children(element, "ConferenceAndSeminar"):
        links = [text_content(link) for link in children(conference, "Link")]
        links = dedupe_preserve_order(links)

        items.append(
            ConferenceSeminar(
                title=child_text(conference, "Title"),
                date_range=parse_date_range(first_child(conference, "Date")),
                location=child_text(conference, "Location"),
                link=links[0] if links else "",
                links=links,
                description=child_text(conference, "Description"),
            )
        )

    return items


def parse_attachment(element: etree._Element) -> AttachmentData:
    file_type = child_text(element, "FileType")
    instructions = child_text(element, "Instructions")
    embedded_base64 = child_text(element, "EmbeddedData")

    raw_bytes: bytes | None = None
    data_uri = ""
    mime_type = ""
    payload_base64 = ""

    if embedded_base64:
        try:
            decoded = base64.b64decode(embedded_base64, validate=False)
            decoded_text = decoded.decode("utf-8", errors="ignore").strip()

            if decoded_text.startswith("data:"):
                data_uri = decoded_text
                parsed_mime, parsed_payload = parse_data_uri(decoded_text)
                mime_type = parsed_mime
                payload_base64 = parsed_payload
                if payload_base64:
                    raw_bytes = base64.b64decode(payload_base64, validate=False)
            else:
                raw_bytes = decoded
        except Exception:
            raw_bytes = None

    return AttachmentData(
        file_type=file_type,
        instructions=instructions,
        mime_type=mime_type,
        embedded_base64=embedded_base64,
        payload_base64=payload_base64,
        data_uri=data_uri,
        raw_bytes=raw_bytes,
    )


def parse_data_uri(value: str) -> tuple[str, str]:
    match = re.match(r"^data:([^;,]+);base64,(.*)$", value, flags=re.DOTALL)
    if not match:
        return "", ""

    return match.group(1).strip(), match.group(2).strip()


def parse_rendering(element: etree._Element | None) -> RenderingMetadata | None:
    if element is None:
        return None

    design = first_child(element, "Design")
    if design is None:
        return RenderingMetadata()

    sections: list[RenderingSection] = []
    order = first_child(design, "SectionsOrder")

    if order is not None:
        for section in children(order, "Section"):
            sections.append(
                RenderingSection(
                    title=child_text(section, "Title"),
                    custom=parse_bool(child_text(section, "Custom")) or False,
                )
            )

    return RenderingMetadata(
        template=child_text(design, "Template"),
        colour=child_text(design, "Color"),
        font_size=child_text(design, "FontSize"),
        logo=child_text(design, "Logo"),
        page_numbers=parse_bool(child_text(design, "PageNumbers")),
        sections_order=sections,
    )


def parse_unhandled_profile_blocks(profile: etree._Element) -> list[UnhandledBlock]:
    fully_handled = {
        "ID",
        "ExecutiveSummary",
        "EmploymentHistory",
        "EducationHistory",
        "PersonQualifications",
        "Attachment",
        "ConferencesAndSeminars",
        "Others",
    }

    unhandled: list[UnhandledBlock] = []

    for child in profile:
        name = local_name(child)

        if name in fully_handled:
            continue

        content = text_content(child)
        if not content:
            continue

        unhandled.append(
            UnhandledBlock(
                path=element_path(child),
                title=child_text(child, "Title"),
                text=content,
                xml=etree.tostring(child, encoding="unicode", with_tail=False),
            )
        )

    return unhandled


def parse_date_range(element: etree._Element | None) -> DateRange:
    if element is None:
        return DateRange()

    start = parse_named_date(element, "StartDate")
    end = parse_named_date(element, "EndDate")

    ongoing_text = (
        child_text(element, "Ongoing")
        or first_descendant_text(element, "CurrentIndicator")
    )

    return DateRange(
        start=start,
        end=end,
        ongoing=parse_bool(ongoing_text),
        raw=text_content(element),
    )


def parse_named_date(element: etree._Element, name: str) -> ParsedDate | None:
    date_element = first_child(element, name)
    if date_element is None:
        return None

    raw = first_descendant_text(date_element, "FormattedDateTime") or text_content(date_element)
    return parse_date_value(raw) if raw else None


def parse_date_value(raw: str) -> ParsedDate:
    text = clean_text(raw)
    if not text:
        return ParsedDate()

    year_match = re.fullmatch(r"(\d{4})", text)
    if year_match:
        return ParsedDate(
            raw=text,
            year=int(year_match.group(1)),
            precision="year",
        )

    month_match = re.fullmatch(r"(\d{4})-(\d{2})", text)
    if month_match:
        return ParsedDate(
            raw=text,
            year=int(month_match.group(1)),
            month=int(month_match.group(2)),
            precision="month",
        )

    day_match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if day_match:
        return ParsedDate(
            raw=text,
            year=int(day_match.group(1)),
            month=int(day_match.group(2)),
            day=int(day_match.group(3)),
            precision="day",
        )

    return ParsedDate(raw=text)


def child_text(element: etree._Element | None, name: str) -> str:
    child = first_child(element, name)
    return text_content(child)


def first_descendant_text(element: etree._Element | None, name: str) -> str:
    descendant = first_descendant(element, name)
    return text_content(descendant)


def text_content(element: etree._Element | None) -> str:
    if element is None:
        return ""

    return clean_text("".join(element.itertext()))


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\xa0", " ")).strip()


def parse_bool(value: Any) -> bool | None:
    text = str(value or "").strip().lower()

    if text in {"true", "1", "yes", "y"}:
        return True

    if text in {"false", "0", "no", "n"}:
        return False

    return None


def first_child(element: etree._Element | None, name: str) -> etree._Element | None:
    if element is None:
        return None

    for child in element:
        if local_name(child) == name:
            return child

    return None


def children(element: etree._Element | None, name: str) -> list[etree._Element]:
    if element is None:
        return []

    return [child for child in element if local_name(child) == name]


def first_descendant(element: etree._Element | None, name: str) -> etree._Element | None:
    if element is None:
        return None

    for descendant in element.iter():
        if descendant is not element and local_name(descendant) == name:
            return descendant

    return None


def local_name(element: etree._Element | Any) -> str:
    tag = getattr(element, "tag", element)

    if not isinstance(tag, str):
        return ""

    return etree.QName(tag).localname


def element_path(element: etree._Element) -> str:
    names: list[str] = []
    current: etree._Element | None = element

    while current is not None:
        names.append(local_name(current))
        current = current.getparent()

    return "/".join(reversed(names))


def normalise_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def normalise_dimension_key(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")


def dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        item = clean_text(value)
        if not item:
            continue

        key = item.casefold()
        if key in seen:
            continue

        seen.add(key)
        result.append(item)

    return result


def looks_urlish(value: str) -> bool:
    text = value.strip()
    if not text:
        return False

    parsed = urlparse(text)
    return bool(parsed.scheme and parsed.netloc)


__all__ = [
    "CandidateParseError",
    "CodeLabel",
    "ParsedDate",
    "DateRange",
    "Address",
    "PersonIdentity",
    "LanguageCompetency",
    "AttachmentData",
    "WorkExperience",
    "EducationExperience",
    "Course",
    "PublicationGroup",
    "ConferenceSeminar",
    "OtherBlock",
    "RenderingSection",
    "RenderingMetadata",
    "UnhandledBlock",
    "ParsedCandidate",
    "parse_candidate_file",
    "parse_candidate_xml",
    "parse_candidate_root",
    "parse_date_value",
    "parse_date_range",
]