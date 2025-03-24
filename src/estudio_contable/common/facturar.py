from estudio_contable.common.funciones_pub import elegir_cliente, afip_login, afip_elegir_aplicativo, elegir_tab
from estudio_contable.common.func_comp_en_linea import cel_seleccionar_empresa, cel_facturar_mucho
from dotenv import dotenv_values
from pathlib import Path
import pandas as pd
import time

variables = dotenv_values()

user, password = elegir_cliente() 
facturas_a_subir = Path(variables.get('EXCEL_FILE_PATH'))
df = pd.read_excel(facturas_a_subir,sheet_name='ventas_a_subir')

# Esta es la estructura del df de ventas requerido por el momento:
# fecha          datetime64[ns]
# comprobante             int64
# fecha_desde    datetime64[ns]
# fecha_hasta    datetime64[ns]
# servicio               object
# unidades                int64
# precio                  int64


driver = afip_login(user, password)



afip_elegir_aplicativo(driver,1)    # Elegimos la app Comprobantes emitidos
time.sleep(1)
elegir_tab(driver,1)           # Vamos a la pestaña de la app
time.sleep(1)

# Esto está hardcodeado según mis necesidades. Las necesidades del cliente pueden variar. TODO: Sacar el hardcodeo
cel_seleccionar_empresa(driver, 2)  # Elegimos la empresa a la que le vamos a cargar facturas
time.sleep(1)

cel_facturar_mucho(driver, df)