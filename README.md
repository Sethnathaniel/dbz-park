# Dragon Ball Park

## Lancer l'application

```bash
cp .env.example .env        # puis changer POSTGRES_PASSWORD et JWT_SECRET
docker compose up -d --build
```

L'app répond sur **http://localhost:8080** (`FRONT_PORT` dans `.env`). Trois
conteneurs : `db` (Postgres), `backend` (FastAPI, qui applique les migrations à
son démarrage), `frontend` (nginx, qui sert le front et fait suivre `/api` au
back — une seule origine pour le navigateur, donc pas de CORS).

Au premier démarrage le back crée un compte `admin` / `admin` et 30 billets
libres. Aucune route ne crée d'attraction : il faut, pour l'instant, les insérer
dans la base.

Pour développer, on ne lance que la base (`docker compose up -d db`) et on suit
`backend/README.md` et `frontend/README.md`. Le contrat entre les deux est dans
[`API.md`](API.md).

---

> La suite décrit l'ancienne version Django du projet, remplacée par `backend/`
> et `frontend/`.

Application Django de billetterie pour un parc d'attractions Dragon Ball Z.

Structure de code reprise de `bonjour_plant` : un projet `core/` (settings,
urls) et une app `park_management/` organisée en pages (`pages/<nom>/` avec
`urls.py`, `views.py`, `forms.py`).

Le style suit la même approche : Bootstrap et Bootstrap Icons servis depuis
`static/` (pas de CDN), plus une feuille `dbz-park.css` qui pose les couleurs du
parc. Le gabarit `park_management/templates/park_management/index.html` porte
l'en-tête et le menu du compte, en haut à droite ; toutes les pages en héritent.

## Lancement

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Fonctionnalités actuelles

- Un visiteur peut créer un compte (`/compte/inscription/`) et se connecter (`/compte/connexion/`).
- **Mes billets** (`/`) : les billets ne sont pas créés ici. La billetterie les écrit
  dans la même base, le visiteur en reçoit le numéro par mail, et cette page ne fait
  que rattacher un billet libre à son compte — un numéro, et rien d'autre. Le rôle
  (`normal`, `sayan`, `super_sayan`) est fixé à l'achat et suit le billet.
  Un numéro inconnu ou déjà pris est refusé, sans dire par qui.
- **Attractions** (`/attractions/`) : les attractions du parc, avec leur photo (une
  illustration par défaut si elle manque), leur capacité maximale, la durée d'un tour
  (`min_duration`, `max_duration`) et le monde qu'elles portent en ce moment. Ce
  dernier chiffre n'est pas stocké : il se compte sur les présences.
- **File d'attente virtuelle** (`QueueEntry`) : une place tenue par un billet sur une
  attraction. On garde la date d'inscription (`joined_at`, qui donne aussi le rang
  dans la file), l'état prêt (`is_ready`) et l'heure à laquelle il est passé prêt
  (`ready_at`). L'attraction porte la tolérance de cet état prêt, en secondes
  (`max_ready_waiting`) : au-delà, le billet a laissé passer son tour et sa place est
  à donner à un autre (`ready_expired()`, `Attraction.expired_ready_entries()`).
  La table ne tient que la file du moment : une place disparaît quand son porteur
  entre ou se désiste, d'où un billet au plus par attraction.
  Depuis la page des attractions, le visiteur rejoint une file (`join_queue`), la
  quitte quand il veut (`leave_queue`), et valide sa place une fois appelé
  (`validate_queue_entry`) : la place est alors supprimée et une présence prend le
  relais, dans la même transaction. Le billet joué n'est pas demandé : on prend le
  meilleur rôle parmi ceux qui restent (super saiyan, puis saiyan, puis normal —
  `Billet.objects.best_role_first()`).
- **Présences** (`AttractionVisit`) : qui se trouve dans l'attraction et depuis quand
  (`entered_at`). Là aussi, rien que le présent : la ligne est écrite à l'entrée et
  effacée à la sortie, donc la table est la liste de ceux qui sont à l'intérieur.
  Rien n'appelle encore les billets (`is_ready` se pose depuis `/admin/` ou le shell) :
  c'est le travail de l'attraction, pas de l'interface visiteur.
- **Console** (`/console/`) : réservée aux comptes admin (`is_staff`). Elle liste, par
  attraction, les visiteurs appelés — qui, quel billet, quel rôle, depuis combien de
  temps, et si le délai de tolérance est dépassé — avec deux décisions : **Accepter**
  (le visiteur entre, sa place quitte la file) ou **Refuser** (la place est retirée).
  Un visiteur connecté qui tente d'y accéder reçoit un 403.
  Rien n'appelle encore les billets (`is_ready`) : cela se pose depuis `/admin/` ou le
  shell, en attendant que l'attraction le fasse elle-même.
- Les comptes admin ont aussi accès à `/admin/` (`python manage.py createsuperuser`).

Pour se donner de quoi essayer, `/admin/` permet de créer des billets libres (numéro
+ rôle, sans visiteur) et des attractions, comme le ferait la billetterie.
