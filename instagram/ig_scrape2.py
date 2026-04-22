import time
import os
import json
import csv
from playwright.sync_api import sync_playwright

COOKIE_PATH = "state_ig.json"

def login_y_guardar_sesion(page, context):
    print("Iniciando sesión manualmente...")
    page.goto("https://www.instagram.com")

    print("--- TIENES 5 MINUTOS PARA COMPLETAR EL LOGIN MANUALMENTE (2FA, CAPTCHA, ETC.) ---")
    
    try:
        # tiempo de espera (5 minutos)
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
        
        # 1. cargar sesión guardada si existe
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

        # --- SCRAPING ---
        print("Ya estás dentro de Instagram.")
        buscar = "demian_lml_c"
        # ir a perfil
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
                // Función para obtener el texto completo de la estadística
                const extraerEstadistica = () => {
                    let validStats = [];
                    // Extraer usando el span con clase .html-span
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
                
                // Extraer nombre
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
        
        # publicaciones
        try:
            print("\n--- Analizando Publicaciones Individuales (Abriéndolas) ---")
            # Encontrar todos los elementos de publicaciones
            enlaces_posts = page.locator("div._aagu").all()
            
            # Limitamos 
            cantidad = min(3, len(enlaces_posts))
            
            if cantidad == 0:
                print("No hay publicaciones visibles para abrir.")
                
            lista_publicaciones = []
                
            for i in range(cantidad):
                print(f"\nAbriendo publicación #{i + 1}...")
                enlace = enlaces_posts[i]
                
                # Hacer clic en la publicación
                enlace.click()
                
                # Esperar a que emerja el modal oscuro ("dialog") de Instagram
                page.wait_for_selector("div[role='dialog']", timeout=15000)
                time.sleep(2) # Darle unos segundos extra para que el servidor entregue los likes/comentarios
                
                # Extraer información del modal
                datos_post = page.evaluate("""
                    () => {
                        const dialog = document.querySelector("div[role='dialog']");
                        if (!dialog) return { likes: '0', comentarios: '0', fecha: 'Desconocida' };
                        
                        let likes = '0';
                        let comentarios = '0';
                        let fecha = 'Desconocida';
                        
                        // 1. Extraer Fecha
                        const timeEl = dialog.querySelector('time');
                        if (timeEl) {
                            fecha = timeEl.getAttribute('title') || timeEl.innerText;
                        }
                        
                        // 2. Extraer Likes (Suele estar en un enlace que dice "Les gusta a ..." o "Me gusta")
                        const likeEls = dialog.querySelectorAll('section span, a[href*="liked_by"] span');
                        for (let el of likeEls) {
                            if (el.innerText && parseInt(el.innerText.replace(/\\D/g, '')) > 0) {
                                likes = el.innerText;
                                break;
                            }
                        }
                        
                        // 3. Extraer Comentarios
                        // Contamos cuántos botones de "Responder" existen en la publicación.
                        let countRespuestas = 0;
                        const botones = dialog.querySelectorAll('div[role="button"], span, div');
                        botones.forEach(btn => {
                            if (btn.innerText && btn.innerText.trim() === 'Responder') {
                                countRespuestas++;
                            }
                        });
                        comentarios = countRespuestas.toString();
                        
                        return { likes: likes, comentarios: comentarios, fecha: fecha };
                    }
                """)
                
                print(f"-> Fecha de Publicación: {datos_post['fecha']}")
                print(f"-> Likes detectados: {datos_post['likes']}")
                print(f"-> Comentarios detectados: {datos_post['comentarios']}")
                
                lista_publicaciones.append(datos_post)
                
                # Apretar tecla ESCAPE para cerrar la foto y poder clickear la siguiente
                page.keyboard.press("Escape")
                time.sleep(1.5) # Pausa breve para que se cierre la animación
                
        except Exception as e:
            print("Ocurrió un error al abrir las publicaciones o están bloqueadas:", e)
            lista_publicaciones = []
            
        time.sleep(2)
        browser.close()
        return perfil, lista_publicaciones

# Función para guardar los datos combinados en formato JSON
def save_to_json(perfil, publicaciones, filename="datos_ig.json"):
    datos_completos = {
        "perfil": perfil,
        "publicaciones": publicaciones
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(datos_completos, f, ensure_ascii=False, indent=4)
    print(f"\nDatos combinados guardados exitosamente en {filename}")

# Función para guardar los datos combinados en formato CSV
def save_to_csv(perfil, publicaciones, filename="datos_ig.csv"):
    if not publicaciones:
        return
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        # Mezclamos los campos del perfil y del post para cada fila
        fieldnames = ["nombre_completo", "total_publicaciones", "total_seguidores", "total_seguidos", "fecha_post", "likes_post", "comentarios_post"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for post in publicaciones:
            fila = {
                "nombre_completo": perfil.get("nombre_completo", ""),
                "total_publicaciones": perfil.get("publicaciones", ""),
                "total_seguidores": perfil.get("seguidores", ""),
                "total_seguidos": perfil.get("seguidos", ""),
                "fecha_post": post.get("fecha", ""),
                "likes_post": post.get("likes", ""),
                "comentarios_post": post.get("comentarios", "")
            }
            writer.writerow(fila)
            
    print(f"Datos combinados guardados exitosamente en {filename}")

if __name__ == "__main__":
    perfil_extraido, publicaciones_extraidas = ejecutar_instagram()
    
    if perfil_extraido and publicaciones_extraidas is not None:
        save_to_json(perfil_extraido, publicaciones_extraidas)
        save_to_csv(perfil_extraido, publicaciones_extraidas)
