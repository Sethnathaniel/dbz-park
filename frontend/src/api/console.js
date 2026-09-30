/** Le poste de l'admin : qui est appelé, et les deux décisions possibles. */
import { api } from './client'
import { endpoints } from './endpoints'
import { USE_MOCK, mock } from './mock'

export function listConsole() {
  return USE_MOCK ? mock.console() : api.get(endpoints.console)
}

export function acceptEntry(entryId) {
  return USE_MOCK ? mock.acceptEntry(entryId) : api.post(endpoints.acceptEntry(entryId))
}

export function refuseEntry(entryId) {
  return USE_MOCK ? mock.refuseEntry(entryId) : api.post(endpoints.refuseEntry(entryId))
}
