from pathlib import Path
from estudio_contable.facturacion.funciones_cel import cel_facturacion

excel_file = Path().cwd() / "modelo_facturacion.xlsx"
user = input('Ingrese su CUIT: ')
password = input('Ingrese su contraseña: ')

cel_facturacion(user, password, excel_file)