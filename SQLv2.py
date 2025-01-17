#!./env/bin/python

#from mysql.connector import connect, Error
#from datetime import datetime


host_sess = '172.16.0.155'
port_sess = "3306"
user_sess = 'tester01'
pass_sess = 'test'
session = [host_sess, port_sess, user_sess, pass_sess]

module_name = 'BMI'
board_ver = '25.5'
build_ver = 'GSM'
module_state = 'print QR'


#Формируем пакет данных, для передачи в MySQL
#base_datetime = datetime.now().strftime("%Y-%m-%d %H.%M.%S.%f") # %f - микросекунды
#data_records = [(user_sess, base_datetime, module_name, board_ver, build_ver, module_state)]


new_base = 'goodwin_bmi_prod'
connect_base = 'goodwin_bmi_prod'

name_table = 'bmi_module_prod'
name_columns = ['(USER,','DATE,','NAME,', 'BOARD_VER,', 'BUILD_VER,', 'STATE)'
               'VALUES ( %s, %s, %s, %s, %s, %s )']


new_table = """bmi_module_prod (                             
    M_ID INT AUTO_INCREMENT PRIMARY KEY,
    USER VARCHAR(100),
    DATE VARCHAR(100),
    NAME VARCHAR(100),
    BOARD_VER VARCHAR(100),
    BUILD_VER VARCHAR(100),
    STATE VARCHAR(100)
)
"""


def show_databases (connect, Error, session) -> bool:
    try:
        with connect(
            host     = session[0],
            port     = session[1],
            user     = session[2],
            password = session[3],
        ) as connection:
            show_db_query = "SHOW DATABASES"
            with connection.cursor() as cursor:
                cursor.execute(show_db_query)
                for db in cursor:
                    print(db)
                return True
                    
    except Error as e:
        print(e)
        return False

def create_database (connect, Error, session, new_base) -> bool:
    try:
        with connect(
            host     = session[0],
            port     = session[1],
            user     = session[2],
            password = session[3],
        ) as connection:
            create_db_query = "CREATE DATABASE " + new_base
            with connection.cursor() as cursor:
                cursor.execute(create_db_query)
                return True

    except Error as e:
         print(e)
         return False

def create_table (connect, Error, session, connect_base, new_table) -> bool:
    try:
        with connect(
            host     = session[0],
            port     = session[1],
            user     = session[2],
            password = session[3],
            database = connect_base,
        ) as connection:
            create_table_query = "CREATE TABLE " + new_table
            with connection.cursor() as cursor:
                cursor.execute(create_table_query)
                for db in cursor:
                    print(db)
                return True

    except Error as e:
        print(e)
        return False

def query_add_data(connect, Error, session, connect_base, name_table, name_columns, data_records):
    try:
        with connect(
            host=session[0],
            port=session[1],
            user=session[2],
            password=session[3],
            database=connect_base,
        ) as connection:
            name_column = ', '.join(name_columns)
            placeholders = ', '.join(['%s'] * len(name_columns))
            insert_data_query = f"INSERT INTO {name_table} ({name_column}) VALUES ({placeholders})"
            with connection.cursor() as cursor:
                cursor.executemany(insert_data_query, data_records)
                connection.commit()
                return True
    except Error as e:
        print(e)
        return False





# тесты
if __name__ == "__main__":


    #CREATE_DATABASE (connect, Error, session, new_base)
    #CREATE_TABLE (connect, Error, session, connect_base, new_table)
    #SHOW_DATABASES (connect, Error, session)
    #QUERY_ADD_DATA (connect, Error, session, connect_base, name_table, name_columns, data_records)



    pass