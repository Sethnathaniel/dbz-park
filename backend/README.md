# Backend — FastAPI

L'API du parc. Le contrat qu'elle doit respecter est à la racine, dans
[`../API.md`](../API.md) : **deux réponses possibles, `200` et `400`**, et pour
un `400` un corps `{"detail": "…"}` que le front affiche tel quel.

## Lancer

Copier `../.env.example` en `../.env`, puis, depuis la racine :

```bash
docker compose up -d db     # la base seule : le back, on le lance à la main
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

- **pas de compte `admin`** → elle le crée, staff, avec le mot de passe `password`. Il est
  en dur : c'est un confort de développement, à changer avant de sortir d'ici.
- **aucun billet** → elle en crée 30, dix par rôle, non assignés (`DBZ-0001` à `DBZ-0030`).

La vérification porte sur le **nom** `admin`, pas sur l'existence d'un staff quelconque :
un autre compte staff n'empêche pas sa création. À l'inverse, un `admin` qui existe déjà
n'est jamais retouché — son mot de passe survit aux redémarrages, même s'il n'est plus
`password`. Si ce nom a été pris par un visiteur, l'API **ne le promeut pas** (cela
donnerait la console au premier qui a réservé le nom) : elle le signale dans les logs.

Les billets, eux, sont tout ou rien : l'API regarde si la table contient *quelque chose*,
donc elle ne discute jamais avec des billets créés ensuite. Le tout sous un verrou
consultatif Postgres, pour que plusieurs workers lancés en même temps ne créent pas les
mêmes lignes deux fois.

## Le worker

Appeler un visiteur n'est pas une route : c'est un worker **Celery**, hors du cycle
HTTP. Celery beat déclenche la tâche toutes les `CALLING_INTERVAL_SECONDS` (5 s), le
worker l'exécute (`app/worker.py`), et Redis sert de broker entre les deux. La règle
elle-même est dans `app/calling.py`, testée à part (`tests/test_calling.py`) :

- d'abord, les appelés qui ont dépassé `max_seconds_allowing_ready` sont **retirés de la
  file** (le « no-show » du SPEC) : leur billet redevient libre ;
- ensuite, places libres = `max_people` − `people_inside` − appelés restants, et autant de
  places en attente passent `ready` : Super Sayan d'abord, puis Saiyan, puis humains
  (`normal`), et à tarif égal le premier arrivé. Cet ordre vit dans `app/priority.py`, et
  sert aussi à la position affichée et au billet choisi pour entrer en file.

Les deux dans la même transaction : une place libérée par un absent part au suivant dans
le même passage. « Trop tard » n'a qu'une définition, `QueueEntry.ready_expired()`,
partagée avec l'API.

Le tout sous un verrou consultatif Postgres, pour que deux workers ne puissent pas
appeler deux fois les mêmes visiteurs. Il tourne dans son propre conteneur :

```bash
docker compose up -d --build worker     # démarre aussi redis, db et backend
docker compose logs -f worker           # « dropped 1 expired call(s), called 2 visitor(s) »
```

**Temporaire** : le même worker fait tourner une seconde tâche, `app/temporary_exits.py`,
qui fait sortir tout visiteur entré depuis 30 s ou plus et baisse `people_inside` d'autant,
comme s'il avait fini son tour. Elle remplace la route de sortie qui n'existe pas encore.
Pour la retirer : supprimer le fichier, et ses deux lignes dans `app/worker.py`.

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
├── calling.py     appeler les visiteurs suivants quand des places se libèrent.
├── worker.py      l'app Celery qui fait tourner calling.py toutes les 5 s.
├── priority.py    l'ordre des tarifs : qui est appelé en premier.
├── temporary_exits.py  temporaire : fait sortir les visiteurs après 30 s.
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
