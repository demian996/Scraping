from playwright.sync_api import sync_playwright
import time
import json
import csv

# Función principal para realizar el scraping de los libros
def scrape_books():
    # Iniciamos Playwright para controlar el navegador
    with sync_playwright() as p:
        # Lanzamos el navegador (headless=True significa que no se verá la ventana)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        allBooks = []      # Lista para almacenar todos los libros de todas las páginas
        pageNumber = 1     # Contador de páginas
        
        # Bucle infinito para recorrer las páginas hasta que no haya más resultados
        while True:
            # Navegar a la URL de la página actual
            page.goto(f"https://books.toscrape.com/catalogue/page-{pageNumber}.html")
            print(f"Scrapeando página {pageNumber}...")
            
            # Verificamos si existen productos en la página; si no, terminamos el bucle
            if page.query_selector(".product_pod") is None:
                print("No se encontraron más libros. Finalizando búsqueda.")
                break
            
            # Ejecutamos código JavaScript en la página para extraer la información
            libros = page.evaluate("""
                () => {
                    // Seleccionamos todos los contenedores de libros
                    const productos = document.querySelectorAll(".product_pod");
                    // Convertimos la lista de nodos a un array y extraemos los datos de cada libro
                    return Array.from(productos).map(libro => ({
                        titulo: libro.querySelector("h3 a").getAttribute("title"),
                        precio: libro.querySelector(".price_color").innerText,
                        stock: libro.querySelector(".instock.availability") ? true : false,
                        rating: libro.querySelector(".star-rating").classList[1]
                    }));
                }
            """)
            
            # Agregamos los libros encontrados a nuestra lista global
            allBooks.extend(libros)
            pageNumber += 1     # Pasamos a la siguiente página
            time.sleep(0.5)     # Pausa breve para no saturar el servidor
            
        browser.close()         # Cerramos el navegador al terminar
        return allBooks

# Ejecutamos la función y obtenemos la lista completa
libros = scrape_books()
print(f"\nTotal de libros extraídos: {len(libros)}")

# Función para guardar los datos en formato JSON
def save_to_json(libros, filename = "libros.json"):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(libros, f, ensure_ascii=False, indent=4)
    print(f"Datos guardados exitosamente en {filename}")

# Función para guardar los datos en formato CSV
def save_to_csv(libros, filename = "libros.csv"):
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        # Definimos los encabezados de las columnas
        writer = csv.DictWriter(f, fieldnames= ["titulo", "precio", "stock", "rating"])
        writer.writeheader()
        writer.writerows(libros)
    print(f"Datos guardados exitosamente en {filename}")

# Guardamos los resultados en ambos formatos
save_to_json(libros)
save_to_csv(libros)