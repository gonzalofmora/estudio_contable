from pathlib import Path
from .funciones_data import conexion_bd

# Conectarse a la base de datos
conn = conexion_bd('estudio_contable.db')

# Crear un cursor
c = conn.cursor()

current_path = Path.cwd()
sql_file_path = current_path / 'crear_tablas_ec.sql'
with open(sql_file_path, 'r') as sql_file:
    sql_script = sql_file.read()

c.executescript(sql_script)


# Ejecutar el comando
conn.commit()

# Cerrar la conexión
conn.close()