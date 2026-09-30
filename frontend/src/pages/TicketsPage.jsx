/**
 * « Mes billets » : le formulaire d'assignation à gauche, la liste à droite.
 * Reprend `tickets/tickets.html`.
 */
import { useCallback, useState } from 'react'

import { assignTicket, listTickets } from '../api/tickets'
import { useAuth } from '../auth/AuthContext'
import Alert from '../components/Alert'
import EmptyState from '../components/EmptyState'
import RoleBadge from '../components/RoleBadge'
import { useApi } from '../hooks/useApi'
import { formatDateTime } from '../utils/format'

export default function TicketsPage() {
  const { user } = useAuth()
  // Stable tant que le visiteur ne change pas : sinon `useApi` rechargerait en boucle.
  const fetchTickets = useCallback(() => listTickets(user.id), [user.id])
  const { data: billets, loading, error, reload } = useApi(fetchTickets)

  const [numero, setNumero] = useState('')
  const [feedback, setFeedback] = useState(null)

  async function handleSubmit(event) {
    event.preventDefault()
    try {
      const billet = await assignTicket(numero)
      setFeedback({ type: 'success', message: `Le billet #${billet.numero} est à vous.` })
      setNumero('')
      reload() // la liste doit montrer le billet qui vient d'arriver
    } catch (err) {
      setFeedback({ type: 'error', message: err.message })
    }
  }

  return (
    <>
      <h1 className="page-title h4">Mes billets</h1>
      <p className="page-subtitle">
        Saisissez le numéro reçu par mail pour rattacher le billet à votre compte.
      </p>

      <Alert message={feedback?.message} type={feedback?.type} />

      <div className="row g-4">
        <div className="col-lg-5">
          <div className="park-card">
            <h2>
              <i className="bi bi-envelope-paper" /> Assigner un billet
            </h2>

            <form onSubmit={handleSubmit} noValidate>
              <div className="mb-3">
                <label className="form-label" htmlFor="numero">
                  Numéro du billet
                </label>
                <input
                  id="numero"
                  className="form-control"
                  value={numero}
                  onChange={(event) => setNumero(event.target.value)}
                  placeholder="DBZ-0001"
                />
              </div>

              <button type="submit" className="btn btn-park">
                <i className="bi bi-ticket-perforated" />
                Assigner
              </button>
            </form>

            <p className="form-text mt-3 mb-0">
              Le rôle du billet est fixé à l'achat : il vous suit tel quel une fois le billet
              assigné.
            </p>
          </div>
        </div>

        <div className="col-lg-7">
          <div className="park-card">
            <h2>
              <i className="bi bi-collection" />
              Mes billets
              <span className="badge rounded-pill text-bg-light ms-auto">
                {billets?.length ?? 0}
              </span>
            </h2>

            {loading && <EmptyState icon="bi-hourglass-split">Chargement…</EmptyState>}
            {error && <Alert message={error} type="error" />}

            {billets?.map((billet) => (
              <div key={billet.id} className={`ticket-card ticket-${billet.role}`}>
                <div>
                  <span className="ticket-numero">#{billet.numero}</span>
                  <span className="ticket-date">
                    Émis le {formatDateTime(billet.created_at)}
                  </span>
                </div>
                <RoleBadge ticket={billet} />
              </div>
            ))}

            {billets?.length === 0 && (
              <EmptyState icon="bi-ticket-detailed">Aucun billet pour l'instant.</EmptyState>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
