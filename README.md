# Dragon Ball Park

Application de billetterie et de files d'attente virtuelles pour un parc
d'attractions Dragon Ball Z.

## Architecture

Le projet est découplé en trois parties indépendantes, qui ne se parlent que par
une API JSON :

```
 navigateur                        serveur API                     base
┌──────────────┐   HTTP + JSON   ┌──────────────┐    SQL (async)  ┌─────────────┐
│  frontend/   │ ──────────────► │  backend/    │ ──────────────► │ PostgreSQL  │
│  React+Vite  │   /api/…        │  FastAPI     │                 │ (Docker)    │
│  port 5173   │ ◄────────────── │  port 8000   │ ◄────────────── │ port 5432   │
└──────────────┘  Bearer <JWT>   └──────────────┘                 └─────────────┘
```

| Partie | Techno | Rôle |
| ------ | ------ | ---- |
| [`frontend/`](frontend/README.md) | React 18, Vite, React Router, Bootstrap | Les écrans. Fichiers statiques une fois construits (`npm run build`), déployables sur un CDN. |
| [`backend/`](backend/README.md) | FastAPI, SQLAlchemy async, Alembic, PyJWT | La logique métier. Ne renvoie que du JSON, jamais de HTML. |
| `docker-compose.yml` | PostgreSQL 17, Redis, nginx | Les cinq conteneurs : la base, le back, le worker et son broker Redis, et le front servi par nginx. |

Quelques choix qui découlent de ce découpage :

- **Un contrat unique, [`API.md`](API.md).** Le front et le back s'y conforment
  tous les deux ; c'est la seule chose qu'ils partagent. Deux codes de réponse
  seulement : `200`, et `400` avec un `{"detail": "…"}` affiché tel quel.
- **Un back sans état.** L'authentification passe par un JWT signé, envoyé en
  `Authorization: Bearer …`. Le serveur ne stocke aucune session : n'importe
  quelle instance de l'API peut répondre, ce qui permet de la dupliquer seule.
  Contrepartie : un jeton ne se révoque pas, il expire (12 h par défaut).
- **Pas de CORS en développement.** Le proxy de Vite renvoie `/api` vers
  `http://localhost:8000` ; pour le navigateur, tout vient de la même origine.
  Une fois déployé, c'est nginx qui joue ce rôle : il sert le front et fait
  suivre `/api` au back.
- **Un front qui tourne sans back.** Avec `VITE_USE_MOCK=true`, le front répond
  depuis de fausses données en mémoire (`frontend/src/api/mock.js`), aux formes
  exactes de `API.md`. `frontend/.env.example` le met à `false`, et l'image Docker
  le force à `false`.

## Déployer

```bash
cp .env.example .env        # puis changer POSTGRES_PASSWORD et JWT_SECRET
docker compose up -d --build
```

L'app répond sur **http://localhost:8080** (`FRONT_PORT` dans `.env`). Le back
applique les migrations à son démarrage, puis crée le compte `admin` / `password`
s'il n'existe pas, et 30 billets libres si la base n'en a aucun.

## Développer

Copier `.env.example` en `.env` à la racine : il sert à la fois à
`docker compose` (identifiants de la base) et au back (mêmes identifiants,
secret des jetons, origines CORS).

**1. La base seule**

```bash
docker compose up -d db
```

**2. Le back** — [uv](https://docs.astral.sh/uv/) requis

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py     # http://localhost:8000/api/docs
```

**3. Le front**

```bash
cd frontend
npm install
cp .env.example .env               # VITE_USE_MOCK=true pour tourner sans back
npm run dev                        # http://localhost:5173
```

Pour ne travailler que sur les écrans, l'étape 3 suffit : en mode maquette, les
comptes `goku` / `kamehameha` (visiteur) et `admin` / `admin` (personnel)
existent déjà.

## Tests

```bash
cd backend
uv run pytest
```

Les tests tournent sur le Postgres du `docker compose`, dans une base à part
(`<POSTGRES_DB>_test`) remise à zéro avant chaque test. Détails dans
[`backend/README.md`](backend/README.md#tests).

## Fonctionnalités

Le cahier des charges complet est dans [`SPEC.md`](SPEC.md), les routes dans
[`API.md`](API.md).

- **Comptes** : inscription et connexion (`/inscription`, `/connexion`).
  Se déconnecter, c'est oublier le jeton côté front : il n'y a pas de route
  pour ça.
- **Mes billets** (`/`) : le visiteur rattache à son compte un billet libre par
  son numéro, ou en achète un. Le rôle du billet est fixé à l'achat : c'est du
  texte libre, `normal`, `sayan` et `super_sayan` sont ceux que le parc vend. Tous
  les billets sont considérés comme payés : il n'y a ni colonne ni route de
  paiement. Le staff voit en plus tous les billets du parc et leur détenteur.
- **Attractions** (`/attractions`) : la liste des attractions et leur
  affluence ; le visiteur y rejoint une file virtuelle, la quitte, et valide sa
  place quand il est appelé. Un worker appelle les visiteurs quand des places se
  libèrent : Super Sayan d'abord, puis Saiyan, puis humains, et dans un même tarif,
  le premier arrivé. Le billet joué est le meilleur qui lui reste libre.
- **Console** (`/console`) : réservée aux comptes `is_staff`. Elle liste, par
  attraction, les visiteurs appelés, avec deux décisions : **Accepter** (le
  visiteur entre) ou **Refuser** (sa place est retirée).

## État d'avancement

| Partie | État |
| ------ | ---- |
| Front | Tous les écrans sont écrits et branchés sur le back ; la maquette reste disponible. |
| Base | Schéma complet (cinq tables), trois migrations. |
| Back | Les 17 routes de `API.md` sont écrites, avec 3 tests chacune. Un worker Celery appelle les visiteurs suivants toutes les 5 s. |
| Déploiement | Base, back, worker, Redis et front conteneurisés (`docker compose up -d --build`). |

Deux routes manquent pour que l'app tienne seule : créer une attraction, et
enregistrer une sortie. En attendant la seconde, une tâche **temporaire** du worker
fait sortir tout visiteur entré depuis 30 s (`backend/app/temporary_exits.py`).

Il n'y a plus de panneau `/admin/` comme dans l'ancienne version Django : les
données de départ (attractions, billets libres) s'écrivent pour l'instant
directement en base.
