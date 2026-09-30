/** Les appels liés au compte. */
import { api, setToken } from './client'
import { endpoints } from './endpoints'

export async function login(credentials) {
  const data = await api.post(endpoints.login, credentials)
  setToken(data.token)
  return data.user
}

export async function signup(form) {
  const data = await api.post(endpoints.signup, form)
  setToken(data.token)
  return data.user
}

/**
 * Se déconnecter, c'est oublier son jeton : c'est un JWT signé que le back ne
 * garde nulle part, il n'y a donc rien à lui demander.
 */
export function logout() {
  setToken(null)
}

/** Qui est connecté, d'après le jeton gardé. Sert au rechargement de la page. */
export function me() {
  return api.get(endpoints.me)
}
