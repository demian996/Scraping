import os
from playwright.sync_api import Page, BrowserContext

COOKIE_PATH = "state_ig.json"


def cargar_contexto(browser):
    """Crea un contexto del navegador, cargando la sesión guardada si existe."""
    if os.path.exists(COOKIE_PATH):
        print("Cargando sesión existente...")
        return browser.new_context(storage_state=COOKIE_PATH)
    else:
        print("No se encontró sesión previa.")
        return browser.new_context()


def esta_logueado(page: Page) -> bool:
    """Verifica si el usuario está logueado buscando el ícono de Inicio."""
    return page.query_selector("svg[aria-label='Inicio']") is not None


def login_y_guardar_sesion(page: Page, context: BrowserContext) -> bool:
    """
    Abre Instagram y espera hasta 5 minutos para que el usuario
    complete el login manualmente (2FA, CAPTCHA, etc.).
    Guarda la sesión en COOKIE_PATH si el login fue exitoso.
    """
    print("Iniciando sesión manualmente...")
    page.goto("https://www.instagram.com")
    print("--- TIENES 5 MINUTOS PARA COMPLETAR EL LOGIN MANUALMENTE (2FA, CAPTCHA, ETC.) ---")

    try:
        page.wait_for_selector("svg[aria-label='Inicio']", timeout=300000)
        context.storage_state(path=COOKIE_PATH)
        print("Sesión guardada correctamente.")
        return True
    except Exception:
        print("Se acabó el tiempo de 5 minutos y no se detectó el inicio de sesión.")
        return False
