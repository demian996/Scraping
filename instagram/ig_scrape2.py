import time
import os
from playwright.sync_api import sync_playwright

COOKIE_PATH = "state_ig.json"

def login_y_guardar_sesion(page, context):
    print("Iniciando sesión manualmente...")
    page.goto("https://www.instagram.com")

    print("--- TIENES 5 MINUTOS PARA COMPLETAR EL LOGIN MANUALMENTE (2FA, CAPTCHA, ETC.) ---")
    
    try:
        # Aumentamos el tiempo de espera a 300 segundos (5 minutos)
        page.wait_for_selector("svg[aria-label='Inicio']", timeout=300000)
        
        # Guardar la sesión una vez que el usuario haya terminado de entrar
        context.storage_state(path=COOKIE_PATH)
        print("Sesión guardada correctamente.")
        return True
    except:
        print("Se acabó el tiempo de 5 minutos y no se detectó el inicio de sesión.")
        return False


def ejecutar_instagram():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        # 1. Intentar cargar sesión guardada si existe
        if os.path.exists(COOKIE_PATH):
            print("Cargando sesión existente...")
            context = browser.new_context(storage_state=COOKIE_PATH)
        else:
            print("No se encontró sesión previa.")
            context = browser.new_context()

        page = context.new_page()
        page.goto("https://www.instagram.com/")

        # 2. Verificar si realmente estamos logueados
        # Buscamos algo que solo aparezca al estar dentro (ej. el icono de Inicio)
        time.sleep(3) # Pausa breve para carga inicial
        esta_logueado = page.query_selector("svg[aria-label='Inicio']") is not None

        if not esta_logueado:
            print("Sesión caducada o no válida.")
            if not login_y_guardar_sesion(page, context):
                browser.close()
                return
        else:
            print("¡Sesión válida! Entrando directamente...")

        # --- AQUÍ EMPIEZA TU SCRAPING O LÓGICA PRINCIPAL ---
        print("Ya estás dentro de Instagram.")
        buscar = "demian_lml_c"
        # Ejemplo: ir a tu perfil
        page.goto(f"https://www.instagram.com/{buscar}")

        page.wait_for_selector("svg[aria-label='Inicio']", timeout=300000)

        # Esperar a que cargue la información del perfil (la cabecera)
        try:
            page.wait_for_selector("header", timeout=15000)
            print(f"Cargando perfil de {buscar}...")
            time.sleep(3) # Dar un poco de tiempo para que se pinte el DOM
        except:
            print("No se encontró el perfil o es privado.")

        # Extraer información del perfil
        perfil = page.evaluate("""
            () => {
                // Función auxiliar para obtener el texto completo de la estadística
                const extraerEstadistica = () => {
                    let validStats = [];
                    // Extraer usando el span con clase .html-span que tú encontraste (Intento 2)
                    const spans = document.querySelectorAll('header span.html-span');
                    
                    if (spans.length >= 3) {
                        spans.forEach(span => {
                            let texto = span.closest('span[dir="auto"]')?.innerText.replace(/\\n/g, ' ') || span.innerText;
                            texto = texto.trim();
                            if (texto.length > 0 && !validStats.includes(texto)) {
                                validStats.push(texto);
                            }
                        });
                        return validStats;
                    }
                    return [];
                };

                const stats = extraerEstadistica();
                
                // Extraer nombre (el selector que mostraste en las imágenes)
                const spanNombre = document.querySelector('header span.x1lliihq[dir="auto"]');
                const nombre_completo = spanNombre ? spanNombre.innerText : "No se encontró el nombre";

                return {
                    nombre_completo: nombre_completo,
                    publicaciones: stats.length > 0 ? stats[0] : "0 publicaciones",
                    seguidores: stats.length > 1 ? stats[1] : "0 seguidores",
                    seguidos: stats.length > 2 ? stats[2] : "0 seguidos"
                };
            }
        """)

        # Imprimir por consola lo extraído
        print(f"\n--- Información del perfil de {buscar} ---")
        print(f"Nombre: {perfil['nombre_completo']}")
        print(f"Estadísticas:")
        print(f"  - {perfil['publicaciones']}")
        print(f"  - {perfil['seguidores']}")
        print(f"  - {perfil['seguidos']}")
        
        # Mantener abierto un momento para ver el resultado
        time.sleep(10)
        browser.close()

if __name__ == "__main__":
    ejecutar_instagram()
