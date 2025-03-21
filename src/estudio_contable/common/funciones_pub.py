from selenium import webdriver                          # webdriver sirve para agarrar el navegador
from selenium.webdriver.common.by import By             # By sirve para filtrar elementos
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys         # Para importar las teclas del teclado
from pathlib import Path
import time                                             # time sirve para hacer demorar el archivo para que cargue
from selenium.webdriver.support.ui import Select        # Para elegir de desplegables
from selenium.webdriver.support.ui import WebDriverWait          # Para que espere mientras carga la página 
from selenium.webdriver.support import expected_conditions as EC 
import zipfile



# Links
link_afip = "https://auth.afip.gob.ar/contribuyente_/login.xhtml"
link_afip_compras_portal_iva = r"https://liva.afip.gob.ar/liva/jsp/verCompras.do?t=21"

## Funciones para navegar en internet

def abrir_navegador(link, carpeta_descargas=None):
    """ Abre el navegador web
    link: el link que querés abrir
    carpeta_descargas: la carpeta donde querés guardar las descargas. None por defecto.
    """
    
    # Configuración para que Chrome no se cierre cuando termina el script
    options = webdriver.ChromeOptions()
    options.add_experimental_option('detach',True)

    if carpeta_descargas:
        carpeta_descargas = Path(carpeta_descargas)
        carpeta_descargas.mkdir(parents=True, exist_ok=True)

        prefs = {
            "download.default_directory": str(carpeta_descargas),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)


    driver = webdriver.Chrome(options=options)

    driver.get(link)
    return driver

def elegir_tab(driver, num):
    """Elegí la pestaña que quieras usar, usando su número correspondiente (primera pestaña es el 0)"""
    tabs = driver.window_handles
    if num < len(tabs):
        driver.switch_to.window(tabs[num])
    else:
        raise IndexError("La tab no existe")
    
## Funciones para trabajar en AFIP

def afip_login(user, password, carpeta_descargas=None):
    driver = abrir_navegador(link_afip,carpeta_descargas=carpeta_descargas)
    username = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "F1:username"))
    )
    #username = driver.find_element(By.ID, "F1:username")
    #username.clear()
    username.send_keys(user)
    driver.find_element(By.ID, "F1:btnSiguiente").click()
    passwd  = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "F1:password"))
    )   
    passwd.send_keys(password)
    #driver.find_element(By.ID, "F1:password").send_keys(password)
    driver.find_element(By.ID, "F1:btnIngresar").click()
    time.sleep(3)
    return driver

def afip_cargar_compras(driver, df):
    campos_dic = {
        "Fecha"                : "cm_fechaEmision",
        "Punto de Venta"       : "cm_ptoVta",
        "Número Desde"         : "cm_numero",
        "Nro. CUIT. Emisor"    : "cm_cuitEmisor",
        "Imp. Total"           : "cm_importeTotal",
        "Imp. Neto No Gravado" : "cm_netoNoGravado",
        "Imp. Op. Exentas"     : "cm_importeExento",
        "Perc. IIBB"           : "cm_percepcionesIIBB",
        "Perc. IVA"            : "cm_percepcionesIVA",
        "Imp. Neto Gravado"    : "cm_netoGravadoIVA21"
    }

    for row in range(len(df["Fecha"])):
        driver.find_element(By.ID, "btnCargaManual").click()
        time.sleep(2)
        fechas_formato_bien = df["Fecha"].dt.strftime('%d/%m/%Y')

        for i in campos_dic:
            campo = driver.find_element(By.ID, campos_dic[i])
            campo.clear()
            if i == "Fecha":
                campo.send_keys(fechas_formato_bien[row])
                campo.send_keys(Keys.ESCAPE)
            else:
                campo.send_keys(df[i][row])
            time.sleep(1)
        driver.find_element(By.ID, "btnAgregarComprobanteManual").click()
        time.sleep(2)

def cerrar_afip(driver):
    """
    TODO Cerrar de verdad
    """
    driver.get("https://portalcf.cloud.afip.gob.ar/portal/app/")
    time.sleep(3)
    driver.find_element(By.ID, "userIconoChico").click()
    driver.find_element(By.CLASS_NAME, "fa.fa-sign-out.h4.text-primary.m-a-0").click()
