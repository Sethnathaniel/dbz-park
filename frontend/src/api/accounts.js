/** La gestion des comptes, réservée au staff : chercher, modifier, supprimer. */
import { api } from './client'
import { endpoints } from './endpoints'
import { USE_MOCK, mock } from './mock'

/** Les comptes dont le nom ou l'e-mail contient `search`. Vide : les premiers du parc. */
export function searchAccounts(search) {
  return USE_MOCK ? mock.searchAccounts(search) : api.get(endpoints.accounts(search))
}

/** `changes` : `{ username, email, is_staff }`. Le mot de passe reste celui du visiteur. */
export function updateAccount(userId, changes) {
  return USE_MOCK
    ? mock.updateAccount(userId, changes)
    : api.post(endpoints.updateAccount(userId), changes)
}

/** Ses places en file disparaissent ; ses billets restent dans le parc, sans détenteur. */
export function deleteAccount(userId) {
  return USE_MOCK ? mock.deleteAccount(userId) : api.post(endpoints.deleteAccount(userId))
}

/** Invalide un billet à la main : il quitte ses files et ne peut plus en rejoindre. */
export function revokeTicket(ticketId) {
  return USE_MOCK
    ? mock.setTicketValidity(ticketId, false)
    : api.post(endpoints.revokeTicket(ticketId))
}

export function restoreTicket(ticketId) {
  return USE_MOCK
    ? mock.setTicketValidity(ticketId, true)
    : api.post(endpoints.restoreTicket(ticketId))
}

/** Invalide un billet valide, rétablit un billet invalidé. */
export function toggleTicketValidity(ticket) {
  return ticket.is_valid ? revokeTicket(ticket.id) : restoreTicket(ticket.id)
}
