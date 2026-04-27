# 📄 Informe  — Instagram Scraper con Playwright

---

## 1. Descripción General

Este proyecto consiste en un scraper de perfiles públicos de Instagram desarrollado en **Python**, utilizando **Playwright** como controlador de navegador. La herramienta extrae información de perfil (nombre, seguidores, seguidos, publicaciones) y datos de cada post (fecha, likes, comentarios, descripción y texto de comentarios), exportando los resultados en formato JSON y CSV.

---

## 2. Por qué Playwright

Playwright fue elegido por una razón técnica concreta: **Instagram renderiza su contenido completamente mediante JavaScript**, lo que hace imposible obtener datos con una simple solicitud HTTP. El HTML que devuelve el servidor en la respuesta inicial está vacío de contenido real; todo el DOM se construye en el navegador del cliente.

Dicho esto, el rol de Playwright en este proyecto es únicamente **abrir y controlar el navegador**, actuando como un puente hacia el DOM renderizado. La lógica de extracción de datos no usa ningún método de Playwright para parsear HTML — toda la extracción se realiza mediante **JavaScript puro** ejecutado directamente en el navegador con `page.evaluate()`, usando selectores nativos del DOM (`querySelectorAll`, `querySelector`, `innerText`, atributos HTML, etc.).

Playwright es simplemente el motor que permite acceder al DOM ya renderizado.

---

## 3. Funcionamiento de las Solicitudes Web

### 3.1 Por qué no se usan solicitudes HTTP directas

Instagram no expone una API pública para consumir datos de perfiles o posts. Todas las rutas internas de su API (como `graphql/query` o los endpoints de la API privada de Instagram) requieren autenticación mediante tokens de sesión firmados, cabeceras específicas (`x-ig-app-id`, `x-csrftoken`, etc.) y en muchos casos están protegidas por sistemas anti-bot que detectan patrones de solicitudes automatizadas.

Por eso, en lugar de intentar replicar esas solicitudes manualmente, la estrategia adoptada fue **operar como un usuario real a través del navegador**, dejando que Instagram cargue su interfaz normalmente y extrayendo los datos desde el DOM visible.

### 3.2 Cómo se accede a la información

El flujo de solicitudes que ocurre es el siguiente:

1. **Carga inicial de Instagram** (`https://www.instagram.com/`) — el navegador realiza la solicitud principal y carga la aplicación React de Instagram.
2. **Navegación al perfil** (`https://www.instagram.com/{cuenta}`) — Instagram realiza internamente solicitudes a su API privada para cargar los datos del perfil y la grilla de posts. Estas solicitudes las gestiona la propia aplicación; el scraper no las intercepta.
3. **Apertura de cada post (modal)** — al hacer clic en una publicación, Instagram carga el contenido del modal mediante más solicitudes internas. El scraper espera a que el modal esté completamente renderizado antes de extraer datos.
4. **Carga de comentarios adicionales** — al hacer clic en el botón "Cargar más comentarios", Instagram solicita más comentarios a su backend. El scraper detecta este botón y lo activa programáticamente.

En todos los casos, **el scraper no construye ni envía solicitudes HTTP manualmente**. Se apoya en el comportamiento natural del navegador y de la aplicación de Instagram.

### 3.3 Extracción mediante selectores del DOM

Una vez que el contenido está renderizado, la extracción se realiza identificando las clases CSS y etiquetas HTML donde Instagram almacena cada dato. Algunos ejemplos concretos del código:

| Dato | Selector utilizado |
|---|---|
| Estadísticas del perfil (posts, seguidores, seguidos) | `header span.html-span` |
| Nombre completo | `header span.x1lliihq[dir="auto"]` |
| Fecha del post | `time` (atributo `title`) |
| Likes | `section span`, `a[href*="liked_by"] span` |
| Descripción del post (caption) | `h1` dentro del modal `div[role='dialog']` |
| Nombre de usuario en comentarios | `h3` dentro del modal |
| Texto de cada comentario | `span[dir='auto']` junto al `h3` del autor |
| Botón de más comentarios | `svg[aria-label='Cargar más comentarios']` |
| Verificación de login | `svg[aria-label='Inicio']` |

Esta estrategia de identificar clases y atributos específicos del DOM es equivalente, en concepto, a lo que haría BeautifulSoup sobre HTML estático — con la diferencia de que aquí se ejecuta dentro del navegador sobre el DOM dinámico ya construido.

---

## 4. Estrategia para Minimizar Bloqueos

Instagram aplica múltiples mecanismos de detección de bots. A continuación se describen las estrategias adoptadas para evitar bloqueos:

### 4.1 Sesión de usuario real con cookies persistentes

El módulo `auth.py` implementa un sistema de sesión persistente. En lugar de hacer login automático (lo que activaría mecanismos de detección), el script **espera hasta 5 minutos para que el usuario complete el login manualmente**, incluyendo 2FA y CAPTCHAs. Una vez que el login es detectado (presencia del ícono de Inicio), la sesión se guarda en `state_ig.json` usando `context.storage_state()`.

En usos posteriores, esta sesión se reutiliza directamente, evitando repetir el login y manteniendo las cookies de sesión legítimas.

```python
# auth.py — carga de sesión guardada
if os.path.exists(COOKIE_PATH):
    return browser.new_context(storage_state=COOKIE_PATH)
```

Esto hace que el scraper opere con las mismas credenciales y cookies que un usuario humano real, lo que reduce significativamente la probabilidad de ser detectado como bot.

### 4.2 Pausas deliberadas y aleatorias entre acciones

A lo largo del código se introducen pausas variables utilizando una función personalizada `random_sleep()` en puntos clave. Esta función genera tiempos de espera aleatorios (por defecto entre 1.7 y 4.3 segundos) para:

- Esperar que el DOM se pinte completamente después de cargar el perfil o la página principal.
- Dejar que el servidor entregue likes y comentarios tras abrir cada post.
- Esperar la respuesta después de cada clic en "Cargar más comentarios".
- Permitir que se completen las animaciones al cerrar cada modal.

Anteriormente se usaban pausas fijas con `time.sleep()`, pero la implementación de `random_sleep()` imita mucho mejor el comportamiento impredecible de un usuario humano, dificultando considerablemente que los sistemas anti-bot detecten un patrón de navegación automatizado.

### 4.3 Navegador con interfaz gráfica (headless=False)

El navegador se lanza en modo visible (`headless=False`), no en modo headless. Instagram y muchas plataformas detectan navegadores headless mediante heurísticas sobre el `user-agent`, propiedades del objeto `navigator` en JavaScript, y comportamiento de renderizado. Al usar un navegador con interfaz gráfica real, el perfil del navegador es idéntico al de un usuario común.

### 4.4 Interacción mediante clics reales y teclado

El scraper interactúa con la página mediante clics en elementos reales (`enlace.click()`, `btn_mas.first.click()`) y pulsaciones de teclado reales (`page.keyboard.press("Escape")`), en lugar de manipular el DOM directamente o llamar funciones internas de la aplicación. Esto hace que el patrón de interacción sea prácticamente indistinguible del de un usuario humano.

### 4.5 Sin paralelismo ni velocidad agresiva

El scraping se realiza de forma completamente secuencial, post por post, sin hilos ni solicitudes paralelas. Esto evita picos de actividad que podrían ser detectados como comportamiento automatizado.

---

## 5. Documentación del Proceso y Desafíos

### 5.1 Estructura modular del proyecto

El código está organizado en cuatro módulos con responsabilidades separadas:

- **`auth.py`** — gestión de sesión (carga, verificación y guardado de cookies).
- **`scraper.py`** — navegación al perfil, extracción de datos de perfil y publicaciones.
- **`exportar.py`** — serialización de resultados a JSON y CSV.
- **`main.py`** — punto de entrada, configuración interactiva y orquestación del flujo.

Adicionalmente existe `ig_scrape2.py`, que es la versión monolítica original del proyecto, conservada como referencia histórica del desarrollo.

### 5.2 Desafío: DOM dinámico y clases CSS inestables

Instagram genera su interfaz con React y aplica clases CSS con nombres generados automáticamente (como `x1lliihq`, `_aagu`) que pueden cambiar entre versiones del frontend. Esto significa que los selectores pueden dejar de funcionar si Instagram actualiza su interfaz.

La estrategia adoptada fue combinar selectores semánticos estables (etiquetas HTML como `h1`, `h3`, `time`, atributos como `dir="auto"`, `aria-label`, y roles como `role='dialog'`) con los pocos nombres de clase que se mantuvieron estables durante el desarrollo. Los selectores semánticos son mucho más resilientes a cambios de frontend.

### 5.3 Desafío: Extracción de estadísticas del perfil

Las estadísticas del perfil (número de publicaciones, seguidores y seguidos) no están en elementos con identificadores únicos. Se encuentran en `span.html-span` dentro del `header`, y su orden en el DOM es lo que determina cuál es cuál. La solución fue extraer todos los spans relevantes en orden y asignarlos posicionalmente.

### 5.4 Desafío: Conteo de comentarios sin acceso a la API

Instagram no expone directamente el número de comentarios de un post en el modal de forma consistente. La solución fue **contar los botones "Responder"** visibles en el DOM, ya que cada comentario de primer nivel tiene exactamente un botón "Responder" asociado. Esto permite estimar el número de comentarios cargados de forma fiable.

### 5.5 Desafío: Carga paginada de comentarios

Los comentarios no se cargan todos de una vez — Instagram los pagina y solo muestra un botón para cargar más. El módulo `cargar_mas_comentarios()` implementa un bucle que detecta la presencia del botón `svg[aria-label='Cargar más comentarios']`, hace clic, espera la respuesta y repite el proceso hasta alcanzar el límite configurado o hasta que no haya más comentarios disponibles.

### 5.6 Desafío: Prevención de duplicados en comentarios

Al recorrer los nodos `h3` del DOM para extraer comentarios, en ciertos casos el DOM podía contener referencias repetidas al mismo comentario. Se implementó una verificación de duplicados antes de agregar cada comentario a la lista, usando una comparación directa de la cadena `"usuario: texto"`.

### 5.7 Desafío: Sesión y autenticación

Instagram tiene mecanismos agresivos de detección de login automatizado. La solución fue no automatizar el login en absoluto — el usuario completa el proceso manualmente (incluyendo 2FA y CAPTCHA si aplica), y el scraper simplemente detecta cuándo el login fue exitoso y guarda el estado de sesión para reutilizarlo.

---

## 6. Conclusión

El scraper desarrollado demuestra que es posible extraer datos de Instagram sin utilizar parsers automáticos ni llamar directamente a APIs privadas, apoyándose en la manipulación directa del DOM renderizado mediante JavaScript nativo y en el comportamiento natural de un navegador real con sesión legítima. Las principales limitaciones del enfoque son la dependencia de la estabilidad del DOM de Instagram y la necesidad de un login manual inicial, que son contrapartidas aceptables frente a las ventajas en términos de evasión de detección y simplicidad de implementación.