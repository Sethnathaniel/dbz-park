/**
 * La validité d'un billet : l'étiquette que tout le monde voit quand il est
 * invalidé, et le bouton du staff pour l'invalider ou le rétablir.
 */

export function InvalidTag({ ticket }) {
  if (ticket.is_valid) return null

  return (
    <span className="invalid-tag">
      <i className="bi bi-slash-circle" />
      invalidé
    </span>
  )
}

export function ValidityButton({ ticket, onToggle }) {
  return ticket.is_valid ? (
    <button type="button" className="btn btn-park-ghost btn-sm" onClick={onToggle}>
      <i className="bi bi-slash-circle" />
      Invalider
    </button>
  ) : (
    <button type="button" className="btn btn-park btn-sm" onClick={onToggle}>
      <i className="bi bi-check2-circle" />
      Rétablir
    </button>
  )
}
