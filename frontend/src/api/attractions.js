/** Le catalogue des attractions et les trois gestes sur une file. */
import { api } from './client'
import { endpoints } from './endpoints'

/**
 * Les attractions, chacune avec ce que le visiteur y a en cours.
 *
 * Le back sépare les deux — le catalogue d'un côté, les places et présences du
 * visiteur de l'autre — et c'est ici qu'on les recolle, sur `attraction_id`.
 * Les pages reçoivent donc une carte complète, sans savoir qu'il a fallu deux
 * appels.
 */
export async function listAttractionCards() {
  const [attractions, mine] = await Promise.all([
    api.get(endpoints.attractions),
    api.get(endpoints.myQueue),
  ])
  return attractions.map((attraction) => ({
    ...attraction,
    entry: mine.entries.find((entry) => entry.attraction_id === attraction.id) ?? null,
    visit: mine.visits.find((visit) => visit.attraction_id === attraction.id) ?? null,
  }))
}

export function joinQueue(attractionId) {
  return api.post(endpoints.joinQueue(attractionId))
}

export function leaveQueue(entryId) {
  return api.post(endpoints.leaveQueue(entryId))
}

export function validateQueue(entryId) {
  return api.post(endpoints.validateQueue(entryId))
}
