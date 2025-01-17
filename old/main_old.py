'''
# -*- coding: utf-8 -*-

import sys
import os
import yaml

#from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QSize, QCoreApplication, QMetaObject, Qt
from PyQt5.QtWidgets import QWidget, QGridLayout, QGroupBox, QFormLayout, \
    QLabel, QLineEdit, QComboBox, QPushButton, QTextBrowser, QApplication, \
    QMainWindow

from mysql.connector import connect, Error
from datetime import datetime

from QrBarCode import QRcode, print_QR
from SQLv2 import create_database, create_table, show_databases, query_add_data
'''

class ConfigLoader:
    def __init__(self, config_path):
        self.config_path = config_path
    
    def load_config(self):
        # Изменение текущего каталога на каталог conf
        os.chdir(self.config_path)

        # Открытие файла конфигурации
        with open("conf.yaml", "r") as config_file:
            # Считывание значений из файла конфигурации
            config = yaml.safe_load(config_file)

        # Возвращение считанных значений
        return config


class Ui_PrintQR(object):
 
    #text = None

    def setupUi(self, PrintQR):

        # Создание экземпляра класса ConfigLoader
        config_loader = ConfigLoader("conf")

        # Загрузка конфигурации
        self.config = config_loader.load_config()

        self.host_sess = self.config["host_sess"]
        self.port_sess = self.config["port_sess"]
        self.user_sess = self.config["user_sess"]
        self.pass_sess = self.config["pass_sess"]
        self.connect_base = self.config["connect_base"]
        self.name_table = self.config["name_table"]
        self.modules = self.config["modules"]
        self.module = self.modules[0]
        self.boards = self.config["boards"]
        self.board = self.boards[0]
        self.builds = self.config["builds"]
        self.build = self.builds[0]
        #self.module_state = self.config["module_state"]
        self.name_columns = self.config["name_columns"]

        #self.host_sess = self.config["host_sess"]

        PrintQR.setObjectName("PrintQR")
        PrintQR.resize(503, 270)
        PrintQR.setAutoFillBackground(False)
        self.centralwidget = QWidget(PrintQR)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")

        #Группа: база данных 
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName("groupBox")
        self.formLayout = QFormLayout(self.groupBox)
        self.formLayout.setObjectName("formLayout")

        ##Адрес сервера
        self.label = QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)
        #Ввод адреса сервера
        self.host = QLineEdit(self.groupBox)
        self.host.setMinimumSize(QSize(110, 0))
        self.host.setText("")
        self.host.setObjectName("host")
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.host)

        #Имя пользователя
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)
        #Ввод имени пользователя
        self.input_user = QLineEdit(self.groupBox)
        self.input_user.setMinimumSize(QSize(110, 0))
        self.input_user.setObjectName("input_user")
        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.input_user)

        #Пароль пользователя 
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)
        #Ввод пароля пользователя
        self.input_pass = QLineEdit(self.groupBox)
        self.input_pass.setMinimumSize(QSize(110, 0))
        self.input_pass.setObjectName("input_pass")
        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.input_pass)

        #Имя базы данных
        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName("label_7")
        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_7)
        #Отображение имени базы данных
        self.lineEdit = QLineEdit(self.groupBox)
        self.lineEdit.setAutoFillBackground(False)
        self.lineEdit.setText("")
        self.lineEdit.setFrame(True)
        self.lineEdit.setDragEnabled(False)
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setObjectName("lineEdit")
        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.lineEdit)

        #Группа: информация о модуле
        self.gridLayout.addWidget(self.groupBox, 0, 0, 2, 1)
        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName("groupBox_2")
        self.formLayout_2 = QFormLayout(self.groupBox_2)
        self.formLayout_2.setObjectName("formLayout_2")

        #Наименование модуля
        self.label_4 = QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_4)
        #Список имен модулей
        self.module_names = QComboBox(self.groupBox_2)
        self.module_names.setMinimumSize(QSize(15, 0))
        self.module_names.setObjectName("module_names")
        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.module_names)

        #Версия модуля
        self.label_5 = QLabel(self.groupBox_2)
        self.label_5.setObjectName("label_5")
        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_5)
        #Список версий модулей
        self.boards_ver = QComboBox(self.groupBox_2)
        self.boards_ver.setMinimumSize(QSize(15, 0))
        self.boards_ver.setObjectName("boards_ver")
        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.boards_ver)

        #Версия сборки
        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName("label_6")
        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_6)
        #Список версий сборки
        self.builds_ver = QComboBox(self.groupBox_2)
        self.builds_ver.setEnabled(True)
        self.builds_ver.setMinimumSize(QSize(15, 0))
        self.builds_ver.setObjectName("builds_ver")
        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.builds_ver)
        self.gridLayout.addWidget(self.groupBox_2, 0, 1, 1, 1)

        #Кнопка: повторно распечатать QR-код
        self.pushButton_2 = QPushButton(self.centralwidget)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout.addWidget(self.pushButton_2, 1, 1, 1, 1)
        self.pushButton_2.setEnabled(False)

        #Кнопка: подключение к базе данных
        self.ConnectBD = QPushButton(self.centralwidget)
        self.ConnectBD.setObjectName("ConnectBD")
        self.gridLayout.addWidget(self.ConnectBD, 2, 0, 1, 1)

        #Кнопка: Сгенерировать и распечатать QR-код
        self.pushButton = QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 2, 1, 1, 1)

        #Окно вывода
        self.TextBrowser = QTextBrowser(self.centralwidget)
        self.TextBrowser.setObjectName("TextBrowser")
        self.gridLayout.addWidget(self.TextBrowser, 3, 0, 1, 2)
        PrintQR.setCentralWidget(self.centralwidget)

        self.TextBrowser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)


        self.ConnectBD.clicked.connect(self.onButtonClick)
        self.pushButton.clicked.connect(self.qrButtonClick)
        self.pushButton_2.clicked.connect(self.qr2ButtonClick)
        
        self.module_names.addItems(self.modules)
        self.boards_ver.addItems(self.boards)
        self.builds_ver.addItems(self.builds)


        
        self.module_names.currentIndexChanged.connect(self.moduleActivated)
        self.boards_ver.currentIndexChanged.connect(self.boardActivated)
        self.builds_ver.currentIndexChanged.connect(self.buildActivated)

        self.TextBrowser.textChanged.connect(self.TextBrowser.verticalScrollBar().maximum)


        self.retranslateUi(PrintQR)
        QMetaObject.connectSlotsByName(PrintQR)
    

    def retranslateUi(self, PrintQR):
        _translate = QCoreApplication.translate
        PrintQR.setWindowTitle(_translate("PrintQR", "PrintQR"))
        self.groupBox.setTitle(_translate("PrintQR", "База данных"))
        self.label.setText(_translate("PrintQR", "Адрес сервера"))
        self.label_2.setText(_translate("PrintQR", "Имя пользователя"))
        self.label_3.setText(_translate("PrintQR", "Пароль пользователя"))
        self.label_7.setText(_translate("PrintQR", "Имя базы данных"))
        self.groupBox_2.setTitle(_translate("PrintQR", "Иформация о модуле"))
        self.label_4.setText(_translate("PrintQR", "Наименование"))
        self.label_5.setText(_translate("PrintQR", "Версия платы"))
        self.label_6.setText(_translate("PrintQR", "Версия сборки"))
        self.pushButton_2.setText(_translate("PrintQR", "Повторно распечатать QR-code"))
        self.ConnectBD.setText(_translate("PrintQR", "Подключение к Базе данных"))
        self.pushButton.setText(_translate("PrintQR", "Сгенерировать и распечатать QR-code"))
        self.host.setText(_translate("PrintQR", self.host_sess + ":" + self.port_sess))
        self.lineEdit.setText(_translate("PrintQR", self.connect_base)) #Метод устанавливающий названия элементов приложения


    def onButtonClick (self):

        sess = self.host.text()
        fsess = sess.split(":")
        self.host_sess = fsess[0]
        self.port_sess = fsess[1]
        self.user_sess = self.input_user.text()
        self.pass_sess = self.input_pass.text()
        session = [self.host_sess, self.port_sess, self.user_sess, self.pass_sess]

        state_base =  show_databases (connect, Error, session)

        text = self.TextBrowser.toPlainText()

        if state_base == True: text += "Подключение установлено.\n"
        else: text += "Не удалось подключиться!\n"
        self.TextBrowser.setText(text)
        self.TextBrowser.verticalScrollBar().setValue(self.TextBrowser.verticalScrollBar().maximum()) #Метод кнопки подключение к базе данных


    def qrButtonClick (self):

        point_datetime = datetime.now()
        base_datetime = point_datetime.strftime("%Y-%m-%d %H:%M:%S") # %f - микросекунды
        print_datatime = point_datetime.strftime("%y%m%d%H%M%S") # %f - микросекунды
        
        if len(self.board) == 3: self.print_data = print_datatime + "  " + self.board
        else: self.print_data = print_datatime + " " + self.board
        

        data_records = [(base_datetime, self.user_sess, self.module, self.board, self.build)]

        sess = self.host.text()
        fsess = sess.split(":")
        self.host_sess = fsess[0]
        self.port_sess = fsess[1]
        self.user_sess = self.input_user.text()
        self.pass_sess = self.input_pass.text()
        session = [self.host_sess, self.port_sess, self.user_sess, self.pass_sess]

        state_base2 = query_add_data (connect, Error, session, self.connect_base, self.name_table, self.name_columns, data_records)
        
        text = self.TextBrowser.toPlainText()

        if state_base2 == True:
           text += "Данные добавлены.\n"
        else:
           text += "Ошибка при добавлении данных!\n"
           self.TextBrowser.setText(text)
           self.TextBrowser.verticalScrollBar().setValue(self.TextBrowser.verticalScrollBar().maximum())
           return

        QRcode (self.print_data)
        state_print = print_QR ()
        if state_print == None: text += "QR-code печать выполнена.\n"
        else: text += "Ошибка печати QR-code!\n"

        self.TextBrowser.setText(text)
        self.TextBrowser.verticalScrollBar().setValue(self.TextBrowser.verticalScrollBar().maximum())
        self.pushButton_2.setEnabled(True) #Метод кнопки сгенерировать и распечатать QR
        
  
    def qr2ButtonClick (self):

        text = self.TextBrowser.toPlainText()
        
        QRcode (self.print_data)
        state_print = print_QR ()
        if state_print == None: text += "QR-code печать выполнена повторно.\n"
        else: text += "Ошибка повторной печати QR-code!\n"
        
        self.TextBrowser.setText(text)
        self.TextBrowser.verticalScrollBar().setValue(self.TextBrowser.verticalScrollBar().maximum())
        self.pushButton_2.setEnabled(False) #Метод кнопки повтрорно распечатать QR
        

    def moduleActivated (self):
        self.module = self.module_names.currentText()
        print(self.module)
       
    def boardActivated (self):
        self.board = self.boards_ver.currentText()
        print(self.board)

    def buildActivated (self):
        self.build = self.builds_ver.currentText()
        print(self.build)
        

    
if __name__ == "__main__":


    app  = QApplication(sys.argv)
    main = QMainWindow()
    win = Ui_PrintQR()
    # 
    win.setupUi(main)
    main.show()
    status = app.exec_()
    sys.exit(status)
