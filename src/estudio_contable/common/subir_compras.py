from dotenv import load_dotenv
import pandas as pd
import os
import time

from estudio_contable.common.funciones_pub import afip_login, afip_cargar_compras, elegir_tab, link_afip_compras_portal_iva

"""
Pasos para subir las compras a AFIP

1° Cambiar la info correspondiente en el archivo .env:
    - Ruta de acceso al excel (excel_path)
    - Usuario AFIP (user)
    - Contraseña de AFIP (password)

2° Ejecutar el archivo (subir_compras.py)

3° Navegar una vez iniciada la sesión hasta el aplicativo Portal IVA y dejar listo para que el archivo empiece a cargar facturas. Confirmar con Enter (falta automatizar)
"""

variables = load_dotenv()
excel_path = os.getenv('EXCEL_FILE_PATH')
compras_a_subir = pd.read_excel(excel_path, sheet_name="Compras_a_subir", dtype={
    "Punto de Venta": str,
    "Número Desde": str,
    "Número Hasta": str,
    "Nro. CUIT. Emisor": str})

number_columns = [
    'Neto 21%',
    'Neto 10,5%',
    'Imp. Neto No Gravado',
    'Imp. Op. Exentas',
    'IVA 21%',
    'IVA 10,5%',
    'Perc. IIBB',
    'Perc. IVA',
    'Imp. Total'
]

compras_a_subir[number_columns] = compras_a_subir[number_columns].round(2)

user = os.getenv('USER')
password = os.getenv('PASSWORD')



driver = afip_login(user, password)

time.sleep(2)
continuar = input("Enter para continuar")

elegir_tab(driver, 1)
driver.get(link_afip_compras_portal_iva)

time.sleep(2)
afip_cargar_compras(driver, compras_a_subir)