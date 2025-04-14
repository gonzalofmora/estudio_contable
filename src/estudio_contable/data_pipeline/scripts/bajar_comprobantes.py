from estudio_contable.common.funciones_pub import mc_obtener_comprobantes
from dotenv import dotenv_values
from pathlib import Path
variables = dotenv_values()

tipo_comprobantes = variables.get('TIPO_COMPROBANTES')
carpeta_de_descarga = Path(variables.get('MC_FOLDER_ORIGIN_PATH'))
carpeta_de_destino = Path(f"{variables.get('MC_FOLDER_DESTINATION_PATH')}/{tipo_comprobantes.capitalize()}")
mes =  variables.get('MES')
tipo_archivo = variables.get('TIPO_ARCHIVO') # 'excel' | 'csv'
en_cantidad = (variables.get('EN_CANTIDAD') == 'True')

# True para todos los clientes, False para uno solo
mc_obtener_comprobantes(tipo_archivo, tipo_comprobantes, mes, carpeta_de_descarga, carpeta_de_destino, en_cantidad)

