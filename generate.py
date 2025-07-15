from datetime import datetime, UTC # Importa UTC directamente
import requests
import os # Importa os para acceder a variables de entorno

# 👤 Tus datos
USERNAME = "minguitof"
NAME = "M4r10"
BIRTHDATE = datetime(2001, 2, 4)

# 🧠 Calculos
# Usamos datetime.now(UTC) que es la forma recomendada y reemplaza utcnow()
today = datetime.now(UTC) 
age = today.year - BIRTHDATE.year - ((today.month, today.day) < (BIRTHDATE.month, BIRTHDATE.day))

# 🚀 API de GitHub
def fetch_stats():
    user_url = f"https://api.github.com/users/{USERNAME}"
    repos_url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100"
    
    # Es una buena práctica usar un token de GitHub para evitar límites de tasa.
    # Asegúrate de configurar una variable de entorno GH_TOKEN en tu workflow de GitHub Actions.
    # Por ejemplo, en tu YAML:
    # env:
    #   GH_TOKEN: ${{ secrets.GITHUB_TOKEN }} # O el nombre de tu secreto
    github_token = os.environ.get("GH_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    public_repos = 0
    total_stars = 0
    total_forks = 0

    # Manejo de errores para la solicitud de usuario
    try:
        user_response = requests.get(user_url, headers=headers)
        user_response.raise_for_status() # Lanza una excepción para errores HTTP (4xx o 5xx)
        user = user_response.json()
        public_repos = user.get("public_repos", 0)
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos del usuario {USERNAME}: {e}")
        # Continuar con valores predeterminados si falla

    # Manejo de errores para la solicitud de repositorios
    try:
        repos_response = requests.get(repos_url, headers=headers)
        repos_response.raise_for_status() # Lanza una excepción para errores HTTP (4xx o 5xx)
        repos = repos_response.json()
        # Asegúrate de que 'repos' sea una lista antes de iterar
        if isinstance(repos, list):
            total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
            total_forks = sum(repo.get("forks_count", 0) for repo in repos)
        else:
            print(f"La respuesta de repositorios no es una lista: {repos}")
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener repositorios de {USERNAME}: {e}")
        # Continuar con valores predeterminados si falla

    return public_repos, total_stars, total_forks

def fetch_commit_count():
    events_url = f"https://api.github.com/users/{USERNAME}/events/public"
    github_token = os.environ.get("GH_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    commits = 0
    try:
        events_response = requests.get(events_url, headers=headers)
        events_response.raise_for_status() # Lanza una excepción para errores HTTP (4xx o 5xx)
        events = events_response.json()
        if isinstance(events, list):
            commits = sum(1 for e in events if e.get("type") == "PushEvent")
        else:
            print(f"La respuesta de eventos no es una lista: {events}")
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener eventos de {USERNAME}: {e}")
        # Continuar con 0 commits si falla
    return commits

# 📦 Stats
repos, stars, forks = fetch_stats()
commits = fetch_commit_count()

# 📝 Template tipo neofetch
# Usamos una "raw string" (r"""...""") para evitar la advertencia de secuencia de escape
content = rf""" 
 ![Mi Arte ASCII](/mi_perfil_readme_5.svg)
"""

# Guardar el archivo
with open("README.md", "w", encoding="utf-8") as f:
    f.write(content)

