import time
from playwright.sync_api import sync_playwright

from auth import cargar_contexto, esta_logueado, login_y_guardar_sesion
from scraper import extraer_perfil, scrape_publicaciones
from exportar import save_to_json, save_to_csv


# ---------------------------------------------------------------------------
# Configuración interactiva
# ---------------------------------------------------------------------------

def pedir_configuracion() -> tuple[str, int, int | str]:
    """Pide por consola los parámetros del scraping y retorna (cuenta, n_posts, n_comentarios)."""
    print("=" * 50)
    print("   Instagram Scraper — Configuración")
    print("=" * 50)

    cuenta = input("\nCuenta de Instagram a scrapear: ").strip()
    if not cuenta:
        cuenta = "demian_lml_c"
        print(f"Sin cuenta ingresada. Usando '{cuenta}' por defecto.")

    pub_input = input("Número de publicaciones a abrir: ").strip()
    try:
        limite_publicaciones = int(pub_input)
        if limite_publicaciones <= 0:
            raise ValueError
    except ValueError:
        print("Valor inválido. Se usarán 3 publicaciones por defecto.")
        limite_publicaciones = 3

    com_input = input("Comentarios a extraer por publicación (número o 'todos'): ").strip()
    if com_input.lower() == 'todos':
        limite_comentarios = 'todos'
    else:
        try:
            limite_comentarios = int(com_input)
        except ValueError:
            print("Valor inválido. Se usarán 15 comentarios por defecto.")
            limite_comentarios = 15

    return cuenta, limite_publicaciones, limite_comentarios


# ---------------------------------------------------------------------------
# Flujo principal
# ---------------------------------------------------------------------------

def ejecutar(cuenta: str, limite_publicaciones: int, limite_comentarios):
    """Orquesta el scraping completo: login → perfil → posts → exportar."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = cargar_contexto(browser)
        page = context.new_page()

        page.goto("https://www.instagram.com/")
        time.sleep(3)

        if not esta_logueado(page):
            print("Sesión caducada o no válida.")
            if not login_y_guardar_sesion(page, context):
                browser.close()
                return
        else:
            print("¡Sesión válida! Entrando directamente...")

        print("Ya estás dentro de Instagram.")

        perfil = extraer_perfil(page, cuenta)
        publicaciones = scrape_publicaciones(page, limite_publicaciones, limite_comentarios)

        time.sleep(2)
        browser.close()

    return perfil, publicaciones


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cuenta, limite_publicaciones, limite_comentarios = pedir_configuracion()

    resultado = ejecutar(cuenta, limite_publicaciones, limite_comentarios)

    if resultado:
        perfil, publicaciones = resultado
        if perfil and publicaciones is not None:
            save_to_json(perfil, publicaciones)
            save_to_csv(perfil, publicaciones)
