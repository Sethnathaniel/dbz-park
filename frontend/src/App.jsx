/**
 * Les routes de l'application — l'équivalent des `urls.py` côté Django.
 *
 * Toutes passent par `<Layout />`, qui pose l'en-tête. Les pages qui demandaient
 * `LoginRequiredMixin` sont enveloppées dans `<RequireAuth>`, et la console
 * ajoute `staffOnly`.
 */
import { Route, Routes } from 'react-router-dom'

import Layout from './components/Layout'
import EmptyState from './components/EmptyState'
import RequireAuth from './auth/RequireAuth'
import AccountsPage from './pages/AccountsPage'
import AttractionsPage from './pages/AttractionsPage'
import ConsolePage from './pages/ConsolePage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import TicketsPage from './pages/TicketsPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        {/* Ouvert à tous */}
        <Route path="/connexion" element={<LoginPage />} />
        <Route path="/inscription" element={<SignupPage />} />

        {/* Réservé aux visiteurs connectés */}
        <Route
          index
          element={
            <RequireAuth>
              <TicketsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/attractions"
          element={
            <RequireAuth>
              <AttractionsPage />
            </RequireAuth>
          }
        />

        {/* Réservé à l'équipe du parc */}
        <Route
          path="/console"
          element={
            <RequireAuth staffOnly>
              <ConsolePage />
            </RequireAuth>
          }
        />
        <Route
          path="/comptes"
          element={
            <RequireAuth staffOnly>
              <AccountsPage />
            </RequireAuth>
          }
        />

        <Route
          path="*"
          element={<EmptyState icon="bi-signpost-2">Cette page n'existe pas.</EmptyState>}
        />
      </Route>
    </Routes>
  )
}
