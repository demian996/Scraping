from playwright.sync_api import sync_playwright
import time

def login_scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        #Navegar a la pagina de login
        page.goto("https://quotes.toscrape.com/login")

        #Llenar el formulario de login
        time.sleep(1)
        page.fill("#username", "admin")
        time.sleep(2)
        page.fill("#password", "admin")

        #Dar click en el boton de login
        time.sleep(2)
        page.click("input[type='submit']")

        #Esperar a que cargue la pagina
        page.wait_for_url("https://quotes.toscrape.com/")

        #verificamos que estemos loguados
        if page.query_selector("a[href='/logout']"):
            print("Login exitoso")
        else:
            print("Login fallido")

        #extraemos las quotes
        quotes = page.evaluate("""
            () => {
                const citas = document.querySelectorAll(".quote");
                return Array.from(citas).map(cita => ({
                    texto: cita.querySelector(".text").innerText,
                    autor: cita.querySelector(".author").innerText,
                    tags: Array.from(cita.querySelectorAll(".tag")).map(tag => tag.innerText)
                }));
            }
        """)
        time.sleep(5)
        browser.close()
        return quotes

citas = login_scrape()
for cita in citas[:5]:
    print(f"Texto: {cita['texto']}")
    print(f"Autor: {cita['autor']}")
    print(f"Tags: {cita['tags']}")
    print()