import time
import random
from playwright.sync_api import Page

def random_sleep(min_val=1.7, max_val=4.3):
    """Pausa la ejecución por un tiempo aleatorio entre min_val y max_val segundos."""
    time.sleep(random.uniform(min_val, max_val))


# ---------------------------------------------------------------------------
# Extracción del perfil
# ---------------------------------------------------------------------------

def extraer_perfil(page: Page, cuenta: str) -> dict:
    """
    Navega al perfil de `cuenta` y extrae nombre, publicaciones,
    seguidores y seguidos desde el header de Instagram.
    """
    page.goto(f"https://www.instagram.com/{cuenta}")
    page.wait_for_selector("svg[aria-label='Inicio']", timeout=300000)

    try:
        page.wait_for_selector("header", timeout=15000)
        print(f"Cargando perfil de {cuenta}...")
        random_sleep()
    except Exception:
        print("No se encontró el perfil o es privado.")

    perfil = page.evaluate("""
        () => {
            const extraerEstadistica = () => {
                let validStats = [];
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
            const spanNombre = document.querySelector('header span.x1lliihq[dir="auto"]');
            const nombre_completo = spanNombre ? spanNombre.innerText : "No se encontró el nombre";

            return {
                nombre_completo: nombre_completo,
                publicaciones: stats.length > 0 ? stats[0] : "0 publicaciones",
                seguidores:    stats.length > 1 ? stats[1] : "0 seguidores",
                seguidos:      stats.length > 2 ? stats[2] : "0 seguidos"
            };
        }
    """)

    print(f"\n--- Información del perfil de {cuenta} ---")
    print(f"Nombre: {perfil['nombre_completo']}")
    print(f"Estadísticas:")
    print(f"  - {perfil['publicaciones']}")
    print(f"  - {perfil['seguidores']}")
    print(f"  - {perfil['seguidos']}")

    return perfil


# ---------------------------------------------------------------------------
# Carga de comentarios
# ---------------------------------------------------------------------------

def _contar_respuestas(page: Page) -> int:
    """Cuenta cuántos botones 'Responder' hay visibles en el modal actual."""
    return page.evaluate("""() => {
        const dialog = document.querySelector("div[role='dialog']");
        if (!dialog) return 0;
        let count = 0;
        const botones = dialog.querySelectorAll('div[role="button"], span, div');
        botones.forEach(btn => {
            if (btn.innerText && btn.innerText.trim() === 'Responder') count++;
        });
        return count;
    }""")


def cargar_mas_comentarios(page: Page, limite_comentarios):
    """
    Hace clic en 'Cargar más comentarios' repetidamente hasta alcanzar
    el límite pedido o hasta que no haya más botón disponible.
    """
    max_comentarios = 999999 if limite_comentarios == 'todos' else limite_comentarios

    while True:
        count = _contar_respuestas(page)
        if limite_comentarios != 'todos' and count >= max_comentarios:
            break

        btn_mas = page.locator("svg[aria-label='Cargar más comentarios']")
        if btn_mas.count() > 0 and btn_mas.first.is_visible():
            try:
                btn_mas.first.click(timeout=3000, force=True)
                random_sleep()
            except Exception:
                break
        else:
            break


# ---------------------------------------------------------------------------
# Extracción de datos de un post (modal abierto)
# ---------------------------------------------------------------------------

_JS_EXTRAER_POST = """
    (maxCom) => {
        const dialog = document.querySelector("div[role='dialog']");
        if (!dialog) return { likes: '0', comentarios: '0', fecha: 'Desconocida', descripcion: '', detalle_comentarios: [] };

        let likes = '0';
        let comentarios = '0';
        let fecha = 'Desconocida';
        let descripcion = '';

        // 1. Fecha
        const timeEl = dialog.querySelector('time');
        if (timeEl) fecha = timeEl.getAttribute('title') || timeEl.innerText;

        // 2. Likes
        const likeEls = dialog.querySelectorAll('section span, a[href*="liked_by"] span');
        for (let el of likeEls) {
            if (el.innerText && parseInt(el.innerText.replace(/\\D/g, '')) > 0) {
                likes = el.innerText;
                break;
            }
        }

        // 3. Cantidad de comentarios (conteo de botones "Responder")
        let countRespuestas = 0;
        const botones = dialog.querySelectorAll('div[role="button"], span, div');
        botones.forEach(btn => {
            if (btn.innerText && btn.innerText.trim() === 'Responder') countRespuestas++;
        });
        comentarios = countRespuestas.toString();

        // 4. Descripción del post (caption del autor en <h1>)
        const h1Caption = dialog.querySelector('h1');
        if (h1Caption) {
            const spanDesc = h1Caption.closest('span[dir="auto"]') || h1Caption.parentElement?.querySelector("span[dir='auto']");
            descripcion = spanDesc ? spanDesc.innerText.trim() : h1Caption.innerText.trim();
        }
        if (!descripcion) {
            const h2Caption = dialog.querySelector('h2');
            if (h2Caption) {
                const spanDesc = h2Caption.parentElement?.querySelector("span[dir='auto']");
                descripcion = spanDesc ? spanDesc.innerText.trim() : '';
            }
        }

        // 5. Texto de los comentarios (bloques con <h3> = nombre de usuario)
        let detalle_comentarios = [];
        const authores = dialog.querySelectorAll("h3");
        for (let autorH3 of authores) {
            const contenedor = autorH3.parentElement;
            if (!contenedor) continue;

            const textoDiv = contenedor.querySelector("span[dir='auto']");
            const textoBloque = contenedor.parentElement ? contenedor.parentElement.innerText : contenedor.innerText;

            if (textoDiv && textoBloque.includes('Responder')) {
                let combined = autorH3.innerText.trim() + ": " + textoDiv.innerText.trim();
                if (!detalle_comentarios.includes(combined)) {
                    detalle_comentarios.push(combined);
                }
                if (detalle_comentarios.length >= maxCom) break;
            }
        }

        return { likes, comentarios, fecha, descripcion, detalle_comentarios };
    }
"""


def extraer_datos_post(page: Page, max_comentarios: int) -> dict:
    """Evalúa el JS de extracción sobre el modal de post actualmente abierto."""
    return page.evaluate(_JS_EXTRAER_POST, max_comentarios)


# ---------------------------------------------------------------------------
# Scraping de publicaciones
# ---------------------------------------------------------------------------

def scrape_publicaciones(page: Page, limite_publicaciones: int, limite_comentarios) -> list:
    """
    Abre cada publicación del perfil (hasta `limite_publicaciones`),
    carga comentarios y extrae todos los datos del modal.
    Retorna una lista de dicts con la info de cada post.
    """
    max_comentarios = 999999 if limite_comentarios == 'todos' else limite_comentarios

    print("\n--- Analizando Publicaciones Individuales (Abriéndolas) ---")
    enlaces_posts = page.locator("div._aagu").all()
    cantidad = min(limite_publicaciones, len(enlaces_posts))

    if cantidad == 0:
        print("No hay publicaciones visibles para abrir.")
        return []

    lista_publicaciones = []

    for i in range(cantidad):
        print(f"\nAbriendo publicación #{i + 1}...")
        enlaces_posts[i].click()

        page.wait_for_selector("div[role='dialog']", timeout=15000)
        random_sleep()

        print(f"Cargando comentarios (objetivo: {limite_comentarios})...")
        cargar_mas_comentarios(page, limite_comentarios)

        datos_post = extraer_datos_post(page, max_comentarios)

        # Imprimir resumen en consola
        print(f"-> Fecha de Publicación: {datos_post['fecha']}")
        print(f"-> Likes detectados:     {datos_post['likes']}")
        print(f"-> Comentarios:          {datos_post['comentarios']}")
        desc = datos_post.get('descripcion', '')
        if desc:
            print(f"-> Descripción: {desc[:200]}{'...' if len(desc) > 200 else ''}")
        else:
            print("-> Descripción: (sin descripción)")
        if datos_post['detalle_comentarios']:
            print("-> Top comentarios extraídos:")
            for j, c_text in enumerate(datos_post['detalle_comentarios']):
                print(f"     {j+1}. {c_text}")

        lista_publicaciones.append(datos_post)

        page.keyboard.press("Escape")
        random_sleep()

    return lista_publicaciones
