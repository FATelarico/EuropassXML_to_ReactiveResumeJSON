<img height="128" src="https://raw.githubusercontent.com/FATelarico/EuropassXML_to_ReactiveResumeJSON/refs/heads/main/200_media/210_svg/Europass_Simbol.svg"/> <img height="128" src="https://raw.githubusercontent.com/FATelarico/EuropassXML_to_ReactiveResumeJSON/refs/heads/main/200_media/211_png/transform.png"/><img height="128" src="https://raw.githubusercontent.com/FATelarico/EuropassXML_to_ReactiveResumeJSON/refs/heads/main/200_media/210_svg/reactive-resume.svg"/> 

# Europass XML to Reactive Resume JSON

A Python utility that converts Europass Candidate XML exports into JSON Resume v5 files for import into Reactive Resume.

The converter reads a Europass `Candidate` XML file, extracts CV/resume content, sanitises HTML fragments, maps the data into the JSON Resume v5 structure expected by Reactive Resume, and reuses a provided sample JSON file as the output template for layout, typography, design, and other non-content defaults.

The package is published on [PyPI](https://pypi.org/project/europassxml-to-reactiveresumejson/) and can be installed with:

```python
python3 -m pip install europassxml_to_reactiveresumejson`
```

## Status

This project is in active development.

The current target is **Reactive Resume JSON Resume v5 import compatibility**, not human readability or plain-text editability. The converter prioritises the JSON shape accepted or emitted by Reactive Resume, using the application's own samples as templates.

## Supported input

The converter currently targets the Europass XML dialect represented by files with a root element similar to:

```xml
<Candidate xmlns="http://www.europass.eu/1.0">
    ...
</Candidate>
```

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

The repository uses a package layout. The Python source lives inside the `europass_converter/` package directory, while project metadata and auxiliary files remain at repository root.


```
.
├── 100_src
│   ├── install_dependencies.sh
│   ├── sample.json
│   ├── sample.pdf
│   └── sample.xml
├── 200_media
│   ├── 210svg
│   │   └── [...]
│   ├── 211png
│   │   └── [...]
│   └── media.qrc
├── adv.ui
├── europass_converter
│   ├── cli.py
│   ├── contacts.py
│   ├── converter.py
│   ├── gui.py
│   ├── __init__.py
│   ├── languages.py
│   ├── map_resume.py
│   ├── parse_candidate.py
│   ├── sanitize_html.py
│   ├── template.py
│   ├── ui_adv.py
│   ├── ui_mainwindow.py
│   └── version.py
├── mainwindow.ui
├── media_rc.py
├── pyproject.toml
├── README.md
├── LICENSE-docs
└── LICENSE
```

## Releases

Source distributions and wheels are available from both PyPI and the repository’s GitHub Releases page.

## Install CLI

Install the command-line converter from [PyPI](https://pypi.org/project/europassxml-to-reactiveresumejson/):

```bash
python -m pip install europassxml_to_reactiveresumejson
````

Installation from a release wheel downloaded from the repository’s [Releases](https://github.com/FATelarico/EuropassXML_to_ReactiveResumeJSON/releases/latest) page is also possible:

```bash
python -m pip install ./europassxml_to_reactiveresumejson-*.whl
```

Show the available options:

```bash
europass-convert --help
```

Or:

```bash
python -m europass_converter.cli --help
```

Check the installed version:

```bash
europass-convert --version
```

Or:

```bash
python -m europass_converter.cli --version
```

### Convert a file

```bash
europass-convert "./path/to/cv.xml" \
  --template "./100_src/sample.json" \
  --output "./out/resume.json" \
  --no-split-pages
```

The resulting file can then be imported into Reactive Resume as a JSON Resume v5 file.

### Use a Europass PDF

Some Europass PDF files contain the original XML as an embedded attachment called `attachment.xml`.

The command-line converter expects an XML file as input. To extract it from a Europass PDF CV:

```bash
# sudo apt-get install poppler-utils   # install `pdfdetach` if needed
pdfdetach -savefile attachment.xml -o cv.xml cv.pdf
```

Then convert the extracted XML:

```bash
europass-convert "./cv.xml" \
  --template "./100_src/sample.json" \
  --output "./out/resume.json" \
  --no-split-pages
```

## Install GUI

Install the package with GUI support from [PyPI](https://pypi.org/project/europassxml-to-reactiveresumejson/):

```bash
python -m pip install "europassxml_to_reactiveresumejson[gui]"
```

Or from a downloaded release wheel:

```bash
python -m pip install "europassxml_to_reactiveresumejson-*.whl[gui]"
```

Launch the GUI:

```bash
europass-convert-gui
```

The GUI accepts either:

* a Europass Candidate XML file; or
* a Europass PDF containing an embedded `attachment.xml`.

If a PDF is selected, the GUI attempts to extract the embedded XML automatically. If extraction succeeds, the XML is saved beside the selected output JSON as `Europass.xml`. If the PDF does not contain `attachment.xml`, conversion is not started.

Advanced options available in the GUI include:

* indentation level;
* compact JSON output;
* verbosity level;
* debug traceback logging;
* parsed intermediate representation logging.

When enabled, diagnostic can be written to file at the same time as the output JSON: `XMLconv.log` for `stout` and `debug.log` for `stderr`.

## Run from source

Clone the repository and prepare the virtual environment:

```bash
bash ./100_src/install_dependencies.sh
```

By default, this installs only the command-line converter dependencies.

To install the GUI dependencies:

```bash
bash ./100_src/install_dependencies.sh --gui
```

To install the development environment, including GUI and development extras:

```bash
bash ./100_src/install_dependencies.sh --dev
```

Run the CLI from the source tree:

```bash
.venv/bin/python -m europass_converter.cli --help
```

Or use the installed console script inside the virtual environment:

```bash
.venv/bin/europass-convert --help
```

### Test the bundled sample

```bash
.venv/bin/python -m europass_converter.cli "./100_src/sample.xml" \
  --template "./100_src/sample.json" \
  --output "./out/resume2.json" \
  --no-split-pages \
  --debug \
  --debug-parsed \
  -v 2
```

Or:

```bash
.venv/bin/europass-convert "./100_src/sample.xml" \
  --template "./100_src/sample.json" \
  --output "./out/resume2.json" \
  --no-split-pages \
  --debug \
  --debug-parsed \
  -v 2
```

This writes the converted JSON file to `./out/resume2.json`.

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

The current default contact priority is XML order unless the user provides `--preferred-email`, `--preferred-phone`, and/or `--preferred-website`.

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

`ConferencesAndSeminars/ConferenceAndSeminar` entries become a `customSections[]` with `type = "projects"`.

### Other blocks

Other Europass `Others` blocks are preserved under a custom section called *Additional information*.

The mapper does not guess whether miscellaneous blocks are awards, interests, skills, or projects until a specific parser rule is implemented.

### Languages

Native languages from `PrimaryLanguageCode` are mapped as:

```text
fluency = "Native"
level = 5
```
Foreign languages from `PersonQualifications/PersonCompetency` are mapped using CEFR scores:

* the numeric level is based on the lowest available CEFR score;
* the displayed fluency is based on the spoken CEFR level;
* if both spoken interaction and spoken production exist, the lower of the two is used;
* incomplete CEFR data is preserved during parsing and handled conservatively during mapping.

### References

If the XML does not provide references, the converter adds the 'Available upon request'  placeholder.

## HTML sanitisation

Europass XML often stores escaped HTML fragments. The converter decodes and sanitises these fragments before inserting them into JSON.

* Allowed semantic tags `p`, `br`, `ul`, `ol`, `li`, `strong`, `em`, `u`, `a`

* Allowed link protocols `http`, `https`, `mailto`, `tel`

* Headings are converted to `p`/`strong` markup.

* Plain text without HTML tags is converted into paragraph HTML.

* The sanitizer also removes/normalises:
    - scripts
    - styles
    - iframes
    - embedded objects
    - unknown attributes
    - inline CSS
    - layout-only spans
    - empty paragraphs
    - empty list items
    - unsafe links

## Layout behaviour

By default, the mapper builds `metadata.layout.pages` using a standard resume order and includes only sections that contain content.

To prevent the converter from creating multiple layout page entries, use:

```bash
--no-split-pages
```

This does not guarantee that the target rendering app will not paginate overflowing content when exported to PDF. It only prevents the converter from splitting `metadata.layout.pages`.

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

It rebuilds only `metadata.layout.pages`.

## Python API

The public converter API is provided by `converter.py`.

### Convert files

```python
from europass_converter.converter import convert_files, resume_to_json

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
from europass_converter.converter import convert_xml_string
from europass_converter.template import load_template

template = load_template("sample.json")

result = convert_xml_string(xml_string, template)
```

## Design principles

The converter is split into small modules with narrow responsibilities:

* `parse_candidate.py` extracts neutral content from XML.
* `contacts.py` classifies and selects contact channels.
* `languages.py` handles CEFR/native language compression.
* `sanitize_html.py` cleans rich text.
* `template.py` prepares a Reactive Resume JSON Resume v5 template.
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
* improve GUI packaging and release builds;
* add an interactive contact selector;
<!-- * add support for multiple Europass XML dialects;-->
* improve publication splitting;
* add richer country/language code resolution;
* add importer validation against the target app;
* add release automation and GitHub Actions packaging checks;
* add CI checks for linting and tests.

## Licensing

Source code in this repository is licensed under the GNU Affero General Public License v3. (AGPL-3.0), unless stated otherwise.

Documentation, including README files, manuals, and explanatory text, is licensed under Creative Commons Attribution-ShareAlike 4.0 International (`CC-BY-SA-4.0`), unless stated otherwise.

Sample files, test fixtures, and third-party assets may be subject to separate licensing terms as indicated in their respective files or directories.
