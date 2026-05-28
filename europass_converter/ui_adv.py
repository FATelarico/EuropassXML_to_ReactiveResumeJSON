# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'adv.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFormLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_adv(object):
    def setupUi(self, adv):
        if not adv.objectName():
            adv.setObjectName(u"adv")
        adv.resize(320, 240)
        self.verticalLayoutWidget = QWidget(adv)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(0, 0, 321, 241))
        self.vbox08 = QVBoxLayout(self.verticalLayoutWidget)
        self.vbox08.setSpacing(3)
        self.vbox08.setObjectName(u"vbox08")
        self.vbox08.setContentsMargins(6, 6, 6, 6)
        self.vspc08a = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.vbox08.addItem(self.vspc08a)

        self.label08 = QLabel(self.verticalLayoutWidget)
        self.label08.setObjectName(u"label08")
        self.label08.setMaximumSize(QSize(16777215, 32))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label08.setFont(font)

        self.vbox08.addWidget(self.label08)

        self.vspc08b = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.vbox08.addItem(self.vspc08b)

        self.vbox09 = QVBoxLayout()
        self.vbox09.setObjectName(u"vbox09")
        self.form10 = QFormLayout()
        self.form10.setObjectName(u"form10")
        self.label10a = QLabel(self.verticalLayoutWidget)
        self.label10a.setObjectName(u"label10a")
        self.label10a.setMinimumSize(QSize(200, 0))
        self.label10a.setMaximumSize(QSize(16777215, 16777215))

        self.form10.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label10a)

        self.spin10 = QSpinBox(self.verticalLayoutWidget)
        self.spin10.setObjectName(u"spin10")
        self.spin10.setMinimumSize(QSize(32, 0))
        self.spin10.setMaximumSize(QSize(64, 16777215))
        self.spin10.setMinimum(0)
        self.spin10.setValue(2)

        self.form10.setWidget(0, QFormLayout.ItemRole.FieldRole, self.spin10)

        self.label10b = QLabel(self.verticalLayoutWidget)
        self.label10b.setObjectName(u"label10b")
        self.label10b.setMinimumSize(QSize(200, 0))

        self.form10.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label10b)

        self.check10 = QCheckBox(self.verticalLayoutWidget)
        self.check10.setObjectName(u"check10")

        self.form10.setWidget(1, QFormLayout.ItemRole.FieldRole, self.check10)


        self.vbox09.addLayout(self.form10)

        self.hbox11 = QHBoxLayout()
        self.hbox11.setObjectName(u"hbox11")
        self.label11 = QLabel(self.verticalLayoutWidget)
        self.label11.setObjectName(u"label11")
        self.label11.setMinimumSize(QSize(64, 0))
        self.label11.setMaximumSize(QSize(64, 16777215))

        self.hbox11.addWidget(self.label11)

        self.combo11 = QComboBox(self.verticalLayoutWidget)
        self.combo11.addItem("")
        self.combo11.addItem("")
        self.combo11.addItem("")
        self.combo11.setObjectName(u"combo11")

        self.hbox11.addWidget(self.combo11)


        self.vbox09.addLayout(self.hbox11)

        self.hbox12 = QHBoxLayout()
        self.hbox12.setObjectName(u"hbox12")
        self.check12a = QCheckBox(self.verticalLayoutWidget)
        self.check12a.setObjectName(u"check12a")
        self.check12a.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.hbox12.addWidget(self.check12a)

        self.check12b = QCheckBox(self.verticalLayoutWidget)
        self.check12b.setObjectName(u"check12b")
        self.check12b.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.hbox12.addWidget(self.check12b)


        self.vbox09.addLayout(self.hbox12)

        self.vspc09 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.vbox09.addItem(self.vspc09)

        self.hbox13 = QHBoxLayout()
        self.hbox13.setObjectName(u"hbox13")
        self.hbox13.setContentsMargins(240, -1, -1, -1)
        self.btn13 = QPushButton(self.verticalLayoutWidget)
        self.btn13.setObjectName(u"btn13")
        self.btn13.setMinimumSize(QSize(64, 0))
        self.btn13.setMaximumSize(QSize(64, 16777215))
        self.btn13.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        icon = QIcon(QIcon.fromTheme(u"emblem-default"))
        self.btn13.setIcon(icon)

        self.hbox13.addWidget(self.btn13)


        self.vbox09.addLayout(self.hbox13)


        self.vbox08.addLayout(self.vbox09)


        self.retranslateUi(adv)

        QMetaObject.connectSlotsByName(adv)
    # setupUi

    def retranslateUi(self, adv):
        adv.setWindowTitle(QCoreApplication.translate("adv", u"Dialog", None))
        self.label08.setText(QCoreApplication.translate("adv", u"Advanced options", None))
        self.label10a.setText(QCoreApplication.translate("adv", u"JSON indentation level", None))
        self.label10b.setText(QCoreApplication.translate("adv", u"Write compact single-line JSON", None))
        self.label11.setText(QCoreApplication.translate("adv", u"Verbosity", None))
        self.combo11.setItemText(0, QCoreApplication.translate("adv", u"suppresses diagnostics", None))
        self.combo11.setItemText(1, QCoreApplication.translate("adv", u"prints diagnostics when present", None))
        self.combo11.setItemText(2, QCoreApplication.translate("adv", u"also prints a success summary", None))

        self.check12a.setText(QCoreApplication.translate("adv", u"Full traceback", None))
        self.check12b.setText(QCoreApplication.translate("adv", u"Debug parsed JSON", None))
        self.btn13.setText(QCoreApplication.translate("adv", u"Apply", None))
    # retranslateUi

