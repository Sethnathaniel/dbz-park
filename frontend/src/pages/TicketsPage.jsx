/**
 * « Mes billets » : à gauche l'achat et l'assignation, à droite la liste.
 *
 * Un billet acheté ici est aussitôt à vous et utilisable dans les files. Le
 * staff voit en plus, en bas, tous les billets du parc et leur détenteur.
 */
import { useCallback, useState } from 'react'

import { useAuth } from '../auth/AuthContext'
import { assignTicket, buyTicket, listAllTickets, listTickets } from '../api/tickets'
import Alert from '../components/Alert'
import EmptyState from '../components/EmptyState'
import RoleBadge from '../components/RoleBadge'
import { useApi } from '../hooks/useApi'
import { formatDateTime } from '../utils/format'
import { ROLES } from '../utils/roles'

export default function TicketsPage() {
  const { user } = useAuth()
  // `useApi` veut une fonction stable : sans useCallback, l'appel repartirait
  // à chaque rendu.
  const fetchMine = useCallback(() => listTickets(user.id), [user.id])
  const { data: tickets, loading, error, reload } = useApi(fetchMine)

  const [role, setRole] = useState('normal')
  const [numero, setNumero] = useState('')
  const [busy, setBusy] = useState(false)
  const [feedback, setFeedback] = useState(null)

  async function handleBuy(event) {
    event.preventDefault()
    setBusy(true)
    try {
      const ticket = await buyTicket(role)
      setFeedback({ type: 'success', message: `Le billet #${ticket.numero} est à vous.` })
      await reload()
    } catch (err) {
      setFeedback({ type: 'error', message: err.message })
    } finally {
      setBusy(false)
    }
  }

  async function handleAssign(event) {
    event.preventDefault()
    try {
      const ticket = await assignTicket(numero)
      setFeedback({ type: 'success', message: `Le billet #${ticket.numero} est à vous.` })
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
        Achetez un billet, ou rattachez à votre compte celui que vous avez reçu par mail.
      </p>

      <Alert message={feedback?.message} type={feedback?.type} />

      <div className="row g-4">
        <div className="col-lg-5">
          <div className="park-card">
            <h2>
              <i className="bi bi-bag-plus" /> Acheter un billet
            </h2>

            <form onSubmit={handleBuy} noValidate>
              <div className="mb-3">
                <label className="form-label" htmlFor="role">
                  Type de billet
                </label>
                <select
                  id="role"
                  className="form-select"
                  value={role}
                  onChange={(event) => setRole(event.target.value)}
                >
                  {ROLES.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <button type="submit" className="btn btn-park" disabled={busy}>
                <i className="bi bi-cart-check" />
                {busy ? 'Achat…' : 'Acheter'}
              </button>
            </form>

            <p className="form-text mt-3 mb-0">
              Le rôle est fixé à l'achat. Les files, elles, suivent l'ordre d'arrivée.
            </p>
          </div>

          <div className="park-card">
            <h2>
              <i className="bi bi-envelope-paper" /> Assigner un billet
            </h2>

            <form onSubmit={handleAssign} noValidate>
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
                {tickets?.length ?? 0}
              </span>
            </h2>

            {loading && <EmptyState icon="bi-hourglass-split">Chargement…</EmptyState>}
            {error && <Alert message={error} type="error" />}

            {tickets?.map((ticket) => (
              <div key={ticket.id} className={`ticket-card ticket-${ticket.role}`}>
                <div>
                  <span className="ticket-numero">#{ticket.numero}</span>
                  <span className="ticket-date">
                    {ticket.created_at && `Acheté le ${formatDateTime(ticket.created_at)}`}
                  </span>
                </div>

                <div className="ticket-side">
                  <RoleBadge ticket={ticket} />
                </div>
              </div>
            ))}

            {tickets?.length === 0 && (
              <EmptyState icon="bi-ticket-detailed">Aucun billet pour l'instant.</EmptyState>
            )}
          </div>
        </div>
      </div>

      {user.is_staff && <AllTickets />}
    </>
  )
}

/** Tous les billets du parc et qui les détient — ce que le guichet consulte. */
function AllTickets() {
  const { data: tickets, loading, error } = useApi(listAllTickets)

  return (
    <div className="park-card mt-4">
      <h2>
        <i className="bi bi-archive" />
        Tous les billets
        <span className="badge rounded-pill text-bg-light ms-auto">{tickets?.length ?? 0}</span>
      </h2>

      {loading && <EmptyState icon="bi-hourglass-split">Chargement…</EmptyState>}
      {error && <Alert message={error} type="error" />}

      {tickets?.map((ticket) => (
        <div key={ticket.id} className={`ticket-card ticket-${ticket.role}`}>
          <div>
            <span className="ticket-numero">#{ticket.numero}</span>
            <span className="ticket-date">{ticket.user?.username ?? 'non attribué'}</span>
          </div>

          <div className="ticket-side">
            <RoleBadge ticket={ticket} />
          </div>
        </div>
      ))}

      {tickets?.length === 0 && (
        <EmptyState icon="bi-ticket-detailed">Aucun billet dans le parc.</EmptyState>
      )}
    </div>
  )
}
