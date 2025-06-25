from datetime import datetime
import requests

# 👤 Tus datos
USERNAME = "minguitof"
NAME = "M4r10"
BIRTHDATE = datetime(2001, 2, 4)

# 🧠 Calculos
today = datetime.utcnow()
age = today.year - BIRTHDATE.year - ((today.month, today.day) < (BIRTHDATE.month, BIRTHDATE.day))

# 🚀 API de GitHub
def fetch_stats():
    user_url = f"https://api.github.com/users/{USERNAME}"
    repos_url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100"
    headers = {"Accept": "application/vnd.github.v3+json"}

    user = requests.get(user_url, headers=headers).json()
    repos = requests.get(repos_url, headers=headers).json()

    public_repos = user.get("public_repos", 0)
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos)

    return public_repos, total_stars, total_forks

def fetch_commit_count():
    events_url = f"https://api.github.com/users/{USERNAME}/events/public"
    headers = {"Accept": "application/vnd.github.v3+json"}
    events = requests.get(events_url, headers=headers).json()
    return sum(1 for e in events if e["type"] == "PushEvent")

# 📦 Stats
repos, stars, forks = fetch_stats()
commits = fetch_commit_count()

# 📝 Template tipo neofetch
content = f""" 
{NAME}@github
--------------------------
💻 Nombre: {NAME} \n
🎂 Edad: {age} años \n
📦 Repos públicos: {repos} \n
⭐ Estrellas recibidas: {stars} \n
🍴 Forks recibidos: {forks} \n
⚡ Commits recientes: {commits} \n

🧠 Stack: Python, JS, .NET Core, C#, GitHub Actions \n

<pre>             ,.-:~:-.                    ,.-·::':¯:¯:`^·,                       ,._., ._
           /':::::::::'`,             ,:´:::::::::::::::::::';'      ,:'/¯/`:,    /::::::::::'/:/':~-.,
         /;:-·~·-:;':::',          /::::;:-· ´' ¯¯'`^·, /     /:/_/::::/'; /:-·:;:-·~·';/:::::::::'`·-.
       ,'´          '`:;::`,       /;:´                   ';/'    /:'     '`:/::; ';           '`~-:;:::::::::'`,
      /                `;::'\     /'      ,:'´¯'`·.,     '/     ;         ';:';   ',.                 '`·-:;::::'i
    ,'                   '`,::; ,'      /            '`*'´    ,.,|         'i::i   `'i      ,_            '`;:::'¦
   i'       ,';´'`;         '\:::;     ';:~.·-.,..-·~'´:'/:::';';        ;'::i     'i      ;::/`:,          i'::/
 ,'        ;' /´:`';         ';::';        '`~·-:;: -·~'´¯';/''i        'i::i'   _;     ;:/;;;;:';        ¦'/
 ;        ;/:;::;:';         ',::'\                          /   ';       'i::;'  /::';   ,':/::::::;'       ,´
'i        '´        `'         'i:::'`·,                 .·'      ;      'i:/', /:;::i  ,'/::::;·´        ,'´
¦       '/`' *^~-·'´\         ';'/    '`~·-–--·^*'´        '';     ;/   '`·.     `'¯¯          ,·
'`., .·´              `·.,_,.·´'                                ';   /-•X99•-`' ~·- .,. -·~ ´
                                                                   `'´
                                                                   
 </pre>

--------------------------
"""

# Guardar el archivo
with open("README.md", "w", encoding="utf-8") as f:
    f.write(content)

