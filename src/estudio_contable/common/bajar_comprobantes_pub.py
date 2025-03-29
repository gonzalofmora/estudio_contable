from estudio_contable.common.funciones_pub import mc_obtener_comprobantes
from dotenv import dotenv_values
from pathlib import Path


variables = dotenv_values()
origen = Path(variables.get('MC_FOLDER_ORIGIN_PATH'))
destino = Path(variables.get('MC_FOLDER_DESTINATION_PATH'))

mes =  "01/02/2025 - 28/02/2025"

# True para todos los clientes, False para uno solo
mc_obtener_comprobantes(0,"ventas", mes, origen, destino,True)
