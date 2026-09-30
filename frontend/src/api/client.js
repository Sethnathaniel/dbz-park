/**
 * Le seul endroit du front qui parle réellement au réseau.
 *
 * Tout passe par `api.get` et `api.post` : ils ajoutent la racine de l'API,
 * le jeton d'authentification, et transforment une réponse en erreur ou en
 * données. Les pages, elles, n'ont jamais à connaître `fetch`.
 */

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const TOKEN_KEY = 'dbz-park-token'

// ── Le jeton ────────────────────────────────────────────────────────────────
// On garde un jeton plutôt qu'un cookie de session : le back reste sans état,
// donc n'importe quel serveur derrière le load balancer peut répondre.

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

// ── L'erreur que le front sait afficher ─────────────────────────────────────

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

// ── L'appel ─────────────────────────────────────────────────────────────────

async function request(path, { method = 'GET', body } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  let response
  try {
    response = await fetch(BASE_URL + path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    // Le serveur n'a pas répondu du tout : coupure réseau, back éteint.
    throw new ApiError("Le serveur ne répond pas.", 0)
  }

  // Le contrat ne connaît que deux réponses : 200, et 400 avec un `detail`.
  // Un 200 peut n'avoir aucun corps (rejoindre une file, quitter une file) : le
  // `catch` le ramène alors à `null`, ce que les appelants savent lire.
  const data = await response.json().catch(() => null)

  if (!response.ok) {
    // Le back renvoie son explication dans `detail` ; sinon un texte générique.
    throw new ApiError(data?.detail || "La requête a échoué.", response.status)
  }

  return data
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body }),
}
