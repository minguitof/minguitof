from PIL import Image
import datetime
import requests # Necesario para hacer peticiones HTTP a la API de GitHub
import os       # Necesario para acceder a variables de entorno (como tu token de GitHub)
import glob

# --- Funciones de Utilidad ---

def calcular_edad_exacta(fecha_nacimiento_str):
    """
    Calcula la edad exacta en años, meses y días desde una fecha de nacimiento.
    Formato de fecha_nacimiento_str: 'YYYY-MM-DD'
    """
    fecha_nacimiento = datetime.datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
    today = datetime.date.today()
    
    años = today.year - fecha_nacimiento.year
    if (today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        años -= 1
    
    fecha_aniversario = fecha_nacimiento.replace(year=fecha_nacimiento.year + años)
    
    if today >= fecha_aniversario:
        meses = today.month - fecha_aniversario.month
        dias = today.day - fecha_aniversario.day
        
        if dias < 0:
            last_day_of_prev_month = (today.replace(day=1) - datetime.timedelta(days=1)).day
            dias = last_day_of_prev_month + dias
            meses -= 1
            
            if meses < 0:
                meses += 12
    else:
        fecha_aniversario_pasado = fecha_nacimiento.replace(year=fecha_nacimiento.year + años)
        
        meses = today.month - fecha_aniversario_pasado.month
        dias = today.day - fecha_aniversario_pasado.day

        if dias < 0:
            last_day_of_prev_month = (today.replace(day=1) - datetime.timedelta(days=1)).day
            dias = last_day_of_prev_month + dias
            meses -= 1
        
        if meses < 0:
            meses += 12

    return f"{años} años, {meses} meses, {dias} días"

def convertir_imagen_a_ascii(ruta_imagen, ancho_salida=100):
    """
    Converts a given image to ASCII art.
    """
    try:
        imagen = Image.open(ruta_imagen)
    except FileNotFoundError:
        print(f"Error: La imagen en la ruta '{ruta_imagen}' no fue encontrada.")
        return None
    except Exception as e:
        print(f"Error al abrir la imagen: {e}")
        return None

    imagen = imagen.convert("L") #Convierte la imagen a escala de grises. | L = Luminosidad

    ancho_original, alto_original = imagen.size
    relacion_aspecto = alto_original / ancho_original
    alto_salida = int(ancho_salida * relacion_aspecto * 0.55) 
    imagen = imagen.resize((ancho_salida, alto_salida))

    ascii_chars = "#W$@%*+=-. " # Puedes cambiar valores para mas detalles ASCII Art, izquierda a derecha | claro a oscuro

    pixels = imagen.getdata()
    ascii_art = ""
    for pixel_value in pixels:
        index = int(pixel_value / 255 * (len(ascii_chars) - 1))
        ascii_art += ascii_chars[index]

    ascii_lines = [ascii_art[i:i + ancho_salida] for i in range(0, len(ascii_art), ancho_salida)]
    
    return "\n".join(ascii_lines)

# --- FUNCIONES PARA OBTENER DATOS DE GITHUB ---
def obtener_datos_github(username, github_token=None):
    """
    Obtiene estadísticas de GitHub para un usuario dado.
    Requiere un token de GitHub para evitar límites de tasa para peticiones grandes.
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    stats = {
        "total_repos": 0,
        "total_stars": 0,
        "total_forks": 0,
        "total_followers": 0,
        "total_commits": 0, 
    }

    try:
        # 1. Obtener datos del usuario (seguidores)
        user_url = f"https://api.github.com/users/{username}"
        user_response = requests.get(user_url, headers=headers)
        user_response.raise_for_status() 
        user_data = user_response.json()
        stats["total_followers"] = user_data.get("followers", 0)
        
        # 2. Obtener repositorios (para sumar estrellas y forks)
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner" 
        page = 1
        while True:
            current_repos_url = f"{repos_url}&page={page}"
            repos_response = requests.get(current_repos_url, headers=headers)
            repos_response.raise_for_status()
            repos_data = repos_response.json()

            if not repos_data: 
                break

            for repo in repos_data:
                if not repo.get("private", False): 
                    stats["total_repos"] += 1 
                    stats["total_stars"] += repo.get("stargazers_count", 0)
                    stats["total_forks"] += repo.get("forks_count", 0)
            page += 1
        
        # 3. Commits: Obtener commits a través de eventos públicos (aproximación)
        events_url = f"https://api.github.com/users/{username}/events/public?per_page=100" 
        events_response = requests.get(events_url, headers=headers)
        events_response.raise_for_status()
        events_data = events_response.json()

        if isinstance(events_data, list):
            for event in events_data:
                if event.get("type") == "PushEvent":
                    for commit in event.get("payload", {}).get("commits", []):
                        if commit.get("author", {}).get("name", "").lower() == username.lower(): # Asegurarse de que el autor sea el usuario
                            stats["total_commits"] += 1
        
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de GitHub: {e}")
        print("Asegúrate de que el nombre de usuario sea correcto y el token de GitHub válido si lo usas.")
    except Exception as e:
        print(f"Ocurrió un error inesperado al procesar datos de GitHub: {e}")

    return stats

# --- FUNCION PRINCIPAL DE GENERACION SVG ---

def generar_svg_con_info(ascii_art_string, info_sections, output_filename="readme_profile.svg", 
                         bg_color="#161b22", text_color="#c9d1d9", 
                         key_color="#ffa657", value_color="#a5d6ff", font_size=16,
                         border_color="#444c56", border_width=2, border_radius=10):
    """
    Generates an SVG file with ASCII art on the left and profile data on the right.
    """
    ascii_lines = ascii_art_string.split('\n')
    
    char_width_px = 9.6 
    line_height_factor = 1.2 

    # --- SVG Dimensions ---
    ascii_max_width_chars = max(len(line) for line in ascii_lines)
    ascii_panel_width = int(ascii_max_width_chars * char_width_px) + 0
    
    info_panel_base_width = 525 
    
    info_total_lines = 0
    if info_sections and info_sections[0].get("title") == "username_header":
        info_total_lines += 2 
        
    for section in info_sections:
        if section.get("title") and section["title"] != "username_header":
            info_total_lines += 1 
        info_total_lines += len(section.get('items', []))
        if section.get('extra_line_after', False): 
            info_total_lines += 1 

    info_height = info_total_lines * font_size * line_height_factor
    
    min_required_svg_height = int(max(len(ascii_lines) * font_size * line_height_factor, info_height)) + 80 

    svg_width = ascii_panel_width + info_panel_base_width + 30 

    svg_height = max(int(len(ascii_lines) * font_size * line_height_factor) + 0, info_height + 80)


    icon_map = {
        "Nombre": "👤", 
        "Edad": "🎂", "Ubicación": "📍", "Intereses": "💡",
        "Stack": "💻", 
        "Lenguajes de Programación": "🧠", "Tecnologías Web": "🌐", 
        "Bases de Datos": "💾", "Herramientas DevOps": "🛠️",
        "Hobbies": "🎮", 
        "Email": "📧", "LinkedIn": "🔗", 
        "Total Repositorios": "📦", "Estrellas Totales": "⭐", 
        "Forks Totales": "🍴", "Total Commits": "⚡", 
        "Seguidores": "👥", "Líneas de Código (LOC)": "📈",
    }

    svg_content = f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="{svg_width}px" height="{svg_height}px" font-size="{font_size}px">
<style>
@font-face {{
  src: local('Consolas'), local('Consolas Bold');
  font-family: 'ConsolasFallback';
  font-display: swap;
  -webkit-size-adjust: 109%;
  size-adjust: 109%;
}}
.key {{fill: {key_color};}}
.value {{fill: {value_color};}}
.header-line {{fill: {text_color};}}
.section-title {{fill: {key_color}; font-weight: bold;}}
text, tspan {{white-space: pre;}}
</style>
<rect width="100%" height="100%" fill="{bg_color}" stroke="{border_color}" stroke-width="{border_width}" rx="{border_radius}" ry="{border_radius}"/>

<g id="ascii-panel">
<text fill="{text_color}">
"""
    ascii_panel_height = len(ascii_lines) * font_size * line_height_factor
    ascii_start_y = (svg_height - ascii_panel_height) / 2 + font_size 

    for i, line in enumerate(ascii_lines):
        x_pos = 15 + (ascii_panel_width - (len(line) * char_width_px)) / 2 
        y_pos = ascii_start_y + (i * font_size * line_height_factor)
        svg_content += f'<tspan x="{x_pos}" y="{y_pos}">{line}</tspan>\n'

    svg_content += """</text>
</g>
<g id="info-panel">
"""
    info_panel_height_actual = info_total_lines * font_size * line_height_factor 
    info_panel_start_y = (svg_height - info_panel_height_actual) / 2 + font_size 


    info_x_start = ascii_panel_width + 15
    current_y = info_panel_start_y 

    guiones_longitud_dinamica = int((info_panel_base_width - (info_x_start - ascii_panel_width)) / char_width_px) - 2 


    svg_content += f"""<text x="{info_x_start}" y="{info_panel_start_y}" fill="{text_color}">"""

    for section in info_sections:
        if section.get("title") == "username_header":
            username_text = section["username"]

            remaining_space_for_username = guiones_longitud_dinamica - len(username_text)
            
            if remaining_space_for_username < 0:
                remaining_space_for_username = 0

            dashes_left_username = remaining_space_for_username // 2
            dashes_right_username = remaining_space_for_username - dashes_left_username 
            
            centered_username_line = f"{'-' * dashes_left_username}{username_text}{'-' * dashes_right_username}"
            
            if len(centered_username_line) > guiones_longitud_dinamica:
                centered_username_line = centered_username_line[:guiones_longitud_dinamica]

            svg_content += f'<tspan x="{info_x_start}" y="{current_y}">{centered_username_line}</tspan>\n'
            current_y += font_size * line_height_factor
            
            svg_content += f'<tspan x="{info_x_start}" y="{current_y}">{"-" * guiones_longitud_dinamica}</tspan>\n' 
            current_y += font_size * line_height_factor * 1.2 
        elif section.get("title"):
            title_text_content = f"- {section['title']}"
            
            dashes_needed = guiones_longitud_dinamica - len(title_text_content)
            
            if dashes_needed < 0:
                dashes_needed = 0
            
            dashes_content = '-' * dashes_needed

            svg_content += f'<tspan x="{info_x_start}" y="{current_y}" class="section-title">{title_text_content}</tspan>'
            
            dashes_start_x = info_x_start + (len(title_text_content) * char_width_px)
            
            if dashes_start_x + (len(dashes_content) * char_width_px) > (info_x_start + info_panel_base_width - 30): 
                max_dashes_chars = int(((info_x_start + info_panel_base_width - 30) - dashes_start_x) / char_width_px)
                if max_dashes_chars < 0: max_dashes_chars = 0
                dashes_content = '-' * max_dashes_chars

            svg_content += f'<tspan x="{dashes_start_x}" y="{current_y}" fill="{text_color}">{dashes_content}</tspan>\n'
            
            current_y += font_size * line_height_factor * 1.2 

        for item_key, item_value in section.get('items', []):
            icon = icon_map.get(item_key, "") + " " 
            
            if item_key in ["Stack", "Lenguajes de Programación", "Tecnologías Web", 
                             "Bases de Datos", "Herramientas DevOps", "Hobbies",
                             "Email", "LinkedIn", "Twitter", "Discord"]: 
                svg_content += f'<tspan x="{info_x_start}" y="{current_y}" class="key">{icon}{item_key}: </tspan>'
                svg_content += f'<tspan class="value">{str(item_value)}</tspan>\n'
            elif item_key == "Líneas de Código (LOC)":
                parts = str(item_value).split(" ", 1) 
                total_loc = parts[0]
                details_loc = parts[1] if len(parts) > 1 else ""

                svg_content += f'<tspan x="{info_x_start}" y="{current_y}" class="key">{icon}{item_key}: </tspan>'
                svg_content += f'<tspan class="value">{total_loc}</tspan>'
                
                if details_loc:
                    add_part = ""
                    del_part = ""
                    
                    details_stripped = details_loc.replace('(', '').replace(')', '').strip()
                    parts_inner = [p.strip() for p in details_stripped.split(',')]
                    
                    for p in parts_inner:
                        if p.startswith('+'):
                            add_part = p
                        elif p.startswith('-'):
                            del_part = p

                    svg_content += f'<tspan class="value"> (</tspan>'
                    if add_part:
                        svg_content += f'<tspan fill="#3fb950">{add_part}</tspan>'
                    if add_part and del_part:
                        svg_content += f'<tspan class="value">,</tspan><tspan> </tspan>'
                    if del_part:
                        svg_content += f'<tspan fill="#f85149">{del_part}</tspan>'
                    svg_content += f'<tspan class="value">)</tspan>'

                svg_content += '\n'
            else: # For short, standard key-value pairs with dots
                key_str = f"{icon}{item_key}: "
                value_str = str(item_value)

                key_char_len = len(key_str)
                value_char_len = len(value_str)
                
                available_chars_for_line = guiones_longitud_dinamica 
                
                dots_char_count = max(0, available_chars_for_line - key_char_len - value_char_len - 1) 
                
                dots_content = "." * dots_char_count

                svg_content += f'<tspan x="{info_x_start}" y="{current_y}" class="key">{key_str}</tspan>'
                
                dots_x_pos = info_x_start + (key_char_len * char_width_px)
                svg_content += f'<tspan x="{dots_x_pos}" y="{current_y}" fill="{text_color}">{dots_content}</tspan>'
                
                value_x_pos = dots_x_pos + (dots_char_count * char_width_px) + (char_width_px * 1) 
                svg_content += f'<tspan x="{value_x_pos}" y="{current_y}" class="value">{value_str}</tspan>\n'
            
            current_y += font_size * line_height_factor

        if section.get('extra_line_after', False):
            current_y += font_size * line_height_factor * 0.5 

    svg_content += """</text>
</g> </svg>"""

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(svg_content)

# --- SCRIPT USAGE ---
if __name__ == "__main__":
    ruta_de_tu_foto = "me.jpg" 
    ancho_deseado_ascii = 50

    # 🚨🚨🚨 INICIO DE LA SECCIÓN QUE DEBES AÑADIR/VERIFICAR 🚨🚨🚨

    # ¡IMPORTANTE! Cambia esto por tu usuario de GitHub REAL
    tu_github_username = "minguitof" # <--- ¡PON AQUÍ TU USUARIO DE GITHUB!
    
    # Intenta obtener el token de GitHub de una variable de entorno por seguridad
    github_token = os.getenv("GITHUB_TOKEN") 
    if not github_token:
        print("Advertencia: No se encontró la variable de entorno GITHUB_TOKEN.")
        print("Las peticiones a la API de GitHub pueden estar sujetas a límites de tasa.")
        print("Para un uso prolongado o para evitar problemas, considera configurar GITHUB_TOKEN.")
        print("Puedes obtener uno en: GitHub -> Settings -> Developer settings -> Personal access tokens -> Tokens (classic)")
        print("Necesitas al menos el permiso 'public_repo' o 'repo'.")
    
    # Obtener los datos de GitHub (¡ESTO ES LO QUE HACE LA CONSULTA REAL!)
    github_stats = obtener_datos_github(tu_github_username, github_token)

    # 🚨🚨🚨 FIN DE LA SECCIÓN QUE DEBES AÑADIR/VERIFICAR 🚨🚨🚨

    mis_datos_secciones = [
        {
            "title": "username_header",
            "username": "M4r10@github",
            "items": [
                ("Edad", calcular_edad_exacta("2001-02-04")),
                ("Ubicación", "Medellín, Colombia"),
                ("Intereses", "Desarrollo web, Backend"),
            ],
            "extra_line_after": True
        },
        {
            "title": "Stack",
            "items": [
                ("Stack", "Python, JS, .NET Core, C#, GitHub Actions"),
                ("Lenguajes de Programación", "JavaScript, C#"),
                ("Tecnologías Web", "HTML, CSS, Vue.js, Node.js"), 
                ("Bases de Datos", "MSSQL Server, MySQL"), 
                ("Herramientas DevOps", "GitHub Actions"), 
            ],
            "extra_line_after": True
        },
        {
            "title": "Hobbies",
            "items": [
                ("Hobbies", "Lectura, Gimnasio"),
            ],
            "extra_line_after": True
        },
        {
            "title": "Contacto",
            "items": [
                ("Email", "jhonechavarria0506@gmail.com"),
                ("LinkedIn", "john-mario-echavarria-bermudez/"),
            ],
            "extra_line_after": True
        },
        {
            "title": "GitHub Stats",
            "items": [
                ("Total Repositorios", github_stats["total_repos"]),   # <--- ¡ESTO USARÁ EL VALOR DE LA API!
                ("Estrellas Totales", github_stats["total_stars"]),   # <--- ¡ESTO USARÁ EL VALOR DE LA API!
                ("Forks Totales", github_stats["total_forks"]),       # <--- ¡ESTO USARÁ EL VALOR DE LA API!
                ("Total Commits", github_stats["total_commits"]),     # <--- ¡ESTO USARÁ EL VALOR DE LA API!
                ("Seguidores", github_stats["total_followers"]),      # <--- ¡ESTO USARÁ EL VALOR DE LA API!
                ("Líneas de Código (LOC)", "5,000 (+6000, -1000)"), # Este es el único que dejaste manual, y está bien 
            ],
            "extra_line_after": False
        }
    ]

    bg_color = "#161b22" 
    text_color = "#c9d1d9" 
    key_color = "#ffa657" 
    value_color = "#a5d6ff" 

    border_color = "#444c56" 
    border_width = 2 
    border_radius = 10 
    
    print(f"Generando SVG de perfil para: {ruta_de_tu_foto}...")
    
    ascii_result = convertir_imagen_a_ascii(ruta_de_tu_foto, ancho_salida=ancho_deseado_ascii)

    

    if ascii_result:
        
        # Define un nombre de archivo SVG fijo, sin fechas.
        svg_filename = "readme_profile.svg" # <--- ¡CAMBIO CLAVE AQUÍ! Este será el nombre fijo.

        # *** Eliminamos toda la lógica de borrado de SVGs antiguos y el uso de glob ***
        # Ya no es necesario, porque siempre vamos a sobrescribir el mismo archivo.
        
        # 1. Generar el archivo SVG
        generar_svg_con_info(ascii_result,
                             mis_datos_secciones,
                             output_filename=svg_filename, # Ahora usa el nombre fijo
                             bg_color=bg_color,
                             text_color=text_color,
                             key_color=key_color,
                             value_color=value_color,
                             border_color=border_color,
                             border_width=border_width,
                             border_radius=border_radius
                             )
        print(f"¡SVG de perfil generado como '{svg_filename}'!")

        # 2. Actualizar el archivo README.md para que apunte al nuevo SVG
        readme_content = rf"""
![Perfil GitHub CSV-Dark](./{svg_filename})
"""
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

        print(f"¡README.md actualizado con el nuevo SVG!")
        print("Ahora puedes hacer commit y push de '{svg_filename}' y 'README.md' a tu repositorio.")

    else:
        print("\nNo se pudo generar el arte ASCII para el SVG. No se actualizará el README.md.")
