"""
Contact handling for the Europass-to-resume converter.

This module converts loosely parsed contact channels into a neutral structured
selection. It does not generate IDs and does not emit final app-compatible JSON.

Policy implemented:
- Return neutral structured data.
- Do not generate IDs.
- Preferred email/phone/website parameters are supported for later CLI/UI use.
- Without explicit preferences, use first valid email/phone/website in XML order.
- Recognised social/academic profiles become profiles, not basics.website.
- WhatsApp / messaging remains a custom contact field.
- Invalid emails/URLs/phones are preserved as custom fields.
- Deduplicate:
  - emails case-insensitively;
  - URLs by normalised URL key;
  - phones by digit sequence;
  - profiles by normalised URL;
  - custom fields by text + link.
- Add https:// to website/profile URLs if missing.
- Website labels remove the scheme but preserve the rest.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qs, urlparse, urlunparse


EMAIL_ICON = "envelope-simple"
PHONE_ICON = "phone"
WEBSITE_ICON = "globe"
WHATSAPP_ICON = "chat-circle-text"

PROFILE_ICONS: dict[str, str] = {
    "LinkedIn": "linkedin-logo",
    "GitHub": "github-logo",
    "Google Scholar": "graduation-cap",
    "ORCID": "identification-card",
    "ResearchGate": "graduation-cap",
    "Academia.edu": "graduation-cap",
}

EMAIL_RE = re.compile(
    r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$",
    re.IGNORECASE,
)

URL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
MAILTO_RE = re.compile(r"^mailto:", re.IGNORECASE)
TEL_RE = re.compile(r"^tel:", re.IGNORECASE)


@dataclass(frozen=True)
class ContactChannel:
    """
    Loose, parser-facing contact channel.

    parse_candidate.py can construct this directly, or select_contacts() can
    coerce dictionaries into this structure.
    """

    kind: str
    value: str
    label: str = ""
    url: str = ""
    network: str = ""
    use: str = ""
    icon: str = ""
    source: str = ""


@dataclass(frozen=True)
class WebsiteCandidate:
    """
    Neutral website/link candidate.
    """

    url: str
    label: str
    icon: str = WEBSITE_ICON
    source: str = ""


@dataclass(frozen=True)
class ProfileCandidate:
    """
    Neutral social/academic profile candidate.
    """

    network: str
    username: str
    website: WebsiteCandidate
    icon: str
    source: str = ""


@dataclass(frozen=True)
class CustomContactField:
    """
    Neutral custom contact field.

    map_resume.py can later convert this to:
    basics.customFields[].
    """

    text: str
    link: str = ""
    icon: str = ""
    source: str = ""


@dataclass(frozen=True)
class ContactSelection:
    """
    Result of contact selection and classification.
    """

    primary_email: str = ""
    primary_phone: str = ""
    primary_website: WebsiteCandidate | None = None
    profiles: list[ProfileCandidate] = field(default_factory=list)
    custom_fields: list[CustomContactField] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)


def select_contacts(
    channels: Iterable[ContactChannel | Mapping[str, Any]],
    *,
    preferred_email: str | None = None,
    preferred_phone: str | None = None,
    preferred_website: str | None = None,
) -> ContactSelection:
    """
    Classify and select contact information.

    Args:
        channels:
            ContactChannel objects or loose dictionaries from the XML parser.

        preferred_email:
            Optional future CLI/UI-selected primary email.

        preferred_phone:
            Optional future CLI/UI-selected primary phone.

        preferred_website:
            Optional future CLI/UI-selected primary website URL.

    Returns:
        ContactSelection with one primary email, one primary phone, one primary
        website, profile candidates, custom fields, and diagnostics.
    """

    diagnostics: list[str] = []

    email_candidates: list[str] = []
    phone_candidates: list[str] = []
    website_candidates: list[WebsiteCandidate] = []
    profiles: list[ProfileCandidate] = []
    custom_fields: list[CustomContactField] = []

    seen_emails: set[str] = set()
    seen_phones: set[str] = set()
    seen_websites: set[str] = set()
    seen_profiles: set[str] = set()
    seen_custom_fields: set[tuple[str, str]] = set()

    for raw_channel in channels:
        channel = coerce_contact_channel(raw_channel)
        kind = normalise_kind(channel.kind, channel.value, channel.url, channel.network)
        raw_value = channel.url or channel.value

        if not raw_value.strip():
            continue

        if kind == "email":
            email = normalise_email_value(raw_value)
            if is_valid_email(email):
                key = normalise_email_key(email)
                if key not in seen_emails:
                    seen_emails.add(key)
                    email_candidates.append(email)
                continue

            _add_custom_field(
                custom_fields,
                seen_custom_fields,
                CustomContactField(
                    text=channel.label or raw_value.strip(),
                    link="",
                    icon=channel.icon or EMAIL_ICON,
                    source=channel.source,
                ),
            )
            diagnostics.append(f"Invalid email preserved as custom field: {raw_value.strip()}")
            continue

        if kind == "phone":
            phone = normalise_phone_display(raw_value)
            if is_valid_phone(phone):
                key = normalise_phone_key(phone)
                if key not in seen_phones:
                    seen_phones.add(key)
                    phone_candidates.append(phone)
                continue

            _add_custom_field(
                custom_fields,
                seen_custom_fields,
                CustomContactField(
                    text=channel.label or raw_value.strip(),
                    link="",
                    icon=channel.icon or PHONE_ICON,
                    source=channel.source,
                ),
            )
            diagnostics.append(f"Invalid phone preserved as custom field: {raw_value.strip()}")
            continue

        if kind == "messaging":
            text = channel.label or build_messaging_label(channel)
            link = ""

            maybe_url = normalise_url_for_link(raw_value)
            if maybe_url and is_safe_web_url(maybe_url):
                link = maybe_url

            _add_custom_field(
                custom_fields,
                seen_custom_fields,
                CustomContactField(
                    text=text,
                    link=link,
                    icon=channel.icon or messaging_icon(channel),
                    source=channel.source,
                ),
            )
            continue

        if kind in {"website", "profile"}:
            url = normalise_url_for_link(raw_value)
            if not url or not is_safe_web_url(url):
                _add_custom_field(
                    custom_fields,
                    seen_custom_fields,
                    CustomContactField(
                        text=channel.label or raw_value.strip(),
                        link="",
                        icon=channel.icon or WEBSITE_ICON,
                        source=channel.source,
                    ),
                )
                diagnostics.append(f"Invalid URL preserved as custom field: {raw_value.strip()}")
                continue

            detected_profile = detect_profile(url, network_hint=channel.network)

            if detected_profile is not None:
                profile_key = normalise_url_key(detected_profile.website.url)
                if profile_key not in seen_profiles:
                    seen_profiles.add(profile_key)
                    profiles.append(detected_profile)
                continue

            website_key = normalise_url_key(url)
            if website_key not in seen_websites:
                seen_websites.add(website_key)
                website_candidates.append(
                    WebsiteCandidate(
                        url=url,
                        label=channel.label or label_from_url(url),
                        icon=channel.icon or WEBSITE_ICON,
                        source=channel.source,
                    )
                )
            continue

        _add_custom_field(
            custom_fields,
            seen_custom_fields,
            CustomContactField(
                text=channel.label or raw_value.strip(),
                link="",
                icon=channel.icon,
                source=channel.source,
            ),
        )

    primary_email, additional_emails = choose_primary_email(
        email_candidates,
        preferred_email=preferred_email,
        diagnostics=diagnostics,
    )

    primary_phone, additional_phones = choose_primary_phone(
        phone_candidates,
        preferred_phone=preferred_phone,
        diagnostics=diagnostics,
    )

    primary_website, additional_websites = choose_primary_website(
        website_candidates,
        preferred_website=preferred_website,
        diagnostics=diagnostics,
    )

    for email in additional_emails:
        _add_custom_field(
            custom_fields,
            seen_custom_fields,
            CustomContactField(
                text=email,
                link=f"mailto:{email}",
                icon=EMAIL_ICON,
            ),
        )

    for phone in additional_phones:
        _add_custom_field(
            custom_fields,
            seen_custom_fields,
            CustomContactField(
                text=phone,
                link="",
                icon=PHONE_ICON,
            ),
        )

    for website in additional_websites:
        _add_custom_field(
            custom_fields,
            seen_custom_fields,
            CustomContactField(
                text=website.label,
                link=website.url,
                icon=website.icon,
                source=website.source,
            ),
        )

    return ContactSelection(
        primary_email=primary_email,
        primary_phone=primary_phone,
        primary_website=primary_website,
        profiles=profiles,
        custom_fields=custom_fields,
        diagnostics=diagnostics,
    )


def coerce_contact_channel(value: ContactChannel | Mapping[str, Any]) -> ContactChannel:
    """
    Coerce loose parser dictionaries into ContactChannel.

    Accepted dictionary aliases are intentionally broad because parse_candidate.py
    has not been fixed yet.
    """

    if isinstance(value, ContactChannel):
        return value

    if not isinstance(value, Mapping):
        return ContactChannel(kind="other", value=str(value))

    kind = first_present(
        value,
        "kind",
        "type",
        "channel",
        "channel_code",
        "channelCode",
        "communication_type",
        "communicationType",
    )

    raw_value = first_present(
        value,
        "value",
        "text",
        "data",
        "contact",
        "address",
        "number",
        "email",
        "phone",
    )

    url = first_present(value, "url", "href", "link", "uri", "website")
    label = first_present(value, "label", "display", "displayText", "name")
    network = first_present(value, "network", "platform", "service")
    use = first_present(value, "use", "usage", "purpose")
    icon = first_present(value, "icon")
    source = first_present(value, "source", "path")

    return ContactChannel(
        kind=str(kind or ""),
        value=str(raw_value or ""),
        label=str(label or ""),
        url=str(url or ""),
        network=str(network or ""),
        use=str(use or ""),
        icon=str(icon or ""),
        source=str(source or ""),
    )


def first_present(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return ""


def normalise_kind(kind: str, value: str = "", url: str = "", network: str = "") -> str:
    """
    Reduce loose contact kinds into internal categories.
    """

    raw = " ".join([kind, network]).strip().lower()
    compact = re.sub(r"[^a-z0-9]+", "", raw)
    raw_value = f"{value} {url}".strip()

    if any(token in compact for token in {"email", "mail"}):
        return "email"

    if "whatsapp" in compact or "instantmessaging" in compact or "messaging" in compact:
        return "messaging"

    if any(token in compact for token in {"telephone", "phone", "mobile", "cell", "tel"}):
        return "phone"

    if any(token in compact for token in {"social", "profile", "linkedin", "github", "scholar", "orcid", "researchgate", "academia"}):
        return "profile"

    if any(token in compact for token in {"web", "website", "url", "homepage", "portfolio", "blog"}):
        return "website"

    if is_valid_email(normalise_email_value(raw_value)):
        return "email"

    if looks_like_url(raw_value):
        return "website"

    if is_valid_phone(raw_value):
        return "phone"

    return "other"


def choose_primary_email(
    emails: list[str],
    *,
    preferred_email: str | None,
    diagnostics: list[str],
) -> tuple[str, list[str]]:
    """
    Choose the primary email and return remaining emails.
    """

    if not emails:
        return "", []

    if preferred_email:
        preferred = normalise_email_value(preferred_email)
        preferred_key = normalise_email_key(preferred)

        for index, email in enumerate(emails):
            if normalise_email_key(email) == preferred_key:
                return email, emails[:index] + emails[index + 1 :]

        if is_valid_email(preferred):
            diagnostics.append(
                "Preferred email was not present in extracted contacts; using it anyway."
            )
            return preferred, emails

        diagnostics.append(
            f"Preferred email is invalid or unavailable; using first extracted email: {preferred_email}"
        )

    return emails[0], emails[1:]


def choose_primary_phone(
    phones: list[str],
    *,
    preferred_phone: str | None,
    diagnostics: list[str],
) -> tuple[str, list[str]]:
    """
    Choose the primary phone and return remaining phones.
    """

    if not phones:
        return "", []

    if preferred_phone:
        preferred = normalise_phone_display(preferred_phone)
        preferred_key = normalise_phone_key(preferred)

        for index, phone in enumerate(phones):
            if normalise_phone_key(phone) == preferred_key:
                return phone, phones[:index] + phones[index + 1 :]

        if is_valid_phone(preferred):
            diagnostics.append(
                "Preferred phone was not present in extracted contacts; using it anyway."
            )
            return preferred, phones

        diagnostics.append(
            f"Preferred phone is invalid or unavailable; using first extracted phone: {preferred_phone}"
        )

    return phones[0], phones[1:]


def choose_primary_website(
    websites: list[WebsiteCandidate],
    *,
    preferred_website: str | None,
    diagnostics: list[str],
) -> tuple[WebsiteCandidate | None, list[WebsiteCandidate]]:
    """
    Choose the primary website and return remaining websites.
    """

    if not websites and not preferred_website:
        return None, []

    if preferred_website:
        preferred_url = normalise_url_for_link(preferred_website)

        if preferred_url and is_safe_web_url(preferred_url):
            preferred_key = normalise_url_key(preferred_url)

            for index, website in enumerate(websites):
                if normalise_url_key(website.url) == preferred_key:
                    return website, websites[:index] + websites[index + 1 :]

            diagnostics.append(
                "Preferred website was not present in extracted contacts; using it anyway."
            )
            return (
                WebsiteCandidate(
                    url=preferred_url,
                    label=label_from_url(preferred_url),
                    icon=WEBSITE_ICON,
                ),
                websites,
            )

        diagnostics.append(
            f"Preferred website is invalid or unavailable; using first extracted website: {preferred_website}"
        )

    if not websites:
        return None, []

    return websites[0], websites[1:]


def normalise_email_value(value: Any) -> str:
    """
    Strip mailto: and whitespace from an email-like value.
    """

    text = str(value or "").strip()
    text = MAILTO_RE.sub("", text).strip()
    return text


def normalise_email_key(value: Any) -> str:
    return normalise_email_value(value).lower()


def is_valid_email(value: Any) -> bool:
    text = normalise_email_value(value)
    return bool(text and EMAIL_RE.match(text))


def normalise_phone_display(value: Any) -> str:
    """
    Preserve original phone formatting as much as possible.
    """

    text = str(value or "").strip()
    text = TEL_RE.sub("", text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def normalise_phone_key(value: Any) -> str:
    """
    Return digit-only key for phone deduplication.
    """

    return re.sub(r"\D+", "", str(value or ""))


def is_valid_phone(value: Any) -> bool:
    """
    Basic phone validation.

    This intentionally avoids strict country-specific validation. The converter
    only needs to avoid obviously non-phone values becoming basics.phone.
    """

    digits = normalise_phone_key(value)
    return 5 <= len(digits) <= 20


def looks_like_url(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False

    if URL_SCHEME_RE.match(text):
        return True

    if text.lower().startswith(("www.", "scholar.google.", "linkedin.", "github.")):
        return True

    return "." in text and " " not in text


def normalise_url_for_link(value: Any) -> str:
    """
    Produce a link URL suitable for the app.

    Adds https:// if no scheme is present. Leaves mailto: and tel: untouched.
    """

    text = str(value or "").strip()
    if not text:
        return ""

    if MAILTO_RE.match(text) or TEL_RE.match(text):
        return text

    if not URL_SCHEME_RE.match(text):
        text = f"https://{text}"

    parsed = urlparse(text)

    if not parsed.scheme or not parsed.netloc:
        return ""

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    path = parsed.path or ""
    if path != "/":
        path = path.rstrip("/")

    return urlunparse(
        (
            scheme,
            netloc,
            path,
            "",
            parsed.query,
            "",
        )
    )


def is_safe_web_url(value: Any) -> bool:
    parsed = urlparse(str(value or "").strip())
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def normalise_url_key(value: Any) -> str:
    """
    Normalise URL for deduplication.

    Treat http and https as equivalent for deduplication, and ignore trailing
    slash and fragments.
    """

    url = normalise_url_for_link(value)
    if not url:
        return ""

    parsed = urlparse(url)
    netloc = parsed.netloc.lower().removeprefix("www.")
    path = (parsed.path or "").rstrip("/")

    query = parsed.query
    return urlunparse(("https", netloc, path, "", query, ""))


def label_from_url(value: Any) -> str:
    """
    Build display label from URL by removing http(s) scheme and trailing slash.
    """

    url = normalise_url_for_link(value)
    if not url:
        return str(value or "").strip()

    parsed = urlparse(url)

    label = parsed.netloc + (parsed.path or "")
    if parsed.query:
        label += f"?{parsed.query}"

    return label.removeprefix("www.").rstrip("/")


def detect_profile(url: str, *, network_hint: str = "") -> ProfileCandidate | None:
    """
    Detect recognised CV-relevant social/academic profiles.
    """

    normalised_url = normalise_url_for_link(url)
    if not normalised_url or not is_safe_web_url(normalised_url):
        return None

    parsed = urlparse(normalised_url)
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.strip("/")

    hinted = network_hint.strip()

    if "linkedin.com" in host:
        return _profile("LinkedIn", _last_path_part(path), normalised_url, hinted)

    if host == "github.com":
        return _profile("GitHub", _first_path_part(path), normalised_url, hinted)

    if host == "scholar.google.com":
        return _profile(
            "Google Scholar",
            _google_scholar_username(parsed.query) or "Google Scholar",
            normalised_url,
            hinted,
        )

    if host == "orcid.org":
        return _profile("ORCID", _first_path_part(path), normalised_url, hinted)

    if "researchgate.net" in host:
        return _profile("ResearchGate", _last_path_part(path), normalised_url, hinted)

    if host.endswith("academia.edu"):
        return _profile("Academia.edu", _last_path_part(path), normalised_url, hinted)

    return None


def _profile(
    detected_network: str,
    username: str,
    url: str,
    network_hint: str = "",
) -> ProfileCandidate:
    network = network_hint or detected_network
    canonical_network = detected_network

    return ProfileCandidate(
        network=network,
        username=username or network,
        website=WebsiteCandidate(
            url=url,
            label=label_from_url(url),
            icon=PROFILE_ICONS[canonical_network],
        ),
        icon=PROFILE_ICONS[canonical_network],
    )


def _first_path_part(path: str) -> str:
    return path.split("/", 1)[0].strip()


def _last_path_part(path: str) -> str:
    parts = [part for part in path.split("/") if part.strip()]
    return parts[-1] if parts else ""


def _google_scholar_username(query: str) -> str:
    values = parse_qs(query)
    user = values.get("user", [""])[0]
    return user.strip()


def build_messaging_label(channel: ContactChannel) -> str:
    kind_text = " ".join([channel.kind, channel.network]).lower()
    value = channel.value or channel.url

    if "whatsapp" in kind_text:
        return f"WhatsApp: {value.strip()}"

    if channel.network:
        return f"{channel.network}: {value.strip()}"

    return value.strip()


def messaging_icon(channel: ContactChannel) -> str:
    kind_text = " ".join([channel.kind, channel.network]).lower()

    if "whatsapp" in kind_text:
        return WHATSAPP_ICON

    return channel.icon or "chat-circle-text"


def _add_custom_field(
    custom_fields: list[CustomContactField],
    seen: set[tuple[str, str]],
    field: CustomContactField,
) -> None:
    text = field.text.strip()
    link = field.link.strip()

    if not text and not link:
        return

    key = (text.casefold(), normalise_url_key(link) if link else "")
    if key in seen:
        return

    seen.add(key)
    custom_fields.append(
        CustomContactField(
            text=text,
            link=link,
            icon=field.icon,
            source=field.source,
        )
    )


__all__ = [
    "EMAIL_ICON",
    "PHONE_ICON",
    "WEBSITE_ICON",
    "WHATSAPP_ICON",
    "PROFILE_ICONS",
    "ContactChannel",
    "WebsiteCandidate",
    "ProfileCandidate",
    "CustomContactField",
    "ContactSelection",
    "select_contacts",
    "coerce_contact_channel",
    "normalise_kind",
    "choose_primary_email",
    "choose_primary_phone",
    "choose_primary_website",
    "normalise_email_value",
    "normalise_email_key",
    "is_valid_email",
    "normalise_phone_display",
    "normalise_phone_key",
    "is_valid_phone",
    "looks_like_url",
    "normalise_url_for_link",
    "normalise_url_key",
    "is_safe_web_url",
    "label_from_url",
    "detect_profile",
]