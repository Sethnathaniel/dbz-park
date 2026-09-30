/**
 * Les mises en forme de dates que faisaient les filtres de gabarit Django
 * (`|time:"H:i"`, `|date:"d/m/Y à H:i"`, `|timesince`). Le back envoie des
 * dates ISO, le front les écrit en français.
 */

/** « 14:05 » — l'heure d'un appel ou d'une entrée. */
export function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

/** « 17/09/2026 à 14:05 » — la date d'assignation d'un billet. */
export function formatDateTime(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  return `${date.toLocaleDateString('fr-FR')} à ${formatTime(iso)}`
}

/** « 3 minutes » — depuis combien de temps un visiteur est appelé. */
export function timeSince(iso) {
  if (!iso) return ''
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return `${seconds} secondes`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''}`
  const hours = Math.floor(minutes / 60)
  return `${hours} heure${hours > 1 ? 's' : ''}`
}

// Les tarifs que le parc vend aujourd'hui. Le back accepte n'importe quel rôle :
// un rôle inconnu s'affiche tel quel plutôt que de disparaître.
const ROLE_LABELS = { normal: 'Normal', sayan: 'Saiyan', super_sayan: 'Super Saiyan' }

/** « Super Saiyan » — le libellé d'un rôle, que le back ne fournit plus. */
export function roleLabel(role) {
  return ROLE_LABELS[role] ?? role
}

/** « 2 min », « 1 min 30 s » — la durée d'un tour, que le back envoie en secondes. */
export function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60)
  const rest = seconds % 60
  if (minutes && rest) return `${minutes} min ${rest} s`
  if (minutes) return `${minutes} min`
  return `${rest} s`
}
