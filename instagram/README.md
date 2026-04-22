# Instagram Scraper Básico con Playwright

Este directorio contiene herramientas para realizar web scraping en perfiles de Instagram utilizando **Python** y **Playwright sincronizado**.

## Descripción del script `ig_scrape2.py`

`ig_scrape2.py` es el script principal desarrollado para extraer automáticamente estadísticas tanto de una cuenta específica de Instagram como de sus publicaciones recientes. Está armado para no requerir inicios de sesión repetitivos, manteniendo las buenas prácticas de manejo de sesiones para herramientas de automatización.

### Funcionamiento y Flujo

1. **Gestión de la Sesión:** 
   El script verifica si existe un archivo de cookies llamado `state_ig.json`. Si lo encuentra y es válido, entra a Instagram directamente saltándose el inicio de sesión. Si el archivo no existe o caducó, abre Instagram y proporciona una ventana de **5 minutos** para que el usuario coloque sus credenciales a mano y venza cualquier captcha o 2FA (verificación de doble factor). Una vez detectado el éxito, guarda la sesión automáticamente para uso futuro.

2. **Extracción de Datos de Perfil:**
   El bot se dirige al perfil deseado y, sin necesidad de explorar fotografías puntuales, extrae directamente de la cabecera del perfil:
   - Nombre.
   - Cantidad total de publicaciones.
   - Cantidad total de seguidores.
   - Cantidad total de cuentas seguidas.

3. **Interacción y Extracción de Publicaciones:**
   Una vez lograda la información de la cabecera, el bot busca en la cuadrícula de imágenes usando clases nativas de la web de Instagram (como `_aagu`) y da clic de manera iterativa a las primeras configuradas (las 3 más recientes por defecto) para expandirlas. 
   Por cada foto/post extrae:
   - La fecha exacta (detectada en la etiqueta HTML `<time>`).
   - El número de Me gustas (Likes).
   - El número real de comentarios dejados por usuarios (verificados rastreando los botones de "Responder" para evadir conteos irreales).
   Finalmente simula oprimir la tecla `Escape` (esc) para cerrar el modal de la foto e ir a la siguiente de manera natural.

4. **Exportación de Datos (Archivos generados):**
   Al finalizar toda la iteración, el script junta la información en formato **"Uno a muchos"** y exporta la salida en la misma raíz:
   - **`datos_ig.json`**: Un archivo JSON estructurado donde podrás ver el bloque `"perfil"` global y una matriz listando detalles de sus `"publicaciones"`.
   - **`datos_ig.csv`**: Un documento Excel tabular plano. Cada post analizado es una nueva fila que incluye como prefijo el nombre y número de seguidores del perfil correspondiente.

## Ejecución

Simplemente desde terminal (con el entorno virtual o Playwright instalado):

```bash
python ig_scrape2.py
```
> [!NOTE]
> Procura no abrir o interactuar bruscamente con la ventana que Playwright eleva si está en modo "headless=False" para no interrumpir el flujo del DOM que el script espera leer.
