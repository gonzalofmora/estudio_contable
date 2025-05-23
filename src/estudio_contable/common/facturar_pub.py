from pathlib import Path
from dotenv import dotenv_values
from estudio_contable.common.funciones_pub import cel_facturacion

excel_file = Path().cwd() / "plantilla_facturador.xlsx"
variables = dotenv_values()
user = variables.get('USER')
password = variables.get('PASSWORD')

cel_facturacion(user, password, excel_file)