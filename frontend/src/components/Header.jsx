/**
 * L'en-tête du parc : la marque à gauche, les onglets et le menu du compte à
 * droite. Reprend `park_management/templates/park_management/index.html`.
 *
 * Le menu déroulant est tenu par un état React plutôt que par le JavaScript de
 * Bootstrap : une seule façon de faire dans le projet, et rien à charger.
 */
import { useState } from 'react'
import { NavLink, Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

// NavLink donne lui-même `isActive` : c'est ce qui remplace le test sur
// `request.resolver_match.url_name` du gabarit Django.
const navClass = ({ isActive }) => `nav-link-btn${isActive ? ' active' : ''}`

export default function Header() {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const navigate = useNavigate()

  async function handleLogout() {
    setMenuOpen(false)
    await logout()
    navigate('/connexion')
  }

  return (
    <header className="park-header">
      <div className="header-inner">
        <Link className="brand-link" to="/">
          <img src="/dbz-park-icon.svg" alt="Dragon Ball Park" />
          <div>
            <p className="brand-name">Dragon Ball Park</p>
            <span className="brand-tagline">Le parc où votre puissance monte en flèche</span>
          </div>
        </Link>

        <nav className="header-nav">
          {user ? (
            <>
              <NavLink to="/" end className={navClass}>
                <i className="bi bi-ticket-perforated" />
                Mes billets
              </NavLink>
              <NavLink to="/attractions" className={navClass}>
                <i className="bi bi-rocket-takeoff" />
                Attractions
              </NavLink>
              {user.is_staff && (
                <>
                  <NavLink to="/console" className={navClass}>
                    <i className="bi bi-sliders" />
                    Console
                  </NavLink>
                  <NavLink to="/comptes" className={navClass}>
                    <i className="bi bi-people" />
                    Comptes
                  </NavLink>
                </>
              )}

              <div className="dropdown">
                <button
                  type="button"
                  className="nav-link-btn"
                  onClick={() => setMenuOpen((open) => !open)}
                  aria-expanded={menuOpen}
                >
                  <i className="bi bi-person-circle" />
                  {user.username}
                  <i className="bi bi-chevron-down small" />
                </button>

                {menuOpen && (
                  <ul className="dropdown-menu dropdown-menu-end park-dropdown show">
                    <li>
                      <Link className="dropdown-item" to="/" onClick={() => setMenuOpen(false)}>
                        <i className="bi bi-ticket-perforated" />
                        Mes billets
                      </Link>
                    </li>
                    <li>
                      <Link
                        className="dropdown-item"
                        to="/attractions"
                        onClick={() => setMenuOpen(false)}
                      >
                        <i className="bi bi-rocket-takeoff" />
                        Attractions
                      </Link>
                    </li>
                    {user.is_staff && (
                      <li>
                        <Link
                          className="dropdown-item"
                          to="/console"
                          onClick={() => setMenuOpen(false)}
                        >
                          <i className="bi bi-sliders" />
                          Console
                        </Link>
                      </li>
                    )}
                    {user.is_staff && (
                      <li>
                        <Link
                          className="dropdown-item"
                          to="/comptes"
                          onClick={() => setMenuOpen(false)}
                        >
                          <i className="bi bi-people" />
                          Comptes
                        </Link>
                      </li>
                    )}
                    <li>
                      <hr className="dropdown-divider" />
                    </li>
                    <li>
                      <button type="button" className="dropdown-item" onClick={handleLogout}>
                        <i className="bi bi-box-arrow-right" />
                        Déconnexion
                      </button>
                    </li>
                  </ul>
                )}
              </div>
            </>
          ) : (
            <NavLink to="/connexion" className="nav-link-btn">
              <i className="bi bi-box-arrow-in-right" />
              Connexion
            </NavLink>
          )}
        </nav>
      </div>
    </header>
  )
}
