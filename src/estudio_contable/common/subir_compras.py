from dotenv import load_dotenv
import pandas as pd
import os
import time

from estudio_contable.common.funciones_pub import afip_login, afip_cargar_compras, elegir_tab, link_afip_compras_portal_iva

variables = load_dotenv()
excel_path = os.getenv('EXCEL_FILE_PATH')
compras_a_subir = pd.read_excel(excel_path, sheet_name="Compras_a_subir", dtype={
    "Punto de Venta": str,
    "Número Desde": str,
    "Número Hasta": str,
    "Nro. CUIT. Emisor": str})


user = os.getenv('USER')
password = os.getenv('PASSWORD')



driver = afip_login(user, password)

time.sleep(2)
continuar = input("Enter para continuar")

elegir_tab(driver, 1)
driver.get(link_afip_compras_portal_iva)

time.sleep(2)
afip_cargar_compras(driver, compras_a_subir)