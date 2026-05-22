# Europass XML to Reactive Resume JSON

A Python utility that converts Europass Candidate XML exports into JSON Resume v5 files for import into Reactive Resume.

The converter reads a Europass `Candidate` XML file, extracts CV/resume content, sanitises HTML fragments, maps the data into the JSON Resume v5 structure expected by Reactive Resume, and reuses a provided sample JSON file as the output template for layout, typography, design, and other non-content defaults.

## Status

This project is in active development.

The current target is **Reactive Resume JSON Resume v5 import compatibility**, not human readability or plain-text editability. The converter prioritises the JSON shape accepted or emitted by Reactive Resume, using the applicaiton's own samples as templates.

## Supported input

The converter currently targets the Europass XML dialect represented by files with a root element similar to:

```xml
<Candidate xmlns="http://www.europass.eu/1.0">
    ...
</Candidate>
````

The supported XML structure includes, among others:

* `CandidatePerson`
* `CandidateProfile`
* `EmploymentHistory`
* `EducationHistory`
* `PersonQualifications`
* `ConferencesAndSeminars`
* `Others`
* `Attachment`
* `RenderingInformation`

The older `LearnerInfoType` Europass schema is not the primary target of this converter.

## Output

The converter produces JSON Resume v5 output intended for import into Reactive Resume.

The output is based on a provided Reactive Resume-compatible template file. The template is used to preserve non-content fields such as:

- picture styling
- section wrapper settings
- template name
- page settings
- layout metadata
- design colours
- typography
- custom CSS settings
- notes

Existing resume content in the template is cleared and replaced with converted Europass content.

## Repository structure

```text
europass_converter/
├── converter.py          # high-level conversion orchestration
├── parse_candidate.py    # parses Europass Candidate XML
├── map_resume.py         # maps parsed content into Reactive Resume JSON Resume v5
├── sanitize_html.py      # sanitises escaped or raw HTML fragments
├── template.py           # loads and prepares the JSON template
├── contacts.py           # selects and classifies contact channels
├── languages.py          # handles CEFR/native language logic
└── cli.py                # command-line interface
```

## Installation

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install lxml beautifulsoup4 bleach
```

The project uses only the standard library for the CLI.

## Basic usage

From the repository root:

```bash
python cli.py ./100_src/sample.xml \
  --template ./100_src/sample.json \
  --output ./out/resume.json
```

Or, if installed/executed as a module:

```bash
python -m europass_converter.cli ./100_src/sample.xml \
  --template ./100_src/sample.json \
  --output ./out/resume.json
```

If `--output` is omitted, the converted JSON is written to standard output:

```bash
python cli.py ./100_src/sample.xml --template ./100_src/sample.json > resume.json
```

## CLI options

```text
positional arguments:
  xml_path                      Path to the Europass Candidate XML file.

required options:
  --template PATH               Path to the Reactive Resume JSON Resume v5 template.

optional output options:
  --output PATH                 Path to write the converted JSON.
  --indent N                    JSON indentation level. Default: 2.
  --compact                     Write compact single-line JSON.

optional contact-selection options:
  --preferred-email EMAIL       Preferred primary email if several are found.
  --preferred-phone PHONE       Preferred primary phone if several are found.
  --preferred-website URL       Preferred primary website if several are found.

optional layout options:
  --no-split-pages              Put all content into one metadata.layout.pages entry.

diagnostic options:
  -v, --verbose {0,1,2}         Verbosity level.
                                0 = suppress diagnostics
                                1 = print diagnostics if present
                                2 = print diagnostics and success summary

  --debug                       Print a full traceback on errors.
  --debug-parsed                Print the parsed intermediate representation.
```

Example with diagnostics and no converter-level page splitting:

```bash
python cli.py ./100_src/sample.xml \
  --template ./100_src/sample.json \
  --output ./out/resume.json \
  --no-split-pages \
  --debug \
  --debug-parsed \
  -v 2
```

## Exit codes

```text
0 = success
1 = conversion, parsing, or template error
2 = invalid CLI arguments
```

Argument errors are handled by `argparse`.

## Conversion policy

The converter follows these mapping rules.

### Personal information

| Europass XML source           | JSON target                                                    |
| ----------------------------- | -------------------------------------------------------------- |
| `CandidatePerson/PersonName`  | `basics.name`                                                  |
| email contact channels        | `basics.email`, additional emails to `basics.customFields`     |
| telephone contact channels    | `basics.phone`, additional phones to `basics.customFields`     |
| website contact channels      | `basics.website`, additional websites to `basics.customFields` |
| social/academic profile links | `sections.profiles.items[]`                                    |
| address locality              | `basics.location`                                              |
| nationality                   | `basics.customFields`                                          |
| birth date/year               | `basics.customFields`                                          |

The current default contact priority is XML order unless the user provides:

```bash
--preferred-email
--preferred-phone
--preferred-website
```

### Work experience

`EmploymentHistory/EmployerHistory/PositionHistory` entries become `sections.experience.items[]`.

The mapper preserves:

* organisation
* position
* city/country
* date range
* first organisation website
* sanitised description

Career progression embedded in the Europass description is kept inside the description unless later parser versions can reliably extract structured roles.

### Education

`EducationHistory/EducationOrganizationAttendance` entries become `sections.education.items[]`.

The mapper preserves:

* institution
* degree
* education period
* location
* website
* grade
* thesis
* credits
* sanitised description

Raw programme concentration codes are intentionally discarded.

### Courses

Europass `Others` blocks with title `Course` become certification items:

```text
sections.certifications.items[]
```

### Publications

Europass `Others` blocks with title `Pubblications` or `Publications` are parsed as publication groups.

The mapper attempts to split only obvious HTML list items into individual publication records. If the group cannot be split safely, it is preserved as a custom `Publications` section.

### Conferences and seminars

`ConferencesAndSeminars/ConferenceAndSeminar` entries become a custom section:

```text
customSections[] with type = "projects"
```

### Other blocks

Other Europass `Others` blocks are preserved under a custom section:

```text
Additional information
```

The mapper does not guess whether miscellaneous blocks are awards, interests, skills, or projects unless a specific parser rule exists.

### Languages

Native languages from `PrimaryLanguageCode` are mapped as:

```text
fluency = "Native"
level = 5
```

Foreign languages from `PersonQualifications/PersonCompetency` are mapped using CEFR scores.

Policy:

* the numeric level is based on the lowest available CEFR score;
* the displayed fluency is based on the spoken CEFR level;
* if both spoken interaction and spoken production exist, the lower of the two is used;
* incomplete CEFR data is preserved during parsing and handled conservatively during mapping.

### References

If the XML does not provide references, the converter adds a sample-style placeholder:

```text
Available upon request
```

## HTML sanitisation

Europass XML often stores escaped HTML fragments. The converter decodes and sanitises these fragments before inserting them into JSON.

Allowed semantic tags:

```text
p, br, ul, ol, li, strong, em, u, a
```

Allowed link protocols:

```text
http, https, mailto, tel
```

The sanitizer removes or normalises:

* scripts
* styles
* iframes
* embedded objects
* unknown attributes
* inline CSS
* layout-only spans
* empty paragraphs
* empty list items
* unsafe links

Headings are converted to paragraph/strong markup.

Plain text without HTML tags is converted into paragraph HTML.

## Layout behaviour

By default, the mapper builds `metadata.layout.pages` using a standard resume order and includes only sections that contain content.

Use:

```bash
--no-split-pages
```

to prevent the converter from creating multiple layout page entries.

This does not guarantee that the target rendering app will not visually paginate overflowing content. It only prevents the converter from splitting `metadata.layout.pages`.

## Template handling

The converter treats the provided JSON template as the source of Reactive Resume-compatible defaults.

It clears content fields such as:

* `basics.name`
* `basics.email`
* `basics.phone`
* `basics.location`
* `summary.content`
* `sections.*.items`
* `customSections`

It preserves non-content fields such as:

* `metadata.template`
* `metadata.css`
* `metadata.page`
* `metadata.design`
* `metadata.typography`
* `metadata.notes`
* `metadata.layout.sidebarWidth`
* picture styling

The converter rebuilds only `metadata.layout.pages`.

## Development notes

### Run with debug output

```bash
python cli.py ./100_src/sample.xml \
  --template ./100_src/sample.json \
  --output ./out/resume.json \
  --debug \
  --debug-parsed \
  -v 2
```

### Common issue: missing `build_single_page`

If `--no-split-pages` raises:

```text
NameError: name 'build_single_page' is not defined
```

ensure that `map_resume.py` contains the `build_single_page()` helper and that `rebuild_layout()` calls it only when `split_pages=False`.

### Common issue: lxml element truthiness warning

If you see:

```text
FutureWarning: Truth-testing of elements was a source of confusion...
```

avoid expressions such as:

```python
candidate_person or supplier_person
```

Use an explicit `is not None` check instead.

## Python API

The public converter API is provided by `converter.py`.

### Convert files

```python
from converter import convert_files, resume_to_json

result = convert_files(
    "sample.xml",
    "sample.json",
    preferred_email=None,
    preferred_phone=None,
    preferred_website=None,
    split_pages=True,
)

json_text = resume_to_json(result.resume, indent=2)
```

### Convert parsed data

```python
from converter import convert_parsed
from parse_candidate import parse_candidate_file
from template import load_template

parsed = parse_candidate_file("sample.xml")
template = load_template("sample.json")

result = convert_parsed(parsed, template)
```

### Convert XML string

```python
from converter import convert_xml_string
from template import load_template

template = load_template("sample.json")

result = convert_xml_string(xml_string, template)
```

## Design principles

The converter is split into small modules with narrow responsibilities:

* `parse_candidate.py` extracts neutral content from XML.
* `contacts.py` classifies and selects contact channels.
* `languages.py` handles CEFR/native language compression.
* `sanitize_html.py` cleans rich text.
* `template.py` prepares an Reactive Resume JSON Resume v5 template.
* `map_resume.py` applies the mapping policy.
* `converter.py` orchestrates parsing and mapping.
* `cli.py` handles command-line arguments and file output.

This separation keeps the conversion policy testable and prevents XML parsing, template preparation, and JSON mapping from becoming tangled.

## Limitations

Current limitations:

* only the uploaded Europass `Candidate` XML dialect is targeted;
* the older Europass `LearnerInfoType` schema is not the primary supported input;
* strict generic JSON Resume compatibility is not the priority;
* the output is optimised for Reactive Resume JSON Resume v5 import;
* programme concentration codes are discarded;
* employer emails are ignored;
* detailed language CEFR sub-scores are compressed;
* publication parsing is conservative;
* unknown non-empty XML blocks are preserved as unhandled content rather than guessed into specific sections;
* visual pagination may still occur in the target app even when `--no-split-pages` is used.

## Suggested future work

Possible improvements:

* add tests for each module;
* add strict-schema output mode;
* add a GUI or interactive contact selector;
* add support for multiple Europass XML dialects;
* improve publication splitting;
* add richer country/language code resolution;
* add importer validation against the target app;
* add packaging configuration with `pyproject.toml`;
* add CI checks for linting and tests.

## Licence

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike licence.

Licence: **CC BY-NC-SA**

You may share and adapt the material with attribution, for non-commercial purposes, provided that derivative works are distributed under the same licence.
