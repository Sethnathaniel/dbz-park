# Backend — FastAPI

L'API du parc. Le contrat qu'elle doit respecter est à la racine, dans
[`../API.md`](../API.md) : **deux réponses possibles, `200` et `400`**, et pour
un `400` un corps `{"detail": "…"}` que le front affiche tel quel.

## Lancer

Copier `../.env.example` en `../.env`, puis, depuis la racine :

```bash
docker compose up -d        # la base, et rien d'autre pour l'instant
```

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

Le `.env` de la racine sert aux deux : `docker compose` y prend les identifiants
de la base, `app/config.py` y prend les mêmes, plus le secret des jetons.

L'API répond sur `http://localhost:8000/api/…`, la documentation interactive sur
`http://localhost:8000/api/docs`. Le front (port 5173) renvoie déjà `/api` ici
via le proxy de Vite : pas de CORS à régler en développement.

## Au démarrage

Avant la première requête, l'API vérifie deux choses et les répare si besoin
(`app/bootstrap.py`, appelé par le `lifespan`) :

- **aucun compte `is_staff`** → elle crée `admin` / `admin`. Le mot de passe est en dur :
  c'est un confort de développement, à ne pas laisser sortir d'ici.
- **aucun billet** → elle en crée 30, dix par rôle, non assignés (`DBZ-0001` à `DBZ-0030`).

Les deux tests sont tout ou rien : ils regardent si la table contient *quelque chose*,
donc ils ne discutent jamais avec des données créées ensuite. Un deuxième démarrage ne
dit rien et ne touche à rien. Le tout sous un verrou consultatif Postgres, pour que
plusieurs workers lancés en même temps ne créent pas les mêmes lignes deux fois.

Un cas est traité à part : si le nom `admin` est déjà pris par un visiteur alors qu'il
n'y a pas de staff, l'API **ne le promeut pas** — cela donnerait la console au premier
qui a réservé le nom. Elle écrit une erreur dans les logs et laisse la console fermée.

## Ce qu'il y a dans quel fichier

```
app/
├── config.py      le .env de la racine, lu une fois. Seul endroit qui connaît l'environnement.
├── db.py          le moteur async et la session par requête (`SessionDep`).
├── security.py    empreintes bcrypt, et le JWT signé qui sert de jeton.
├── dependencies.py qui appelle : `CurrentUser` (connecté) et `StaffUser` (console).
├── errors.py      `ApiError("…")` → 400 + detail. La seule erreur du projet.
├── main.py        l'app, montée sous /api, et la traduction 422 → 400.
├── bootstrap.py   ce que le démarrage garantit : un staff, et des billets.
├── admission.py   faire entrer quelqu'un : place libre et compteur, en une requête.
├── models/        les cinq tables. Rien d'autre ne décrit le schéma.
├── schemas/       les formes d'entrée et de sortie de `../API.md`.
└── routers/       un module par domaine, comme `frontend/src/api/`.
alembic/           les migrations. `env.py` lit l'URL dans `app.config`.
```

Deux règles qui expliquent le découpage :

- **Un modèle ne sort jamais d'un handler.** Il passe par un schéma, qui décide
  de ce qui est publié — c'est ce qui évite qu'une colonne ajoutée en base se
  retrouve dans une réponse.
- **Une erreur ne se fabrique pas à la main.** `raise ApiError("…")`, jamais un
  `HTTPException` avec un code choisi sur place : c'est ce qui garantit que le
  contrat n'a bien que deux codes.

## État d'avancement

Les 15 routes de `../API.md` sont écrites. Deux trous restent dans le contrat lui-même,
listés à la fin de `API.md` : rien n'appelle un visiteur (`is_ready` ne se pose qu'à la
main), et aucune route n'enregistre une sortie (`people_inside` ne fait que monter).

Deux choix d'implémentation qui ne se devinent pas en lisant le contrat :

- **Une seule horloge : Python.** Postgres tourne en UTC dans le conteneur, la machine
  non. Tout ce que la file compare (`joined_at`, `ready_at`, `entered_at`) est écrit avec
  `datetime.now()` côté API, jamais par le `now()` de la base.
- **L'entrée dans une attraction** (`app/admission.py`) vérifie la place libre et
  incrémente `people_inside` dans le même `UPDATE` : deux admissions simultanées ne
  peuvent pas se partager le dernier siège. La validation du visiteur et l'acceptation
  de la console passent toutes deux par là.

## Tests

```bash
uv run pytest
```

Les tests tournent sur un **vrai Postgres** — celui du `docker compose` — mais dans une
base à part, `<POSTGRES_DB>_test`, créée au premier lancement et vidée puis repeuplée
avant *chaque* test (`TRUNCATE … RESTART IDENTITY`). Les données de développement ne
sont jamais touchées, et les identifiants sont déterministes : `tests/seed.py` les nomme
(`TICKET_FREE`, `ENTRY_GOKU_READY`…) plutôt que de laisser des `1`, `2`, `3` dans les
assertions.

Trois tests par route : le bon scénario, et deux refus qui comptent. Quand une route
écrit, son bon scénario vérifie l'effet et pas seulement le `200` : la place a disparu,
le compteur a bougé, la file a avancé.

L'heure de fermeture des files est forcée à 24 pendant les tests (fixture `queues_open`) :
sans ça, la suite échouerait tous les soirs après 19 h.

Deux propriétés de sécurité sont testées explicitement, parce qu'elles se cassent sans
bruit : `login` répond la même chose pour un mot de passe faux et un compte inconnu, et
la console refuse un visiteur connecté avec le message exact qu'elle sert à un inconnu.

## Écarts avec le schéma de départ

Le schéma DBML fourni a été suivi, avec cinq ajustements :

| Schéma fourni | Ici | Pourquoi |
| ------------- | --- | -------- |
| `billet_role` | `ticket_role` | le reste du projet est passé à l'anglais. |
| `attraction_visit.billet_id` | `ticket_id` | la table visée s'appelle `ticket`. |
| index nommés en français | `uq_queue_entry_ticket_per_attraction`, `uq_visit_ticket_per_attraction` | même raison. |
| `user(id, username)` | `+ email`, `password_hash`, `is_staff` | le contrat demande une inscription avec email, une connexion, et une console réservée au personnel. |
| — | rien pour le paiement | décidé : tous les billets sont considérés comme payés, il n'y a donc ni colonne ni route d'argent. |

`ticket.numero` garde son nom : c'est celui de la colonne dans le schéma.

L'ordre de déclaration de `ticket_role` est l'ordre de priorité des tarifs
(`super_sayan`, `sayan`, `normal`), et Postgres trie un enum dans son ordre de
déclaration : `ORDER BY role` donne donc le meilleur billet en premier, sans
`CASE WHEN`.
