/** Les billets du visiteur : les lire, en acheter un, en rattacher un. */
import { api } from './client'
import { endpoints } from './endpoints'

export function listTickets(userId) {
  return api.get(endpoints.userTickets(userId))
}

/** Achète un billet depuis l'application : il est utilisable aussitôt. */
export function buyTicket(role) {
  return api.post(endpoints.tickets, { role })
}

/** Rattache au compte un billet acheté ailleurs (guichet, site), par son numéro. */
export function assignTicket(numero) {
  return api.post(endpoints.assignTicket, { numero })
}
