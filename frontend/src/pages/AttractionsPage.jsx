/**
 * Les attractions du parc, et ce que le visiteur y a en cours.
 * Reprend `attractions/attractions.html`.
 */
import { useEffect, useRef, useState } from 'react'

import { joinQueue, leaveQueue, listAttractionCards, validateQueue } from '../api/attractions'
import Alert from '../components/Alert'
import AttractionCard from '../components/AttractionCard'
import EmptyState from '../components/EmptyState'
import { useApi } from '../hooks/useApi'

/**
 * Ce qu'il faut dire au visiteur quand une attraction où il a une place s'arrête
 * ou repart entre deux lectures de la liste. `null` s'il n'y a rien de neuf.
 */
function incidentNews(before, after) {
  for (const card of after) {
    const was = before.find((c) => c.id === card.id)
    if (!was || !card.entry) continue
    if (card.incident_reason && !was.incident_reason) {
      return {
        type: 'warning',
        message: `${card.name} est hors service : ${card.incident_reason}. Votre file est en pause, vous gardez votre place.`,
      }
    }
    if (!card.incident_reason && was.incident_reason) {
      return { type: 'success', message: `${card.name} est de nouveau ouverte : la file reprend.` }
    }
  }
  return null
}

export default function AttractionsPage() {
  const { data: cards, loading, error, reload } = useApi(listAttractionCards)
  const [feedback, setFeedback] = useState(null)

  // La liste d'avant, pour voir ce qui a changé à chaque relecture.
  const previousCards = useRef(null)
  useEffect(() => {
    if (!cards) return
    const news = previousCards.current && incidentNews(previousCards.current, cards)
    if (news) setFeedback(news)
    previousCards.current = cards
  }, [cards])

  /**
   * Les trois gestes sur une file suivent le même déroulé : appeler l'API,
   * afficher le retour, recharger la liste. Une seule fonction les porte tous.
   */
  async function runAction(action, successMessage) {
    try {
      await action()
      setFeedback({ type: 'success', message: successMessage })
      await reload()
    } catch (err) {
      setFeedback({ type: 'error', message: err.message })
    }
  }

  // Seulement au premier chargement : un rechargement ne doit pas faire clignoter la page.
  if (loading && !cards) {
    return <EmptyState icon="bi-hourglass-split">Chargement des attractions…</EmptyState>
  }

  return (
    <>
      <h1 className="page-title h4">Attractions</h1>
      <p className="page-subtitle">
        Rejoignez la file virtuelle, et présentez-vous quand vous êtes appelé.
      </p>

      <Alert message={feedback?.message} type={feedback?.type} />
      {error && <Alert message={error} type="error" />}

      <div className="row g-4">
        {cards?.map((card) => (
          <div className="col-sm-6 col-lg-4" key={card.id}>
            <AttractionCard
              card={card}
              onChange={reload}
              onJoin={() =>
                runAction(() => joinQueue(card.id), `Vous êtes dans la file de ${card.name}.`)
              }
              onLeave={() =>
                runAction(
                  () => leaveQueue(card.entry?.id),
                  `Vous avez quitté la file de ${card.name}.`,
                )
              }
              onValidate={() =>
                runAction(() => validateQueue(card.entry?.id), `Bienvenue dans ${card.name} !`)
              }
            />
          </div>
        ))}

        {cards?.length === 0 && (
          <div className="col-12">
            <div className="park-card">
              <EmptyState icon="bi-rocket-takeoff">Aucune attraction pour l'instant.</EmptyState>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
