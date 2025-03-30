from estudio_contable.common.funciones_pub import mc_obtener_comprobantes
from dotenv import dotenv_values
from pathlib import Path
variables = dotenv_values()

tipo_comprobantes = "ventas"
carpeta_de_descarga = Path(variables.get('MC_FOLDER_ORIGIN_PATH'))
carpeta_de_destino = Path(f"{variables.get('MC_FOLDER_DESTINATION_PATH')}/{tipo_comprobantes.capitalize()}")
mes =  "01/03/2025 - 30/03/2025"
tipo_archivo = 0 # excel = 0 | csv = 1

# True para todos los clientes, False para uno solo
mc_obtener_comprobantes(tipo_archivo, tipo_comprobantes, mes, carpeta_de_descarga, carpeta_de_destino, False)
