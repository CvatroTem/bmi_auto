#!./env/bin/python
# -*- coding: utf-8 -*-


import serial
import serial.tools.list_ports
#from encoder import encode, decode
import time
from datetime import datetime
import logging

def search ():
    port = []
    start_time = datetime.now()
    while (port == []):
        duration = datetime.now() - start_time
        time.sleep(0.5)
        print('Ports search...')
        ports = serial.tools.list_ports.comports(include_links=False)
        sp_ports = []
        if duration.seconds > 4:
            return sp_ports
        for port in ports :
            sp_ports.append(port.device)
            #print('Port found '+ sp_ports[-1])
    return sp_ports
       

def connection(port):
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        
        if ser.is_open:
            print('Port is already open ' + ser.name)
            logging.info(f'Port is already open {ser.name}')
        else:
            ser.open()
            print('Port is now open ' + ser.name)
            logging.info(f'Port is now open {ser.name}')

        time.sleep(0.1)
        return ser

    except serial.SerialException as e:
        # Обработка ошибок при открытии порта
        print(f"Ошибка открытия порта {port}: {e}")
        logging.error(f"Ошибка открытия порта {port}: {e}", exc_info=True)
        return None

    except Exception as e:
        # Общая обработка других возможных ошибок
        print(f"Непредвиденная ошибка при работе с портом {port}: {e}")
        logging.error(f"Непредвиденная ошибка при работе с портом {port}: {e}", exc_info=True)
        return None


def write(ser, result):
    try:
        print(f"Writing: {result}")  # Для отладки
        ser.write(result)
        ser.flush()
        #print(f'Successfully written: {result}')
        return True
    except Exception as e:
        print(f'Write error: {e}')
        return False


def read(ser):
    try:
        response = b''
        while ser.inWaiting() > 0:  # while there's still incoming data
            response += ser.read(ser.inWaiting())  # read everything 
        print(f"Received: {response}")  # Для отладки
        return response
    except Exception as e:
        print(f'Read error: {e}')
        return None


def encode_command(cmd):
    return b'\r\n' + cmd + b'\r\n'

def decode_command(cmd):
    return cmd.replace(b'\r\n', b'')
    #return cmd.strip(b'\r\n')

def retry_command(ser, cmd, max_retries=5, delay_retries=1, delay_step=1):
    for _ in range(max_retries):
        #start_time = time.time()
        
        write(ser, encode_command(cmd))
        time.sleep(delay_retries)
        response = read(ser)
        
        #end_time = time.time()
        #elapsed_time = end_time - start_time
        #
        #print(f"Затраченное время: {elapsed_time} секунд")
        
        if response:
            return decode_command(response)
        
        time.sleep(delay_step)
    
    return None

def only_read (ser, max_retries=5, delay_step=1): 
    for _ in range(max_retries):
        response = read(ser)
        if response:
            return decode_command(response)
        
        time.sleep(delay_step)
    return None




def check_connection(ser):
    response = retry_command(ser, b"AT")
    return response == b"\r\nOK\r\n"

def test_sdram(ser):
    response = retry_command(ser, b"SDRAMTST")
    if response:
        time.sleep(4)
        response = read(ser)
    return response == b"\r\nSDRAMTST OK\r\n"




if __name__ == "__main__":
    ports = search()
    if len(ports) == 0:
        print("No ports found.")
        exit(1)
        
    ser = connection(ports[0])

    if check_connection(ser):
        print("Connection successful.")
        if test_sdram(ser):
            print("SDRAM test successful.")
        else:
            print("SDRAM test failed.")
    else:
        print("Connection failed.")

    ser.close()


## тесты
#if __name__ == "__main__":
#
#    while True:
#        port = search ()
#        if (port != 0):
#            break
#    
#    ser = connection(port)
#    print(ser)
#    
#    pass
