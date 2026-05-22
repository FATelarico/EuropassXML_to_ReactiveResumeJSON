"""
Language and CEFR handling for the Europass-to-resume converter.

This module is intentionally pure utility code. It does not parse XML and does
not write Reactive Resume/app-compatible JSON directly.

Policy implemented:
- Native / mother-tongue languages become fluency="Native" and level=5.
- For foreign languages with CEFR sub-scores:
  - numeric level is based on the lowest available CEFR level;
  - displayed fluency is based on the spoken level;
  - if both spoken interaction and spoken production are present, use the
    lower of those two spoken levels;
  - if no spoken level exists, fall back to the lowest available CEFR level.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


CEFR_LEVELS: tuple[str, ...] = ("A1", "A2", "B1", "B2", "C1", "C2")

CEFR_RANK: dict[str, int] = {
    level: index for index, level in enumerate(CEFR_LEVELS)
}

# Reactive Resume-style numeric level: 0 hides level, 1-5 displays increasing skill.
# C1 and C2 both map to 5 because the target format only supports 0-5.
CEFR_TO_NUMERIC_LEVEL: dict[str, int] = {
    "A1": 1,
    "A2": 2,
    "B1": 3,
    "B2": 4,
    "C1": 5,
    "C2": 5,
}

NATIVE_FLUENCY = "Native"
NATIVE_NUMERIC_LEVEL = 5

_NATIVE_MARKERS: set[str] = {
    "native",
    "mother tongue",
    "mother-tongue",
    "mothertongue",
    "first language",
    "first-language",
    "primary language",
    "primary-language",
    "l1",
}


@dataclass(frozen=True)
class LanguageLevel:
    """
    Normalised language-level result for later mapping into resume JSON.

    Attributes:
        fluency:
            Display text for the target resume item. For CEFR-scored foreign
            languages, this is the spoken CEFR level where available.

        level:
            Numeric level in the app-compatible 0-5 scale.

        cefr_level:
            Conservative CEFR level based on the lowest available CEFR score.
            None for native languages or when no CEFR score is available.

        is_native:
            Whether this language was classified as native/mother tongue.
    """

    fluency: str
    level: int
    cefr_level: str | None
    is_native: bool = False


def normalise_cefr(value: Any) -> str | None:
    """
    Extract and normalise a CEFR level from arbitrary input.

    Accepts values such as:
    - "B2"
    - "b2"
    - "B 2"
    - "CEFR C1"
    - "Level: A2"

    Returns:
        A canonical CEFR value such as "B2", or None if no valid level is found.
    """

    if value is None:
        return None

    text = str(value).strip().upper()
    if not text:
        return None

    match = re.search(r"\b([ABC])\s*([12])\b", text)
    if not match:
        return None

    level = f"{match.group(1)}{match.group(2)}"
    return level if level in CEFR_RANK else None


def is_cefr(value: Any) -> bool:
    """Return True if value contains a valid CEFR level."""
    return normalise_cefr(value) is not None


def is_native_marker(value: Any) -> bool:
    """
    Return True if value indicates native/mother-tongue status.
    """

    if value is None:
        return False

    text = str(value).strip().lower()
    if not text:
        return False

    compact = re.sub(r"[\s_\-]+", " ", text)
    squashed = re.sub(r"[\s_\-]+", "", text)

    return compact in _NATIVE_MARKERS or squashed in _NATIVE_MARKERS


def _flatten_values(values: Iterable[Any]) -> list[Any]:
    """
    Flatten simple nested lists/tuples/sets while treating strings as scalars.
    """

    flattened: list[Any] = []

    for value in values:
        if value is None:
            continue

        if isinstance(value, Mapping):
            flattened.extend(value.values())
            continue

        if isinstance(value, (list, tuple, set, frozenset)):
            flattened.extend(_flatten_values(value))
            continue

        flattened.append(value)

    return flattened


def lowest_cefr(*values: Any) -> str | None:
    """
    Return the lowest CEFR level found among the supplied values.

    Examples:
        lowest_cefr("C1", "B2", "A2") -> "A2"
        lowest_cefr(["B1", "B2"]) -> "B1"
        lowest_cefr({"reading": "C1", "writing": "B2"}) -> "B2"
    """

    levels = [
        level
        for value in _flatten_values(values)
        if (level := normalise_cefr(value)) is not None
    ]

    if not levels:
        return None

    return min(levels, key=lambda level: CEFR_RANK[level])


def highest_cefr(*values: Any) -> str | None:
    """
    Return the highest CEFR level found among the supplied values.

    This is not part of the main conversion policy, but is useful for diagnostics
    and possible future UI summaries.
    """

    levels = [
        level
        for value in _flatten_values(values)
        if (level := normalise_cefr(value)) is not None
    ]

    if not levels:
        return None

    return max(levels, key=lambda level: CEFR_RANK[level])


def cefr_to_numeric_level(value: Any) -> int:
    """
    Convert a CEFR value to the target app's 0-5 numeric scale.

    Unknown or missing values return 0.
    """

    level = normalise_cefr(value)
    if level is None:
        return 0

    return CEFR_TO_NUMERIC_LEVEL[level]


def _normalise_key(key: Any) -> str:
    """
    Normalise score-field names for loose matching.

    Examples:
        "Spoken Interaction" -> "spokeninteraction"
        "spoken-production" -> "spokenproduction"
    """

    return re.sub(r"[^a-z0-9]+", "", str(key).lower())


def spoken_cefr(scores: Mapping[str, Any]) -> str | None:
    """
    Extract the spoken CEFR level from a dictionary of language sub-scores.

    Preferred source:
    - spoken interaction
    - spoken production

    If both are present, use the lower of the two.

    Fallback source:
    - speaking
    - spoken
    - oral
    """

    interaction_values: list[str] = []
    production_values: list[str] = []
    generic_spoken_values: list[str] = []

    for key, value in scores.items():
        level = normalise_cefr(value)
        if level is None:
            continue

        normalised_key = _normalise_key(key)

        if normalised_key in {
            "spokeninteraction",
            "oralinteraction",
            "interaction",
            "interactingspoken",
        }:
            interaction_values.append(level)
            continue

        if normalised_key in {
            "spokenproduction",
            "oralproduction",
            "production",
            "spokensustainedmonologue",
        }:
            production_values.append(level)
            continue

        if normalised_key in {
            "spoken",
            "speaking",
            "oral",
            "speeches",
            "speech",
        }:
            generic_spoken_values.append(level)

    spoken_values = interaction_values + production_values
    if spoken_values:
        return lowest_cefr(spoken_values)

    if generic_spoken_values:
        return lowest_cefr(generic_spoken_values)

    return None


def compress_language_level(
    scores: Mapping[str, Any] | Iterable[Any] | None = None,
    *,
    native: bool = False,
    declared_fluency: Any = None,
) -> LanguageLevel:
    """
    Compress Europass-style language information into the target app model.

    Args:
        scores:
            Either a mapping of sub-scores, e.g.
            {
                "listening": "C1",
                "reading": "C1",
                "spokenInteraction": "B2",
                "spokenProduction": "C1",
                "writing": "B2",
            }

            Or a simple iterable of CEFR values, e.g. ["C1", "B2", "C1"].

        native:
            Explicitly mark this as native/mother tongue.

        declared_fluency:
            Optional source fluency text. Used mainly for detecting native
            status or as a fallback when no CEFR scores exist.

    Returns:
        LanguageLevel:
            A normalised result suitable for later mapping into:
            sections.languages.items[].
    """

    if native or is_native_marker(declared_fluency):
        return LanguageLevel(
            fluency=NATIVE_FLUENCY,
            level=NATIVE_NUMERIC_LEVEL,
            cefr_level=None,
            is_native=True,
        )

    if scores is None:
        fallback_cefr = normalise_cefr(declared_fluency)
        if fallback_cefr is not None:
            return LanguageLevel(
                fluency=fallback_cefr,
                level=cefr_to_numeric_level(fallback_cefr),
                cefr_level=fallback_cefr,
                is_native=False,
            )

        return LanguageLevel(
            fluency=str(declared_fluency).strip() if declared_fluency else "",
            level=0,
            cefr_level=None,
            is_native=False,
        )

    if isinstance(scores, Mapping):
        conservative_level = lowest_cefr(scores)
        spoken_level = spoken_cefr(scores)
    else:
        conservative_level = lowest_cefr(scores)
        spoken_level = None

    display_fluency = spoken_level or conservative_level

    if display_fluency is None:
        fallback_cefr = normalise_cefr(declared_fluency)
        if fallback_cefr is not None:
            display_fluency = fallback_cefr
            conservative_level = fallback_cefr

    if display_fluency is None:
        display_fluency = str(declared_fluency).strip() if declared_fluency else ""

    return LanguageLevel(
        fluency=display_fluency,
        level=cefr_to_numeric_level(conservative_level),
        cefr_level=conservative_level,
        is_native=False,
    )


def cefr_details_as_text(scores: Mapping[str, Any]) -> str:
    """
    Return a compact human-readable CEFR detail string.

    This is useful if a later mapper wants to preserve the detailed Europass
    sub-scores in a description or custom field.

    Example output:
        "Listening: C1; Reading: C1; Spoken interaction: B2; Spoken production: C1; Writing: B2"
    """

    labels = {
        "listening": "Listening",
        "reading": "Reading",
        "spokeninteraction": "Spoken interaction",
        "spokenproduction": "Spoken production",
        "writing": "Writing",
        "speaking": "Speaking",
        "spoken": "Spoken",
        "oral": "Oral",
    }

    parts: list[str] = []

    for key, value in scores.items():
        level = normalise_cefr(value)
        if level is None:
            continue

        normalised_key = _normalise_key(key)
        label = labels.get(normalised_key, str(key).strip() or "Level")
        parts.append(f"{label}: {level}")

    return "; ".join(parts)


__all__ = [
    "CEFR_LEVELS",
    "CEFR_RANK",
    "CEFR_TO_NUMERIC_LEVEL",
    "NATIVE_FLUENCY",
    "NATIVE_NUMERIC_LEVEL",
    "LanguageLevel",
    "normalise_cefr",
    "is_cefr",
    "is_native_marker",
    "lowest_cefr",
    "highest_cefr",
    "cefr_to_numeric_level",
    "spoken_cefr",
    "compress_language_level",
    "cefr_details_as_text",
]