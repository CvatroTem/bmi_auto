#!./env/bin/python
# -*- coding: utf-8 -*-

#from barcode.writer import ImageWriter
#import barcode
#from PIL import Image

#from Main import print_datatime
from qrcode import QRCode, constants
from os import startfile
from pyautogui import press
from time import sleep
#Модули для определения окон и работы с ними
from win32gui import  IsWindowVisible, GetWindowText, EnumWindows, FindWindow, \
ShowWindow, SetForegroundWindow
import win32.lib.win32con as win32con
import win32print
from win32api import ShellExecute


# Генерация QR-кода
def QRcode(print_data):
    try:
        print(f"Data received by QRcode function: {print_data}")  # Отладочное сообщение

        qr = QRCode(
            version=1,
            error_correction=constants.ERROR_CORRECT_L,
            box_size=20,
            border=4,
        )

        qr.add_data(print_data.encode('utf-8'))  # Кодирование данных
        qr.make(fit=True)

        image = qr.make_image(fill_color="black", back_color="white")
        image.save("qrcode_test.png")  # Сохранение изображения для проверки

        if "[BppuM]" in print_data:
            cropped = image.crop((65, 65, 680, 680))  # Обрезка для Borodino
        elif "[Bppu]" in print_data:
            cropped = image.crop((65, 65, 680, 680))  # Обрезка для Borodino
        elif "[Siz]" in print_data:
            cropped = image.crop((80, 80, 610, 610))  # Обрезка для Borodino
        elif "[GBraFe]" in print_data:
            cropped = image.crop((80, 80, 610, 610))  # Обрезка для Borodino
        elif "[Beacon]" in print_data:
            cropped = image.crop((80, 80, 610, 610))  # Обрезка для Borodino
        elif "[BS]" in print_data:
            cropped = image.crop((80, 80, 610, 610))  # Обрезка для Borodino
        else:
            cropped = image.crop((65, 65, 515, 515))  # Обычная обрезка

        cropped.save('qrcode.png')  # Сохранение обрезанного изображения

    except Exception as e:
        print(f"Error in QRcode function: {e}")

# Печать QR-кода
def print_QR():
    out = startfile("qrcode.png", "print")
    sleep(1)

    hwnd = FindWindow(None, "Печать изображений")
    ShowWindow(hwnd, win32con.SW_NORMAL)
    SetForegroundWindow(hwnd)

    press('enter')
    return out


"""
#Поиск необходимого принтера
def get_printer_by_name(printer_name):
    printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL, None, 1)
    for printer in printers:
        if printer[2] == printer_name:
            return printer[0]
    return False

#Печать определенным принтером
def get_print (printer_name, printer_port):

    
    # Открываем принтер
    hPrinter = win32print.OpenPrinter(printer_name)

    try:
        # Открываем документ для печати
        doc_name = "qrcode.png"
        doc_type = "RAW"
        output_file = None
        job_info = (doc_name, doc_type, output_file)
        hJob = win32print.StartDocPrinter(hPrinter, 1, job_info)

        try:
            # Начинаем страницу
            win32print.StartPagePrinter(hPrinter)

            # Печатаем файл
            with open("qrcode.png", "rb") as f:
                data = f.read()
                win32print.WritePrinter(hPrinter, data)

            # Заканчиваем страницу
            win32print.EndPagePrinter(hPrinter)

        finally:
            # Закрываем документ
            win32print.EndDocPrinter(hPrinter)

    finally:
        # Закрываем принтер
        win32print.ClosePrinter(hPrinter)




    #try:
    #    ShellExecute(0, "print", "qrcode.png", f"/D:{printer_port}", ".", 0)
    #    print (printer_port)
    #except ValueError as e:
    #    print (str(e))



"""


#Brother PT-P700
#Brother PT-2430PC

"""
def BARcode ():

    ean = barcode.get_barcode_class('ean8')
    ean2 = ean('2531122', writer=ImageWriter())
    ean2.save('barcode2')

def PIL_BAR ():

    image = Image.open('barcode2.png')
    #image.show()
    width, height = image.size
    new_height  = 180
    new_width  = int(new_height * width / height)
    image = image.resize((new_width, new_height), Image.ANTIALIAS)

    print(image.format, image.size, image.mode)
    image.save("barcode3.png")

    cropped = image.crop((45, 10, 220, 100)) #(x1, y1, x2, y2) (35, 50, 245, 135) (33, 45, 191, 135)
    cropped.save('barcode4.png')

def print_bar ():

    out = os.startfile("barcode4.png", "print")
    time.sleep(0.5)
    pyautogui.press('enter')
    print(out)
    time.sleep(3)

""" # barcode


# тесты
if __name__ == "__main__":

    #QRcode ()
    #PIL_QR ()
    #print_QR ()
    QRcode ("[Bppu]D89E11C91F9A")
    print_QR ()
   

    pass