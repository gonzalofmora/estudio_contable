#import json
#import shutil
import time                                                                    # time sirve para hacer demorar el archivo para que cargue
#import zipfile
#from datetime                                import datetime, timedelta
#from dotenv                                  import dotenv_values              # Para cargar environment variables
from pathlib                                 import Path
#from selenium                                import webdriver                  # webdriver sirve para agarrar el navegador
from selenium.webdriver.common.by            import By                         # By sirve para filtrar elementos
#from selenium.webdriver.common.action_chains import ActionChains               # Para realizar cadenas de comandos de teclado
#from selenium.webdriver.common.keys          import Keys                       # Para importar las teclas del teclado
from selenium.webdriver.support              import expected_conditions as EC  # Para esperar los elementos
#from selenium.webdriver.support.ui           import Select                     # Para elegir de desplegables
from selenium.webdriver.support.ui           import WebDriverWait              # Para que espere mientras carga la página 
from estudio_contable.common.funciones_pub   import abrir_navegador, clientes_arba, extraer_zip
from selenium.common.exceptions import TimeoutException


## Links ARBA
link_arba = "https://sso.arba.gov.ar/Login/login?service=https%3A//www.arba.gov.ar/Gestionar/PanelAutogestion.asp"
arba_presentaciones_link ="https://app.arba.gov.ar/IBPresentaciones/welcome.do"
arba_inicio_dj_link = "https://app.arba.gov.ar/IBPresentaciones/preInicioDDJJ.do"
arba_detalle_dj_link = "https://app.arba.gov.ar/IBPresentaciones/detalleDJView.do"
arba_deducciones_link = "https://dfe.arba.gov.ar/DomicilioElectronico/dfeSetUpInicio.do"
arba_deducciones_descargar_link = "https://dfe.arba.gov.ar/DomicilioElectronico/preDescargarRetenciones.do"



def arba_descargar_deducciones(user, password, año, mes, contador=0, carpeta_descargas=None):
    driver = arba_login(user, password, carpeta_descargas=carpeta_descargas)
    driver.get(arba_deducciones_link)
    time.sleep(1)
    driver.get(arba_deducciones_descargar_link)
    cuit_en_arba = arba_confirmar_cuit(driver)

    if (cuit_en_arba == None) & (contador <= 5):
        contador += 1 
        arba_descargar_deducciones(user, password, año, mes, contador, carpeta_descargas=None)
    else:
        periodo_button = driver.find_elements(By.CLASS_NAME, "camposFormulario")
        periodo_button[0].send_keys(año)
        periodo_button[1].send_keys(mes)
        consultar_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "Consultar")))
        consultar_button.click()
        descargar_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "Descargar archivo")))
        descargar_button.click()
        return driver

def arba_descargar_y_guardar(carpeta_destino):
    año = input('Ingresá el año: ')
    mes = input('Ingresá el mes: ')
    for cliente in clientes_arba:
        user     = clientes_arba[cliente][0]
        password = clientes_arba[cliente][1]
        arba_descargar_deducciones(user, password, año, mes, carpeta_destino)
        archivo = Path(fr"{carpeta_destino}\RP-{user}-202502C.zip")
        extraer_zip(archivo, carpeta_destino)

def arba_login(user, password, carpeta_descargas=None):
    driver = abrir_navegador(link_arba, carpeta_descargas=carpeta_descargas)
    username = driver.find_element(By.ID, "CUIT")
    username.clear()
    username.send_keys(user)
    passwd = driver.find_element(By.ID, "clave_Cuit")
    passwd.clear()
    passwd.send_keys(password)
    driver.find_element(By.CLASS_NAME, "btn.btn-lg.btn-block.btn-primary").click()
    return driver



def arba_confirmar_cuit(driver):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'subtituloColumna')))
        cuit_en_arba = driver.find_element(By.CLASS_NAME, 'subtituloColumna')
        text = cuit_en_arba.text
        if not text:
            print('Arba cargó mal')
            return None
        cuit = text.split()[1].replace('-', '')
        return cuit
    except (IndexError, TimeoutException) as e:
        print(f'Arba cargó mal porque: {e}')
        return None