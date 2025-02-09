# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'design_v1.1.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_PrintQR(object):
    def setupUi(self, PrintQR):
        PrintQR.setObjectName("PrintQR")
        PrintQR.resize(503, 270)
        PrintQR.setAutoFillBackground(False)
        self.centralwidget = QtWidgets.QWidget(PrintQR)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setObjectName("groupBox")
        self.formLayout = QtWidgets.QFormLayout(self.groupBox)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.host = QtWidgets.QLineEdit(self.groupBox)
        self.host.setMinimumSize(QtCore.QSize(100, 0))
        self.host.setText("")
        self.host.setObjectName("host")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.host)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.input_user = QtWidgets.QLineEdit(self.groupBox)
        self.input_user.setMinimumSize(QtCore.QSize(100, 0))
        self.input_user.setObjectName("input_user")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.input_user)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.input_pass = QtWidgets.QLineEdit(self.groupBox)
        self.input_pass.setMinimumSize(QtCore.QSize(100, 0))
        self.input_pass.setObjectName("input_pass")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.input_pass)
        self.label_7 = QtWidgets.QLabel(self.groupBox)
        self.label_7.setObjectName("label_7")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_7)
        self.lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit.setAutoFillBackground(False)
        self.lineEdit.setText("")
        self.lineEdit.setFrame(True)
        self.lineEdit.setDragEnabled(False)
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setObjectName("lineEdit")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.lineEdit)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 2, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName("groupBox_2")
        self.formLayout_2 = QtWidgets.QFormLayout(self.groupBox_2)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_4 = QtWidgets.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.module_name = QtWidgets.QComboBox(self.groupBox_2)
        self.module_name.setMinimumSize(QtCore.QSize(15, 0))
        self.module_name.setObjectName("module_name")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.module_name)
        self.label_5 = QtWidgets.QLabel(self.groupBox_2)
        self.label_5.setObjectName("label_5")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.board_ver = QtWidgets.QComboBox(self.groupBox_2)
        self.board_ver.setMinimumSize(QtCore.QSize(15, 0))
        self.board_ver.setObjectName("board_ver")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.board_ver)
        self.label_6 = QtWidgets.QLabel(self.groupBox_2)
        self.label_6.setObjectName("label_6")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_6)
        self.build_ver = QtWidgets.QComboBox(self.groupBox_2)
        self.build_ver.setEnabled(True)
        self.build_ver.setMinimumSize(QtCore.QSize(15, 0))
        self.build_ver.setObjectName("build_ver")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.build_ver)
        self.gridLayout.addWidget(self.groupBox_2, 0, 1, 1, 1)
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout.addWidget(self.pushButton_2, 1, 1, 1, 1)
        self.ConnectBD = QtWidgets.QPushButton(self.centralwidget)
        self.ConnectBD.setObjectName("ConnectBD")
        self.gridLayout.addWidget(self.ConnectBD, 2, 0, 1, 1)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 2, 1, 1, 1)
        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser.setObjectName("textBrowser")
        self.gridLayout.addWidget(self.textBrowser, 3, 0, 1, 2)
        PrintQR.setCentralWidget(self.centralwidget)

        self.retranslateUi(PrintQR)
        QtCore.QMetaObject.connectSlotsByName(PrintQR)

    def retranslateUi(self, PrintQR):
        _translate = QtCore.QCoreApplication.translate
        PrintQR.setWindowTitle(_translate("PrintQR", "MainWindow"))
        self.groupBox.setTitle(_translate("PrintQR", "База данных"))
        self.label.setText(_translate("PrintQR", "Адрес сервера"))
        self.label_2.setText(_translate("PrintQR", "Имя пользователя"))
        self.label_3.setText(_translate("PrintQR", "Пароль пользователя"))
        self.input_pass.setText(_translate("PrintQR", "192.192.192.192"))
        self.label_7.setText(_translate("PrintQR", "Имя базы данных"))
        self.groupBox_2.setTitle(_translate("PrintQR", "Иформация о модуле"))
        self.label_4.setText(_translate("PrintQR", "Наименование"))
        self.label_5.setText(_translate("PrintQR", "Версия платы"))
        self.label_6.setText(_translate("PrintQR", "Версия сборки"))
        self.pushButton_2.setText(_translate("PrintQR", "Повторно распечатать QR"))
        self.ConnectBD.setText(_translate("PrintQR", "Подключение к Базе данных"))
        self.pushButton.setText(_translate("PrintQR", "Сгенерировать и распечатать QR-Code"))
