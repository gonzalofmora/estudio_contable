from estudio_contable.common.funciones_pub import agip_regimen_simplificado
from dotenv import dotenv_values

variables = dotenv_values()

user = variables.get('USER')
password = variables.get('PASSWORD')
carpeta_descargas = variables.get('DESCARGAS')

driver = agip_regimen_simplificado(user, password, carpeta_descargas)