import json
import shutil
import time                                                                    # time sirve para hacer demorar el archivo para que cargue
import zipfile
from datetime                                import datetime, timedelta
from dotenv                                  import dotenv_values              # Para cargar environment variables
from pathlib                                 import Path
from selenium                                import webdriver                  # webdriver sirve para agarrar el navegador
from selenium.webdriver.common.by            import By                         # By sirve para filtrar elementos
from selenium.webdriver.common.action_chains import ActionChains               # Para realizar cadenas de comandos de teclado
from selenium.webdriver.common.keys          import Keys                       # Para importar las teclas del teclado
from selenium.webdriver.support              import expected_conditions as EC  # Para esperar los elementos
from selenium.webdriver.support.ui           import Select                     # Para elegir de desplegables
from selenium.webdriver.support.ui           import WebDriverWait              # Para que espere mientras carga la página 


"""
# Glosario de iniciales de las funciones
    mc = Mis comprobantes
    cel = Comprobantes en Línea
"""
# # Environment Variables
variables = dotenv_values()
# El diccionario tiene que tener la siguiente estructura:
#     clientes = '{cliente1: ["cuit", "contraseña"], cliente2: ["cuit", "contraseña"], ...}'   | Tiene que ser un json para poder estar como environment variable.
clientes = json.loads(variables.get('CLIENTES'))

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

def tabear(driver, tabeos=1, con_barra=False):
    "Acción para tabear muchas veces y apretar enter. con_barra sirve para apretar la barra en vez del enter"
    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB * tabeos)
    if con_barra:
        actions.send_keys(Keys.SPACE)
    else:
        actions.send_keys(Keys.ENTER)
    actions.perform()


## Funciones para trabajar con la (eventual) base de datos
def elegir_cliente():

    while True:
        try:
            cliente = input("> Nombre del cliente: ")
            user     = clientes[cliente][0]
            password = clientes[cliente][1]
            codigo_mis_comp = clientes[cliente][2]
            return  user, password, codigo_mis_comp

        except Exception as e:
            print(f"Ese cliente no existe bro, fijate qué onda.")

## Funciones para trabajar en AFIP
def afip_cargar_compras(driver, df):
    campos_dic = {
        "Tipo"                 : "button[data-id='cm_tipoComprobante']",
        "Fecha"                : "cm_fechaEmision",
        "Punto de Venta"       : "cm_ptoVta",
        "Número Desde"         : "cm_numero",
        "Nro. CUIT. Emisor"    : "cm_cuitEmisor",
        "Imp. Total"           : "cm_importeTotal",
        "Imp. Neto No Gravado" : "cm_netoNoGravado",
        "Imp. Op. Exentas"     : "cm_importeExento",
        "Perc. IIBB"           : "cm_percepcionesIIBB",
        "Perc. IVA"            : "cm_percepcionesIVA",
        "Neto 21%"    : "cm_netoGravadoIVA21",
        "Neto 10,5%"    : "cm_netoGravadoIVA105",
    }
        
    for row in range(len(df["Fecha"])):
        driver.find_element(By.ID, "btnCargaManual").click()
        time.sleep(2)
        for i in campos_dic:
            if i == "Fecha":
                campo = driver.find_element(By.ID, campos_dic[i])
                campo.clear()
                campo.send_keys(df["Fecha"].dt.strftime('%d/%m/%Y')[row])
                campo.send_keys(Keys.ESCAPE)
            elif i == "Tipo":
                dropdown_button = driver.find_element(By.CSS_SELECTOR, campos_dic[i])
                actions = ActionChains(driver)
                actions.move_to_element(dropdown_button).click()
                actions.perform()
                time.sleep(1)
                actions.send_keys(str(df[i][row]))
                actions.send_keys(Keys.ENTER)
                actions.perform()
                print(df[i][row])
                #break
            else:
                campo = driver.find_element(By.ID, campos_dic[i])
                campo.clear()
                campo.send_keys(df[i][row])
            time.sleep(1)
        print(f"Comprobante n° {row +1} impreso")        
        driver.find_element(By.ID, "btnAgregarComprobanteManual").click()
        time.sleep(2)

def afip_cerrar_sesion(driver):
    """
    TODO Cerrar de verdad
    """
    driver.get("https://portalcf.cloud.afip.gob.ar/portal/app/")
    #time.sleep(3)
    user_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "userIconoChico")))
    user_btn.click()
    #driver.find_element(By.ID, "userIconoChico").click()
    cerrar_sesion_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "fa.fa-sign-out.h4.text-primary.m-a-0")))
    cerrar_sesion_btn.click()
    #driver.find_element(By.CLASS_NAME, "fa.fa-sign-out.h4.text-primary.m-a-0").click()

def afip_elegir_aplicativo(driver, aplicativo=0, elegir_applicativo=False):
    """
    Aplicativos:
    0 → Mis Comprobantes,
    1 → Comprobantes en línea,
    2 → SIFERE WEB,
    3 → SIFERE Consultas,
    4 → Portal IVA
    """
    aplicativos = ["Mis Comprobantes", "Comprobantes en línea", "Sifere WEB - DDJJ", "Sifere WEB - Consultas", "Portal IVA"]
    aplicativo_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "buscadorInput")))
    
    if elegir_applicativo:
        input = input("> ")
        aplicativo_input.send_keys(input)
    else:
        aplicativo_input.send_keys(aplicativos[aplicativo])

    aplicativo_input.send_keys(Keys.ARROW_DOWN)
    aplicativo_input.send_keys(Keys.ENTER)
    time.sleep(2)

    tabs = driver.window_handles
    elegir_tab(driver, len(tabs)-1 )

def afip_login(user, password, carpeta_descargas=None):
    driver = abrir_navegador(link_afip,carpeta_descargas=carpeta_descargas)
    username = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "F1:username")))
    username.clear()
    username.send_keys(user)

    siguiente_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "F1:btnSiguiente")))
    siguiente_btn.click()

    passwd  = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "F1:password")))
    passwd.clear()
    passwd.send_keys(password)

    ingresar_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "F1:btnIngresar")))
    ingresar_btn.click()
    time.sleep(3)
    return driver


### Funciones para trabajar con el portal Mis Comprobantes dentro de AFIP
def mc_descargar_comprobantes(driver, mes, tipo=1):
    """
    tipo = 0 → excel
    tipo = 1 → csv
    """
    fecha_emision_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "fechaEmision")))
    fecha_emision_button.clear()
    fecha_emision_button.send_keys(mes)
    fecha_emision_button.send_keys(Keys.ENTER)

    buscar_comprobantes_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "buscarComprobantes")))
    buscar_comprobantes_btn.click()
    #driver.find_element(By.ID, "buscarComprobantes").click()
    #time.sleep(3)
    
    if tipo == 0:
        excel_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn.btn-default.buttons-excel.buttons-html5.btn-defaut.btn-sm.sinborde")))
        excel_button.click()
    else:
        csv_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[span="CSV"]')))
        csv_button.click()
    time.sleep(1)

def mc_log_in(driver,tipo="ventas", cliente=0):
    """
    tipo: 'ventas':  Comprobantes emitidos (default) 
    tipo: 'compras': Comprobantes recibidos
    cliente: 0 para el representado excepto que tenga una empresa a su nombre. En ese caso, la empresa es 0, y 1 el representado
    """
    afip_elegir_aplicativo(driver, 0)
    driver.get(f"https://fes.afip.gob.ar/mcmp/jsp/setearContribuyente.do?idContribuyente={cliente}")
    time.sleep(1)
    if tipo == "ventas":
        driver.get("https://fes.afip.gob.ar/mcmp/jsp/comprobantesEmitidos.do")
    else:
        driver.get("https://fes.afip.gob.ar/mcmp/jsp/comprobantesRecibidos.do")
    time.sleep(3)

def mc_obtener_comprobantes(tipo_de_archivo, tipo_de_comprobantes, mes, carpeta_descargas, carpeta_destino, en_cantidad=False):
    """
    tipo_de_archivo: 0 para excel | 1 para csv
    tipo_de_comprobantes: 'compras' | 'ventas'
    mes (ejemplo de formato): 01/02/2025 - 28/02/2025
    carpeta_descargas: a donde va a ir a parar el archivo descargado
    carpeta_destino: a donde va a terminar el archivo descargado
    """

    if en_cantidad:
        for cliente in clientes:
            user = clientes[cliente][0]
            password = clientes[cliente][1]
            mc_cod = clientes[cliente][2]
            mc_hacer_todo(user, password, mc_cod, tipo_de_archivo, tipo_de_comprobantes, mes, carpeta_descargas, carpeta_destino)
    else:
        user, password, mc_cod = elegir_cliente()
        mc_hacer_todo(user, password, mc_cod, tipo_de_archivo, tipo_de_comprobantes, mes, carpeta_descargas, carpeta_destino)

def mc_hacer_todo(user, password, mc_cod, tipo_de_archivo, tipo_de_comprobantes, mes, carpeta_descargas,  carpeta_destino):
    driver  = afip_login(user, password, carpeta_descargas)
    mc_log_in(driver, tipo_de_comprobantes, mc_cod)
    mc_descargar_comprobantes(driver, mes,tipo_de_archivo)
    afip_cerrar_sesion(driver)
    mc_renombrar_y_mover(carpeta_descargas, carpeta_destino)

def mc_renombrar_y_mover(origen, destino):

    folder = Path(origen)
    destination = Path(destino)
    destination.mkdir(parents=True, exist_ok=True)


    today = datetime.today()
    today_start = datetime(today.year, today.month, today.day)
    today_end = today_start + timedelta(days=1)

    xlsx_files = folder.glob("*.xlsx")

    for file in xlsx_files:
        creation_time = datetime.fromtimestamp(file.stat().st_mtime)
        if today_start <= creation_time < today_end:
            if today.month <= 10:
                new_name = file.with_stem(f"{file.stem} - {today.year}0{today.month-1}")
            else:
                new_name = file.with_stem(f"{file.stem} - {today.year}{today.month-1}")
            file.rename(new_name)
            print(f"Renamed: {file.name} → {new_name.name}")
            shutil.move(new_name, destination / new_name.name)
            print(f"Archivo trasladado")

