from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey, text, and_
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy_utils import database_exists, create_database
from typing import Tuple




Base = declarative_base()

# Получение списка баз данных
def show_databases(engine) -> bool:
    try:
        if not engine:
            return False
        connection = engine.connect()
        result = connection.execute(text("SHOW DATABASES"))
        for row in result:
            print(row)
        return True
    except Exception as e:
        print(e)
        return False

# Создание базы данных (не проверено)
def create_database(engine, new_base) -> bool:
    try:
        if not engine:
            return False
        db_url = f"{engine.url}/{new_base}"
        if not database_exists(db_url):
            create_database(db_url)
            return True
        else:
            print(f"Database '{new_base}' already exists.")
            return False
    except Exception as e:
        print(e)
        return False

# Создание таблицы (не проверено)
def create_table(engine, connect_base, new_table) -> bool:
    try:
        if not engine:
            return False
        metadata = MetaData()
        table = Table(
            new_table,
            metadata,
            # Здесь добавьте столбцы вашей таблицы, например:
            Column("id", Integer, primary_key=True),
            Column("name", String(255)),
            Column("value", Integer),
        )
        metadata.create_all(engine)
        return True
    except Exception as e:
        print(e)
        return False

# Передача данных в таблицу (не проверено)
def add_data(engine, connect_base, name_table, data_records) -> bool:
    try:
        if not engine:
            return False
        
        Session = sessionmaker(bind=engine)
        session = Session()

        table = Table(name_table, Base.metadata, autoload_with=engine)

        for record in data_records:
            new_row = table(**record)
            session.add(new_row)

        session.commit()
        session.close()
        return True

    except Exception as e:
        print(e)
        return False

# Обновление в таблице статусов  (не проверено)
def add_update_data(engine, name_table, entity_id, user, column_name, value) -> bool:
    try:
        if not engine:
            return False
        
        metadata = MetaData()
        metadata.bind = engine
        table = Table(name_table, metadata, autoload_with=engine)

        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Проверяем, существует ли строка с данным ENTITY_ID
        row_exists = session.query(table).filter_by(ENTITY_ID=entity_id).first()

        if row_exists:
            # Если строка существует, обновляем ее
            update_statement = text(f"UPDATE {name_table} SET {column_name} = :value, USER = :user WHERE ENTITY_ID = :entity_id")
            session.execute(update_statement, {'value': value, 'user': user, 'entity_id': entity_id})
        else:
            # Если строки не существует, добавляем новую
            new_row_data = {"ENTITY_ID": entity_id, "USER": user, column_name: value}
            insert_statement = table.insert().values(new_row_data)
            session.execute(insert_statement)

        session.commit()
        session.close()
        return True

    except Exception as e:
        print(e)
        return False



# Поиск данных (не проверено)
def search_data(engine, name_table, search_params) -> Tuple[bool, list]:
    results = []
    try:
        if not engine:
            return False, results

        Session = sessionmaker(bind=engine)
        session = Session()

        table = Table(name_table, Base.metadata, autoload_with=engine)

        query = session.query(table).filter(and_(*[getattr(table.c, k) == v for k, v in search_params.items()]))
        results = query.all()

        session.close()
        return True, results

    except Exception as e:
        print(e)
        return False, e




if __name__ == "__main__":


    pass