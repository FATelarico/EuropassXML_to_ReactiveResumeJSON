import subprocess
import sys
import sysconfig
from pathlib import Path

from pypdf import PdfReader

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QMainWindow,
    QDialog,
    QApplication,
    QFileDialog,
    QMessageBox,
)
from .ui_mainwindow import Ui_EuropassXML_to_ReactiveResumeJSON # Ui_MainWindow
from .ui_adv import Ui_adv # Ui_Dialog

import media_rc

def get_data_file(relative_path: str) -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent / relative_path,
        Path(sysconfig.get_path("data")) / relative_path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[-1]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_EuropassXML_to_ReactiveResumeJSON() # Ui_MainWindow()
        self.ui.setupUi(self)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY_ROOT = Path(__file__).resolve().parent


def load_ui(path: Path, parent=None):
    if not path.exists():
        raise FileNotFoundError(f"UI file not found: {path}")

    loader = QUiLoader()
    ui_file = QFile(str(path))

    if not ui_file.open(QFile.ReadOnly):
        raise RuntimeError(f"Could not open UI file: {path}")

    window = loader.load(ui_file, parent)
    ui_file.close()

    if window is None:
        raise RuntimeError(f"Could not load UI file: {path}")

    return window


def extract_attachment_xml_from_pdf(
    pdf_path: Path,
    output_dir: Path,
    save_as: str = "attachment.xml",
) -> Path:
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        raise RuntimeError(f"Could not read PDF file:\n{exc}") from exc

    attachments = getattr(reader, "attachments", None)

    if not attachments:
        raise FileNotFoundError(
            "No embedded files were found in the selected PDF.\nIs it a PDF CV exported from Europass?"
        )

    for filename, file_data_list in attachments.items():
        if Path(filename).name.lower() == "attachment.xml":
            xml_path = output_dir / save_as
            xml_path.write_bytes(file_data_list[0])
            return xml_path

    available = ", ".join(attachments.keys())

    raise FileNotFoundError(
        "The selected PDF does not contain attachment.xml.\n\n"
        f"Embedded files found: {available or 'none'}"
    )


class App:
    def __init__(self):
        self.window = MainWindow()
        self.adv_window = None
        self.adv_ui = None

        self.input_path = None
        self.output_path = None

        self.window.setWindowTitle("Europass Converter")
        self.setup_main_window()

    def setup_main_window(self):
        self.window.ui.check03.setEnabled(False)
        self.window.ui.check03.setChecked(False)

        self.window.ui.combo06.setItemData(
            0,
            # str(PROJECT_ROOT / "100_src" / "sample.json"),
            str(get_data_file("100_src/sample.json")),
        )

        self.window.ui.tool04.clicked.connect(self.select_input_file)
        self.window.ui.btn07a.clicked.connect(self.open_advanced_window)
        self.window.ui.btn07b.clicked.connect(self.run_converter)

    def setup_advanced_window(self):
        self.adv_ui.combo11.clear()
        self.adv_ui.combo11.addItems(["0", "1", "2"])

        self.adv_ui.spin10.setValue(2)
        self.adv_ui.check10.setChecked(False)
        self.adv_ui.check12a.setChecked(False)
        self.adv_ui.check12b.setChecked(False)

        self.adv_ui.btn13.clicked.connect(self.adv_window.close)

    def get_advanced_values(self):
        if self.adv_ui is None:
            return {
                "indent": 2,
                "compact": False,
                "verbose": "0",
                "debug": False,
                "debug_parsed": False,
            }

        return {
            "indent": self.adv_ui.spin10.value(),
            "compact": self.adv_ui.check10.isChecked(),
            "verbose": self.adv_ui.combo11.currentText(),
            "debug": self.adv_ui.check12a.isChecked(),
            "debug_parsed": self.adv_ui.check12b.isChecked(),
        }

    def select_input_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Select input file",
            "",
            "Input files (*.xml *.pdf);;XML files (*.xml);;PDF files (*.pdf)",
        )

        if not path:
            return

        self.input_path = Path(path)
        self.window.ui.ledit04.setText(str(self.input_path))

        is_pdf = self.input_path.suffix.lower() == ".pdf"
        self.window.ui.check03.setEnabled(is_pdf)
        # self.window.ui.check03.setChecked(is_pdf)

    def open_advanced_window(self):
        if self.adv_ui is None:
            self.adv_window = QDialog(self.window)
            self.adv_ui = Ui_adv()
            self.adv_ui.setupUi(self.adv_window)
            self.setup_advanced_window()

        self.adv_window.show()
        self.adv_window.raise_()
        self.adv_window.activateWindow()

    def run_converter(self):
        if self.input_path is None:
            QMessageBox.warning(
                self.window,
                "Missing input",
                "Select an XML or PDF file first.",
            )
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Save converted JSON",
            str(self.input_path.with_suffix(".json")),
            "JSON files (*.json)",
        )

        if not output_path:
            return

        self.output_path = Path(output_path)
        output_dir = self.output_path.parent

        xml_input_path = self.input_path

        if self.input_path.suffix.lower() == ".pdf":
            try:
                xml_input_path = extract_attachment_xml_from_pdf(
                    self.input_path,
                    output_dir,
                    save_as="Europass.xml",
                )
            except FileNotFoundError as exc:
                QMessageBox.warning(
                    self.window,
                    "Missing attachment.xml",
                    str(exc),
                )
                return
            except Exception as exc:
                QMessageBox.critical(
                    self.window,
                    "PDF extraction failed",
                    str(exc),
                )
                return

        elif self.input_path.suffix.lower() != ".xml":
            QMessageBox.warning(
                self.window,
                "Unsupported input file",
                "Select either an XML file or a PDF containing attachment.xml.",
            )
            return

        template_path = Path(self.window.ui.combo06.currentData())
        adv = self.get_advanced_values()

        cmd = [
            sys.executable,
            "-m",
            "europass_converter.cli",
            str(xml_input_path),
            "--template",
            str(template_path),
            "--output",
            str(self.output_path),
            "--indent",
            str(adv["indent"]),
            "--verbose",
            adv["verbose"],
        ]

        if self.window.ui.check05.isChecked():
            cmd.append("--no-split-pages")

        if adv["compact"]:
            cmd.append("--compact")

        preferred_email = self.window.ui.tedit08a.toPlainText().strip()
        preferred_phone = self.window.ui.tedit08b.toPlainText().strip()
        preferred_website = self.window.ui.tedit08c.toPlainText().strip()

        if preferred_email:
            cmd += ["--preferred-email", preferred_email]

        if preferred_phone:
            cmd += ["--preferred-phone", preferred_phone]

        if preferred_website:
            cmd += ["--preferred-website", preferred_website]

        if adv["debug"]:
            cmd.append("--debug")

        if adv["debug_parsed"]:
            cmd.append("--debug-parsed")

        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            text=True,
            capture_output=True,
        )

        # combined_log = result.stdout + "\n" + result.stderr

        if int(adv["verbose"]) > 0:
            (output_dir / "XMLconv.log").write_text(
                result.stdout, # combined_log,
                encoding="utf-8",
            )

        if adv["debug"] or adv["debug_parsed"]:
            (output_dir / "debug.log").write_text(
                result.stderr,
                encoding="utf-8",
            )

        if result.returncode != 0:
            QMessageBox.critical(
                self.window,
                "Conversion failed",
                f"Conversion failed. See logs in:\n{output_dir}",
            )
            return

        message_lines = [
            f"Output written to:\n{self.output_path}",
        ]

        if self.window.ui.check03.isChecked():
            message_lines.append(
                f"\nExtracted XML saved to:\n{output_dir / 'Europass.xml'}"
            )

        if int(adv["verbose"]) > 0:
            message_lines.append(
                f"\nLog saved to:\n{output_dir / 'XMLconv.log'}"
            )

        if adv["debug"] and adv["debug_parsed"]:
            message_lines.append(
                f"\nConversion and parsing debug outputs saved to:\n{output_dir / 'debug.log'}"
            )
        elif adv["debug"]:
            message_lines.append(
                f"\nConversion debug info saved to:\n{output_dir / 'debug.log'}"
            )
        elif adv["debug_parsed"]:
            message_lines.append(
                f"\nDebug info for the parsing was saved to:\n{output_dir / 'debug.log'}"
            )

        QMessageBox.information(
            self.window,
            "Conversion complete",
            "\n".join(message_lines),
        )

    def show(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()



def main():
    app = QApplication(sys.argv)

    try:
        gui = App()
        gui.show()
        sys.exit(app.exec())
    except Exception as exc:
        print(f"ERROR: {exc}")
        QMessageBox.critical(None, "Startup error", str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()