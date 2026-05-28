# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QTextEdit, QToolButton,
    QVBoxLayout, QWidget)
import media_rc

class Ui_EuropassXML_to_ReactiveResumeJSON(object):
    def setupUi(self, EuropassXML_to_ReactiveResumeJSON):
        if not EuropassXML_to_ReactiveResumeJSON.objectName():
            EuropassXML_to_ReactiveResumeJSON.setObjectName(u"EuropassXML_to_ReactiveResumeJSON")
        EuropassXML_to_ReactiveResumeJSON.resize(640, 480)
        EuropassXML_to_ReactiveResumeJSON.setMinimumSize(QSize(640, 480))
        EuropassXML_to_ReactiveResumeJSON.setMaximumSize(QSize(640, 480))
        self.verticalLayoutWidget = QWidget(EuropassXML_to_ReactiveResumeJSON)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(0, 20, 641, 461))
        self.vbox00 = QVBoxLayout(self.verticalLayoutWidget)
        self.vbox00.setObjectName(u"vbox00")
        self.vbox00.setContentsMargins(12, 12, 12, 12)
        self.vspc00b = QSpacerItem(20, 2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.vbox00.addItem(self.vspc00b)

        self.hbox01 = QHBoxLayout()
        self.hbox01.setObjectName(u"hbox01")
        self.hspc01a = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hbox01.addItem(self.hspc01a)

        self.logo01a = QLabel(self.verticalLayoutWidget)
        self.logo01a.setObjectName(u"logo01a")
        self.logo01a.setMaximumSize(QSize(256, 128))
        self.logo01a.setPixmap(QPixmap(u":/210_svg/Europass_Simbol.svg"))
        self.logo01a.setScaledContents(True)
        self.logo01a.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hbox01.addWidget(self.logo01a)

        self.vbox02 = QVBoxLayout()
        self.vbox02.setSpacing(0)
        self.vbox02.setObjectName(u"vbox02")
        self.logo02 = QLabel(self.verticalLayoutWidget)
        self.logo02.setObjectName(u"logo02")
        self.logo02.setMinimumSize(QSize(128, 128))
        self.logo02.setMaximumSize(QSize(64, 64))
        self.logo02.setPixmap(QPixmap(u":/211_png/transform.png"))
        self.logo02.setScaledContents(True)
        self.logo02.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.vbox02.addWidget(self.logo02)

        self.vspc02 = QSpacerItem(20, 52, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.vbox02.addItem(self.vspc02)


        self.hbox01.addLayout(self.vbox02)

        self.logo01b = QLabel(self.verticalLayoutWidget)
        self.logo01b.setObjectName(u"logo01b")
        self.logo01b.setMaximumSize(QSize(128, 128))
        self.logo01b.setPixmap(QPixmap(u":/210_svg/reactive-resume.svg"))
        self.logo01b.setScaledContents(True)
        self.logo01b.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hbox01.addWidget(self.logo01b)

        self.hspc01b = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hbox01.addItem(self.hspc01b)


        self.vbox00.addLayout(self.hbox01)

        self.vspc00b_2 = QSpacerItem(20, 13, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.vbox00.addItem(self.vspc00b_2)

        self.vbox03 = QVBoxLayout()
        self.vbox03.setSpacing(2)
        self.vbox03.setObjectName(u"vbox03")
        self.hbox04 = QHBoxLayout()
        self.hbox04.setObjectName(u"hbox04")
        self.label04 = QLabel(self.verticalLayoutWidget)
        self.label04.setObjectName(u"label04")

        self.hbox04.addWidget(self.label04)

        self.ledit04 = QLineEdit(self.verticalLayoutWidget)
        self.ledit04.setObjectName(u"ledit04")

        self.hbox04.addWidget(self.ledit04)

        self.tool04 = QToolButton(self.verticalLayoutWidget)
        self.tool04.setObjectName(u"tool04")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.FolderVisiting))
        self.tool04.setIcon(icon)

        self.hbox04.addWidget(self.tool04)


        self.vbox03.addLayout(self.hbox04)

        self.check03 = QCheckBox(self.verticalLayoutWidget)
        self.check03.setObjectName(u"check03")
        self.check03.setEnabled(False)

        self.vbox03.addWidget(self.check03)


        self.vbox00.addLayout(self.vbox03)

        self.hbox05 = QHBoxLayout()
        self.hbox05.setObjectName(u"hbox05")
        self.label05 = QLabel(self.verticalLayoutWidget)
        self.label05.setObjectName(u"label05")
        self.label05.setMinimumSize(QSize(23, 22))
        self.label05.setMaximumSize(QSize(23, 22))
        self.label05.setPixmap(QPixmap(u":/210_svg/document.svg"))
        self.label05.setScaledContents(True)

        self.hbox05.addWidget(self.label05)

        self.check05 = QCheckBox(self.verticalLayoutWidget)
        self.check05.setObjectName(u"check05")
        self.check05.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.check05.setChecked(True)

        self.hbox05.addWidget(self.check05)

        self.hspc05 = QSpacerItem(60, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.hbox05.addItem(self.hspc05)


        self.vbox00.addLayout(self.hbox05)

        self.hbox06 = QHBoxLayout()
        self.hbox06.setObjectName(u"hbox06")
        self.icon06 = QLabel(self.verticalLayoutWidget)
        self.icon06.setObjectName(u"icon06")
        self.icon06.setMinimumSize(QSize(22, 22))
        self.icon06.setMaximumSize(QSize(22, 22))
        self.icon06.setPixmap(QPixmap(u":/210_svg/template.svg"))
        self.icon06.setScaledContents(True)

        self.hbox06.addWidget(self.icon06)

        self.label06 = QLabel(self.verticalLayoutWidget)
        self.label06.setObjectName(u"label06")

        self.hbox06.addWidget(self.label06)

        self.combo06 = QComboBox(self.verticalLayoutWidget)
        self.combo06.addItem("")
        self.combo06.setObjectName(u"combo06")

        self.hbox06.addWidget(self.combo06)

        self.hspc06 = QSpacerItem(60, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.hbox06.addItem(self.hspc06)

        self.tool06 = QToolButton(self.verticalLayoutWidget)
        self.tool06.setObjectName(u"tool06")

        self.hbox06.addWidget(self.tool06)


        self.vbox00.addLayout(self.hbox06)

        self.grid08 = QGridLayout()
        self.grid08.setObjectName(u"grid08")
        self.tedit08b = QTextEdit(self.verticalLayoutWidget)
        self.tedit08b.setObjectName(u"tedit08b")
        self.tedit08b.setMaximumSize(QSize(324, 24))
        self.tedit08b.setAutoFillBackground(False)
        self.tedit08b.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tedit08b.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tedit08b.setTabChangesFocus(True)

        self.grid08.addWidget(self.tedit08b, 1, 2, 1, 1)

        self.label08b = QLabel(self.verticalLayoutWidget)
        self.label08b.setObjectName(u"label08b")
        self.label08b.setMinimumSize(QSize(0, 24))
        self.label08b.setMaximumSize(QSize(164, 24))

        self.grid08.addWidget(self.label08b, 1, 1, 1, 1)

        self.tedit08a = QTextEdit(self.verticalLayoutWidget)
        self.tedit08a.setObjectName(u"tedit08a")
        self.tedit08a.setMaximumSize(QSize(324, 24))
        self.tedit08a.setAutoFillBackground(False)
        self.tedit08a.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tedit08a.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tedit08a.setTabChangesFocus(True)

        self.grid08.addWidget(self.tedit08a, 0, 2, 1, 1)

        self.label08a = QLabel(self.verticalLayoutWidget)
        self.label08a.setObjectName(u"label08a")
        self.label08a.setMinimumSize(QSize(0, 24))
        self.label08a.setMaximumSize(QSize(164, 24))

        self.grid08.addWidget(self.label08a, 0, 1, 1, 1)

        self.label08c = QLabel(self.verticalLayoutWidget)
        self.label08c.setObjectName(u"label08c")
        self.label08c.setMinimumSize(QSize(0, 24))
        self.label08c.setMaximumSize(QSize(164, 24))

        self.grid08.addWidget(self.label08c, 2, 1, 1, 1)

        self.tedit08c = QTextEdit(self.verticalLayoutWidget)
        self.tedit08c.setObjectName(u"tedit08c")
        self.tedit08c.setMaximumSize(QSize(324, 24))
        self.tedit08c.setAutoFillBackground(False)
        self.tedit08c.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tedit08c.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tedit08c.setTabChangesFocus(True)

        self.grid08.addWidget(self.tedit08c, 2, 2, 1, 1)

        self.icon08a = QLabel(self.verticalLayoutWidget)
        self.icon08a.setObjectName(u"icon08a")
        self.icon08a.setMinimumSize(QSize(22, 22))
        self.icon08a.setMaximumSize(QSize(22, 22))
        self.icon08a.setPixmap(QPixmap(u":/210_svg/email.svg"))
        self.icon08a.setScaledContents(True)

        self.grid08.addWidget(self.icon08a, 0, 0, 1, 1)

        self.icon08b = QLabel(self.verticalLayoutWidget)
        self.icon08b.setObjectName(u"icon08b")
        self.icon08b.setMinimumSize(QSize(22, 22))
        self.icon08b.setMaximumSize(QSize(22, 22))
        self.icon08b.setPixmap(QPixmap(u":/210_svg/phone.svg"))
        self.icon08b.setScaledContents(True)

        self.grid08.addWidget(self.icon08b, 1, 0, 1, 1)

        self.icon08c = QLabel(self.verticalLayoutWidget)
        self.icon08c.setObjectName(u"icon08c")
        self.icon08c.setMinimumSize(QSize(22, 22))
        self.icon08c.setMaximumSize(QSize(22, 22))
        self.icon08c.setPixmap(QPixmap(u":/210_svg/websites.svg"))
        self.icon08c.setScaledContents(True)

        self.grid08.addWidget(self.icon08c, 2, 0, 1, 1)


        self.vbox00.addLayout(self.grid08)

        self.hbox07 = QHBoxLayout()
        self.hbox07.setObjectName(u"hbox07")
        self.hbox07.setContentsMargins(400, -1, -1, -1)
        self.btn07a = QPushButton(self.verticalLayoutWidget)
        self.btn07a.setObjectName(u"btn07a")

        self.hbox07.addWidget(self.btn07a)

        self.hspc07 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.hbox07.addItem(self.hspc07)

        self.btn07b = QPushButton(self.verticalLayoutWidget)
        self.btn07b.setObjectName(u"btn07b")

        self.hbox07.addWidget(self.btn07b)


        self.vbox00.addLayout(self.hbox07)

        self.vspc00a = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.vbox00.addItem(self.vspc00a)


        self.retranslateUi(EuropassXML_to_ReactiveResumeJSON)

        QMetaObject.connectSlotsByName(EuropassXML_to_ReactiveResumeJSON)
    # setupUi

    def retranslateUi(self, EuropassXML_to_ReactiveResumeJSON):
        EuropassXML_to_ReactiveResumeJSON.setWindowTitle(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"EuropassXML_to_ReactiveResumeJSON", None))
        self.logo01a.setText("")
        self.logo02.setText("")
        self.logo01b.setText("")
        self.label04.setText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Select Europass file", None))
        self.ledit04.setPlaceholderText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Path to Europass file", None))
        self.tool04.setText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"...", None))
        self.check03.setText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Save XML extracted from Europass CV (only applies to PDF files)", None))
        self.label05.setText("")
        self.check05.setText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Prevent the converter from creating metdata for page splitting, RR will still paginate PDFs", None))
        self.icon06.setText("")
        self.label06.setText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Select a ReactiveResume template", None))
        self.combo06.setItemText(0, QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Rhyhorn", None))

        self.tool06.setText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"...", None))
        self.tedit08b.setPlaceholderText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Default: First phone number in the Europass file", None))
        self.label08b.setText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Preferred phone number", None))
        self.tedit08a.setPlaceholderText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Default: First email in the Europass file", None))
        self.label08a.setText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Preferred email", None))
        self.label08c.setText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Preferred website", None))
        self.tedit08c.setPlaceholderText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Default: First phone number in the Europass file", None))
        self.icon08a.setText("")
        self.icon08b.setText("")
        self.icon08c.setText("")
        self.btn07a.setText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Advanced", None))
        self.btn07b.setText(QCoreApplication.translate("EuropassXML_to_ReactiveResumeJSON", u"Convert", None))
    # retranslateUi

