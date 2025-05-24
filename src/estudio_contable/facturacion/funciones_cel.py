from selenium.common.exceptions              import StaleElementReferenceException
from selenium.webdriver.common.by            import By                         # By sirve para filtrar elementos
from selenium.webdriver.support              import expected_conditions as EC  # Para esperar los elementos
from selenium.webdriver.support.ui           import Select                     # Para elegir de desplegables
from selenium.webdriver.support.ui           import WebDriverWait              # Para que espere mientras carga la página 
from estudio_contable.common.basicos import afip_login, afip_elegir_aplicativo, Elemento, Alerta, Boton, Desplegable, Lista
import pandas as pd
import time


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

def inicio_facturacion(driver, representante):
    # Página 1: Seleccionar empresa a representar
    btn_empresa = BotonesEnOrdenCEL(driver, 'contribuyentes', representante) 
    time.sleep(1)
    btn_empresa.click()

    return driver

def facturar(driver, comprobante):
    # Página 2: Seleccionar acción a realizar
    btn_accion = BotonesEnOrdenCEL(driver, 'acciones', 1)
    time.sleep(1)
    btn_accion.click()

    # Página 3: Puntos de Venta y Tipos de Comprobantes
    desplegable_punto_de_venta = Desplegable(driver, (By.NAME, 'puntoDeVenta'))
    desplegable_punto_de_venta.seleccionar_indice(comprobante['Punto de Venta'])
    time.sleep(1)
    if (comprobante['Tipo de Representante'] == 'MONO') & (comprobante['Tipo de Comprobante'] != 'Factura C'):
        desplegable_tipo_comp = TipoComprobantes(driver, comprobante['Tipo de Representante'])
        try:
            desplegable_tipo_comp.seleccionar_indice(desplegable_tipo_comp.options[comprobante['Tipo de Comprobante']])
        except StaleElementReferenceException:
            desplegable_tipo_comp = TipoComprobantes(driver, comprobante['Tipo de Representante'])
            desplegable_tipo_comp.seleccionar_indice(desplegable_tipo_comp.options[comprobante['Tipo de Comprobante']])

    elif (comprobante['Tipo de Representante'] == 'RI') & (comprobante['Tipo de Comprobante'] != 'Factura A'):
        desplegable_tipo_comp = TipoComprobantes(driver, comprobante['Tipo de Representante'])
        try:
            desplegable_tipo_comp.seleccionar_indice(desplegable_tipo_comp.options[comprobante['Tipo de Comprobante']])
        except StaleElementReferenceException:
            desplegable_tipo_comp = TipoComprobantes(driver, comprobante['Tipo de Representante'])
            desplegable_tipo_comp.seleccionar_indice(desplegable_tipo_comp.options[comprobante['Tipo de Comprobante']])
    time.sleep(1)
    btn_continuar  = Boton(driver, (By.XPATH, "//input[@value='Continuar >']"))
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

def facturar_todo(driver, excel_file):
    df_datos_generales = pd.read_excel(excel_file, sheet_name="datos_generales")
    representante      = df_datos_generales['eleccion'][0]
    df_comprobantes    = pd.read_excel(excel_file, sheet_name="comprobantes")
    df_comprobantes    = df_comprobantes.iloc[:,0:13].dropna()
    driver = inicio_facturacion(driver, representante)

    for _, row in df_comprobantes.iterrows():
        comprobante = {
            'Tipo de Representante'  : df_datos_generales['eleccion'][1],
            'Punto de Venta'         : str(int(row['punto_de_venta'])),
            'Tipo de Comprobante'    : row['tipo_comprobante'],
            'Fecha del Comprobante'  : row['fecha_comprobante'].strftime('%d/%m/%Y'),
            'Concepto'               : row['concepto'],
            'Fecha Desde'            : row['fecha_desde'].strftime('%d/%m/%Y'),
            'Fecha Hasta'            : row['fecha_hasta'].strftime('%d/%m/%Y'),
            'Fecha Vto del Pago'     : row['fecha_vto_pago'].strftime('%d/%m/%Y'),
            'Acitividad'             : str(int(row['actividad'])),
            'Condición IVA Receptor' : row['condicion_iva_receptor'],
            'Forma de Pago'          : row['forma_de_pago'],
            'Detalle de venta'       : row['detalle'],
            'Cantidad'               : str(int(row['cantidad'])),
            'Precio'                 : row['precio_unitario']
        }
        driver = facturar(driver, comprobante)
        print(f'{row}')
        print('-' * 40)

def cel_facturacion(user, password, excel_file):
    driver = cel_ingreso(user, password)
    facturar_todo(driver, excel_file)