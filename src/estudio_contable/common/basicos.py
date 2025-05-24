import time                                                                    # time sirve para hacer demorar el archivo para que cargue
from pathlib                                 import Path
from selenium                                import webdriver                  # webdriver sirve para agarrar el navegador
from selenium.common.exceptions              import StaleElementReferenceException
from selenium.common.exceptions              import TimeoutException
from selenium.webdriver.common.by            import By                         # By sirve para filtrar elementos
from selenium.webdriver.support              import expected_conditions as EC  # Para esperar los elementos
from selenium.webdriver.common.keys          import Keys                       # Para importar las teclas del teclado
from selenium.webdriver.support.ui           import Select                     # Para elegir de desplegables
from selenium.webdriver.support.ui           import WebDriverWait              # Para que espere mientras carga la página 



# Links
link_afip = "https://auth.afip.gob.ar/contribuyente_/login.xhtml"

# Clases base

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
        return WebDriverWait(self.driver, self.TIMEOUT).until(EC.alert_is_present())
    
    def aceptar(self):
        self.object.accept()

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


# Funciones para interactuar con AFIP

def afip_login(user, password, carpeta_descargas=None):
    """
    Función para loguearse a AFIP
    user: CUIT
    password: contarseña de afip
    carpeta_descargas: a donde configurar el driver para descargar archivos.
    return: WebDriver
    """
    driver = abrir_navegador(link_afip, carpeta_descargas)
    btn_cuit = Boton(driver, (By.ID, 'F1:username'))
    btn_cuit.send_keys(user, clear=True)
    btn_siguiente = Boton(driver, (By.ID, 'F1:btnSiguiente'))
    btn_siguiente.click()
    btn_pass = Boton(driver, (By.ID, 'F1:password'))
    btn_pass.send_keys(password, clear=True)
    btn_ingresar = Boton(driver, (By.ID, 'F1:btnIngresar'))
    btn_ingresar.click()

    return driver

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
    def enviar_al_buscador(driver, aplicativo):
        btn_buscador = Boton(driver, (By.ID, 'buscadorInput'))
        btn_buscador.send_keys(aplicativo, True)
        btn_buscador.send_keys(Keys.DOWN)
        btn_buscador.send_keys(Keys.ENTER)

    aplicativos = ["Mis Comprobantes", "Comprobantes en línea", "Sifere WEB - DDJJ", "Sifere WEB - Consultas", "Portal IVA", "CCMA - CUENTA"]
    if elegir_applicativo:
        nuevo_aplicativo = input("> ")
        enviar_al_buscador(driver, nuevo_aplicativo)
    else:
        enviar_al_buscador(driver, aplicativos[aplicativo])
    time.sleep(2)

    tabs = driver.window_handles
    elegir_tab(driver, len(tabs)-1 )