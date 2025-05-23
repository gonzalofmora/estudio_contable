import json
import logging
import pandas  as pd
import shutil
import time                                                                    # time sirve para hacer demorar el archivo para que cargue
import zipfile
from datetime                                import datetime
from dotenv                                  import dotenv_values              # Para cargar environment variables
from pathlib                                 import Path
from selenium                                import webdriver                  # webdriver sirve para agarrar el navegador
from selenium.common.exceptions              import StaleElementReferenceException
from selenium.common.exceptions              import TimeoutException
from selenium.webdriver.common.by            import By                         # By sirve para filtrar elementos
from selenium.webdriver.common.action_chains import ActionChains               # Para realizar cadenas de comandos de teclado
from selenium.webdriver.common.keys          import Keys                       # Para importar las teclas del teclado
from selenium.webdriver.support              import expected_conditions as EC  # Para esperar los elementos
from selenium.webdriver.support.ui           import Select                     # Para elegir de desplegables
from selenium.webdriver.support.ui           import WebDriverWait              # Para que espere mientras carga la página 
from sqlalchemy                              import create_engine              # Para interactuar con la base de datos


"""
# Glosario de iniciales de las funciones
    mc = Mis comprobantes
    cel = Comprobantes en Línea
"""

logger = logging.getLogger(__name__)

# # Environment Variables
variables = dotenv_values()
# El diccionario tiene que tener la siguiente estructura:
#     clientes = '{cliente1: ["cuit", "contraseña", "codigo_mc"], cliente2: ["cuit", "contraseña", "codigo_mc"], ...}'   | Tiene que ser un json para poder estar como environment variable.
clientes      = json.loads(variables.get('CLIENTES'))
clientes_arba = json.loads(variables.get('CLIENTES_ARBA'))

# Info de la base
info_base_pg = {
    'DB_NAME'       : variables.get('DB_NAME'),
    'SQL_FILE_PATH' : variables.get('SQL_FILE_PATH'),
    'DB_USER'       : variables.get('DB_USER'),
    'DB_PASSWORD'   : variables.get('DB_PASSWORD'),
    'DB_HOST'       : variables.get('DB_HOST'),
    'DB_PORT'       : int(variables.get('DB_PORT'))
}



# Links
link_afip = "https://auth.afip.gob.ar/contribuyente_/login.xhtml"
link_afip_compras_portal_iva = r"https://liva.afip.gob.ar/liva/jsp/verCompras.do?t=21"
link_agip = "https://claveciudad.agip.gob.ar/"
link_agip_rs = 'https://lb.agip.gob.ar/ConsultaRS/'
LINK_SEH_LANUS = 'https://consultaweb.lanus.gob.ar/DeclaracionJurada/'
LINK_SEH_LOMAS = 'https://sag.lomasdezamora.gov.ar/#comercio-mensual'

# Funciones para trabajar con directorios
def extraer_zip(archivo, destino, eliminar=True):
    """
    arhivo: archivo .zip a extraer
    destino: carpeta donde se van a extraer los archivos
    eliminar: opción para eliminar o no el .zip después de la extracción
    """
    file = Path(archivo)
    archvivos_extraidos = file.stem
    destino_final = destino / archvivos_extraidos
    destino_final.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(archivo, 'r') as zip_ref:
        zip_ref.extractall(destino_final)
    
    if eliminar:
        archivo.unlink()

## Funciones para navegar en internet
def abrir_navegador(link, carpeta_descargas=None, modo_descarga=0):
    """ Abre el navegador web
    link: el link que querés abrir
    carpeta_descargas: la carpeta donde querés guardar las descargas. None por defecto.
    modo_descarga: Hay varias formas de configurar la descargas de archivos. Cada página tiene sus vericuetos
        0 → Sirve para AFIP
        1 → Sirve para AGIP Régimen simplificado
    """
    
    # Configuración para que Chrome no se cierre cuando termina el script
    options = webdriver.ChromeOptions()
    options.add_experimental_option('detach',True)

    dict_pref = {
        0 : {
            "download.default_directory": str(carpeta_descargas),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        },
        1 : {
            "download.default_directory": str(carpeta_descargas),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True
        },
    }

    if carpeta_descargas:
        carpeta_descargas = Path(carpeta_descargas)
        carpeta_descargas.mkdir(parents=True, exist_ok=True)

        prefs = dict_pref[modo_descarga]
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

def encontrar_elemento(driver, locator, description="", attempts=3, wait_time=2):
    """
    Función para encontrar un elemento en la web. En caso de que el elemento no esté, lo intentará buscar nuevamente
    driver: WebDriver
    locator: Tupla (locator_type, locator_value) | Ejemplo (By.ID, 'F1:username')
    description: Descripción del botón buscado
    attempts: intentos de búsqueda del botón
    wait_time: tiempo de espera antes de volver a buscar

    return: el elemento en caso de encontrarlo | error
    """
    for attempt in range(attempts):
        try:
            WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located(locator))
            elemento = WebDriverWait(driver, timeout=10).until(EC.element_to_be_clickable(locator))
            return elemento
        
        # except ElementClickInterceptedException:
        #     print(f'Elemento interceptado, intentando hacer click vía JavaScript: {description}')
        #     driver.execute_script("arguments[0].click();", elemento)
        #     return elemento
        
        except TimeoutException as e:
            if attempt < attempts - 1:
                logger.warning(f'No se entontró el elemento {description} porque {e}. Reintentando...')
                driver.refresh()
                time.sleep(wait_time)
            else:
                logger.error(f'El elemento {description} no está porque {e}.')
                raise RuntimeError(f'No se encontró el elemento {description}') from e

def interactuar_con_elemento(driver, locator, description="", action=0, send_input=None):
    """
    Función para interactuar con los elementos. Por ahora solo para clickear o enviar un input al elemento.
    driver: WebDriver
    locator: Tupla (locator_type, locator_value) | Ejemplo (By.ID, 'F1:username')
    description: Descripción del botón buscado
    action: 
        0 → clickear
        1 → Ingresar input
        2 → Ingresar input de desplegable y elegirlo (enter)
        3 → Seleccionar con espacio
    send_input: el input que se le quiera mandar
    return: el elemento. 
    """
    elemento = encontrar_elemento(driver, locator, description)
    if action == 1:
        elemento.clear()
        elemento.send_keys(send_input)
    elif action == 2:
        elemento.clear()
        elemento.send_keys(send_input)
        elemento.send_keys(Keys.ARROW_DOWN)
        elemento.send_keys(Keys.ENTER)
    elif action == 3:
        elemento.send_keys(Keys.SPACE)
    else:
        elemento.click()
    return elemento

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
    Función para elegir qué aplicativo de AFIP abrir
    driver: webDriver
    aplicativo:
        0 → Mis Comprobantes,
        1 → Comprobantes en línea,
        2 → SIFERE WEB,
        3 → SIFERE Consultas,
        4 → Portal IVA
        5 → Autónomos
    elegir_aplicativo: permite elegir aplicativo que no esté en la lista. Se elige escribiéndolo
    sin return
    """
    aplicativos = ["Mis Comprobantes", "Comprobantes en línea", "Sifere WEB - DDJJ", "Sifere WEB - Consultas", "Portal IVA", "CCMA - CUENTA"]
    if elegir_applicativo:
        nuevo_aplicativo = input("> ")
        interactuar_con_elemento(driver, (By.ID, 'buscadorInput'), "Buscador de AFIP", 2, nuevo_aplicativo)
    else:
        interactuar_con_elemento(driver, (By.ID, 'buscadorInput'), "Buscador de AFIP", 2, aplicativos[aplicativo])
    time.sleep(2)

    tabs = driver.window_handles
    elegir_tab(driver, len(tabs)-1 )

def afip_login(user, password, carpeta_descargas=None):
    """
    Función para loguearse a AFIP
    user: CUIT
    password: contarseña de afip
    carpeta_descargas: a donde configurar el driver para descargar archivos.

    return: WebDriver
    """
    driver = abrir_navegador(link_afip, carpeta_descargas)
    interactuar_con_elemento(driver, (By.ID, 'F1:username'), 'Input del Cuit', 1, user)
    interactuar_con_elemento(driver, (By.ID, 'F1:btnSiguiente'), 'Botón "Siguiente"', 0)
    interactuar_con_elemento(driver, (By.ID, 'F1:password'), 'Input de la contraseña', 1, password)
    interactuar_con_elemento(driver, (By.ID, 'F1:btnIngresar'), 'Botón "Ingresar"', 0)
    time.sleep(2)
    return driver

def afip_vep_aut_mon(user, password, tipo_vep, opcion_vep, eleccion_manual=False):
    """
    Función para generar un VEP para el pago de autónomos o monotributo
    user: cuit del cliente
    password: contraseña de AFIP
    tipo_vep: 'aut' | 'mon' → Sí o sí tiene que ser alguno de estos dos valores. Así busca el botón
    opcion_vep: 
        1 → Red Link
        2 → Pago Mis Cuentas
    """
    opciones_vep = {
        1 : ['1001', 'Red Link'], 
        2 : ['1002', 'Pago Mis Cuentas']
    }
    driver = afip_login(user, password)
    afip_elegir_aplicativo(driver, 5)
    interactuar_con_elemento(driver, (By.NAME, 'CalDeud'), 'Botón "CÁLCULO DE DEUDA"')
    interactuar_con_elemento(driver, (By.NAME, 'GENVOL'), 'Botón "VOLANTE DE PAGO"')
    
    if eleccion_manual:
        input('Seleccione el VEP a generar y luego ingrese ENTER')
        interactuar_con_elemento(driver, (By.NAME, 'GenerarVEP'), 'Botón "GENERAR VEP O QR"')
        interactuar_con_elemento(driver, (By.XPATH, f"(//input[@name='check_{tipo_vep}_capital'])[2]"), 'Casilla de pago')
        confirmar = input('Confirmar monto (s/n): ')
        if confirmar == 's':
            interactuar_con_elemento(driver, (By.NAME, 'GenerarVEP'), 'Botón "GENERAR VEP O QR"')
        else:
            input('Seleccione el VEP a generar y luego ingrese ENTER')
            interactuar_con_elemento(driver, (By.NAME, 'GenerarVEP'), 'Botón "GENERAR VEP O QR"')
    interactuar_con_elemento(driver, (By.ID, opciones_vep[opcion_vep][0]), f'Botón "{opciones_vep[opcion_vep][1]}"')
    interactuar_con_elemento(driver, (By.XPATH, "//button[normalize-space()='Aceptar']"), 'Confirmar Generación del VEP')
    interactuar_con_elemento(driver, (By.XPATH, "//span[contains(@class, 'material-icons') and normalize-space()='picture_as_pdf']"), 'Descargar PDF')

### Funciones para trabajar con el portal Mis Comprobantes dentro de AFIP
def mc_descargar_comprobantes(driver, mes, tipo='csv'):
    """
    tipo: 'excel' | 'csv'
    """
    fecha_emision_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "fechaEmision")))
    fecha_emision_button.clear()
    fecha_emision_button.send_keys(mes)
    fecha_emision_button.send_keys(Keys.ENTER)

    buscar_comprobantes_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "buscarComprobantes")))
    buscar_comprobantes_btn.click()
    #driver.find_element(By.ID, "buscarComprobantes").click()
    #time.sleep(3)
    
    if tipo == 'csv':
        csv_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[span="CSV"]')))
        csv_button.click()
    elif tipo == 'excel':
        excel_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn.btn-default.buttons-excel.buttons-html5.btn-defaut.btn-sm.sinborde")))
        excel_button.click()
    else:
        tipo_elegido = input('Por favor elegí entre "excel" o "csv": ')
        mc_descargar_comprobantes(driver, mes, tipo_elegido)
        
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
    mc_renombrar_y_mover(carpeta_descargas, carpeta_destino, mes)

def mc_renombrar_y_mover(origen, destino, mes):

    folder = Path(origen)
    destination = Path(destino)
    destination.mkdir(parents=True, exist_ok=True)
    mes_num = mes[3:5]
    año     = mes[6:10]
    xlsx_files = folder.glob("*.xlsx")

    for file in xlsx_files:
        new_name = file.with_stem(f"{file.stem} - {año}{mes_num}")
        file.rename(new_name)
        print(f"Renamed: {file.name} → {new_name.name}")
        shutil.move(new_name, destination / new_name.name)
        print(f"Archivo trasladado a {destination}")

### Funciones para actualizar la base de datos 

#### Funciones generales

def insertar_en_base(df, info_base_pg, table, table_key):
    """
    Función para insertar datos en la base de datos
    df      = datos a insertar
    db_path = base donde insertar
    table   = tabla donde insertar
    unique_column = columna de identificación para eliminar duplicados antes de agregar nueva data a la tabla
    return la cantidad de inserciones
    """
    
    engine = create_engine(f"postgresql+psycopg2://{info_base_pg['DB_USER']}:{info_base_pg['DB_PASSWORD']}@{info_base_pg['DB_HOST']}:{info_base_pg['DB_PORT']}/{info_base_pg['DB_NAME']}")
    datos_existentes = pd.read_sql(f'SELECT {table_key} FROM {table}', engine)
    datos_nuevos     = df[~df[table_key].isin(datos_existentes[table_key])]
    cantidad_insertada = datos_nuevos.to_sql(table, engine, if_exists='append', index=False)
    return cantidad_insertada

#### Funciones para Mis Comprobantes

def extraer_comprobantes(mc_zip_file: Path, eliminar_zip: bool=True):
    """Extrae (sueltos) todos los archivos del ZIP dado en el directorio padre del archivo."""
    with zipfile.ZipFile(mc_zip_file, 'r') as zip_ref:
        zip_ref.extractall(path=mc_zip_file.parent)
    
    if eliminar_zip:
        mc_zip_file.unlink()

def extraer_todos_los_comprobantes(zip_folder: Path):
    """Extrae (sueltos) todos los archivos de todos los zips."""
    zip_folder_list = list(zip_folder.glob('*.zip'))
    for zip_file in zip_folder_list:
        extraer_comprobantes(zip_file)

def mc_insertar_ventas_raw(df):
    """
    df: comprobantes a insertar
    TODO Abstraer la función para que funcione para otro tipo de comprobantes. Quizá hacer un diccionario de funciones (no recuerdo como se llama)
    """
    
    engine = create_engine(f"postgresql+psycopg2://{info_base_pg['DB_USER']}:{info_base_pg['DB_PASSWORD']}@{info_base_pg['DB_HOST']}:{info_base_pg['DB_PORT']}/{info_base_pg['DB_NAME']}")
    ventas_en_tabla = pd.read_sql('SELECT tipo_de_comprobante, punto_de_venta, nro_de_comprobante_desde FROM ventas_raw', engine)

    # Creamos la composite key para identificar los comprobantes únicos
    ventas_en_tabla['composite_key'] = ventas_en_tabla['tipo_de_comprobante'].astype(str) + '_' + ventas_en_tabla['punto_de_venta'].astype(str) + '_' + ventas_en_tabla['nro_de_comprobante_desde'].astype(str)
    df['composite_key']              = df['tipo_de_comprobante'].astype(str) + '_' + df['punto_de_venta'].astype(str) + '_' + df['nro_de_comprobante_desde'].astype(str)
    nuevas_ventas_unicas = df[~df['composite_key'].isin(ventas_en_tabla['composite_key'])]
    nuevas_ventas_unicas = nuevas_ventas_unicas.drop('composite_key', axis=1)

    cantidad_insertada = nuevas_ventas_unicas.to_sql('ventas_raw', engine, if_exists='append', index=False)
    
    return cantidad_insertada

def mc_pre_procesamiento_ventas_csv(file_path: Path):
    # Renombre de columnas
    columnas = {
        'Fecha de Emisión'      : 'fecha',
        'Tipo de Comprobante'   : 'tipo_de_comprobante',
        'Punto de Venta'        : 'punto_de_venta',
        'Número Desde'          : 'nro_de_comprobante_desde',
        'Número Hasta'          : 'nro_de_comprobante_hasta',
        'Cód. Autorización'     : 'cod_autorizacion',
        'Tipo Doc. Receptor'    : 'tipo_doc_receptor',
        'Nro. Doc. Receptor'    : 'nro_doc_receptor',
        'Denominación Receptor' : 'receptor',
        'Tipo Cambio'           : 'tipo_de_cambio',
        'Moneda'                : 'moneda',
        'Imp. Neto Gravado'     : 'neto_gravado',
        'Imp. Neto No Gravado'  : 'no_gravado',
        'Imp. Op. Exentas'      : 'exento',
        'Otros Tributos'        : 'otros_tributos',
        'IVA'                   : 'iva',
        'Imp. Total'            : 'importe_total'
    }
        # Columnas que hay que aclarar el type
    tipos_columnas = {
        'Tipo de Comprobante'   : str,
        'Punto de Venta'        : str,
        'Número Desde'          : str,
        'Número Hasta'          : str,
        'Cód. Autorización'     : str,
        'Tipo Doc. Receptor'    : str,
        'Nro. Doc. Receptor'    : str,
        'Denominación Receptor' : str,
        'Moneda'                : str,
    }

    # Pre-procesamiento
    cuit_cliente, fecha_de_bajada  = file_path.stem.split()[0][-25:].split('_')
    fecha_datetime = datetime.strptime(fecha_de_bajada, '%Y%m%d-%H%M')

    # Importación
    df_ventas_csv = pd.read_csv(
        file_path,
        delimiter   = ';',
        decimal     = ',',
        dtype       = tipos_columnas,
    )

    # Procesamiento
    df_ventas_csv          = df_ventas_csv.rename(columns=columnas)
    df_ventas_csv['fecha'] = pd.to_datetime(df_ventas_csv['fecha']).dt.date

    # Nuevas columnas
    df_ventas_csv['cuit_cliente'] = cuit_cliente
    df_ventas_csv['fecha_descarga'] = fecha_datetime
    df_ventas_csv['porcentaje_iva'] = round(df_ventas_csv['iva'] / df_ventas_csv['neto_gravado'], 2)

    # Data Frame transformado
    return df_ventas_csv


## Funciones AGIP

def agip_login(user, password, carpeta_descargas=None):
    driver = abrir_navegador(link_agip, carpeta_descargas, 1)
    interactuar_con_elemento(driver, (By.ID, "cuit"), 'Input: "CUIT"', 1, user)
    interactuar_con_elemento(driver, (By.ID, "clave"), 'Input: "CLAVE"', 1, password)
    interactuar_con_elemento(driver, (By.CSS_SELECTOR,"a.btn.btn-primary.btn-block.btn-lg"), 'Botón "Ingresar"')
    return driver

def agip_cerrar_sesion(driver):
    """
    Función para cerrar sesión en AGIP. Busca el desplegable del usuario y cierra la sesión
    driver: webDriver
    """
    interactuar_con_elemento(driver, (By.ID, "li-navbar-concc-ident-impu"), "Desplegable del usuario" )
    interactuar_con_elemento(driver, (By.ID, "li-navbar-concc-salir"), "Botón para cerrar sesión" )

def agip_regimen_simplificado(user, password, carpeta_descargas=None):
    driver = agip_login(user, password, carpeta_descargas)
    interactuar_con_elemento(driver, (By.XPATH, "//h5[normalize-space()='Consulta Regimen Simplificado']"), 'Botón "Consulta Régimen Simplificado"')
    interactuar_con_elemento(driver, (By.ID, "myModalBtnOk"), 'Pop-up: "Ok"')
    interactuar_con_elemento(driver, (By.XPATH, "(//input[@type='checkbox' and contains(@class, 'check')])[last() - 1]"), 'Anteúltima Chechbox mes de pago',3)
    confirmar = input('Confirmar pago(s/n): ') == 's'
    if confirmar:
        interactuar_con_elemento(driver, (By.ID, "btnGenerarVeps"), 'Botón: "Obtener Boletas / Pagos"')
    else:
        input('Seleccione el mes a pagar y luego ENTER')
        interactuar_con_elemento(driver, (By.ID, "btnGenerarVeps"), 'Botón: "Obtener Boletas / Pagos"')
    
    # Originalmente abría un iframe. Tuve que cambiar la función abrir_navegador para que no lo abra y lo baje directo. Quizá no funcione para VEPs
    interactuar_con_elemento(driver, (By.ID, "img-btn-pago-efectivo"), 'Botón: "Ver boletas" (genera Boleta de Pago)')
    time.sleep(2)
    driver.refresh()
    agip_cerrar_sesion(driver)
    
    return driver

### Funciones para interactuar con la página de Seguridad e Higiene de Lanús

def seh_lanus(user, password, monto=0, carpeta_descargas=None):
    """
    Función para liquidar Seguridad e Higiene de Lanús
    user: CUIT
    password: Contraseña SEH Lanús
    monto: monto mensual que facturó el cliente
    carpeta_descargas: Ubicación del pdf a descargar
    return WebDriver
    """
    mes = input("Ingresar mes a liquidar (ene = 01): ")
    driver = abrir_navegador(LINK_SEH_LANUS, carpeta_descargas)
    actions = ActionChains(driver)
    
    interactuar_con_elemento(driver, (By.ID, 'txtCuenta'),"Input: CUIT", 1, user)
    actions.send_keys(Keys.TAB).perform()
    time.sleep(1)
    interactuar_con_elemento(driver, (By.ID, 'txtClave'),"Input: Clave", 1, password)
    interactuar_con_elemento(driver, (By.ID, 'btnConsultar'),"Botón: Consultar")
    
    interactuar_con_elemento(driver, (By.ID, 'txtMes'),"Input: Mes", 1, mes)
    actions.send_keys(Keys.TAB).perform()
    interactuar_con_elemento(driver, (By.ID, 'btnConsultar'),"Botón: Consultar")
    #actions.send_keys(Keys.TAB).perform()
    interactuar_con_elemento(driver, (By.XPATH, "(//input[@id='TextBox1'])[1]"),"Input: Monto Mensual", 1, monto)
    # El checkbox al parecer no es un EC.element_to_be_clickable. Rompe la función encontrar_elemento. Hay que usar javascript para clickearlo
    checkbox = WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located((By.XPATH, "//input[@id='lblLeyendaSF']")))
    driver.execute_script("arguments[0].click();", checkbox)
    input('ENTER para continuar')
    #actions.send_keys(Keys.TAB).perform()
    interactuar_con_elemento(driver, (By.ID, 'btnGrabar'),"Botón: Aceptar")
    interactuar_con_elemento(driver, (By.ID, 'btnAceptar'),"Botón: Grabar")
    interactuar_con_elemento(driver, (By.ID, 'hideModalPopupViaServer'),"Pop-up de Confirmación: Aceptar")
    input('ENTER para continuar')
    #interactuar_con_elemento(driver, (By.ID, 'btnConsultar'), "Botón: Boleta de pago")
    #btn_aceptar = WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located((By.ID, 'btnGravar')))
    #driver.execute_script("arguments[0].click();", btn_aceptar)

    return driver


### Funciones para interactuar con la página de Seguridad e Higiene de Lomas

def seh_lomas(user_type, user, password, monto, carpeta_descargas=None):
    """
    Función para liquidar SEH Lomas.
    user_type:
        1 = DNI
        2 = CUIL/CUIT
    user: nro de identidad según user_type
    password: contraseña de SEH Lomas
    monto: monto facturado
    carpeta_descargas: Path de descarga de la documentación
    """
    driver = abrir_navegador(LINK_SEH_LOMAS, carpeta_descargas)
    time.sleep(1)
    interactuar_con_elemento(driver, (By.ID, 'Button3'), "Pop-up: Aceptar")
    desplegable = Select(encontrar_elemento(driver, (By.ID, 'ctl06_ddlTipo'), "Desplegable: Seleccionar Tipo"))
    desplegable.select_by_index(user_type)
    interactuar_con_elemento(driver, (By.ID, 'ctl06_user'), "Input: DNI/CUIL/CUIT", 1, user)
    interactuar_con_elemento(driver, (By.ID, 'ctl06_password'), "Input: Clave", 1, password)
    tabear(driver, 1)
    time.sleep(1)
    interactuar_con_elemento(driver, (By.XPATH, "//a[contains(text(), 'Declaraciones Juradas')]"),"Botón: Declaraciones Juradas")
    interactuar_con_elemento(driver, (By.XPATH, "//a[@mdata='comercio-mensual']"),"Botón: Mensual por Ingresos")
    driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "app"))))
    interactuar_con_elemento(driver, (By.ID, 'btnAceptar2'), "Botón: Consultar")
    interactuar_con_elemento(driver, (By.XPATH, "(//input[@id='TextBox1'])[1]"), "Input: Monto mensual", 1, monto)
    empleados = input('Ingrese cantidad de empleados: ')
    interactuar_con_elemento(driver, (By.XPATH, "(//input[@id='TextBox1'])[2]"), "Input: Empleados", 1, empleados)
    checkbox = WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located((By.XPATH, "//input[@id='lblLeyendaSF']")))
    driver.execute_script("arguments[0].click();", checkbox)
    input('ENTER para confirmar la declaración')
    interactuar_con_elemento(driver, (By.ID, 'btnGrabar'),"Botón: Aceptar")
    input('ENTER cuando se pueda grabar la declaración')
    interactuar_con_elemento(driver, (By.ID, 'btnAceptar'),"Botón: Grabar")
    input('ENTER después de imprimir')
    driver.switch_to.default_content()
    interactuar_con_elemento(driver, (By.XPATH, "//a[contains(text(), 'Consulta de Deuda ')]"),"Botón: Consulta de Deuda")
    interactuar_con_elemento(driver, (By.XPATH, "//a[@mdata='estado-de-deuda']"),"Botón: Estado de Deuda")
    driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "app"))))
    interactuar_con_elemento(driver, (By.ID, 'rdbComercio'))
    interactuar_con_elemento(driver, (By.ID, 'btnConsultar'))
    input('ENTER Cuando se vea la deuda')
    driver.switch_to.default_content()
    driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "app"))))
    checkbox = WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located((By.XPATH, "(//div[@class='checkbox-inline'])[last()]")))
    driver.execute_script("arguments[0].click();", checkbox)
    interactuar_con_elemento(driver, (By.XPATH, "//button[@id='btnConsultar']"))
    input('ENTER después de imprimir')

    driver.quit()

    return driver

# Clases y funciones para interactuar con Comprobantes en Línea en AFIP

def cel_ingreso(user, password):
    driver = afip_login(user, password)
    afip_elegir_aplicativo(driver, 1)
    return driver



# Clases
# | Elemento                → Clase base para interactuar con elementos de Selenium. Según el tipo de elemento, la subclase indicará cómo encontrarlo.
# |   Boton                 → Subclase de elemento en la que entran casillas, botones de input o botones de interacción. Se puede mandar un input o clickearlos.
# |     FormaDePagoCEL      → Subclase de botón que te permite elegir cualquiera de todas las formas de pago disponibles y seleccionarlas como un botón concreto
# |     BotonesEnOrden      → Subclase de botón que te permite elegir entre varias tandas de botones ordenados en lista. Hay que seleccionar la tanda y luego el nro de botón a clickear.
# |   Desplegable           → Subclase de elemento que es una lista desplegable. Permite elegir opciones de un listado
# |     TipoComprobantesRI  → Subclase de desplegable que te da las opciones para los tipo de comprobantes que podés elegir siendo Responsable Inscripto
# |     MonedasCEL          → Subclase de desplegable para elegir la divisa en caso de pagar con Moneda extranjera. 
# |     ConceptosCEL        → Subclase de desplegable para elegir el tipo de bien entregado (Producto, Servicio o ambos)
# |     CondicionIvaFA      → Subclase de desplegable para elegir la condición de IVA del receptor de la factura
# |   Lista                 → Subclase de elemento que toma varios elementos enlistados de la página web y te permite elegir entre ellos. Enlistados según si comparten mismo name por ejemplo. Creo que quedó obsoleta. Se puede usar el xpath y crear una subclase de Botón con todos los botones del mismo xpath. 



class Elemento(object):
    TIMEOUT = 10
    RETRY_DELAY = 0.5
    MAX_RETRIES = 3

    def __init__(self, driver, locator):
        self.driver = driver
        self.locator = locator
        self.object = None
        self._get_object_with_retries()

    def _get_object(self):
        """A implementar"""
        raise NotImplementedError('Esto lo tiene que implementar cada subclase')
    
    def _get_object_with_retries(self):
        for _ in range(self.MAX_RETRIES):
            try:
                self.object = self._get_object()
                return
            except (TimeoutException, StaleElementReferenceException):
                time.sleep(self.RETRY_DELAY)
        raise TimeoutException(f'No se encontró el objeto después de {self.MAX_RETRIES} intentos.')
    
    def _ensure_fresh(self):
        """Refrescar el objeto por si no está clickeable"""
        if self._is_stale():
            self._get_object_with_retries()
    
    def _is_stale(self):
        try:
            if isinstance(self.object, list):
                return self._is_stale_element(self.object[0])
            elif hasattr(self.object, 'options'):
                return self._is_stale_element(self.object._el)
            else:
                return self._is_stale_element(self.object)
        except Exception:
            return True
        
    def _is_stale_element(self, element):
        try:
            element.is_enabled()
            return False
        except StaleElementReferenceException:
            return True

class Boton(Elemento):
    def __init__(self, driver, locator):
        super().__init__(driver, locator)

    def _get_object(self):
        self.object = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(self.locator))
        return self.object

    def click(self):
        self._ensure_fresh()
        self.object.click()

    def send_keys(self, keys, clear=False):
        self._ensure_fresh()
        if clear:
            self.object.clear()
        self.object.send_keys(keys)

class Alerta(Elemento):
    def __init__(self, driver):
        super().__init__(driver, None)
    
    def _get_object(self):
        self.object = WebDriverWait(self.driver, self.TIMEOUT).until(EC.alert_is_present())
    
    def aceptar(self):
        self.object.accept()


class FormaDePagoCEL(Boton):
    FORMAS_DE_PAGO = {
        'Contado'                          : 1,
        'Tarjeta de Débito'                : 2,
        'Tarjeta de Crédito'               : 3,
        'Cuenta Corriente'                 : 4,
        'Cheque'                           : 5,
        'Transferencia Bancaria'           : 6,
        'Otra'                             : 7,
        'Otros medios de pago electrónico' : 8
    }

    def __init__(self, driver, opcion):
        locator = (By.ID, f'formadepago{self.FORMAS_DE_PAGO[opcion]}')
        super().__init__(driver, locator)



class Desplegable(Elemento):

    def __init__(self, driver, locator, options=None):
        self._objeto_raw = None
        super().__init__(driver, locator)
        self.options = options or {}
        
    def _get_object(self):
        self.objeto_raw = WebDriverWait(self.driver, self.TIMEOUT).until(EC.element_to_be_clickable(self.locator))        
        return Select(self.objeto_raw)

    
    def seleccionar_indice(self, index):
        self._ensure_fresh()
        self.object.select_by_index(index)

class Lista(Elemento):

    def __init__(self, driver, locator, options=None):
        super().__init__(driver, locator)
        self.options = options or {}
        
    def _get_object(self):
        objeto = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_all_elements_located(self.locator))
        return objeto
    
    def __getitem__(self, index):
        self._ensure_fresh()
        return self.object[index]
    

class ListaEmpresasCEL(Lista):
    options = {
        'Empresa 1' : 0,
        'Empresa 2' : 1,
        'Empresa 3' : 2,
        'Empresa 4' : 3,
        'Empresa 5' : 4
        
    }
    def __init__(self, driver):
        locator = (By.CLASS_NAME, 'btn_empresa')
        super().__init__(driver, locator, self.options)


class ListaAccionesCEL(Lista):
    options = {
        'Generar Comprobantes' : 0,
        'Consultar'            : 1
    }

    def __init__(self, driver):
        locator = (By.CLASS_NAME, 'ui-button')
        super().__init__(driver, locator, self.options)

class TipoComprobantes(Desplegable):
    options = {
            'RI' : {
        'Factura A'         : 0,
        'Nota de Débito A'  : 1,
        'Nota de Crédito A' : 2,
        'Recibo A'          : 3,
        'Factura B'         : 4,
        'Nota de Débito B'  : 5,
        'Nota de Crédito B' : 6,
        'Recibo B'          : 7,
        'Factura T'         : 8,
        'Nota de Débito T'  : 9,
        'Nota de Crédito T' : 10
        },
    'MONO' : {
        'Factura C'                        : 0,
        'Nota de Débito C'                 : 1,
        'Nota de Crédito C'                : 2,
        'Recibo C'                         : 3,
        'Factura de Crédito Electrónica C' : 4,
        'Nota de Débito Electrónica C'     : 5,
        'Nota de Crédito Electrónica C'    : 6
    }
    
}
    
    def __init__(self, driver, tipo_contribuyente):
        locator = (By.NAME, 'universoComprobante')
        super().__init__(driver, locator, self.options[tipo_contribuyente])


class MonedasCEL(Desplegable):
    MONEDAS = {
        'seleccionar'          : 0,
        'Dólar Estadounidense' : 15,
        'Dólar Libre EEUU'     : 16
    }

    def __init__(self, driver):
        locator = (By.NAME, 'moneda')
        super().__init__(driver, locator, self.MONEDAS)

class ConceptosCEL(Desplegable):
    CONCEPTOS = {
        'Productos' : 1,
        'Servicios' : 2,
        'Productos y Servicios' : 3
    }

    def __init__(self, driver):
        locator = (By.NAME, 'idConcepto')
        super().__init__(driver, locator, self.CONCEPTOS)


class CondicionIva(Desplegable):
    options = {
        'RI' : {
            'seleccionar' : 0,
            'IVA Responsable Inscripto' : 1,
            'Responsable Monotributo'   : 2,
            'Monotributista Social'     : 3,
            'Monotributista TIP'        : 4
    },
        'MONO' : {
            'seleccionar'                  : 0,
            'IVA Responsable Inscripto'    : 1,
            'IVA Sujeto Exento'            : 2,
            'Consumidor Final'             : 3,
            'Responsable Monotributo'      : 4,
            'Sujeto No Categorizado'       : 5,
            'Proveedor del Exterior'       : 6,
            'Cliente del Exterior'         : 7,
            'IVA Liberado - Ley N° 19.640' : 8,
            'Monotributista Social'        : 9,
            'IVA No Alcanzado'             : 10,
            'Monotributista TIP'           : 11
        }
}
    def __init__(self, driver, tipo_factura):
        locator = (By.NAME, 'idIVAReceptor')
        super().__init__(driver, locator, self.options[tipo_factura])

class BotonesEnOrdenCEL(Boton):
    LOCATORS = {
        'contribuyentes' : "(//input[@class='btn_empresa ui-button ui-widget ui-state-default ui-corner-all'])",
        'acciones'       : "(//a[contains(@class, 'ui-button') and contains(@class, 'ui-widget') and contains(@class, 'ui-state-default') and contains(@class, 'ui-corner-all') and contains(@class, 'ui-button-text-icons')])"
    }

    def __init__(self, driver, locator, num):
        locator = (By.XPATH, f'{self.LOCATORS[locator]}[{num}]')
        super().__init__(driver, locator)


class IvaCEL(Desplegable):
    options = {
        'No gravado' : 1,
        'Exento'     : 2,
        '0%'         : 3,
        '2.5%'       : 4,
        '5%'         : 5,
        '10.5%'      : 6,
        '21%'        : 7,
        '27%'        : 8
    }

    def __init__(self, driver):
        locator = (By.XPATH, "(//select[@name='detalleTipoIVA'])")
        super().__init__(driver, locator, self.options)


def opcionales_pagina_4(driver, conceptos='Productos', moneda='ARS'):
    not_productos = []
    not_ars = []
    
    if conceptos != 'Productos':
        btn_fecha_desde = Boton(driver, (By.NAME, 'periodoFacturadoDesde'))
        btn_fecha_hasta = Boton(driver, (By.NAME, 'periodoFacturadoHasta'))
        btn_fecha_vencimiento_pago = Boton(driver, (By.NAME, 'vencimientoPago'))
        not_productos = [btn_fecha_desde, btn_fecha_hasta, btn_fecha_vencimiento_pago]
    
    if moneda != 'ARS':
        casilla_moneda_extranjera = Boton(driver, (By.XPATH, "//input[@name='monedaExtranjera']"))
        casilla_pago_misma_moneda = Boton(driver, (By.XPATH, "//input[@id='cancelacionMonedaExtranjera']"))
        btn_moneda = MonedasCEL(driver)
        btn_tipo_de_cambio = Boton(driver, (By.NAME, 'tipoCambio'))
        not_ars = [casilla_moneda_extranjera, casilla_pago_misma_moneda, btn_moneda, btn_tipo_de_cambio]

    resultados = {
        'Fecha' : not_productos,
        'Pago'   : not_ars
    }

    return resultados

def facturar(driver, comprobante):
    # Página 1: Seleccionar empresa a representar
    btn_empresa = BotonesEnOrdenCEL(driver, 'contribuyentes', comprobante['Representante']) 
    time.sleep(1)
    btn_empresa.click()

    # Página 2: Seleccionar acción a realizar
    btn_accion = BotonesEnOrdenCEL(driver, 'acciones', 1)
    time.sleep(1)
    btn_accion.click()

    # Página 3: Puntos de Venta y Tipos de Comprobantes
    desplegable_punto_de_venta = Desplegable(driver, (By.NAME, 'puntoDeVenta'))
    desplegable_punto_de_venta.seleccionar_indice(comprobante['Punto de Venta'])
    desplegable_tipo_comp = TipoComprobantes(driver, comprobante['Tipo de Representante'])
    desplegable_tipo_comp.seleccionar_indice(desplegable_tipo_comp.options[comprobante['Tipo de Comprobante']]) # Requiere input
    btn_continuar  = Boton(driver, (By.XPATH, "//input[@value='Continuar >']"))
    time.sleep(1)
    btn_continuar.click()

    # Página 4: Datos de emisión (Paso 1 de 4)
    btn_fecha_comprobante = Boton(driver, (By.NAME, 'fechaEmisionComprobante'))
    btn_fecha_comprobante.send_keys(comprobante['Fecha del Comprobante'], clear=True)
    desplegable_conceptos = ConceptosCEL(driver)
    desplegable_conceptos.seleccionar_indice(desplegable_conceptos.options[comprobante['Concepto']])
    resultados = opcionales_pagina_4(driver, comprobante['Concepto'])

    if resultados['Fecha']:
        btn_fecha_desde, btn_fecha_hasta, btn_vto_pago = resultados['Fecha']
        btn_fecha_desde.send_keys(comprobante['Fecha Desde'], clear=True)
        btn_fecha_hasta.send_keys(comprobante['Fecha Hasta'], clear=True)
        btn_vto_pago.send_keys(comprobante['Fecha Vto del Pago'], clear=True)
    # TODO if resultados['Pago']:

    desplegable_actividad = Desplegable(driver, (By.NAME, 'actiAsociadaId'))
    desplegable_actividad.seleccionar_indice(comprobante['Acitividad'])
    time.sleep(1)
    btn_continuar.click()

    # Página 5: Datos del receptor (Paso 2 de 4)
    desplegable_condicion_iva = CondicionIva(driver, comprobante['Tipo de Representante'])
    desplegable_condicion_iva.seleccionar_indice(desplegable_condicion_iva.options[comprobante['Condición IVA Receptor']])
    casilla_forma_de_pago = FormaDePagoCEL(driver, comprobante['Forma de Pago'])
    casilla_forma_de_pago.click()
    time.sleep(1)
    btn_continuar.click()

    # Página 6: Datos de la operación (Paso 3 de 4)
    btn_producto_servicio = Boton(driver, (By.XPATH, "(//textarea[@name='detalleDescripcion'])[1]"))
    btn_cantidad          = Boton(driver, (By.XPATH, "(//input[@name='detalleCantidad'])[1]"))
    btn_precio_unitario   = Boton(driver, (By.XPATH, "(//input[@name='detallePrecio'])[1]"))
    btn_producto_servicio.send_keys(comprobante['Detalle de venta'], True)
    btn_cantidad.send_keys(comprobante['Cantidad'], True)
    btn_precio_unitario.send_keys(comprobante['Precio'], True)
    time.sleep(1)
    btn_continuar.click()

    # Página 7: Confirmación

    btn_confirmar = Boton(driver, (By.ID, "btngenerar"))
    btn_confirmar.click()
    alerta = Alerta(driver)
    alerta.aceptar()
    btn_menu_ppal = Boton(driver, (By.XPATH, "//input[@value='Menú Principal']"))
    time.sleep(1)
    btn_menu_ppal.click()

    print('El comprobante fue facturado con éxito')

    return driver