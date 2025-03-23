from estudio_contable.common.funciones_pub import elegir_cliente, afip_login, mc_log_in, mc_descargar_comprobantes, afip_cerrar_sesion, mc_renombrar_y_mover
from dotenv import dotenv_values
from pathlib import Path


variables = dotenv_values()
origen = Path(variables.get('MC_FOLDER_ORIGIN_PATH'))
destino = Path(variables.get('MC_FOLDER_DESTINATION_PATH'))

mes =  "01/02/2025 - 28/02/2025"
user, password = elegir_cliente()
driver  = afip_login(user, password)

mc_log_in(driver, "ventas", 0)

mc_descargar_comprobantes(driver, mes,0)

afip_cerrar_sesion(driver)

mc_renombrar_y_mover(origen, destino)
