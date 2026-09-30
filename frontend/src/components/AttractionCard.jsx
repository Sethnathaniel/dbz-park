/**
 * La carte d'une attraction : sa photo, ses deux faits, puis le panneau du bas.
 *
 * Ce panneau porte l'un des quatre cas, dans l'ordre où le contrat les donne :
 * le visiteur est à l'intérieur, il est appelé, son tour est passé, il attend —
 * ou bien il peut rejoindre la file.
 */
import { useEffect, useState } from 'react'

import CapacityBadge from './CapacityBadge'
import { queuePosition } from '../api/attractions'
import { formatDuration, formatTime } from '../utils/format'

// La photo par défaut, quand l'attraction n'a pas encore la sienne.
const DEFAULT_PHOTO = '/attraction-default.svg'

// Toutes les 10 s : assez pour voir la file avancer, assez peu pour ne pas
// marteler le back avec une carte par attraction.
const POSITION_REFRESH_MS = 10_000

/**
 * Le rang du visiteur, rafraîchi tout seul pendant qu'il attend.
 *
 * La liste des attractions donne déjà un rang au chargement ; ensuite, plutôt
 * que de la recharger entière, on ne redemande que ce qui bouge : le rang
 * baisse à mesure que ceux de devant sont appelés ou quittent la file.
 */
function useLivePosition(entry, initialPosition) {
  const [position, setPosition] = useState(initialPosition)

  // Une nouvelle liste d'attractions fait autorité sur ce qu'on affichait.
  useEffect(() => setPosition(initialPosition), [initialPosition])

  const entryId = entry?.id
  const waiting = Boolean(entryId) && !entry.is_ready

  useEffect(() => {
    if (!waiting) return undefined

    let cancelled = false
    const tick = () =>
      queuePosition(entryId)
        .then((data) => {
          if (!cancelled) setPosition(data.position)
        })
        // Un rang qui ne revient pas n'est pas une raison d'alerter le
        // visiteur : on garde le dernier connu jusqu'au prochain essai.
        .catch(() => {})

    const timer = setInterval(tick, POSITION_REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [entryId, waiting])

  return position
}

/** Le bouton de sortie de file, le même dans les trois états d'une place. */
function LeaveButton({ onLeave }) {
  return (
    <button type="button" className="btn btn-park-ghost btn-sm w-100 mt-2" onClick={onLeave}>
      <i className="bi bi-box-arrow-left" />
      Quitter la file
    </button>
  )
}

export default function AttractionCard({ card, onJoin, onLeave, onValidate }) {
  // `visit`, `entry` et `position` viennent de `GET /queue/`, recollés au
  // catalogue par `listAttractionCards`.
  const { visit, entry } = card
  const position = useLivePosition(entry, card.position)

  return (
    <div className="attraction-card">
      <img
        className="attraction-photo"
        src={card.photo_url || DEFAULT_PHOTO}
        alt={card.name}
      />

      <div className="attraction-body">
        <h2 className="attraction-name">{card.name}</h2>

        <div className="attraction-facts">
          <CapacityBadge icon="bi-people-fill">
            {card.people_inside}/{card.max_people}
          </CapacityBadge>
          <CapacityBadge icon="bi-stopwatch">{formatDuration(card.avg_duration)}</CapacityBadge>
        </div>

        {/* 1. Le visiteur est dans l'attraction. */}
        {visit && (
          <div className="queue-panel queue-inside">
            <p className="queue-line">
              <i className="bi bi-person-check-fill" />
              Vous êtes à l'intérieur avec le billet <strong>#{visit.ticket.numero}</strong>, depuis{' '}
              {formatTime(visit.entered_at)}.
            </p>
          </div>
        )}

        {/* 2. Il est appelé, et le délai n'est pas passé. */}
        {!visit && entry?.is_ready && !entry.ready_expired && (
          <div className="queue-panel queue-ready">
            <p className="queue-line">
              <i className="bi bi-bell-fill" />
              C'est à vous — billet <strong>#{entry.ticket.numero}</strong>, appelé à{' '}
              {formatTime(entry.ready_at)}. Vous avez {entry.max_seconds_allowing_ready} secondes
              pour vous présenter.
            </p>
            <button type="button" className="btn btn-park btn-sm w-100" onClick={onValidate}>
              <i className="bi bi-check2-circle" />
              Valider ma place
            </button>
            <LeaveButton onLeave={onLeave} />
          </div>
        )}

        {/* 3. Il a laissé passer son tour. */}
        {!visit && entry?.is_ready && entry.ready_expired && (
          <div className="queue-panel queue-expired">
            <p className="queue-line">
              <i className="bi bi-hourglass-bottom" />
              Votre tour est passé : la place du billet <strong>#{entry.ticket.numero}</strong>{' '}
              revient à la file.
            </p>
            <LeaveButton onLeave={onLeave} />
          </div>
        )}

        {/* 4. Il attend son tour. */}
        {!visit && entry && !entry.is_ready && (
          <div className="queue-panel queue-waiting">
            <p className="queue-line">
              <i className="bi bi-hourglass-split" />
              Billet <strong>#{entry.ticket.numero}</strong> dans la file depuis{' '}
              {formatTime(entry.joined_at)} — {position}
              <sup>e</sup> position.
            </p>
            <LeaveButton onLeave={onLeave} />
          </div>
        )}

        {/* 5. Rien en cours : il peut rejoindre. Le back choisit le billet. */}
        {!visit && !entry && (
          <div className="queue-join">
            <button type="button" className="btn btn-park btn-sm w-100" onClick={onJoin}>
              <i className="bi bi-hourglass-split" />
              Rejoindre la file
            </button>
            <p className="queue-note">Votre premier billet libre sera utilisé.</p>
          </div>
        )}
      </div>
    </div>
  )
}
