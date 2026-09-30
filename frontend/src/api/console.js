/** Le poste de l'admin : qui est appelé, les deux décisions possibles, et les incidents. */
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

/** Met l'attraction hors service : sa file se met en pause, personne ne perd sa place. */
export function declareIncident(attractionId, reason) {
  return USE_MOCK
    ? mock.declareIncident(attractionId, reason)
    : api.post(endpoints.declareIncident(attractionId), { reason })
}

export function resumeAttraction(attractionId) {
  return USE_MOCK
    ? mock.resumeAttraction(attractionId)
    : api.post(endpoints.resumeAttraction(attractionId))
}
