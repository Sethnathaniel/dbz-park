/** Le poste de l'admin : qui est appelé, et les deux décisions possibles. */
import { api } from './client'
import { endpoints } from './endpoints'

export function listConsole() {
  return api.get(endpoints.console)
}

export function acceptEntry(entryId) {
  return api.post(endpoints.acceptEntry(entryId))
}

export function refuseEntry(entryId) {
  return api.post(endpoints.refuseEntry(entryId))
}
