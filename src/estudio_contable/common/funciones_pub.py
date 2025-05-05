import json
import logging
import pandas  as pd
import shutil
import time                                                                    # time sirve para hacer demorar el archivo para que cargue
import zipfile
from datetime                                import datetime, timedelta
from dotenv                                  import dotenv_values              # Para cargar environment variables
from pathlib                                 import Path
from selenium                                import webdriver                  # webdriver sirve para agarrar el navegador
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
            elemento = WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located(locator))
            logger.info(f'Elemento {description} encontrado')
            return elemento
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

def afip_vep_aut_mon(user, password, tipo_vep, eleccion_manual=False):
    """
    Función para generar un VEP para el pago de autónomos o monotributo
    user: cuit del cliente
    password: contraseña de AFIP
    tipo_vep: 'aut' | 'mon' → Sí o sí tiene que ser alguno de estos dos valores. Así busca el botón
    """
    driver = afip_login(user, password)
    afip_elegir_aplicativo(driver, 5)
    interactuar_con_elemento(driver, (By.NAME, 'CalDeud'), 'Botón Calculo de Deuda')
    interactuar_con_elemento(driver, (By.NAME, 'GENVOL'), 'Botón Generar Volante de Pago')
    
    if eleccion_manual:
        input('Seleccione el VEP a generar y luego ingrese ENTER')
        interactuar_con_elemento(driver, (By.NAME, 'GenerarVEP'), 'Botón para generar el VEP')
    else:
        interactuar_con_elemento(driver, (By.NAME, f'check_{tipo_vep}_capital'), 'Casilla de pago mensual autónomos (último mes)')
        confirmar = input('Confirmar monto (s/n): ')
        if confirmar == 's':
            interactuar_con_elemento(driver, (By.NAME, 'GenerarVEP'), 'Botón para generar el VEP')
        else:
            input('Seleccione el VEP a generar y luego ingrese ENTER')
            interactuar_con_elemento(driver, (By.NAME, 'GenerarVEP'), 'Botón para generar el VEP')

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



