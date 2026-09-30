/**
 * Les appels liés au compte.
 *
 * Chaque fonction a la même forme : si on est en mode maquette, elle répond
 * depuis `mock`, sinon elle part pour de vrai. C'est le seul `if` à retirer
 * quand le back sera branché pour de bon.
 */
import { api, setToken } from './client'
import { endpoints } from './endpoints'
import { USE_MOCK, mock } from './mock'

export async function login(credentials) {
  const data = USE_MOCK ? await mock.login(credentials) : await api.post(endpoints.login, credentials)
  setToken(data.token)
  return data.user
}

export async function signup(form) {
  const data = USE_MOCK ? await mock.signup(form) : await api.post(endpoints.signup, form)
  setToken(data.token)
  return data.user
}

/**
 * Se déconnecter, c'est oublier le jeton : le back n'a pas de route pour ça,
 * donc aucun appel réseau — et rien qui puisse échouer avant d'oublier.
 */
export async function logout() {
  setToken(null)
}

/** Qui est connecté, d'après le jeton gardé. Sert au rechargement de la page. */
export function me() {
  return USE_MOCK ? mock.me() : api.get(endpoints.me)
}
