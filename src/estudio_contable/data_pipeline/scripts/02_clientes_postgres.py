"""
Este archivo lo que hace es insertar los clientes en la base de datos. Los clientes vienen de un excel propio. Estas son las columnas que va a tener por el momento la tabla de clientes de la base de datos y por ende las columnas que debe tener el excel propio:

    id_cliente      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cliente         TEXT UNIQUE,
    razon_social    TEXT UNIQUE,
    cuit_cliente    TEXT UNIQUE,
    cuit_afip       TEXT,
    clave_afip      TEXT,
    clave_arba      TEXT,
    clave_agip      TEXT,
    usuario_seh     TEXT,
    clave_seh       TEXT,
    codigo_mis_comp INTEGER

"""

import pandas as pd
from dotenv import dotenv_values
from sqlalchemy import create_engine
from pathlib import Path

# De acá sale el excel propio y la info para conectarnos a la base de datos
variables = dotenv_values() 

# Info de la base
DB_NAME       = variables.get('DB_NAME')
SQL_FILE_PATH = variables.get('SQL_FILE_PATH')
DB_USER       = variables.get('DB_USER')
DB_PASSWORD   = variables.get('DB_PASSWORD')
DB_HOST       = variables.get('DB_HOST')
DB_PORT       = int(variables.get('DB_PORT'))


# La tabla de clientes propia
## Los types con los que pandas tiene que leer las columnas del excel
tipos_columnas = {
    'cuit_cliente'    : str,
    'cuit_afip'       : str,
    'contraseña_afip' : str,
    'contraseña_arba' : str,
    'contraseña_agip' : str,
    'usuario_seh'     : str,
    'contraseña_seh'  : str,
}
tabla_clientes = pd.read_excel(variables.get('TABLA_CLIENTES'), dtype=tipos_columnas)

# La inserción en la base de datos
table = 'clientes'                                                                                               # Tabla donde vamos a importar los datos
table_key = 'cuit_cliente'                                                                                       # Columna key para chequear duplicados
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")           # Motor que conecta a la base
datos_existentes = pd.read_sql(f'SELECT {table_key} FROM {table}', engine)                                       # Leemos la info de la tabla en la base
datos_nuevos     = tabla_clientes[~tabla_clientes[table_key].isin(datos_existentes[table_key])]                  # Nos quedamos con los datos nuevos solamente
inserciones = datos_nuevos.to_sql(table, engine, if_exists='append', index=False)

print(f'Se agregaron {inserciones} nuevos clientes en la base de datos')
