<img height="128" src="https://raw.githubusercontent.com/FATelarico/EuropassXML_to_ReactiveResumeJSON/refs/heads/main/200_media/210_svg/Europass_Simbol.svg"/> <img height="128" src="https://raw.githubusercontent.com/FATelarico/EuropassXML_to_ReactiveResumeJSON/refs/heads/main/200_media/211_png/transform.png"/><img height="128" src="https://raw.githubusercontent.com/FATelarico/EuropassXML_to_ReactiveResumeJSON/refs/heads/main/200_media/210_svg/reactive-resume.svg"/>

<h1> Europass XML to Reactive Resume JSON <img  src="https://img.shields.io/badge/STATUS-in%20development-orange"/> </h1>


<a href="https://pypi.org/project/europassxml-to-reactiveresumejson/" target="_blank"><img src="https://img.shields.io/pypi/v/europassxml-to-reactiveresumejson?pypiBaseUrl=https%3A%2F%2Fpypi.org&style=plastic&logo=pypi&logoColor=%233775A9&color=brightgreen"/></a>
<a href="https://github.com/FATelarico/EuropassXML_to_ReactiveResumeJSON/releases/latest" target="_blank"><img src="https://img.shields.io/github/v/release/FATelarico/EuropassXML_to_ReactiveResumeJSON?include_prereleases&sort=date&display_name=tag&style=plastic&logo=github&logoColor=%23181717&color=brightgreen"/></a>

Convert a Europass CV export into JSON Resume v5 for import into Reactive Resume.

This tool is for people who already have a Europass CV and want to move it into Reactive Resume without rebuilding the resume by hand.

It supports:
- Europass Candidate XML exports
- Europass PDF files that contain embedded XML

The converter maps Europass content into the JSON Resume v5 structure used by Reactive Resume, while preserving layout and design defaults from a supplied Reactive Resume template JSON.

The output is optimised for clean import into Reactive Resume, not as a general-purpose converter to human-readable JSON.

## Typical use cases

- Migrate an existing Europass CV into Reactive Resume
- Reuse Europass export data instead of retyping a resume manually
- Convert Europass XML extracted from a Europass PDF
- Batch or scripted conversion through the CLI

## Quick start

The package is published on [PyPI](https://pypi.org/project/europassxml-to-reactiveresumejson/) and can be installed as:

```bash
python -m pip install europassxml_to_reactiveresumejson
```

> [!NOTE]
> The PyPI distribution name uses hyphens (`europassxml-to-reactiveresumejson`), while the pip install command uses the Python package name with underscores (`europassxml_to_reactiveresumejson`).


###  Try the bundled sample using the GUI

Install the GUI from [PyPI](https://pypi.org/project/europassxml-to-reactiveresumejson/):

```bash
python3 -m venv ./venv
source ./venv/bin/activate
python3 -m pip install europassxml_to_reactiveresumejson[gui]
europass-convert-gui
```

After installation in a virtual environment, the package includes bundled sample files inside the virtual environment directory that can be used as shown:

<img src="https://github.com/FATelarico/EuropassXML_to_ReactiveResumeJSON/blob/main/GUI.gif"/>

###  Try the bundled sample using the CLI

Use the same bundled sample files as for the GUI:

```bash
python3 -m venv env
source env/bin/activate
python3 -m pip install europassxml_to_reactiveresumejson
cd ./env
europass-convert "./100_src/sample.xml" \
  --template "./100_src/sample.json" \
  --output "./sample_Rx.json"
```

Then `sample_Rx.json` can be imported into Reactive Resume. For a successful sample run, expect:

- a generated JSON file at `./output/resume2.json`
- no conversion error
- a resume that imports into Reactive Resume with content populated from the bundled Europass sample

## Usage

More generally, it sufficies to select the Europass files in the GUI to produce a JSON that can be  imported into Reactive Resume. Equivalently, they can be passed to a command like this:

```python
europass-convert "./cv.xml" \
  --template "./template.json" \
  --output "./resume.json"
```

### Supported input

The converter is intended for modern Europass exports using the the `Candidate` XML schema, for example:

```xml
<Candidate xmlns="http://www.europass.eu/1.0">
    ...
</Candidate> 
```

Recognised sections include, among others:

* `CandidatePerson`
* `CandidateProfile`
* `EmploymentHistory`
* `EducationHistory`
* `PersonQualifications`
* `ConferencesAndSeminars`
* `Others`
* `Attachment`
* `RenderingInformation`

Older Europass files using the `LearnerInfoType` schema may not convert correctly.

### Output

The converter produces JSON Resume v5 intended for import into Reactive Resume.

A supplied Reactive-Resume JSON template is used to preserve non-content settings such as photo styling, section wrapper settings, layout metadata, custom CSS settings, and notes.

Existing resume content in the template is cleared and replaced with converted Europass content.

## Installation

### GUI

Besides using PyPI, as shown in the Quick Start, installation from the wheels under the repository's [Releases](https://github.com/FATelarico/EuropassXML_to_ReactiveResumeJSON/releases/latest) page is also possible:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install "europassxml_to_reactiveresumejson[gui]"
```

Alternatively, from a downloaded release wheel:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install europassxml_to_reactiveresumejson-*.whl[gui]
```

Launch the GUI:

```bash
europass-convert-gui
```

The GUI accepts either:

* a Europass Candidate XML file; or
* a Europass PDF containing an embedded `attachment.xml`.

If a PDF is selected, the GUI attempts to extract the embedded XML automatically. If extraction succeeds, the XML can be saved alongside the selected output JSON as `Europass.xml`. If the PDF does not contain `attachment.xml`, conversion is not started.

Advanced GUI options include:

* indentation level
* compact JSON output
* verbosity level
* debug traceback logging
* parsed intermediate representation logging.

When enabled, diagnostic output is written alongside the output JSON:

- `XMLconv.log` for standard output (`stdout`)
- `debug.log` for standard error (`stderr`)

### CLI only

Install the package as a CLI utility from [PyPI](https://pypi.org/project/europassxml-to-reactiveresumejson/):

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install ./europassxml_to_reactiveresumejson-*.whl
```

Show the available options:

```python
europass-convert --help
```

> [!TIP]
> The CLI can also run as a module:
> ```bash
> python3 -m europass_converter.cli --help
> ```

Check the installed version:

```python
europass-convert --version
```

#### Convert a Europass XML file

```python
europass-convert "./path/to/cv.xml" \
  --template "./100_src/sample.json" \
  --output "./output/resume.json" \
  --no-split-pages
```

The resulting file can then be imported into Reactive Resume as a JSON Resume v5 file.

#### Convert from a Europass PDF

Some Europass PDF files contain the original XML as an embedded attachment called `attachment.xml`.

The CLI expects an XML file as input. To extract the XML from a Europass PDF:

```bash
# sudo apt-get install poppler-utils   # install `pdfdetach` if needed
pdfdetach -savefile attachment.xml -o cv.xml cv.pdf
```

Then convert the extracted XML:

```python
europass-convert "./cv.xml" \
  --template "./100_src/sample.json" \
  --output "./output/resume.json" \
  --no-split-pages
```

### From source

Clone the repository and prepare the virtual environment:

```bash
git clone https://github.com/FATelarico/EuropassXML_to_ReactiveResumeJSON.git
cd EuropassXML_to_ReactiveResumeJSON
```
From source, the project can be installed with:
|Installation mode|Command|
|-----------------|-------|
|CLI only         |`bash ./100_src/install_dependencies.sh`|
|GUI support      |`bash ./100_src/install_dependencies.sh --gui`|
|Development      |`bash ./100_src/install_dependencies.sh --dev`|

In all cases, the CLI can be ran:

```bash
# As a module from the source tree
.venv/bin/python -m europass_converter.cli --help
# Or as an installed library
source .venv/bin/activate
europass-convert --help
```

## Conversion mapping

The converter follows these mapping rules.

### Personal information

| Europass XML source           | Reactive Resume JSON                                           |
| ----------------------------- | -------------------------------------------------------------- |
| `CandidatePerson/PersonName`  | `basics.name`                                                  |
| email contact channels        | `basics.email`, additional emails to `basics.customFields`     |
| telephone contact channels    | `basics.phone`, additional phones to `basics.customFields`     |
| website contact channels      | `basics.website`, additional websites to `basics.customFields` |
| social/academic profile links | `sections.profiles.items[]`                                    |
| address locality              | `basics.location`                                              |
| nationality                   | `basics.customFields`                                          |
| birth date/year               | `basics.customFields`                                          |

By default, contact priority follows XML order unless the user provides `--preferred-email`, `--preferred-phone`, and/or `--preferred-website` or fills the corresponding boxes in the GUI.

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

Europass `Others` blocks with title `Course` become certification items: `sections.certifications.items[]`.

### Publications

Europass `Others` blocks with title `Pubblications` or `Publications` are parsed as publication groups.

The mapper splits only obvious HTML list items into individual publication records. If the group cannot be split safely, it is preserved as a custom `Publications` section.

### Conferences and seminars

`ConferencesAndSeminars/ConferenceAndSeminar` entries become a `customSections[]` with `type = "projects"`.

### Other blocks

Other Europass `Others` blocks are preserved under a custom section called 'dditional information'.

The mapper does not guess whether miscellaneous blocks are awards, interests, skills, or projects.

### Languages

Native languages from `PrimaryLanguageCode` are mapped as:

```text
fluency = "Native"
level = 5
```

Foreign languages from `PersonQualifications/PersonCompetency` are mapped using CEFR scores:

* the numeric level is based on the lowest available CEFR score
* the displayed fluency is based on the spoken CEFR level
* if both spoken interaction and spoken production exist, the lower of the two is used
* incomplete CEFR data is preserved during parsing and handled conservatively during mapping.

### References

If the XML does not provide references, the converter aadds an 'Available upon request' placeholder.

## HTML sanitisation

Europass XML often stores escaped HTML fragments. The converter decodes and sanitises these fragments into the output JSON.

* Allowed semantic tags: `p`, `br`, `ul`, `ol`, `li`, `strong`, `em`, `u`, `a`

* Allowed link protocols: `http`, `https`, `mailto`, `tel`

* Headings are converted to `p`/`strong` markup.

* Plain text without HTML tags is converted to paragraph HTML.

* The sanitiser also removes or normalises:
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

By default, the converter builds `metadata.layout.pages` using a standard resume section order and includes only sections that contain content.

To prevent the converter from creating multiple layout page entries, use `--no-split-pages`. In the GUI, this is the default behaviour.

This does not guarantee that the Reactive Resume will not paginate overflowing content when exported to PDF. It only prevents the converter from splitting `metadata.layout.pages`.

## Template handling

The converter treats the provided template JSON as the source of Reactive Resume defaults.

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

It rebuilds only the `metadata.layout.pages` field.

## Python API

> [!CAUTION]
> For most users, the CLI is the primary interface; the Python API is intended for embedding and automation.

The main high-level Python API is provided by `europass_converter.converter`.

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
````

### Convert parsed data

```python
from europass_converter.converter import convert_parsed
from europass_converter.parse_candidate import parse_candidate_file
from europass_converter.template import load_template

parsed = parse_candidate_file("sample.xml")
template = load_template("sample.json")

result = convert_parsed(
    parsed,
    template,
    preferred_email=None,
    preferred_phone=None,
    preferred_website=None,
    split_pages=True,
)
```

### Convert an XML string

```python
from europass_converter.converter import convert_xml_string
from europass_converter.template import load_template

template = load_template("sample.json")

with open("sample.xml", "r", encoding="utf-8") as handle:
    xml_string = handle.read()

result = convert_xml_string(
    xml_string,
    template,
    preferred_email=None,
    preferred_phone=None,
    preferred_website=None,
    split_pages=True,
)
```

## Known limitations

This project converts Europass CV data into a format compatible with Reactive Resume v5. Because the two data models differ, some limitations apply:

* Not every Europass field has a direct equivalent in Reactive Resume. Some information may be simplified, merged, or omitted when no suitable target field exists.
* Custom Europass sections, uncommon metadata, and future schema extensions may not be fully supported.
* Formatting, styling, and layout are not preserved. The conversion focuses on structured content rather than presentation.
* Date formats, language proficiency levels, and other standardised Europass values may be normalised to match Reactive Resume's data model.
* Validation is best-effort. Generated output should always be reviewed before use.
* Support for legacy Europass schemas is incomplete and not a primary development target.
* Reactive Resume itself may evolve over time. Future changes to the Reactive Resume JSON schema could require updates to this converter.

If you encounter unsupported files or mapping issues, please open an issue and attach a minimal reproducible example whenever possible.

## Licensing

Source code in this repository is licensed under the GNU Affero General Public License v3.0 (`AGPL-3.0`), unless stated otherwise.

Documentation, including README files, manuals, and explanatory text, is licensed under Creative Commons Attribution-ShareAlike 4.0 International (`CC-BY-SA-4.0`), unless stated otherwise.

Sample files, test fixtures, and third-party assets may be subject to separate licensing terms as indicated in their respective files or directories.
