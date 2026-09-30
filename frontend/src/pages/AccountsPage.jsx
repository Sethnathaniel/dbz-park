/**
 * La gestion des comptes, pour le staff : retrouver un visiteur, corriger son
 * nom ou son e-mail, lui donner ou lui retirer les droits d'admin, supprimer son
 * compte, et invalider ou rétablir ses billets à la main.
 */
import { useCallback, useState } from 'react'

import {
  deleteAccount,
  searchAccounts,
  toggleTicketValidity,
  updateAccount,
} from '../api/accounts'
import { useAuth } from '../auth/AuthContext'
import Alert from '../components/Alert'
import EmptyState from '../components/EmptyState'
import RoleBadge from '../components/RoleBadge'
import { InvalidTag, ValidityButton } from '../components/TicketValidity'
import { useApi } from '../hooks/useApi'

/** Le formulaire de modification d'un compte, ouvert à la place de sa fiche. */
function AccountForm({ account, isMe, onSave, onCancel }) {
  const [username, setUsername] = useState(account.username)
  const [email, setEmail] = useState(account.email)
  const [isStaff, setIsStaff] = useState(account.is_staff)

  function submit(event) {
    event.preventDefault()
    onSave({ username: username.trim(), email: email.trim(), is_staff: isStaff })
  }

  return (
    <form onSubmit={submit} className="row g-3 mb-3">
      <div className="col-sm-6">
        <label className="form-label" htmlFor={`username-${account.id}`}>
          Nom d'utilisateur
        </label>
        <input
          id={`username-${account.id}`}
          className="form-control"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          minLength={3}
          required
        />
      </div>
      <div className="col-sm-6">
        <label className="form-label" htmlFor={`email-${account.id}`}>
          E-mail
        </label>
        <input
          id={`email-${account.id}`}
          type="email"
          className="form-control"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
      </div>
      <div className="col-12">
        <div className="form-check">
          <input
            id={`staff-${account.id}`}
            type="checkbox"
            className="form-check-input"
            checked={isStaff}
            onChange={(event) => setIsStaff(event.target.checked)}
            // Un admin qui se retire ses droits ne pourrait plus revenir ici.
            disabled={isMe}
          />
          <label className="form-check-label" htmlFor={`staff-${account.id}`}>
            Droits d'admin (console et gestion des comptes)
          </label>
        </div>
      </div>
      <div className="col-12 account-actions">
        <button type="submit" className="btn btn-park btn-sm">
          <i className="bi bi-check2" />
          Enregistrer
        </button>
        <button type="button" className="btn btn-park-ghost btn-sm" onClick={onCancel}>
          Annuler
        </button>
      </div>
    </form>
  )
}

/** Un compte : qui c'est, ce qu'on peut en faire, et ses billets. */
function AccountCard({ account, isMe, onSave, onDelete, onToggleTicket }) {
  const [editing, setEditing] = useState(false)

  async function save(changes) {
    // Le formulaire ne se ferme que si l'enregistrement a réussi : en cas de
    // refus (nom déjà pris…), l'admin corrige sans tout ressaisir.
    if (await onSave(changes)) setEditing(false)
  }

  return (
    <div className="park-card">
      <h2>
        <i className="bi bi-person-circle" />
        {account.username}
        {account.is_staff && <span className="badge rounded-pill text-bg-light">admin</span>}
        {isMe && <span className="badge rounded-pill text-bg-light">vous</span>}

        {!editing && (
          <span className="account-actions ms-auto">
            <button
              type="button"
              className="btn btn-park-ghost btn-sm"
              onClick={() => setEditing(true)}
            >
              <i className="bi bi-pencil" />
              Modifier
            </button>
            {!isMe && (
              <button type="button" className="btn btn-park-ghost btn-sm" onClick={onDelete}>
                <i className="bi bi-trash" />
                Supprimer
              </button>
            )}
          </span>
        )}
      </h2>

      {editing ? (
        <AccountForm
          account={account}
          isMe={isMe}
          onSave={save}
          onCancel={() => setEditing(false)}
        />
      ) : (
        <p className="account-email">{account.email || "Pas d'e-mail renseigné."}</p>
      )}

      {account.tickets.map((ticket) => (
        <div
          key={ticket.id}
          className={`ticket-card ticket-${ticket.role} ${ticket.is_valid ? '' : 'ticket-invalid'}`}
        >
          <div>
            <span className="ticket-numero">#{ticket.numero}</span>
            <InvalidTag ticket={ticket} />
          </div>
          <div className="ticket-side">
            <RoleBadge ticket={ticket} />
            <ValidityButton ticket={ticket} onToggle={() => onToggleTicket(ticket)} />
          </div>
        </div>
      ))}

      {account.tickets.length === 0 && (
        <EmptyState icon="bi-ticket-detailed">Aucun billet sur ce compte.</EmptyState>
      )}
    </div>
  )
}

export default function AccountsPage() {
  const { user: me } = useAuth()

  // Ce qui est tapé, et ce qui est cherché : la recherche part à la validation.
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')

  // `useApi` veut une fonction stable : elle ne change qu'avec la recherche.
  const fetchAccounts = useCallback(() => searchAccounts(query), [query])
  const { data: accounts, loading, error, reload } = useApi(fetchAccounts)
  const [feedback, setFeedback] = useState(null)

  /** Appeler l'API, dire ce qui s'est passé, relire la liste. Rend `true` si ça a marché. */
  async function runAction(action, successMessage) {
    try {
      await action()
      setFeedback({ type: 'success', message: successMessage })
      await reload()
      return true
    } catch (err) {
      setFeedback({ type: 'error', message: err.message })
      return false
    }
  }

  function handleDelete(account) {
    const confirmed = window.confirm(
      `Supprimer le compte de ${account.username} ?\n\n` +
        'Ses places en file seront retirées. Ses billets resteront dans le parc, sans détenteur.',
    )
    if (confirmed) {
      runAction(
        () => deleteAccount(account.id),
        `Le compte de ${account.username} a été supprimé.`,
      )
    }
  }

  return (
    <>
      <h1 className="page-title h4">Comptes</h1>
      <p className="page-subtitle">
        Retrouvez un visiteur par son nom ou son e-mail, modifiez son compte, et contrôlez la
        validité de ses billets.
      </p>

      <form
        className="park-card search-form"
        onSubmit={(event) => {
          event.preventDefault()
          setQuery(search.trim())
        }}
      >
        <input
          className="form-control"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Nom ou e-mail : goku, @dbz.fr…"
        />
        <button type="submit" className="btn btn-park">
          <i className="bi bi-search" />
          Rechercher
        </button>
      </form>

      <Alert message={feedback?.message} type={feedback?.type} />
      {error && <Alert message={error} type="error" />}

      {loading && !accounts && <EmptyState icon="bi-hourglass-split">Chargement…</EmptyState>}

      {accounts?.map((account) => (
        <AccountCard
          key={account.id}
          account={account}
          isMe={account.id === me.id}
          onSave={(changes) =>
            runAction(() => updateAccount(account.id, changes), 'Le compte a été mis à jour.')
          }
          onDelete={() => handleDelete(account)}
          onToggleTicket={(ticket) =>
            runAction(
              () => toggleTicketValidity(ticket),
              ticket.is_valid
                ? `Le billet #${ticket.numero} est invalidé : il a quitté ses files.`
                : `Le billet #${ticket.numero} est de nouveau valide.`,
            )
          }
        />
      ))}

      {accounts?.length === 0 && (
        <div className="park-card">
          <EmptyState icon="bi-person-x">
            {query ? `Aucun compte ne correspond à « ${query} ».` : 'Aucun compte.'}
          </EmptyState>
        </div>
      )}
    </>
  )
}
