# 📸 Instagram Scraper con Playwright

> Herramienta de web scraping para perfiles de Instagram usando **Python** y **Playwright sincronizado**.
>
> 📄 **Lee el [Informe Técnico detallado](informe.md)** para conocer a fondo la arquitectura, la evasión de bloqueos y los desafíos del proyecto.

---

## 📁 Estructura del proyecto

El código está dividido en módulos para mayor legibilidad y mantenimiento:

| Archivo | Responsabilidad |
|---|---|
| `main.py` | 🚀 Punto de entrada: pide configuración y orquesta todo |
| `auth.py` | 🔐 Login, carga y guardado de sesión |
| `scraper.py` | 🕷️ Extracción de perfil, posts y comentarios |
| `exportar.py` | 💾 Guardado de resultados en JSON y CSV |
| `ig_scrape2.py` | 📦 Versión monolítica original (referencia) |

---

## ⚙️ Funcionamiento y Flujo

### 1. 🔐 Gestión de la Sesión (`auth.py`)

Al iniciar, el script verifica si existe un archivo `state_ig.json` con una sesión guardada:

- ✅ **Si existe y es válida** → entra directamente a Instagram sin pedir login.
- ❌ **Si no existe o caducó** → abre el navegador y da **5 minutos** para completar el login manualmente (incluye 2FA, CAPTCHA, etc.). Una vez detectado el ingreso, guarda la sesión automáticamente para usos futuros.

---

### 2. 🧑‍💼 Configuración Interactiva (`main.py`)

Al ejecutar `main.py`, el script pregunta por consola los tres parámetros del scraping:

```
==================================================
   Instagram Scraper — Configuración
==================================================

Cuenta de Instagram a scrapear: natgeo
Número de publicaciones a abrir: 5
Comentarios a extraer por publicación (número o 'todos'): 20
```

- Si se deja vacío algún campo, se usarán los siguientes valores por defecto:
  - **Cuenta a scrapear:** `metroecuador`
  - **Número de publicaciones:** `3`
  - **Comentarios por publicación:** `15`
- El límite de comentarios acepta un número o la palabra `todos`.

---

### 3. 👤 Extracción de Datos de Perfil (`scraper.py`)

El bot navega al perfil y extrae desde el header:

- 📛 Nombre completo
- 📊 Cantidad total de publicaciones
- 👥 Cantidad de seguidores
- 👣 Cantidad de cuentas seguidas

---

### 4. 🖼️ Extracción de Publicaciones (`scraper.py`)

Por cada publicación (hasta el límite configurado), el bot hace clic para abrir el modal y extrae:

- 📅 Fecha exacta de publicación
- ❤️ Número de likes
- 💬 Número de comentarios
- 📝 **Descripción / caption del post** *(nuevo)*
- 🗨️ **Texto de los comentarios** con nombre de usuario (hasta el límite configurado)

Para cargar más comentarios, el bot hace clic automáticamente en el botón **"Cargar más comentarios"** hasta alcanzar el objetivo o agotar los disponibles.

Al terminar cada post, simula la tecla `Escape` para cerrar el modal y continuar con el siguiente.

> [!NOTE]
> **Evasión Anti-Bot:** Todo el proceso de navegación, carga y clics incorpora pausas aleatorias (entre 1.7 y 4.3 segundos) mediante la función `random_sleep()`. Esto simula el ritmo de lectura e interacción de un usuario humano real, previniendo bloqueos de sesión.

---

### 5. 💾 Exportación de Datos (`exportar.py`)

Al finalizar, los datos se exportan en dos formatos:

- **`datos_ig.json`** → estructura anidada con bloque `"perfil"` y lista de `"publicaciones"`, incluyendo descripción y comentarios detallados.
- **`datos_ig.csv`** → tabla plana donde cada post es una fila. Las columnas de comentarios se generan dinámicamente (`comentario_1`, `comentario_2`, ...). Incluye columna `descripcion_post`.

---

## 🛠️ Instalación y Configuración

Para replicar este proyecto en tu entorno local, sigue estos pasos:

1. **Crear y activar un entorno virtual:**
   ```bash
   # En Windows:
   python -m venv venv
   venv\Scripts\activate
   
   # En macOS/Linux:
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Instalar los navegadores de Playwright:**
   Playwright requiere descargar los binarios del navegador para funcionar.
   ```bash
   playwright install chromium
   ```

## ▶️ Ejecución

Una vez completada la configuración y con el entorno virtual activado, inicia el scraper con:

```bash
python main.py
```

> [!NOTE]
> Procura no interactuar con la ventana del navegador mientras el scraper está corriendo para no interrumpir el flujo del DOM que el script espera leer.

> [!TIP]
> Si la sesión caduca con frecuencia, elimina el archivo `state_ig.json` para forzar un nuevo login y regenerar las cookies.
