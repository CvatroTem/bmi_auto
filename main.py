import re
import warnings
import sys
import os
import yaml
import serial
import serial.tools.list_ports
import time
import socket
import requests
import asyncio
from bleak import BleakScanner
import json

import paramiko
import time
import threading
import pytz
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon, QTextCursor
from PyQt5.QtCore import QSize, QCoreApplication, QMetaObject, Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QGridLayout, QGroupBox, QFormLayout, \
    QLabel, QLineEdit, QComboBox, QPushButton, QTextBrowser, QApplication, \
    QMainWindow

from sqlalchemy import create_engine
from mysql.connector import connect, Error
from datetime import datetime, timedelta

from db_utils_v2 import show_databases, search_data, add_update_data
from data.print_design_v5 import Ui_PrintQR
from QrBarCode import QRcode, print_QR
from SQLv2 import show_databases, query_add_data

utc = pytz.UTC
def get_current_time_plus_3_hours():
    return datetime.now() + timedelta(hours=3)
class ConfigLoader:
    def __init__(self, config_path):
        self.config_path = config_path
    
    def load_config(self):
        os.chdir(self.config_path)
        with open("conf.yaml", "r") as config_file:
            config = yaml.safe_load(config_file)
        return config

class MACAddressReader:
    def __init__(self, search_texts=["STMicroelectronics Virtual COM Port", "USB-Enhanced-SERIAL CH343", "Prolific USB-to-Serial Comm Port"]):

        self.search_texts = search_texts
        self.com_port = None

    def find_com_ports(self):
        ports = serial.tools.list_ports.comports(include_links=False)
        for port in ports:
            for search_text in self.search_texts:
                if search_text in port.description:
                    print("Port found " + port.device)
                    return port.device
        return None

    def read_mac_address(self, module_name):
        """
        Функция для получения MAC-адреса. Для G-Tracker и G-Tracker Master сначала переводит устройство в нужный режим,
        а затем переподключается для отправки команды получения MAC-адреса.
        """
        self.com_port = self.find_com_ports()
        if not self.com_port:
            print(f"No ports with the specified description found!")
            return None

        try:
            # Открываем COM порт
            with serial.Serial(self.com_port, baudrate=115200, timeout=1) as ser:
                print(f"Opened port: {self.com_port}")

                # Если выбран G-Tracker или G-Tracker Master, отправляем команду для перевода в режим
                if module_name in ["G-Tracker", "G-Tracker Master"]:
                    print("Sending AT+MODE=5,0 to enter correct mode")
                    try:
                        ser.write(b'AT+MODE=5,0\r\n')
                        time.sleep(2)  # Ждем 2 секунды для обработки команды устройством
                        ser.close()  # Закрываем соединение, чтобы устройство могло переподключиться
                        # print("Device switching modes, waiting for reconnection...")

                        # Ждем, пока устройство переподключится
                        time.sleep(1)  # Увеличьте время ожидания, если необходимо
                        # print("Reconnecting to the device...")

                        # Пытаемся снова подключиться к устройству
                        with serial.Serial(self.com_port, baudrate=115200, timeout=1) as ser:
                            # print("Reconnected to device.")
                            # Отправляем команду для получения MAC-адреса
                            return self._get_mac_address(ser)

                    except serial.SerialException as se:
                        print(f"Error sending AT+MODE command: {se}")
                        return None

                # Если модуль не требует переключения режима, сразу запрашиваем MAC-адрес
                return self._get_mac_address(ser)

        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            return None

    def _get_mac_address(self, ser):
        """
        Вспомогательная функция для получения MAC-адреса.
        """
        
        try:
            ser.write(b'AT+BLEADDR?\r\n')

            response = ser.readlines()
            for line in response:
                decoded_line = line.decode('utf-8').strip()
                print(f"BLEADDR response: {decoded_line}")
                if decoded_line and decoded_line != 'OK':
                    return decoded_line.replace(":", "")  # Удаляем двоеточия из MAC-адреса
        except serial.SerialException as se:
            print(f"Error sending AT+BLEADDR command: {se}")
            return None




class PrintQR(QMainWindow, Ui_PrintQR):
    modules_no_db = ["АФУ", "POE Инжектор", "USB-HUB"]

    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Инициализируем интерфейс на самом себе
        self.parent = self  # Устанавливаем родительский виджет как себя
        self.mac_reader = MACAddressReader()
        self.qr_state_file = os.path.abspath(os.path.join("conf", "qr_state.json"))
        self.qr_state = self.load_qr_state()
        self.last_message = ""
        config_loader = ConfigLoader("conf")
        self.config = config_loader.load_config()

        self.mac_check_tables = [
            "bmi_mark",
            "siz_module",
            "bracelet_module",
            "beacon_module"
        ]
        

        # Инициализация потока сканирования Bluetooth
        self.bluetooth_thread = BluetoothScanThread()
        self.bluetooth_thread.devices_found.connect(self.handle_devices_found)
        self.bluetooth_thread.scan_failed.connect(self.handle_scan_failed)
        
        # Остальная инициализация UI
        self.updateUi()


    def load_qr_state(self):
        """Загружает состояние из файла, если он существует, иначе возвращает пустой словарь."""
        if os.path.exists(self.qr_state_file):
            with open(self.qr_state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}  # Если файла нет, возвращаем пустой словарь

    def save_qr_state(self):
        """Сохраняет текущее состояние в файл после каждой генерации QR-кода, если MAC-адрес корректен."""
        try:
            # Фильтруем только нужные модули
            filtered_qr_state = {module: number for module, number in self.qr_state.items() if module in ["G-Tracker", "Радиомаяк", "Радиометка КСИЗ"]}
            with open(self.qr_state_file, "w", encoding="utf-8") as f:
                json.dump(filtered_qr_state, f, indent=4, ensure_ascii=False)
            self.TextBrowser.append(self.grey + "Состояние QR успешно сохранено.")
        except IOError as e:
            self.TextBrowser.append(self.red + f"Ошибка сохранения состояния QR: {e}")

        
    def update_qr_state(self, module_name, next_number):
        """Обновляет состояние QR и сохраняет его в JSON-файл только для определенных модулей."""
        if module_name in ["G-Tracker", "Радиомаяк", "Радиометка КСИЗ"]:
            try:
                self.qr_state[module_name] = next_number
                self.save_qr_state()
            except Exception as e:
                self.TextBrowser.append(self.red + f"Ошибка при обновлении JSON: {e}")
        else:
            # Для остальных модулей не обновляем qr_state.json
            pass



    def update_ui_number(self, module_name):
        """Обновляет UI номер для модулей G-Tracker, Радиомаяк, Радиометка КСИЗ в Borodino."""
        if module_name in ["G-Tracker", "Радиомаяк", "Радиометка КСИЗ"]:
            self.BorodinoBoxNewDropdown.setVisible(True)
            self.BorodinoLabelProductNumber.setVisible(True)
            
            next_number = self.calculate_next_number(module_name)
            self.BorodinoBoxNewDropdown.blockSignals(True)  # Отключаем сигналы
            
            self.BorodinoBoxNewDropdown.clear()

            if module_name == "G-Tracker":
                counts = list(range(2, 9))  # 2-8
            elif module_name in ["Радиометка КСИЗ", "Радиомаяк"]:
                counts = list(range(1, 17))  # 1-16
            else:
                counts = [next_number]

            self.BorodinoBoxNewDropdown.addItems([str(c) for c in counts])

            index = self.BorodinoBoxNewDropdown.findText(str(next_number), QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.BorodinoBoxNewDropdown.setCurrentIndex(index)
            else:
                self.TextBrowser.append(self.red + f"Значение {next_number} для {module_name} не найдено в выпадающем списке.")

            self.BorodinoBoxNewDropdown.blockSignals(False)  # Включаем сигналы обратно
        else:
            self.BorodinoBoxNewDropdown.setVisible(False)
            self.BorodinoLabelProductNumber.setVisible(False)

    def get_next_qr_number(self, module_name):
        """Возвращает следующий номер для указанного модуля без обновления состояния."""
        if module_name in ["G-Tracker", "Радиомаяк", "Радиометка КСИЗ"]:
            # Получаем текущий MAC-адрес из интерфейса
            mac_address = self.BorodinoInputMACAddress.text()
            if not mac_address:
                self.TextBrowser.append(self.red + "MAC-адрес не указан.")
                return None

            # Проверяем, существует ли MAC-адрес в базе данных
            if self.is_mac_in_database(mac_address):
                self.TextBrowser.append(self.red + "MAC-адрес уже существует в базе данных.")
                return None  # Прерываем процесс, не обновляем JSON

            # Вычисляем следующий номер
            current_number = self.qr_state.get(module_name, self.get_initial_value(module_name))
            
            if module_name == "G-Tracker":
                next_number = current_number + 1 if current_number < 8 else 2
            elif module_name in ["Радиометка КСИЗ", "Радиомаяк"]:
                next_number = current_number + 1 if current_number < 16 else 1
            else:
                next_number = current_number  # По умолчанию без изменений

            return next_number
        return None  # Для других модулей возвращаем None


    def calculate_next_number(self, module_name):
        """Вычисляет следующий номер для указанного модуля без обновления состояния."""
        current_number = self.qr_state.get(module_name, self.get_initial_value(module_name))
        
        if module_name == "G-Tracker":
            next_number = current_number + 1 if current_number < 8 else 2
        elif module_name in ["Радиометка КСИЗ", "Радиомаяк"]:
            next_number = current_number + 1 if current_number < 16 else 1
        else:
            next_number = current_number  # По умолчанию без изменений
        
        # Если номер сбросился на 1, обновляем JSON
        if next_number == 1:
            self.qr_state[module_name] = 0
            self.save_qr_state()
        
        return next_number




    def get_initial_value(self, module_name):
        """Возвращает начальное значение для нового модуля."""
        if module_name == "G-Tracker":
            return 2
        elif module_name == "Радиометка КСИЗ":
            return 1
        elif module_name == "Радиомаяк":
            return 1
        return 1

    def handle_dropdown_selection_change(self, index):
        """
        Обрабатывает изменение выбранного номера изделия в выпадающем списке.
        Устанавливает значение в qr_state на выбранный номер -1 и сохраняет JSON.
        """
        module_name = self.BorodinoBoxNameMod.currentText()
        selected_number_str = self.BorodinoBoxNewDropdown.itemText(index)
        
        try:
            selected_number = int(selected_number_str)
        except ValueError:
            self.TextBrowser.append(self.red + f"Некорректный выбранный номер: {selected_number_str}")
            return
        
        # Получаем начальное значение для проверки
        initial_value = self.get_initial_value(module_name)
        
        # Определяем максимальное допустимое значение
        if module_name == "G-Tracker":
            max_value = 8
        elif module_name in ["Радиометка КСИЗ", "Радиомаяк"]:
            max_value = 16
        else:
            max_value = selected_number  # Должно соответствовать выбранному номеру
        
        # Проверяем, что выбранный номер находится в допустимом диапазоне
        if not (initial_value <= selected_number <= max_value):
            self.TextBrowser.append(self.red + f"Выбранный номер {selected_number} выходит за допустимый диапазон для {module_name}.")
            return
        
        # Обновляем состояние QR
        self.qr_state[module_name] = selected_number - 1
        self.save_qr_state()
       # self.TextBrowser.append(self.green + f"Номер изделия для {module_name} установлен на {selected_number}. JSON обновлён.")



    def updateUi(self):
        self.green = "<span style='background-color: #72fc65;'>__</span>"
        self.red = "<span style='background-color: #fc6565;'>__</span>"
        self.yellow = "<span style='background-color: #fafc65;'>__</span>"
        self.grey = "<span style='background-color: #a6a6a6;'>__</span>"

        # config_loader = ConfigLoader("conf")
        # self.config = config_loader.load_config()

        self.SessHost = self.config["host_sess"]
        self.SessPort = self.config["port_sess"]
        self.SessUser = self.config["user_sess"]
        self.SessPass = self.config["pass_sess"]
        self.ConnectBase = self.config["connect_base"]
        self.NameTable = self.config["name_table"]
        self.modules = self.config["modules"]
        self.module = self.modules[0]
        self.boards = self.config["boards"]
        self.board = self.boards[0]
        self.builds = self.config["builds"]
        self.build = self.builds[0]
        self.NameColumns = self.config["name_columns"]

        self.InputPass.setEchoMode(QLineEdit.Password)

        self._translate = QCoreApplication.translate
        self.InputHost.setText(self._translate("PrintQR", self.SessHost + ":" + self.SessPort))
        self.InputBD.setText(self._translate("PrintQR", self.ConnectBase))
        self.InputUser.setText(self._translate("PrintQR", self.SessUser))
        self.InputPass.setText(self._translate("PrintQR", self.SessPass))

        self.InputBD.setEnabled(False)

        self.StatePrint = not None
        self.StateBase = None
        self.PressButton = None

        self.TextBrowser.setMinimumSize(QSize(0, 150))
        self.TextBrowser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.TextBrowser.textChanged.connect(self.TextBrowser.verticalScrollBar().maximum)

        self.ConnectBD.clicked.connect(self.connect_base)
        self.PushGenPrintQR.clicked.connect(self.qr_click)
        self.BorodinoPushGenPrintQR.clicked.connect(self.borodino_qr_click)
        self.ManualPush.clicked.connect(self.print_copy)
        self.BorodinoReadMACButton.clicked.connect(self.read_mac_address_and_update_ui)
        
        self.BoxNameMod.addItems(self.modules)
        self.BoxName.addItems(self.modules)
        self.BoxBoardVer.addItems(self.boards)
        self.BoxBuildVer.addItems(self.builds)

        self.BoxName.currentIndexChanged.connect(self.moduleActivated)
        self.BoxNameMod.currentIndexChanged.connect(self.moduleActivated)
        self.BoxName.addItems(['Borodino'])
        self.BoxBoardVer.currentIndexChanged.connect(self.boardActivated)
        self.BoxBuildVer.currentIndexChanged.connect(self.buildActivated)

        self.TabsQR.currentChanged.connect(self.tab_changed)
        self.TabsQR.currentChanged.connect(self.moduleActivated)

        self.BorodinoBoxNameMod.currentIndexChanged.connect(self.update_generate_button_state)

        self.ManualNumber.returnPressed.connect(self.update_module_number)
        self.BorodinoBoxNewDropdown.currentIndexChanged.connect(self.handle_dropdown_selection_change)
        self.BorodinoInputMACAddress.textChanged.connect(self.update_generate_button_state)
        self.BorodinoPushGenPrintQR.setEnabled(False)


        self.ProgressBar.setAlignment(Qt.AlignCenter)
        self.ProgressBar.setFormat("")
        self.ProgressBar.setEnabled(False)
        self.ProgressBar.setProperty("value", 0)

    def moduleActivated(self):
        if self.TabsQR.currentIndex() == 1:
            self.module = self.BoxName.currentText()  
        else:
            self.module = self.BoxNameMod.currentText()
            
        if self.module in ("BMI", "Bracelet", "G-Tracker"):
            self.ConnectBase = "goodwin_bmi_prod"
            self.NameTable = "bmi_module"
        elif self.module == "Termit":
            self.ConnectBase = "goodwin_termit_prod"
            self.NameTable = "termit_module"
        elif self.module == "Ural":
            self.ConnectBase = "goodwin_ural_prod"
            self.NameTable = "ural_module"
        elif self.module == "A-Scaner":
            self.ConnectBase = "goodwin_ascaner_prod"
            self.NameTable = "ascaner_module"
        elif self.module == "Borodino":
            self.ConnectBase = "Borodino_series"

        self.InputBD.setText(self.ConnectBase)
        print(self.module)
        print(self.ConnectBase)

        # Вызов метода обновления UI
        self.update_ui_number(self.module)



    def boardActivated(self):
        self.board = self.BoxBoardVer.currentText()
        print(self.board)

    def buildActivated(self):
        self.build = self.BoxBuildVer.currentText()
        print(self.build)

    def tab_changed(self, index):
        if index == 0:
            self.PushGenPrintQR.setFocus()
            self.ManualNumber.clearFocus()
        elif index == 1:
            self.ManualNumber.setFocus()
            self.PushGenPrintQR.clearFocus()

    def update_module_number(self):
        def process_number(number, ver_attr):
            if not number:
                self.DateSearch = None
                return

            # Определение префикса
            prefix = number.split(']')[0][1:]
            if prefix in ["Afd", "Poe", "Hub", "GCh", "Bppu", "BppuM", "GBraFe"]:
                self.current_number = number
                self.DateSearch = None
                self.TextBrowser.append(self.grey + f"{self.current_number}")
                return

            if len(number) != 17:
                self.DateSearch = None
                self.TextBrowser.append(self.red + "Некорректный идентификатор!")
                return

            self.current_number = number.replace('/', '.').replace('ю', '.')
            if not re.match(r"^\d{12}\s+\d+\.\d+$", self.current_number):
                self.TextBrowser.append(self.red + "Некорректный идентификатор!")
                self.ManualNumber.setFocus()
                self.DateSearch = None
                return

            numbers = re.split(" ", self.current_number)
            if len(numbers) == 3:
                setattr(self, ver_attr, numbers[2])
            elif len(numbers) == 2:
                setattr(self, ver_attr, numbers[1])
            else:
                return
            DateNumber = numbers[0]
            self.DateSearch = (
                "20" + DateNumber[0:2]
                + "-" + DateNumber[2:4]
                + "-" + DateNumber[4:6]
                + " " + DateNumber[6:8]
                + ":" + DateNumber[8:10]
                + ":" + DateNumber[10:12]
            )
            text = self.TextBrowser.toPlainText()
            lines = text.split("\n")
            if lines[-1] == f"__{self.DateSearch} {getattr(self, ver_attr)}":
                return
            self.TextBrowser.append(self.grey + f"{self.DateSearch} {getattr(self, ver_attr)}")

        process_number(self.ManualNumber.text(), "ManualVerNumber")


    def show_progress_bar(self, success, failure): 
        if self.PressButton:
            self.ProgressBar.setEnabled(True)
            self.ProgressBar.setFormat("%p%")
            self.ProgressBar.setMaximum(100)
            self.ProgressBar.setStyleSheet("QProgressBar::chunk { background-color: #72fc65; }")

            if self.PressButton == "connect_base":
                if self.StateBase:
                    for i in range(1, 101):  # Полностью заполняем прогресс-бар
                        self.ProgressBar.setValue(i)
                        QThread.msleep(2)
                    self.PressButton = None
                    self.StateBase = None
                    if success:  # Сообщение при успешном завершении
                        self.TextBrowser.append(self.green + success)
                else:
                    for i in range(1, 51):
                        self.ProgressBar.setValue(i)
                        QThread.msleep(2)
                    self.ProgressBar.setStyleSheet("QProgressBar::chunk { background-color: #fc6565; }")
                    self.ProgressBar.setValue(51)
                    self.PressButton = None
                    self.TextBrowser.append(self.red + failure)

                QThread.msleep(300)
                self.ProgressBar.setProperty("value", 0)
                self.ProgressBar.setFormat("")
                self.ProgressBar.setEnabled(False)

            elif self.PressButton == "qr_click":
                if self.StatePrint is None:
                    for i in range(1, 101):  # Полностью заполняем прогресс-бар
                        self.ProgressBar.setValue(i)
                        QThread.msleep(2)
                    if success:  # Сообщение при успешном завершении
                        self.TextBrowser.append(self.green + success)
                    self.PressButton = None
                else:
                    for i in range(1, 51):
                        self.ProgressBar.setValue(i)
                        QThread.msleep(2)
                    self.ProgressBar.setStyleSheet("QProgressBar::chunk { background-color: #fc6565; }")
                    self.ProgressBar.setValue(51)
                    QThread.msleep(300)
                    self.ProgressBar.setProperty("value", 0)
                    self.ProgressBar.setFormat("")
                    self.ProgressBar.setEnabled(False)
                    self.PressButton = None
                    self.TextBrowser.append(self.red + failure)
                    self.PushGenPrintQR.setEnabled(True)
                    self.BorodinoPushGenPrintQR.setEnabled(True)
                    
            # Сбрасываем прогресс-бар после завершения любой операции
            QThread.msleep(300)
            self.ProgressBar.setProperty("value", 0)
            self.ProgressBar.setFormat("")
            self.ProgressBar.setEnabled(False)


    def connect_base(self):   
        self.PressButton = "connect_base"
        success = "Подключение установлено."
        failure = "Не удалось подключиться!"

        self.SessHost = self.InputHost.text().split(":")[0]  # Адрес сервера
        self.SessPort = self.InputHost.text().split(":")[1]  # Порт сервера
        self.SessUser = self.InputUser.text()  # Логин пользователя
        self.SessPass = self.InputPass.text()  # Пароль пользователя
        session = [self.SessHost, self.SessPort, self.SessUser, self.SessPass]

        self.StateBase = show_databases(connect, Error, session)
        self.show_progress_bar(success, failure)

    def qr_click(self):
        self.PushGenPrintQR.setEnabled(False)
        self.PressButton = "qr_click"

        # Захватываем время один раз с использованием UTC
        point_datetime = datetime.now()
        base_datetime = point_datetime.strftime("%Y-%m-%d %H:%M:%S")
        print_datatime = point_datetime.strftime("%y%m%d%H%M%S")

        if len(self.board) == 3:
            self.print_data = print_datatime + "  " + self.board
        else:
            self.print_data = print_datatime + " " + self.board

        self.SessHost = self.InputHost.text().split(":")[0]  # Адрес сервера
        self.SessPort = self.InputHost.text().split(":")[1]  # Порт сервера
        self.SessUser = self.InputUser.text()  # Логин пользователя
        self.SessPass = self.InputPass.text()  # Пароль пользователя
        session = [self.SessHost, self.SessPort, self.SessUser, self.SessPass]
        data_records = [(base_datetime, self.SessUser, self.module, self.board, self.build)]

        name_columns = ["DATETIME_ID", "USER", "NAME_VER", "BOARD_VER", "BUILD_VER"]
        
        self.StateBase = query_add_data(connect, Error, session, self.ConnectBase, self.NameTable, name_columns, data_records)
        
        if not self.StateBase:
            self.TextBrowser.append(self.red + "Ошибка при записи данных в базу данных!")
        else:
            self.TextBrowser.append(self.green + "Данные успешно записаны в базу данных.")

        # Передаем point_datetime в функцию генерации QR-кода
        QRcode(self.print_data)
        self.StatePrint = print_QR()

        if self.StatePrint is None:
            self.TextBrowser.append(self.green + "QR-код успешно отправлен на принтер.")
        else:
            self.TextBrowser.append(self.red + "Ошибка при печати QR-кода!")

        self.PushGenPrintQR.setEnabled(True)

    def process_serial_number_input(self):
        """Функция для обработки строки ввода серийного номера."""
        serial_input = self.InputSerialNumber.text().strip()

        if not serial_input:
            self.TextBrowser.append(self.red + "Строка серийного номера пуста.")
            return

        # Пытаемся найти дату и время в формате 12 цифр
        date_match = re.search(r'\d{12}', serial_input)
        if date_match:
            serial_number = date_match.group(0)
            self.TextBrowser.append(self.green + f"Дата и время найдены: {serial_number}")
            return serial_number

        # Пытаемся найти MAC-адрес (12 символов: цифры и заглавные буквы)
        mac_match = re.search(r'[A-F0-9]{12}', serial_input)
        if mac_match:
            serial_number = mac_match.group(0)
            self.TextBrowser.append(self.green + f"MAC-адрес найден: {serial_number}")
            return serial_number

        # Пытаемся найти id контроллера, например [BS]332315F0007100E2
        id_match = re.search(r'\[BS\](\w+)', serial_input)
        if id_match:
            serial_number = id_match.group(1)
            self.TextBrowser.append(self.green + f"ID контроллера найден: {serial_number}")
            return serial_number

        # Если введен номер с дополнительной информацией типа 241017092120  2.2
        clean_input = re.split(r'\s+', serial_input)
        if len(clean_input) >= 1:
            serial_number = clean_input[0]
            self.TextBrowser.append(self.green + f"Серийный номер после очистки: {serial_number}")
            return serial_number

        # Если ничего не найдено
        self.TextBrowser.append(self.red + "Невозможно определить серийный номер.")
        return None

    def print_copy(self):
        self.update_module_number()

        self.SessHost = self.InputHost.text().split(":")[0]
        self.SessPort = self.InputHost.text().split(":")[1]
        self.SessUser = self.InputUser.text()
        self.SessPass = self.InputPass.text()
        database_url = (f"mysql+mysqlconnector://"
                        f"{self.SessUser}:{self.SessPass}@"
                        f"{self.SessHost}:{self.SessPort}/"
                        f"{self.ConnectBase}")
        engine = create_engine(database_url)

        qr_code = self.ManualNumber.text()

        if not qr_code:
            self.TextBrowser.append(self.red + "Идентификатор не указан.")
            return

        if self.BoxName.currentText() == 'Borodino':
            # Логика для Borodino
            prefix = qr_code.split(']')[0][1:]

            if prefix == "GBraFe":
                connect_base = "goodwin_bracelet_prod"
                name_table = "bracelet_module"
            elif prefix == "GCh":
                connect_base = "goodwin_charge_prod"
                name_table = "charge_module"
            elif prefix in ["Afd", "Poe", "Hub"]:
                # Печать без проверки в базе данных
                QRcode(qr_code)
                self.StatePrint = print_QR()

                if self.StatePrint is None:
                    self.TextBrowser.append(self.green + "QR-code отправлен на принтер.")
                    self.ManualNumber.clear()
                    self.ManualNumber.setFocus()
                else:
                    self.TextBrowser.append(self.red + "Ошибка печати QR-code!")
                return
            elif prefix in ["Bppu", "BppuM"]:
                connect_base = "goodwin_bmi_prod"
                name_table = "bmi_mark"
            elif prefix == "Siz":
                connect_base = "goodwin_siz_prod"
                name_table = "siz_module"
            elif prefix == "BS":
                connect_base = "goodwin_base_station_prod"
                name_table = "base_station_module"
            elif prefix == "Borodino":
                connect_base = "goodwin_borodino_prod"
                name_table = "borodino_module"
            else:
                self.TextBrowser.append(self.red + "Неизвестный префикс QR-кода.")
                return

            self.TextBrowser.append(self.green + f"Проверка в базе данных: {connect_base}, таблица: {name_table}")

            if prefix not in ["Afd", "Poe", "Hub", "GCh"]:
                try:
                    engine = create_engine(f"mysql+mysqlconnector://{self.SessUser}:{self.SessPass}@{self.SessHost}:{self.SessPort}/{connect_base}")
                    search_params = {"QR": qr_code}
                    self.StateBase, ResultSearch = search_data(engine, name_table, search_params)

                    if self.StateBase:
                        self.TextBrowser.append(self.green + "Подключение установлено.")
                        if ResultSearch:
                            self.TextBrowser.append(self.green + "Устройство найдено в базе данных.")
                            print(ResultSearch)
                        else:
                            self.TextBrowser.append(self.red + "Устройство в базе данных не обнаружено!")
                            return
                    else:
                        self.TextBrowser.append(self.red + "Не удалось подключиться!")
                        print(ResultSearch)
                        return
                except Exception as e:
                    self.TextBrowser.append(self.red + f"Ошибка при подключении к базе данных: {e}")
                    return

            QRcode(qr_code)
            self.StatePrint = print_QR()

            if self.StatePrint is None:
                self.TextBrowser.append(self.green + "QR-code отправлен на принтер.")
                self.ManualNumber.clear()
                self.ManualNumber.setFocus()
            else:
                self.TextBrowser.append(self.red + "Ошибка печати QR-code!")
        else:
            # Старая логика для всех остальных модулей
            if len(self.ManualNumber.text()) != 17 and self.BoxName.currentText() not in ["Afd", "Poe", "Hub", "GCh"]:
                self.TextBrowser.append(self.red + "Некорректный идентификатор!")
                self.ManualNumber.setFocus()
                return

            self.current_number = self.ManualNumber.text().replace('/', '.').replace('ю', '.')
            if not re.match(r"^\d{12}\s+\d+\.\d+$", self.current_number) and self.BoxName.currentText() not in ["Afd", "Poe", "Hub", "GCh"]:
                self.TextBrowser.append(self.red + "Некорректный идентификатор!")
                self.ManualNumber.setFocus()
                return

            numbers = re.split(" ", self.current_number)
            DateNumber = numbers[0]
            self.DateSearch = (
                "20" + DateNumber[0:2]
                + "-" + DateNumber[2:4]
                + "-" + DateNumber[4:6]
                + " " + DateNumber[6:8]
                + ":" + DateNumber[8:10]
                + ":" + DateNumber[10:12]
            )

            self.SearchColumn = "DATETIME_ID"
            search_params = {self.SearchColumn: self.DateSearch}
            self.StateBase, ResultSearch = search_data(engine, self.NameTable, search_params)

            if self.StateBase:
                self.TextBrowser.append(self.green + "Подключение установлено.")
                if ResultSearch:
                    self.entity_id = ResultSearch[0][0]
                    ResultDate = ResultSearch[0][1]
                    FormDate = ResultDate.strftime("%Y-%m-%d %H:%M:%S")
                    if FormDate == self.DateSearch:
                        self.TextBrowser.append(self.green + "Устройство найдено в базе данных.")
                        print(ResultSearch)
                else:
                    print(ResultSearch)
                    self.TextBrowser.append(self.red + "Устройство в базе данных не обнаружено!")
                    return
            else:
                self.TextBrowser.append(self.red + "Не удалось подключиться!")
                print(ResultSearch)
                return

            QRcode(self.current_number)
            self.StatePrint = print_QR()

            if self.StatePrint is None:
                self.TextBrowser.append(self.green + "QR-code отправлен на принтер.")
                self.ManualNumber.clear()
                self.ManualNumber.setFocus()
            else:
                self.TextBrowser.append(self.red + "Ошибка печати QR-code!")


    def is_valid_mac(self, mac_address):
        """Функция для проверки правильности MAC-адреса (12 символов, только цифры и заглавные буквы)"""
        pattern = r"^[A-F0-9]{12}$"
        return re.match(pattern, mac_address) is not None
    
    def update_generate_button_state(self):
        """Активирует кнопку 'Сгенерировать и распечатать QR', если поле MAC-адреса заполнено или для модулей, не требующих MAC."""
        selected_module = self.BorodinoBoxNameMod.currentText()
        modules_no_mac = ["Беспроводная зарядка", "АФУ", "POE Инжектор", "USB-HUB", "Базовая станция"]
        
        if selected_module in modules_no_mac:
            # Для этих модулей кнопка всегда активна
            self.BorodinoPushGenPrintQR.setEnabled(True)
        else:
            # Для остальных модулей активна, только если есть MAC-адрес
            mac_text = self.BorodinoInputMACAddress.text().strip()
            self.BorodinoPushGenPrintQR.setEnabled(bool(mac_text))


    def is_mac_in_database(self, mac_address):
        """
        Проверяет наличие MAC-адреса в указанных таблицах, расположенных в разных базах данных.
        :param mac_address: MAC-адрес для проверки (строка без двоеточий, в верхнем регистре)
        :return: True, если MAC-адрес найден в любой из таблиц, иначе False
        """
        mac_address = mac_address.replace(":", "").upper()  # Удаляем двоеточия и приводим к верхнему регистру
        
        table_to_db = {
            "bmi_mark": "goodwin_bmi_prod",
            "siz_module": "goodwin_siz_prod",
            "bracelet_module": "goodwin_bracelet_prod",
            "beacon_module": "goodwin_beacon_prod"
        }

        host = self.SessHost
        port = self.SessPort
        user = self.SessUser
        password = self.SessPass

        try:
            for table, database in table_to_db.items():
                connection = connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database
                )
                cursor = connection.cursor()

                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if not cursor.fetchone():
                    message = f"Таблица {table} не существует в базе {database}, пропускаем."
                    if self.last_message != message:
                        self.TextBrowser.append(self.grey + message)
                        self.last_message = message
                    cursor.close()
                    connection.close()
                    continue

                query = f"SELECT COUNT(*) FROM {table} WHERE MAC = %s"
                cursor.execute(query, (mac_address,))
                result = cursor.fetchone()
                if result and result[0] > 0:
                    message = f"MAC-адрес найден в таблице {table} базы {database}."
                    if self.last_message != message:
                        self.TextBrowser.append(self.red + message)
                        self.last_message = message
                    cursor.close()
                    connection.close()
                    return True

                cursor.close()
                connection.close()

            return False

        except Error as e:
            message = f"Ошибка при подключении к базе данных или выполнении запроса: {e}"
            if self.last_message != message:
                self.TextBrowser.append(self.red + message)
                self.last_message = message
            return False


    def generate_g_tracker_master_qr(self, point_datetime):
        mac_address = self.BorodinoInputMACAddress.text()
        if not mac_address:
            self.TextBrowser.append(self.red + "MAC-адрес не указан.")
            return None

        mac_address = mac_address.replace(":", "")  # Удаление двоеточий из MAC-адреса
        if not self.is_valid_mac(mac_address):
            self.TextBrowser.append(self.red + "Неверный формат MAC-адреса! Введите 12 символов, только цифры и заглавные буквы.")
            return None

        serial_number = point_datetime.strftime("%y%m%d%H%M%S")
        qr_code = f"[BppuM]{mac_address},{serial_number},1"
        self.BorodinoInputMACAddress.clear()
        return qr_code
    
    def generate_g_tracker_qr(self, count, point_datetime):
        mac_address = self.BorodinoInputMACAddress.text()
        if not mac_address:
            self.TextBrowser.append(self.red + "MAC-адрес не указан.")
            return None

        mac_address = mac_address.replace(":", "")  # Удаление двоеточий из MAC-адреса
        
        # Проверка формата MAC-адреса
        if not self.is_valid_mac(mac_address):
            self.TextBrowser.append(self.red + "Неверный формат MAC-адреса! Введите 12 символов, только цифры и заглавные буквы.")
            return None
        serial_number = point_datetime.strftime("%y%m%d%H%M%S")
        
        # Используем переданный count
        qr_code = f"[Bppu]{mac_address},{serial_number},{count}"
        
        self.BorodinoInputMACAddress.clear()
        return qr_code


    
    def generate_siz_qr(self, count):
        mac_address = self.BorodinoInputMACAddress.text()
        if not mac_address:
            self.TextBrowser.append(self.red + "MAC-адрес не указан.")
            return None

        mac_address = mac_address.replace(":", "")
        if not self.is_valid_mac(mac_address):
            self.TextBrowser.append(self.red + "Некорректный MAC-адрес! Введите 12 символов.")
            return None

        # Используем переданный count
        qr_code = f"[Siz]{mac_address},{count}"

        self.BorodinoInputMACAddress.clear()
        return qr_code

    def generate_bracelet_qr(self):
        mac_address = self.BorodinoInputMACAddress.text()
        if not mac_address:
            self.TextBrowser.append(self.red + "MAC-адрес не указан.")
            return None

        mac_address = mac_address.replace(":", "")  # Удаление двоеточий из MAC-адреса
        if not self.is_valid_mac(mac_address):
            self.TextBrowser.append(self.red + "Некорректный MAC-адрес! Должен содержать 12 символов (цифры и заглавные буквы).")
            return None 
        current_index = self.BorodinoBoxNewDropdown.currentIndex()
        count = self.BorodinoBoxNewDropdown.itemText(current_index)
        next_index = (current_index + 1) % self.BorodinoBoxNewDropdown.count()
        self.BorodinoBoxNewDropdown.setCurrentIndex(next_index)

        qr_code = f"[GBraFe]{mac_address}"

        # print(f"Generated QR Code: {qr_code}")

        # self.TextBrowser.append(f"Generated QR Code: {qr_code}")  # Добавление отладочного сообщения в TextBrowser
        self.BorodinoInputMACAddress.clear()
        return qr_code
    
    def generate_beacon_qr(self, count):
        mac_address = self.BorodinoInputMACAddress.text()
        if not mac_address:
            self.TextBrowser.append(self.red + "MAC-адрес не указан.")
            return None

        mac_address = mac_address.replace(":", "")
        if not self.is_valid_mac(mac_address):
            self.TextBrowser.append(self.red + "Некорректный MAC-адрес! Введите 12 символов.")
            return None

        # Используем переданный count
        qr_code = f"[Beacon]{mac_address},{count}"

        self.BorodinoInputMACAddress.clear()
        return qr_code
    
    def generate_wireless_charger_qr(self, point_datetime):
        print_datatime = point_datetime.strftime("%y%m%d%H%M%S")
        qr_code = f"[GCh]{print_datatime}"
        return qr_code



    def check_ip(self, ip):
        self.TextBrowser.append(self.yellow + f"Проверка IP-адреса: {ip}")
        try:
            socket.create_connection((ip, 80), timeout=2)  # Установка тайм-аута в 2 секунды
            self.TextBrowser.append(self.green + f"IP-адрес {ip} доступен.")
            return True
        except Exception as e:
            self.TextBrowser.append(self.red + f"IP-адрес {ip} недоступен: {e}")
            return False

    def change_password_via_ssh(self):
        host = self.config['ssh_host']
        username = self.config['ssh_username']
        current_password = self.config['ssh_password']
        new_password = self.config['new_ssh_password']

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=host, username=username, password=current_password)

            # Открытие интерактивной сессии
            ssh_session = client.invoke_shell()

            def wait_for_prompt(expected_prompt, timeout=10):
                buffer = ""
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if ssh_session.recv_ready():
                        data = ssh_session.recv(1024).decode('utf-8')
                        buffer += data
                        if expected_prompt in buffer:
                            return buffer
                return buffer

            # Ожидание запроса текущего пароля
            output = wait_for_prompt("Current password:")
            
            if "Current password:" in output:
                ssh_session.send(f"{current_password}\n")

                # Ожидание запроса нового пароля
                output = wait_for_prompt("New password:")

                if "New password:" in output:
                    ssh_session.send(f"{new_password}\n")

                    # Ожидание повторного ввода нового пароля
                    output = wait_for_prompt("Retype new password:")

                    if "Retype new password:" in output:
                        ssh_session.send(f"{new_password}\n")

                        # Ожидание подтверждения успешного изменения пароля
                        output = wait_for_prompt("Password changed successfully", timeout=5)
                        if "Password changed successfully" in output:
                            return new_password
        except Exception as e:
            return None
        finally:
            client.close()

    def get_serial_number(self):
        host = self.config['ssh_host']
        username = self.config['ssh_username']
        password = self.config['new_ssh_password']  # Используем новый пароль

        self.TextBrowser.append(f"{self.grey}<span> Начат процесс получения серийного номера для {host}.</span>")
        self.TextBrowser.moveCursor(QTextCursor.End)
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=host, username=username, password=password)

            # Открытие интерактивной сессии для уверенности
            ssh_session = client.invoke_shell()

            # Выполнение команды для получения конфигурации
            ssh_session.send('cat /var/www/html/ini/global_conf.json\n')

            def wait_for_response(timeout=5):
                buffer = ""
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if ssh_session.recv_ready():
                        data = ssh_session.recv(1024).decode('utf-8')
                        buffer += data
                return buffer

            config_content = wait_for_response()

            if not config_content.strip():
                self.TextBrowser.append(f"{self.red}<span> Файл конфигурации пуст.</span>")
                self.TextBrowser.moveCursor(QTextCursor.End)
                return

            match = re.search(r'"gateway_ID":\s*"([0-9A-Fa-f]+)"', config_content)
            if match:
                serial_number = match.group(1)
                self.TextBrowser.append(f"{self.green}<span> Серийный номер успешно получен: {serial_number}</span>")
                self.TextBrowser.moveCursor(QTextCursor.End)
                return serial_number
            else:
                self.TextBrowser.append(f"{self.red}<span> Серийный номер не найден в конфигурации.</span>")
                self.TextBrowser.moveCursor(QTextCursor.End)

        except paramiko.SSHException as ssh_exception:
            self.TextBrowser.append(f"{self.red}<span> Ошибка подключения по SSH: {str(ssh_exception)}</span>")
            self.TextBrowser.moveCursor(QTextCursor.End)
        except Exception as e:
            self.TextBrowser.append(f"{self.red}<span> Ошибка при получении серийного номера: {str(e)}</span>")
            self.TextBrowser.moveCursor(QTextCursor.End)
        finally:
            client.close()



    def connect_to_base_station(self):
        ip = self.base_station_ip
        if self.check_ip(ip):
            serial_number = self.get_serial_number(ip)
            if serial_number:
                self.BorodinoInputMACAddress.setText(serial_number)
            else:
                self.TextBrowser.append(self.red + "Не удалось получить серийный номер контроллера.")
        else:
            self.TextBrowser.append(self.red + "Не удалось найти доступный IP-адрес.")

    def borodino_qr_click(self):
        self.BorodinoPushGenPrintQR.setEnabled(False)
        self.PressButton = "qr_click"

        # Захватываем время один раз
        point_datetime = datetime.now()
        base_datetime = point_datetime.strftime("%Y-%m-%d %H:%M:%S")
        print_datatime = point_datetime.strftime("%y%m%d%H%M%S")

        # Используем одно и то же время для QR и базы данных
        module = self.BorodinoBoxNameMod.currentText()

        # Получаем данные для подключения к базе данных
        self.SessHost = self.InputHost.text().split(":")[0]
        self.SessPort = self.InputHost.text().split(":")[1]
        self.SessUser = self.InputUser.text()
        self.SessPass = self.InputPass.text()
        session = [self.SessHost, self.SessPort, self.SessUser, self.SessPass]

        qr_code = None  # Инициализируем переменную

        # Модули, для которых не нужно сохранять данные в базу данных
        modules_no_db = ["АФУ", "POE Инжектор", "USB-HUB"]

        if module in modules_no_db:
            # Генерация QR-кода без сохранения в базу данных
            if module == "АФУ":
                prefix = "[Afd]"
                qr_code = f"{prefix}{print_datatime}"
            elif module == "POE Инжектор":
                prefix = "[Poe]"
                qr_code = f"{prefix}{print_datatime}"
            elif module == "USB-HUB":
                prefix = "[Hub]"
                qr_code = f"{prefix}{print_datatime}"

            # Печать QR-кода без сохранения в базу
            if qr_code:
                QRcode(qr_code)
                self.StatePrint = print_QR()
                success = "QR-code отправлен на принтер."
                failure = "Ошибка печати QR-code!"
                self.show_progress_bar(success, failure)

            self.BorodinoPushGenPrintQR.setEnabled(True)
            return  # Выходим из метода после обработки этих модулей


        else:
            if module == "G-Tracker Master":
                qr_code = self.generate_g_tracker_master_qr(point_datetime)
                if qr_code is None:
                    self.TextBrowser.append(self.red + "Ошибка: не удалось сгенерировать QR-код.")
                    self.BorodinoPushGenPrintQR.setEnabled(True)
                    return
            elif module == "Браслет":
                qr_code = self.generate_bracelet_qr()
                if qr_code is None:
                    self.TextBrowser.append(self.red + "Ошибка: не удалось сгенерировать QR-код.")
                    self.BorodinoPushGenPrintQR.setEnabled(True)
                    return
            elif module == "Беспроводная зарядка":
                qr_code = self.generate_wireless_charger_qr(point_datetime)
                if qr_code is None:
                    self.TextBrowser.append(self.red + "Ошибка: не удалось сгенерировать QR-код.")
                    self.BorodinoPushGenPrintQR.setEnabled(True)
                    return
            elif module in ["G-Tracker", "Радиомаяк", "Радиометка КСИЗ"]:
                count = self.get_next_qr_number(module)
                if count is None:
                    self.TextBrowser.append(self.red + "Не удалось получить следующий номер для QR-кода.")
                    self.BorodinoPushGenPrintQR.setEnabled(True)
                    return
                if module == "G-Tracker":
                    qr_code = self.generate_g_tracker_qr(count, point_datetime)
                    if qr_code is None:
                        self.TextBrowser.append(self.red + "Ошибка: не удалось сгенерировать QR-код.")
                        self.BorodinoPushGenPrintQR.setEnabled(True)
                        return
                elif module == "Радиомаяк":
                    qr_code = self.generate_beacon_qr(count)
                    if qr_code is None:
                        self.TextBrowser.append(self.red + "Ошибка: не удалось сгенерировать QR-код.")
                        self.BorodinoPushGenPrintQR.setEnabled(True)
                        return
                    # Проверка MAC-адреса в базе данных
                    try:
                        mac_address = qr_code.split(']')[1].split(',')[0]
                    except (IndexError, AttributeError):
                        self.TextBrowser.append(self.red + "Ошибка: Некорректный формат QR-кода.")
                        self.BorodinoPushGenPrintQR.setEnabled(True)
                        return

                    if not self.is_valid_mac(mac_address):
                        self.TextBrowser.append(self.red + "Некорректный MAC-адрес!")
                        self.BorodinoPushGenPrintQR.setEnabled(True)
                        return

                    if self.is_mac_in_database(mac_address):
                        self.TextBrowser.append(self.red + "MAC-адрес уже существует в базе данных.")
                        self.BorodinoPushGenPrintQR.setEnabled(True)
                        return  # Прерываем процесс, если MAC уже существует
                    else:
                        # Выполняем конфигурацию и проверяем успешность
                        configuration_success = self.configure_beacon(qr_code)
                        if not configuration_success:
                            self.TextBrowser.append(self.red + "Конфигурация маяка не удалась. Печать и обновление JSON не будут выполнены.")
                            self.BorodinoPushGenPrintQR.setEnabled(True)
                            return
                        # Если конфигурация успешна, продолжаем и обновляем JSON позже
                elif module == "Радиометка КСИЗ":
                    qr_code = self.generate_siz_qr(count)
                    if qr_code is None:
                        self.TextBrowser.append(self.red + "Ошибка: не удалось сгенерировать QR-код.")
                        self.BorodinoPushGenPrintQR.setEnabled(True)
                        return

        # Проверяем, что qr_code не None и не пустой
        if not qr_code:
            self.TextBrowser.append(self.red + "Ошибка: QR-код не был сгенерирован.")
            self.BorodinoPushGenPrintQR.setEnabled(True)
            return

        # Для модуля "Радиомаяк" конфигурация уже выполнена выше
        if module != "Радиомаяк":
            # Дополнительные проверки и операции для других модулей
            try:
                mac_address = qr_code.split(']')[1].split(',')[0]
            except (IndexError, AttributeError) as e:
                self.TextBrowser.append(self.red + "Ошибка: Некорректный формат QR-кода.")
                self.BorodinoPushGenPrintQR.setEnabled(True)
                return

            # Дополнительная проверка MAC-адреса
            if not self.is_valid_mac(mac_address):
                self.TextBrowser.append(self.red + "Некорректный MAC-адрес! Введите 12 символов, только цифры и заглавные буквы.")
                self.BorodinoPushGenPrintQR.setEnabled(True)
                return

            mac_exists = self.is_mac_in_database(mac_address)

            if mac_exists:
                self.TextBrowser.append(self.red + "MAC-адрес уже существует в базе данных.")
                self.BorodinoPushGenPrintQR.setEnabled(True)
                return  # Прерываем процесс, если MAC уже существует

        # Печатаем QR-код
        QRcode(qr_code)
        self.StatePrint = print_QR()

        if self.StatePrint is None:
            self.TextBrowser.append(self.green + "QR-code успешно отправлен на принтер.")
        else:
            self.TextBrowser.append(self.red + "Ошибка печати QR-code!")
            self.BorodinoPushGenPrintQR.setEnabled(True)
            return

        # Запись в базу данных с использованием base_datetime
        self.StateBase = self.save_to_database(base_datetime, self.SessUser, qr_code, module)


        if not self.StateBase:
            self.TextBrowser.append(self.red + "Ошибка при добавлении данных в базу данных.")
            self.BorodinoPushGenPrintQR.setEnabled(True)
            return

        # Обновляем JSON-файл
        if module == "Радиомаяк":
            # Для Радиомаяка обновляем JSON только после успешной конфигурации
            try:
                self.qr_state[module] = count  # Предполагается, что count уже вычислен
                self.save_qr_state()
                self.TextBrowser.append(self.green + "Состояние QR успешно сохранено.")
            except Exception as e:
                self.TextBrowser.append(self.red + f"Ошибка при обновлении JSON: {e}")
                self.BorodinoPushGenPrintQR.setEnabled(True)
                return
        if module in ["G-Tracker", "Радиометка КСИЗ"]:
            try:
                self.qr_state[module] = count  # `count` определён только для этих модулей
                self.save_qr_state()
                self.TextBrowser.append(self.green + "Состояние QR успешно сохранено.")
            except Exception as e:
                self.TextBrowser.append(self.red + f"Ошибка при обновлении JSON: {e}")
                self.BorodinoPushGenPrintQR.setEnabled(True)
                return
            

        # Очистка поля MAC-адреса
        self.BorodinoInputMACAddress.clear()

        self.BorodinoPushGenPrintQR.setEnabled(True)

        # Обновляем UI только если данные успешно добавлены в базу
        self.update_ui_number(module)



    def updateBorodinoUI(self):
        """Обновление UI для выбранного модуля."""
        self.BorodinoInputMACAddress.clear()
        selected_name = self.BorodinoBoxNameMod.currentText()
        self.update_ui_number(selected_name)

        # Управление видимостью кнопки и поля ввода MAC-адреса
        if selected_name in ["G-Tracker", "G-Tracker Master", "Радиометка КСИЗ", "Радиомаяк", "Браслет"]:
            self.BorodinoReadMACButton.setVisible(True)
            self.BorodinoLabelBuildVer.setVisible(True)
            self.BorodinoInputMACAddress.setVisible(True)
            self.BorodinoLabelBuildVer.setText("MAC-адрес")
            self.BorodinoReadMACButton.setText("Считывание MAC-адреса")
        else:
            # Скрываем кнопку и поле ввода для остальных модулей, включая "Базовая станция"
            self.BorodinoReadMACButton.setVisible(False)
            self.BorodinoLabelBuildVer.setVisible(False)
            self.BorodinoInputMACAddress.setVisible(False)
        
        # Обновляем состояние кнопки после изменения UI
        self.update_generate_button_state()



    def change_password_and_get_serial(self, base_datetime):
        try:
            # Сначала меняем пароль
            self.change_password_via_ssh()

            # После успешной смены пароля пытаемся получить серийный номер
            serial_number = self.get_serial_number()


            if not serial_number:
                self.BorodinoPushGenPrintQR.setEnabled(True)
                self.TextBrowser.append(self.red + "Не удалось получить серийный номер.")
                self.TextBrowser.moveCursor(QTextCursor.End)
                return

            # Создаем QR-код на основе серийного номера
            qr_code = f"[BS]{serial_number}"
            self.TextBrowser.append(f"{self.green} Сгенерирован QR-код: {qr_code}")
            self.TextBrowser.moveCursor(QTextCursor.End)

            # Печатаем QR-код
            QRcode(qr_code)
            self.StatePrint = print_QR()

            if self.StatePrint is None:
                self.TextBrowser.append(self.green + "QR-код отправлен на принтер.")
                self.TextBrowser.moveCursor(QTextCursor.End)
            else:
                self.TextBrowser.append(self.red + "Ошибка при печати QR-кода!")
                self.TextBrowser.moveCursor(QTextCursor.End)

            # Сохраняем данные базовой станции в базу данных
            base_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_to_database(base_datetime, self.SessUser, qr_code, "Базовая станция", controller_id=serial_number)

        finally:
            self.BorodinoPushGenPrintQR.setEnabled(True)
                
    def configure_beacon(self, qr_code):
        commands = []
        
        count = qr_code.split(',')[1]
        hex_count = f"{int(count):02X}"
        uid_command = f"AT+SLOTCONFIG=1,00,8,0000B8F5A30689CEB7A5C9DD0000000000{hex_count}0000\r".encode()
        commands.append(uid_command)
        
        configuration_success = False  # Инициализируем флаг успешной конфигурации
        
        try:
            with serial.Serial(self.mac_reader.com_port, baudrate=115200, timeout=1) as ser:
                for command in commands:
                    ser.write(command)
                    time.sleep(1)
                    response = ser.readlines()
                    for line in response:
                        decoded_line = line.decode('utf-8').strip()
                        self.TextBrowser.append(self.grey + f"Command response: {decoded_line}")
                        if decoded_line == "OK":
                            configuration_success = True  # Устанавливаем флаг, если получен 'OK'
                    if configuration_success:
                        self.TextBrowser.append(self.green + f"Конфигурация маяка успешна. Порядковый номер в комплекте - {count}")
                    else:
                        self.TextBrowser.append(self.red + f"Конфигурация маяка не удалась.")
                        return False  # Возвращаем False, если конфигурация не удалась
        except Exception as e:
            print(f"Error: {e}")
            self.TextBrowser.append(self.red + f"Ошибка при конфигурации маяка: {e}")
            return False  # Возвращаем False в случае исключения

        return configuration_success  # Возвращаем флаг успешной конфигурации




    def save_to_database(self, datetime_id, user, qr, module, controller_id=None):
        self.SessHost = self.InputHost.text().split(":")[0]
        self.SessPort = self.InputHost.text().split(":")[1]
        self.SessUser = self.InputUser.text()
        self.SessPass = self.InputPass.text()
        session = [self.SessHost, self.SessPort, self.SessUser, self.SessPass]

        if qr is None:
            self.TextBrowser.append(self.red + "QR-код не был сгенерирован!")
            return

        mac_address = qr.split(']')[1].split(',')[0]

        if module == "Базовая станция":
            connect_base = "goodwin_base_station_prod"
            name_table = "base_station_module"
            data_records = [(datetime_id, datetime_id, user, qr, controller_id)]
            name_columns = ["DATETIME_UPDATE", "DATETIME_ID", "USER", "QR", "CONTROLLER_ID"]
            self.StateBase = query_add_data(connect, Error, session, connect_base, name_table, name_columns, data_records)

        elif module in ["G-Tracker", "G-Tracker Master"]:
            connect_base = "goodwin_bmi_prod"
            name_table = "bmi_module"
            data_records = [(datetime_id, user, 'G-Tracker', '2.2', '1.0')]
            name_columns = ["DATETIME_ID", "USER", "NAME_VER", "BOARD_VER", "BUILD_VER"]
            self.StateBase = query_add_data(connect, Error, session, connect_base, name_table, name_columns, data_records)
            
            if self.StateBase:
                pass
                # self.TextBrowser.append(self.green + "Данные успешно добавлены в таблицу bmi_module.")
            else:
                self.TextBrowser.append(self.red + "Ошибка при добавлении данных в таблицу bmi_module.")
                return
            
            connection = connect(
                host=self.SessHost, port=self.SessPort, user=self.SessUser, password=self.SessPass, database=connect_base
            )
            cursor = connection.cursor()
            cursor.execute("SELECT ID FROM bmi_module WHERE DATETIME_ID = %s", (datetime_id,))
            result = cursor.fetchone()
            if result:
                entity_id = result[0]
            else:
                self.TextBrowser.append(self.red + "Не удалось найти запись в bmi_module!")
                return
            cursor.close()
            connection.close()

            name_table = "bmi_mark"
            data_records = [(datetime_id, user, qr, mac_address, entity_id)]
            name_columns = ["DATETIME_ID", "USER", "QR", "MAC", "ID"]
            self.StateBase = query_add_data(connect, Error, session, connect_base, name_table, name_columns, data_records)
            if self.StateBase:
                pass
                # self.TextBrowser.append(self.green + "Данные добавлены в таблицу bmi_mark.")
            else:
                self.TextBrowser.append(self.red + "Ошибка при добавлении данных в таблицу bmi_mark!")

        # Аналогичные блоки для других модулей
        elif module == "Радиометка КСИЗ":
            connect_base = "goodwin_siz_prod"
            name_table = "siz_module"
            data_records = [(datetime_id, user, qr, mac_address)]
            name_columns = ["DATETIME_ID", "USER", "QR", "MAC"]
            self.StateBase = query_add_data(connect, Error, session, connect_base, name_table, name_columns, data_records)

        elif module == "Браслет":
            connect_base = "goodwin_bracelet_prod"
            name_table = "bracelet_module"
            data_records = [(datetime_id, user, qr, mac_address)]
            name_columns = ["DATETIME_ID", "USER", "QR", "MAC"]
            self.StateBase = query_add_data(connect, Error, session, connect_base, name_table, name_columns, data_records)

        elif module == "Радиомаяк":
            count = qr.split(',')[1]
            connect_base = "goodwin_beacon_prod"
            name_table = "beacon_module"
            data_records = [(datetime_id, user, qr, mac_address, count)]
            name_columns = ["DATETIME_ID", "USER", "QR", "MAC", "BEACON_NUMBER"]
            self.StateBase = query_add_data(connect, Error, session, connect_base, name_table, name_columns, data_records)

        else:
            connect_base = "goodwin_charge_prod"
            name_table = "charge_module"
            data_records = [(datetime_id, user, qr)]
            name_columns = ["DATETIME_ID", "USER", "QR"]
            self.StateBase = query_add_data(connect, Error, session, connect_base, name_table, name_columns, data_records)

        if self.StateBase:
            self.TextBrowser.append(self.green + "Данные успешно записаны в базу данных.")
        else:
            self.TextBrowser.append(self.red + "Ошибка при записи данных в базу данных!")

        return self.StateBase



    async def scan_bluetooth_devices(self):
        """Асинхронно сканирует окружение Bluetooth и возвращает список устройств."""
        self.TextBrowser.append(self.grey + "Начат сканирование Bluetooth-устройств...")
        devices = await BleakScanner.discover(timeout=5.0)
        self.TextBrowser.append(self.grey + f"Найдено устройств: {len(devices)}")
        device_list = []
        for idx, device in enumerate(devices):
            device_info = f"{idx + 1}. {device.name} ({device.address})"
            self.TextBrowser.append(self.grey + device_info)
            device_list.append((device.name, device.address))
        return device_list

    def handle_devices_found(self, devices):
        """Обрабатывает найденные устройства, выбирает ближайшее с именем, начинающимся с 'GBraFe', и вставляет его MAC-адрес."""
        if not devices:
            self.TextBrowser.append(self.red + "Не найдено ни одного Bluetooth-устройства.")
            return

        # Фильтруем устройства, имена которых начинаются с 'GBraFe'
        gbrafe_devices = [device for device in devices if device[0].startswith("GBraFe")]

        if not gbrafe_devices:
            self.TextBrowser.append(self.red + "Не найдено Bluetooth-устройств'GBraFe'.")
            return

        # Находим устройство с наибольшим RSSI (наиболее близкое)
        closest_device = max(gbrafe_devices, key=lambda d: d[2])

        name, address, rssi = closest_device

        # Удаляем двоеточия из MAC-адреса
        mac_no_colon = address.replace(":", "")

        self.TextBrowser.append(self.green + f"Автоматически выбрано устройство: {name} ({address}) с RSSI {rssi}")

        # Вставляем MAC-адрес без двоеточий в соответствующее поле
        self.BorodinoInputMACAddress.setText(mac_no_colon)


    def handle_scan_failed(self, error_message):
        """Обрабатывает ошибки сканирования Bluetooth."""
        self.TextBrowser.append(self.red + f"Ошибка сканирования Bluetooth: {error_message}")

    def scan_bluetooth_and_select_device(self):
        """Сканирует Bluetooth-устройства и автоматически выбирает ближайшее 'GBraFe' устройство."""
        if not self.bluetooth_thread.isRunning():
            self.bluetooth_thread.start()
        else:
            self.TextBrowser.append(self.yellow + "Сканирование Bluetooth уже выполняется...")

    
    def read_mac_address_and_update_ui(self):
        selected_name = self.BorodinoBoxNameMod.currentText()
        if selected_name == "Базовая станция":
            self.connect_to_base_station()
        elif selected_name == "Браслет":
            # Используем сканирование Bluetooth для получения MAC-адреса браслета
            self.scan_bluetooth_and_select_device()
        else:
            mac_address = self.mac_reader.read_mac_address(selected_name)  # Для других модулей сохраняем текущую логику
            if mac_address:
                self.BorodinoInputMACAddress.setText(mac_address)
            else:
                self.TextBrowser.append(self.red + "Не удалось считать MAC-адрес.")

class BluetoothScanThread(QThread):
    # Сигналы для передачи списка устройств и ошибок
    devices_found = pyqtSignal(list)
    scan_failed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    async def scan_devices(self, timeout=5.0):
        try:
            devices = await BleakScanner.discover(timeout=timeout)
            device_list = []
            for device in devices:
                name = device.name or "Unknown"
                address = device.address
                # Попытка получить RSSI из advertisement, если доступно
                if hasattr(device, 'advertisement') and hasattr(device.advertisement, 'rssi'):
                    rssi = device.advertisement.rssi
                else:
                    # Используем device.rssi, подавляя предупреждение
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", category=FutureWarning)
                        rssi = device.rssi
                device_list.append((name, address, rssi))
            self.devices_found.emit(device_list)
        except Exception as e:
            self.scan_failed.emit(str(e))

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.scan_devices())
        except Exception as e:
            self.scan_failed.emit(str(e))
        finally:
            loop.close()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('conf/logo2.png'))
    win = PrintQR()  # Создаём экземпляр PrintQR, который наследует QMainWindow
    win.show()        # Отображаем окно
    status = app.exec_()
    sys.exit(status)
