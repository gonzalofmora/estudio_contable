"""
Vamos a crear la base de datos. 
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import dotenv_values

# Variables
variables = dotenv_values()

# Configuración
DB_NAME       = variables.get('DB_NAME')
SQL_FILE_PATH = variables.get('SQL_FILE_PATH')
DB_USER       = variables.get('DB_USER')
DB_PASSWORD   = variables.get('DB_PASSWORD')
DB_HOST       = variables.get('DB_HOST')
DB_PORT       = int(variables.get('DB_PORT'))


# Hay que conectarse a la base de datos default 'postgres' para crear una nueva base de datos
conn = psycopg2.connect(
    dbname   = "postgres",
    user     = DB_USER,
    password = DB_PASSWORD, 
    host     = DB_HOST,
    port     = DB_PORT
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) # Esto es necesario para usar el comando de CREATE DATABASE | ni idea realmente
cur = conn.cursor()


# Creamos la base
try:
    cur.execute(f"CREATE DATABASE {DB_NAME};")                # | Me gustaría probar cur.execute(f"CREATE DATABASE {DB_NAME} IF NOT EXISTS;")
    print(f"La base de datos '{DB_NAME}' ha sido creada.")
except psycopg2.errors.DuplicateDatabase:
    print(f"La base de datos '{DB_NAME}' ya existe.")
cur.close()
conn.close()

# Nos conectamos a la nueva base y ejecutamos el script SQL
conn = psycopg2.connect(
    dbname   = DB_NAME,
    user     = DB_USER,
    password = DB_PASSWORD, 
    host     = DB_HOST,
    port     = DB_PORT
)
cur = conn.cursor()

with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
    sql = f.read()
    cur.execute(sql)
    print("Archivo SQL ejecutado")

conn.commit()
cur.close()
conn.close()