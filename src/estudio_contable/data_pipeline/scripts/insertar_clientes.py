"""
Este archivo lo que hace es insertar los clientes en la base de datos. Los clientes vienen de un excel propio. Estas son las columnas que va a tener por el momento la tabla de clientes de la base de datos y por ende las columnas que debe tener el excel propio:

    'id_cliente'      INTEGER PRIMARY KEY AUTOINCREMENT,  | esta es la única que no debe tener el excel. Lo pone solo el programa.
    'cliente'         TEXT UNIQUE,
    'razon_social'    TEXT UNIQUE,
    'cuit_cliente'    TEXT UNIQUE,
    'cuit_afip'       TEXT,
    'clave_afip'      TEXT,
    'clave_arba'      TEXT,
    'clave_agip'      TEXT,
    'usuario_seh'     TEXT,
    'clave_seh'       TEXT,
    'codigo_mis_comp' INTEGER

"""


import pandas as pd
from dotenv import dotenv_values
from estudio_contable.common.funciones_pub import insertar_en_base
from pathlib import Path

# De acá sale el excel propio
variables = dotenv_values()

# Path de la base
db_path = Path.cwd().parent / 'estudio_contable_pub.db'


# Los types con los que pandas tiene que leer las columnas del excel
tipos_columnas = {
    'cuit_cliente'    : str,
    'cuit_afip'       : str,
    'contraseña_afip' : str,
    'contraseña_arba' : str,
    'contraseña_agip' : str,
    'usuario_seh'     : str,
    'contraseña_seh'  : str,
}

# La tabla de clientes propia
tabla_clientes = pd.read_excel(variables.get('TABLA_CLIENTES'), dtype=tipos_columnas)

# La inserción en la base de datos
inserciones = insertar_en_base(tabla_clientes, db_path, 'clientes', 'cuit_cliente')

print(f'Se agregaron {inserciones} nuevos clientes en la base de datos')