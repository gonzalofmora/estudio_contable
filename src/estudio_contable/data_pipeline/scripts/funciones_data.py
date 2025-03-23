from pathlib import Path
import sqlite3

# Directorios

def carpeta_de_destino(operacion, tipo):
    """operacion: compras | ventas
       tipo: 1 (mis comprobantes) | 2 (portal iva)
    """
    if tipo == 1:
        tipo_elegido = "mis_comprobantes"
    elif tipo == 2:
        tipo_elegido = "portal_iva"
    else:
          carpeta_de_destino(input(), input())

    path = Path("..") / "data" / "raw" / operacion / tipo_elegido / "zip"
    return path.resolve()



# Base de datos

def conexion_bd(base_de_datos):
    """Función para conectarte a la base de datos que quieras:
       Params: base_de_datos: el nombre del archivo de tu base de datos. 
    """

    current_dir = Path.cwd()
    db_path = current_dir.parent / base_de_datos
    connection = sqlite3.connect(db_path)
    
    return connection