/**
 * La pastille d'un rôle de billet. Sa couleur vient de la classe
 * `role-badge-<role>` posée dans dbz-park.css : chaque rôle se lit sans son
 * libellé.
 */
import { roleLabel } from '../utils/format'

export default function RoleBadge({ ticket, withIcon = true }) {
  return (
    <span className={`role-badge role-badge-${ticket.role}`}>
      {withIcon && <i className="bi bi-stars" />}
      {roleLabel(ticket.role)}
    </span>
  )
}
