# Dragon Ball Park — Front

Le front du parc, en React. Il reprend les mêmes écrans et le même style que les
gabarits Django, mais il est un projet à part : il se lance, se construit et se
déploie sans le back.

Il parle à l'API FastAPI de `../backend`, selon le contrat décrit dans
[`../API.md`](../API.md). Il n'y a plus de maquette : sans le back, les pages
affichent « Le serveur ne répond pas. ».

## Lancement

Le back d'abord, depuis la racine du projet (voir `../backend/README.md`) :

```bash
docker compose up -d
cd backend && uv run alembic upgrade head && uv run fastapi dev app/main.py
```

Puis le front, dans un autre terminal :

```bash
cd frontend
npm install
cp .env.example .env
npm run dev          # http://localhost:5173
```

Au premier démarrage, le back crée un compte `admin` / `admin` (qui voit la
console) et 30 billets libres, `DBZ-0001` à `DBZ-0030`. Pour un visiteur : créer
un compte depuis `/inscription`, puis rattacher un de ces billets depuis
« Mes billets ».

## Ce qu'il y a dans quel dossier

```
src/
├── api/          ← tout ce qui parle au back. Le reste du front ne connaît pas fetch.
│   ├── endpoints.js  LA liste des URL. Un seul fichier à corriger si le back renomme.
│   ├── client.js     fetch + jeton + erreurs. Le seul endroit qui touche au réseau.
│   └── auth.js · tickets.js · attractions.js · console.js   un fichier par domaine.
├── auth/         qui est connecté (AuthContext) et les pages fermées (RequireAuth).
├── components/   les morceaux réutilisés : en-tête, carte, pastilles, bandeau.
├── hooks/        useApi : charger des données avec ses états (chargement, erreur).
├── pages/        un fichier par écran. C'est là qu'on lit ce que fait la page.
├── styles/       dbz-park.css, la copie du style du parc.
└── utils/        la mise en forme des dates.
```

La règle : **une page ne fait jamais d'appel réseau elle-même**. Elle demande à
`src/api/`, qui demande à `client.js`, qui seul connaît `fetch`. C'est ce qui
permet de changer d'API sans toucher aux écrans.

## D'où vient chaque écran

| Écran React                 | Route          | Venait de                         |
| --------------------------- | -------------- | --------------------------------- |
| `pages/LoginPage.jsx`       | `/connexion`   | `accounts/login.html`             |
| `pages/SignupPage.jsx`      | `/inscription` | `accounts/signup.html`            |
| `pages/TicketsPage.jsx`     | `/`            | `tickets/tickets.html`            |
| `pages/AttractionsPage.jsx` | `/attractions` | `attractions/attractions.html`    |
| `pages/ConsolePage.jsx`     | `/console`     | `console/console.html`            |
| `components/Layout.jsx`     | —              | `index.html` (le gabarit parent)  |

## Les équivalences Django → React

Utile pour expliquer le passage d'un monde à l'autre :

| Django                              | Ici                                          |
| ----------------------------------- | -------------------------------------------- |
| `{% extends "index.html" %}`        | `<Layout />` et son `<Outlet />`              |
| `{% block content %}`               | la page posée par la route                    |
| `urls.py`                           | `src/App.jsx`                                 |
| `LoginRequiredMixin`                | `<RequireAuth>`                               |
| `StaffOnlyMixin` (403)              | `<RequireAuth staffOnly>`                     |
| `{{ user }}` dans tous les gabarits | `useAuth()`                                   |
| `messages` (succès / erreur)        | `<Alert />` + un état dans la page            |
| `{% for %}` / `{% empty %}`         | `.map()` + un test sur `length === 0`         |
| `|time:"H:i"`, `|timesince`         | `src/utils/format.js`                         |
| `{% csrf_token %}`                  | plus rien : jeton `Bearer`, pas de cookie     |
| une vue qui `redirect()` après POST | `runAction()` : appeler, afficher, `reload()` |

## Comment le front parle au back

En développement, `vite.config.js` renvoie `/api` vers `http://localhost:8000` :
pour le navigateur tout vient de la même origine, donc **aucun CORS à régler**.

Si une adresse change côté back, on la corrige dans `src/api/endpoints.js`, et
nulle part ailleurs.

Un seul endroit recolle deux réponses du back : `listAttractionCards()`, dans
`src/api/attractions.js`. Le catalogue (`GET /attractions/`) ne dit rien du
visiteur, et ce que le visiteur a en cours (`GET /queue/`) ne dit rien des
attractions ; la fonction assemble les deux pour que `AttractionCard` reçoive une
carte complète.

## Construire pour la production

```bash
npm run build        # écrit dans dist/
```

`dist/` ne contient que des fichiers statiques : ils se posent sur un CDN ou un
Nginx, sans serveur Python. C'est ce qui rend le front indépendant du back — il
n'a besoin que de l'URL de l'API (`VITE_API_URL`).
