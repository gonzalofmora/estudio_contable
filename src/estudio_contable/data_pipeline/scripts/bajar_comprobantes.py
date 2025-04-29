from estudio_contable.common.funciones_pub import mc_obtener_comprobantes
from dotenv import dotenv_values
from pathlib import Path
variables = dotenv_values()

tipo_comprobantes = variables.get('TIPO_COMPROBANTES')
carpeta_de_descarga = Path(variables.get('MC_FOLDER_ORIGIN_PATH'))
carpeta_de_destino = Path(f"{variables.get('MC_FOLDER_DESTINATION_PATH')}/{tipo_comprobantes.capitalize()}")

meses: dict[str, str] = {
    "enero"      : "01/01/2025 - 31/01/2025",
    "febrero"    : "01/02/2025 - 28/02/2025",
    "marzo"      : "01/03/2025 - 31/03/2025",
    "abril"      : "01/04/2025 - 30/04/2025",
    "mayo"       : "01/05/2025 - 31/05/2025",
    "junio"      : "01/06/2025 - 30/06/2025",
    "julio"      : "01/07/2025 - 31/07/2025",
    "agosto"     : "01/08/2025 - 31/08/2025",
    "septiembre" : "01/09/2025 - 30/09/2025",
    "octubre"    : "01/10/2025 - 31/10/2025",
    "noviembre"  : "01/11/2025 - 30/11/2025",
    "diciembre"  : "01/12/2025 - 31/12/2025"
}

mes          =  meses[input('Elegir mes a descargar: ')]
tipo_archivo = input('Elegir formato: excel | csv: ') 
en_cantidad  = (input('1 para todos los clientes, 0 para uno solo: ') == '1')

# True para todos los clientes, False para uno solo
mc_obtener_comprobantes(tipo_archivo, tipo_comprobantes, mes, carpeta_de_descarga, carpeta_de_destino, en_cantidad)


