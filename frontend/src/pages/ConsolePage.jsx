/**
 * Le poste de l'admin : par attraction, les visiteurs appelés et les deux
 * décisions possibles. Reprend `console/console.html`.
 */
import { useState } from 'react'

import { acceptEntry, listConsole, refuseEntry } from '../api/console'
import Alert from '../components/Alert'
import CapacityBadge from '../components/CapacityBadge'
import EmptyState from '../components/EmptyState'
import RoleBadge from '../components/RoleBadge'
import { useApi } from '../hooks/useApi'
import { formatTime, timeSince } from '../utils/format'

export default function ConsolePage() {
  const { data: rows, loading, error, reload } = useApi(listConsole)
  const [feedback, setFeedback] = useState(null)

  async function runAction(action, successMessage) {
    try {
      await action()
      setFeedback({ type: 'success', message: successMessage })
      await reload()
    } catch (err) {
      setFeedback({ type: 'error', message: err.message })
    }
  }

  if (loading) {
    return <EmptyState icon="bi-hourglass-split">Chargement de la console…</EmptyState>
  }

  return (
    <>
      <h1 className="page-title h4">Console</h1>
      <p className="page-subtitle">
        Les visiteurs appelés, attraction par attraction : à vous de les faire entrer ou de leur
        rendre leur place.
      </p>

      <Alert message={feedback?.message} type={feedback?.type} />
      {error && <Alert message={error} type="error" />}

      {rows?.map((row) => (
        <div className="park-card" key={row.attraction.id}>
          <h2>
            <i className="bi bi-rocket-takeoff" />
            {row.attraction.name}
            <span className="console-facts ms-auto">
              <CapacityBadge icon="bi-people-fill">
                {row.inside}/{row.attraction.max_people}
              </CapacityBadge>
              <CapacityBadge icon="bi-hourglass-split">{row.waiting} en attente</CapacityBadge>
            </span>
          </h2>

          {row.ready.length > 0 ? (
            <div className="table-responsive">
              <table className="table align-middle console-table mb-0">
                <thead>
                  <tr>
                    <th>Visiteur</th>
                    <th>Billet</th>
                    <th>Rôle</th>
                    <th>Appelé à</th>
                    <th>Depuis</th>
                    <th className="text-end">Décision</th>
                  </tr>
                </thead>
                <tbody>
                  {row.ready.map((entry) => (
                    <tr key={entry.id} className={entry.ready_expired ? 'console-expired' : ''}>
                      <td>{entry.username}</td>
                      <td>
                        <strong>#{entry.ticket.numero}</strong>
                      </td>
                      <td>
                        <RoleBadge ticket={entry.ticket} withIcon={false} />
                      </td>
                      <td>{formatTime(entry.ready_at)}</td>
                      <td>
                        {timeSince(entry.ready_at)}
                        <span className="console-tolerance">
                          tolérance {entry.max_seconds_allowing_ready} s
                        </span>
                        {entry.ready_expired && (
                          <span className="expired-tag">
                            <i className="bi bi-hourglass-bottom" />
                            délai dépassé
                          </span>
                        )}
                      </td>
                      <td className="text-end console-actions">
                        <button
                          type="button"
                          className="btn btn-park btn-sm"
                          onClick={() =>
                            runAction(
                              () => acceptEntry(entry.id),
                              `#${entry.ticket.numero} est entré dans ${row.attraction.name}.`,
                            )
                          }
                        >
                          <i className="bi bi-check2-circle" />
                          Accepter
                        </button>
                        <button
                          type="button"
                          className="btn btn-park-ghost btn-sm"
                          onClick={() =>
                            runAction(
                              () => refuseEntry(entry.id),
                              `La place de #${entry.ticket.numero} a été retirée.`,
                            )
                          }
                        >
                          <i className="bi bi-x-circle" />
                          Refuser
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState icon="bi-bell-slash">Personne d'appelé sur cette attraction.</EmptyState>
          )}
        </div>
      ))}

      {rows?.length === 0 && (
        <div className="park-card">
          <EmptyState icon="bi-rocket-takeoff">Aucune attraction pour l'instant.</EmptyState>
        </div>
      )}
    </>
  )
}
