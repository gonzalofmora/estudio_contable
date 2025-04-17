from estudio_contable.common.funciones_pub import extraer_zip
from estudio_contable.common.funciones_arba import  arba_descargar_deducciones
from pathlib import Path
from dotenv import dotenv_values

variables = dotenv_values()

user     = variables.get('USER')
password = variables.get('PASSWORD')


carpeta_deducciones_arba = Path.cwd().parent / 'data/raw/deducciones/ARBA'

arba_descargar_deducciones(user, password, carpeta_deducciones_arba)

archivo = Path(fr"{carpeta_deducciones_arba}\RP-{user}-202502C.zip")

extraer_zip(archivo, carpeta_deducciones_arba)