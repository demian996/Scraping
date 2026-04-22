import json
import csv


def save_to_json(perfil: dict, publicaciones: list, filename: str = "datos_ig.json"):
    """Guarda el perfil y las publicaciones en un archivo JSON."""
    datos_completos = {
        "perfil": perfil,
        "publicaciones": publicaciones
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(datos_completos, f, ensure_ascii=False, indent=4)
    print(f"\nDatos guardados en {filename}")


def save_to_csv(perfil: dict, publicaciones: list, filename: str = "datos_ig.csv"):
    """
    Guarda el perfil y las publicaciones en un archivo CSV.
    Genera columnas dinámicas para cada comentario extraído.
    """
    if not publicaciones:
        print("No hay publicaciones para guardar en CSV.")
        return

    # Calcular el máximo de comentarios en cualquier post para crear las columnas
    max_comentarios_extraidos = max(
        len(post.get("detalle_comentarios", []))
        for post in publicaciones
    )

    fieldnames = [
        "nombre_completo", "total_publicaciones", "total_seguidores", "total_seguidos",
        "fecha_post", "likes_post", "comentarios_post", "descripcion_post"
    ]
    for i in range(max_comentarios_extraidos):
        fieldnames.append(f"comentario_{i+1}")

    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for post in publicaciones:
            detalles = post.get("detalle_comentarios", [])
            fila = {
                "nombre_completo":      perfil.get("nombre_completo", ""),
                "total_publicaciones":  perfil.get("publicaciones", ""),
                "total_seguidores":     perfil.get("seguidores", ""),
                "total_seguidos":       perfil.get("seguidos", ""),
                "fecha_post":           post.get("fecha", ""),
                "likes_post":           post.get("likes", ""),
                "comentarios_post":     post.get("comentarios", ""),
                "descripcion_post":     post.get("descripcion", ""),
            }
            for i in range(max_comentarios_extraidos):
                fila[f"comentario_{i+1}"] = detalles[i] if i < len(detalles) else ""

            writer.writerow(fila)

    print(f"Datos guardados en {filename}")
