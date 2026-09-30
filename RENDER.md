# Héberger le parc sur Render

Tout est décrit dans [`render.yaml`](render.yaml), un *Blueprint* : Render le lit et
crée les cinq services d'un coup, déjà reliés entre eux.

| Service Render | Type | Rôle | Remplace, dans `docker-compose.yml` |
| -------------- | ---- | ---- | ----------------------------------- |
| `dbz-park-front` | Static Site | le front construit (`dist/`), servi par le CDN de Render | `frontend` (nginx) |
| `dbz-park-api` | Web Service, Docker | l'API FastAPI | `backend` |
| `dbz-park-worker` | Background Worker, Docker | Celery : appelle les visiteurs toutes les 5 s | `worker` |
| `dbz-park-redis` | Key Value | le broker du worker | `redis` |
| `dbz-park-db` | Postgres | la base | `db` |

Une différence avec Docker Compose : il n'y a plus de nginx pour faire suivre `/api`.
Le front et l'API ont chacun leur adresse, donc le front appelle l'API par son URL
complète (`VITE_API_URL`) et l'API autorise l'adresse du front (`CORS_ORIGINS`).

## Ce que ça coûte

| Service | Plan | Prix |
| ------- | ---- | ---- |
| Front | Static Site | gratuit |
| API | Free | gratuit — **s'endort après 15 min sans visite**, la requête suivante attend ~1 min |
| Base | Free | gratuit — **supprimée au bout de 30 jours**, 1 Go |
| Redis | Free | gratuit — rien n'est gardé au redémarrage, ce qui ne gêne pas un broker |
| Worker | Starter | **~7 $/mois** : Render n'a pas d'offre gratuite pour les workers |

Sans le worker, l'app marche mais personne n'est jamais appelé : les files restent
figées. Pour une démo plus longue que 30 jours, passer la base en plan payant.

## Avant de commencer

- Un compte sur [render.com](https://render.com), relié à GitHub.
- Render doit pouvoir lire le dépôt `Zarcoks/dbz-park` : c'est son propriétaire qui
  installe l'app GitHub de Render sur le dépôt, ou qui crée le Blueprint lui-même.
- `render.yaml` doit être sur la branche `main` du dépôt : Render lit GitHub, pas ta
  machine.

## Déployer

**1. Créer le Blueprint.** Dashboard → **New** → **Blueprint** → choisir le dépôt,
branche `main`. Render affiche les cinq services qu'il va créer.

**2. Remplir les trois valeurs qu'il demande.** Les URL suivent le nom du service :

| Variable | Service | Valeur |
| -------- | ------- | ------ |
| `ADMIN_PASSWORD` | `dbz-park-api` | un vrai mot de passe : c'est celui du compte `admin`, qui ouvre la console |
| `CORS_ORIGINS` | `dbz-park-api` | `https://dbz-park-front.onrender.com` — sans `/` à la fin |
| `VITE_API_URL` | `dbz-park-front` | `https://dbz-park-api.onrender.com/api` |

**3. Lancer** (*Apply*). Premier déploiement : 5 à 10 minutes. L'API applique les
migrations à son démarrage, puis crée le compte `admin`, 30 billets libres et quatre
attractions.

**4. Vérifier les adresses.** Si un nom était déjà pris sur Render, il y ajoute un
suffixe (`dbz-park-api-x7k2.onrender.com`). Compare les URL affichées sur chaque
service avec celles du tableau, et si elles diffèrent :

- API → *Environment* → corriger `CORS_ORIGINS` : l'API redémarre seule ;
- front → *Environment* → corriger `VITE_API_URL`, puis **Manual Deploy**. Une
  variable `VITE_…` est écrite dans les fichiers au moment du build : la changer
  sans reconstruire ne change rien.

**5. Tester.**

- `https://dbz-park-api.onrender.com/api/health/` répond `{"status":"ok"}` ;
- `https://dbz-park-front.onrender.com` : se connecter en `admin` avec le mot de passe
  choisi, ouvrir la console ;
- dans une fenêtre privée, créer un visiteur, prendre un billet, rejoindre une file :
  il doit être appelé dans les secondes qui suivent (logs de `dbz-park-worker`).

## Ensuite

Chaque push sur `main` redéploie ce qui a changé : un commit dans `backend/` reconstruit
l'API et le worker, un commit dans `frontend/` reconstruit le front.

## Si ça ne marche pas

| Symptôme | Cause probable |
| -------- | -------------- |
| « Le serveur ne répond pas » dans le front, erreur CORS dans la console du navigateur | `CORS_ORIGINS` ne correspond pas exactement à l'adresse du front (https, pas de `/` final) |
| Le front appelle `/api/…` sur sa propre adresse et reçoit du HTML | `VITE_API_URL` absente au build : la remplir, puis **Manual Deploy** du front |
| Le front affiche les comptes `goku` / `admin` de la maquette | `VITE_USE_MOCK` n'est pas à `false` au build |
| Première page très lente | l'API gratuite se réveille : ~1 min, puis normal |
| Personne n'est appelé | le worker ne tourne pas : voir ses logs, et `REDIS_URL` |
| Heures décalées de 1 ou 2 h | `TZ` absente sur l'API ou le worker |
