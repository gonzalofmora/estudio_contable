from estudio_contable.common.funciones_pub import tabear
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys         # Para importar las teclas del teclado
from selenium.webdriver.common.by import By             # By sirve para filtrar elementos
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time 


def cel_seleccionar_empresa(driver, num):
    """Elegí la empresa a representar en el sitio de Comprobantes en Línea"""
    tabear(driver, num)
    time.sleep(1)

def cel_elegir_accion(driver, num):
    """Elegir si generar comprobantes o consultar comprobantes | TODO la consulta"""
    generar_comprobantes_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "btn_gen_cmp")))
    #generar_comprobantes_btn = driver.find_element(By.ID, "btn_gen_cmp")
    if num == 0:
        generar_comprobantes_btn.click()
        time.sleep(1)
    else: cel_elegir_accion(driver, input())

def cel_punto_venta(driver, num):
    """Elegir el punto de venta y el tipo de comprobante a generar. Por ahora solo punto de venta."""
    # Punto de venta
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "puntodeventa"))).click() 
    #driver.find_element(By.ID, "puntodeventa").click()

    for _ in range(num):
        ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
    ActionChains(driver).send_keys(Keys.ENTER).perform()
    time.sleep(1)
    tabear(driver, 3)

def cel_fechas(driver, tipo, fecha):
    """Elegir fecha:
    Fecha de Comp.: 0
    Fecha Desde:    1
    Fecha Hasta:    2"""
    if tipo == 0:
        tipo = "fc"
    elif tipo == 1:
        tipo = "fsd"
    else:
        tipo = "fsh"
    fecha_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, tipo)))
    #fecha_btn = driver.find_element(By.ID, tipo)
    fecha_btn.clear()
    fecha_btn.send_keys(fecha)

def cel_elegir_concepto(driver, concepto):
    """
    conceptos:
    Productos → P
    Servicios → S
    Productos y Servicios → PyS
    """
    conceptos = {
        "P" : 1,
        "S" : 2,
        "PyS": 3
    }
    
    tabear(driver, 2)
    actions = ActionChains(driver)
    for _ in range(conceptos[concepto]):
        actions.send_keys(Keys.ARROW_DOWN)
    actions.send_keys(Keys.ENTER)
    actions.perform()

def cel_elegir_actividad(driver, num):
    """Elegir la actividad del cliente."""
    #Actividad
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "actiAsociadaId"))).click() 
    #driver.find_element(By.ID, "actiAsociadaId").click()

    for _ in range(num):
        ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
    ActionChains(driver).send_keys(Keys.ENTER).perform()
    time.sleep(1)
    tabear(driver, 7)

def cel_condiciones_receptor(driver, tipo_iva, tipo_venta ):
    """Elegir las condiciones de la venta
    tipo_iva = condicion frente al iva
    3 → Consumidor final
    tipo_venta = condición de venta
    1 → Contado"""
    # Condiciones de IVA
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "idivareceptor"))).click() 
    #driver.find_element(By.ID, "idivareceptor").click()    

    for _ in range(tipo_iva):
        ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
    ActionChains(driver).send_keys(Keys.ENTER).perform()
    time.sleep(1)
    tabeos = tipo_venta + 5
    tabear(driver, tabeos, con_barra=True)
    tabeos_para_continuar = 16 - tipo_venta
    tabear(driver, tabeos_para_continuar)

def cel_detalles(driver, tipo, texto):
    """Elegir fecha:
    Producto/Servicio: 0
    Cant.:             1
    Prec. Unitario:    2"""
    if tipo == 0:
        tipo = "detalle_descripcion1"
    elif tipo == 1:
        tipo = "detalle_cantidad1"
    else:
        tipo = "detalle_precio1"
    fecha_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, tipo)))
    #fecha_btn = driver.find_element(By.ID, tipo)
    fecha_btn.clear()
    fecha_btn.send_keys(texto)

def cel_continuar_y_confirmar(driver):
    # Botón de continuar
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@wfd-id='id25']"))).click() 
    #driver.find_element(By.XPATH, "//input[@wfd-id='id25']").click() 

    # Botón de confirmar
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "btngenerar"))).click() 
    #driver.find_element(By.ID, "btngenerar").click()

    # Pop up de confirmación
    wait = WebDriverWait(driver, 2)  
    alert = wait.until(EC.alert_is_present())
    alert.accept()

def cel_terminar(driver, imprimir=False):
    "Elegir si volver al menú principal imprimiendo la factura o no"
    if imprimir:
        # Imprimir
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@value='Imprimir...']"))).click() 
        #driver.find_element(By.XPATH, "//input[@value='Imprimir...']").click()
    # Menú Principal
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@value='Menú Principal']"))).click() 
    #driver.find_element(By.XPATH, "//input[@value='Menú Principal']").click()


#######################################################################################################


def cel_facturar(driver, fecha, fecha_desde, fecha_hasta, servicio, cantidad, precio):
    cel_elegir_accion(driver, 0)            # Elegimos si generar comprobantes o consultarlos
    time.sleep(1)
    cel_punto_venta(driver, 1)              # Elegimos el punto de venta
    time.sleep(1)
    cel_fechas(driver, 0, fecha)            # Elegimos la Fecha del Comprobante
    time.sleep(1)
    cel_elegir_concepto(driver, "PyS")      # Elegimos los conceptos a incluir
    time.sleep(1)
    cel_fechas(driver, 1, fecha_desde)      # Elegimos la Fecha Desde (Solo cuando se incluyen servicios)
    time.sleep(1)
    cel_fechas(driver, 2, fecha_hasta)      # Elegimos la Fecha Hasta (Solo cuando se incluyen servicios)
    time.sleep(1)
    cel_elegir_actividad(driver, 2)         # Elegimos la actividad
    time.sleep(1)
    cel_condiciones_receptor(driver, 3, 1)  # Elegimos las condiciones del receptor
    time.sleep(1)
    cel_detalles(driver, 0, servicio)       # Servicio de la venta
    cel_detalles(driver, 1, cantidad)       # Cantidad vendida
    cel_detalles(driver, 2, precio)         # Precio del bien
    time.sleep(1)
    cel_continuar_y_confirmar(driver)       # Confirmamos la operación
    time.sleep(1)
    cel_terminar(driver)                    # Volvemos al menú principal
    time.sleep(1)

def cel_facturar_mucho(driver, df):

    for _, row in df.iterrows():
        
        fecha = row["fecha"].strftime('%d/%m/%Y')
        fecha_desde = row['fecha_desde'].strftime('%d/%m/%Y')
        fecha_hasta = row['fecha_hasta'].strftime('%d/%m/%Y')
        servicio = row['servicio']
        cantidad = str(row['unidades'])
        precio = float(row['precio'])

        cel_facturar(driver, fecha, fecha_desde, fecha_hasta, servicio, cantidad, precio)
        print(f"Esta venta fue facturada:\n {row}")