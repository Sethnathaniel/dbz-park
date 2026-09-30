/** Les billets : les lire, en acheter un, en rattacher un. */
import { api } from './client'
import { endpoints } from './endpoints'
import { USE_MOCK, mock } from './mock'

/** Les billets d'un visiteur — les siens, ou n'importe lesquels pour le staff. */
export function listTickets(userId) {
  return USE_MOCK ? mock.userTickets(userId) : api.get(endpoints.userTickets(userId))
}

/** Tous les billets du parc, avec leur détenteur. Réservé au staff. */
export function listAllTickets() {
  return USE_MOCK ? mock.allTickets() : api.get(endpoints.tickets)
}

/** Achète un billet depuis l'application : il est aussitôt à vous, et utilisable. */
export function buyTicket(role) {
  return USE_MOCK ? mock.buyTicket({ role }) : api.post(endpoints.tickets, { role })
}

/** Rattache au compte un billet acheté ailleurs (guichet, site), par son numéro. */
export function assignTicket(numero) {
  return USE_MOCK ? mock.assignTicket({ numero }) : api.post(endpoints.assignTicket, { numero })
}
