import { ROLE_LABELS } from '../utils/roles'

/**
 * La pastille d'un rôle de billet. Sa couleur vient de la classe
 * `role-badge-<role>` posée dans dbz-park.css : chaque rôle se lit sans son
 * libellé.
 */
export default function RoleBadge({ ticket, withIcon = true }) {
  return (
    <span className={`role-badge role-badge-${ticket.role}`}>
      {withIcon && <i className="bi bi-stars" />}
      {ROLE_LABELS[ticket.role] ?? ticket.role}
    </span>
  )
}
