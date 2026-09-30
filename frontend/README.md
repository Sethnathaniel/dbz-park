# Dragon Ball Park — Front

Le front du parc, en React. Il reprend les mêmes écrans et le même style que les
gabarits Django, mais il est un projet à part : il se lance, se construit et se
déploie sans le back.

Tant que l'API n'existe pas, il tourne sur des **fausses données**
(`src/api/mock.js`). Le jour où le back répond, on passe `VITE_USE_MOCK` à
`false` et tout est branché.

## Lancement

```bash
cd frontend
npm install
cp .env.example .env
npm run dev          # http://localhost:5173
```

Deux comptes existent dans la maquette :

| Compte  | Mot de passe  | Ce qu'il voit             |
| ------- | ------------- | ------------------------- |
| `goku`  | `kamehameha`  | billets, attractions      |
| `admin` | `admin`       | + la console              |

## Ce qu'il y a dans quel dossier

```
src/
├── api/          ← tout ce qui parle au back. Le reste du front ne connaît pas fetch.
│   ├── endpoints.js  LA liste des URL. Un seul fichier à corriger si le back renomme.
│   ├── client.js     fetch + jeton + erreurs. Le seul endroit qui touche au réseau.
│   ├── mock.js       le faux back, tant que le vrai n'existe pas.
│   └── auth.js · tickets.js · attractions.js · console.js   un fichier par domaine.
├── auth/         qui est connecté (AuthContext) et les pages fermées (RequireAuth).
├── components/   les morceaux réutilisés : en-tête, carte, pastilles, bandeau.
├── hooks/        useApi : charger des données avec ses états (chargement, erreur).
├── pages/        un fichier par écran. C'est là qu'on lit ce que fait la page.
├── styles/       dbz-park.css, la copie du style du parc.
└── utils/        la mise en forme des dates et des durées, les libellés des rôles.
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

## Brancher le vrai back

1. Le back expose les routes décrites dans **`API.md`**.
2. Dans `.env` : `VITE_USE_MOCK=false`.
3. Si les adresses diffèrent, les corriger dans `src/api/endpoints.js` — et
   nulle part ailleurs.

En développement, `vite.config.js` renvoie `/api` vers `http://localhost:8000` :
pour le navigateur tout vient de la même origine, donc **aucun CORS à régler**.

Une fois branché, `src/api/mock.js` peut être supprimé, ainsi que les `USE_MOCK ?`
dans les quatre fichiers de domaine.

## Construire pour la production

```bash
npm run build        # écrit dans dist/
```

`dist/` ne contient que des fichiers statiques : ils se posent sur un CDN ou un
Nginx, sans serveur Python. C'est ce qui rend le front indépendant du back — il
n'a besoin que de l'URL de l'API (`VITE_API_URL`).
