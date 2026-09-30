/** Le catalogue des attractions et les gestes sur une file. */
import { api } from './client'
import { endpoints } from './endpoints'
import { USE_MOCK, mock } from './mock'

/**
 * Les attractions, chacune avec ce que le visiteur y a en cours.
 *
 * Le back sépare les deux — le catalogue (`GET /attractions/`) d'un côté, les
 * places et présences du visiteur (`GET /queue/`) de l'autre — et c'est ici
 * qu'on les recolle, sur `attraction_id`. La carte reçoit donc `entry`, `visit`
 * et `position`, sans savoir qu'il a fallu deux appels.
 */
export async function listAttractionCards() {
  const [attractions, mine] = await Promise.all([
    USE_MOCK ? mock.attractions() : api.get(endpoints.attractions),
    USE_MOCK ? mock.myQueue() : api.get(endpoints.myQueue),
  ])
  return attractions.map((attraction) => {
    const entry = mine.entries.find((e) => e.attraction_id === attraction.id) ?? null
    return {
      ...attraction,
      entry,
      visit: mine.visits.find((v) => v.attraction_id === attraction.id) ?? null,
      position: entry?.position ?? null,
    }
  })
}

export function joinQueue(attractionId) {
  return USE_MOCK ? mock.joinQueue(attractionId) : api.post(endpoints.joinQueue(attractionId))
}

/**
 * Le rang d'une place, recalculé à la volée. Le front l'interroge seul, sans
 * recharger toute la liste des attractions : c'est ce qui permet de rafraîchir
 * l'attente toutes les quelques secondes sans faire travailler le back pour rien.
 */
export function queuePosition(entryId) {
  return USE_MOCK ? mock.queuePosition(entryId) : api.get(endpoints.queuePosition(entryId))
}

export function leaveQueue(entryId) {
  return USE_MOCK ? mock.leaveQueue(entryId) : api.post(endpoints.leaveQueue(entryId))
}

export function validateQueue(entryId) {
  return USE_MOCK ? mock.validateQueue(entryId) : api.post(endpoints.validateQueue(entryId))
}
