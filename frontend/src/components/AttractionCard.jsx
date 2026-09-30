/**
 * La carte d'une attraction : sa photo, ses deux faits, puis le panneau du bas.
 *
 * Ce panneau porte l'un des cinq cas, dans le même ordre que le gabarit
 * Django : le visiteur est à l'intérieur, il est appelé, son tour est passé,
 * il attend — ou bien il peut rejoindre la file. `entry` et `visit` viennent
 * de `GET /queue/`, recollés à l'attraction par `listAttractionCards`.
 */
import CapacityBadge from './CapacityBadge'
import { formatDuration, formatTime } from '../utils/format'

// La photo par défaut, quand l'attraction n'a pas encore la sienne.
const DEFAULT_PHOTO = '/attraction-default.svg'

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
  const { visit, entry } = card

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
              {formatTime(entry.ready_at)}.
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
              {formatTime(entry.joined_at)} — {entry.position}
              <sup>e</sup> position.
            </p>
            <LeaveButton onLeave={onLeave} />
          </div>
        )}

        {/* 5. Rien en cours : il peut rejoindre. Sans billet libre, le back le dira. */}
        {!visit && !entry && (
          <div className="queue-join">
            <button type="button" className="btn btn-park btn-sm w-100" onClick={onJoin}>
              <i className="bi bi-hourglass-split" />
              Rejoindre la file
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
