/**
 * Un faux back, en mémoire, pour que le front tourne avant que l'API existe.
 *
 * Il rend exactement les formes décrites dans `API.md` : le jour où le vrai
 * back répond, on passe VITE_USE_MOCK à false et rien d'autre ne bouge.
 * Les données repartent de zéro à chaque rechargement de la page — c'est une
 * maquette, pas une base.
 */

import { getToken } from './client'

export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'

const ROLE_KEYS = ['normal', 'sayan', 'super_sayan']

// Du meilleur rôle au plus commun : c'est cet ordre qui décide du billet joué.
const ROLE_PRIORITY = ['super_sayan', 'sayan', 'normal']

// ── Les données de départ ───────────────────────────────────────────────────

const db = {
  // Deux comptes pour essayer : un visiteur et un admin.
  users: [
    { id: 1, username: 'goku', password: 'kamehameha', is_staff: false },
    { id: 2, username: 'admin', password: 'admin', is_staff: true },
  ],
  tickets: [
    { id: 1, user_id: 1, numero: 'DBZ-0001', role: 'super_sayan', created_at: '2026-09-17T09:12:00' },
    { id: 2, user_id: 1, numero: 'DBZ-0002', role: 'normal', created_at: '2026-09-17T09:30:00' },
    // Billet libre, pour essayer l'assignation depuis « Mes billets ».
    { id: 3, user_id: null, numero: 'DBZ-0003', role: 'sayan', created_at: '2026-09-17T08:00:00' },
  ],
  attractions: [
    { id: 1, name: 'La Salle du Temps', photo_url: '', max_people: 50, avg_duration: 210, max_seconds_allowing_ready: 300 },
    { id: 2, name: 'Le Vaisseau de Freezer', photo_url: '', max_people: 30, avg_duration: 270, max_seconds_allowing_ready: 180 },
    { id: 3, name: 'Le Palais de Kaio', photo_url: '', max_people: 20, avg_duration: 90, max_seconds_allowing_ready: 240 },
  ],
  entries: [],
  visits: [],
  nextId: 100,
  nextNumero: 4,
}

let currentUser = null

// ── Petits utilitaires ──────────────────────────────────────────────────────

/** Simule le temps d'un aller-retour réseau, pour voir les états de chargement. */
const wait = () => new Promise((resolve) => setTimeout(resolve, 250))

const nextId = () => db.nextId++

/** « DBZ-0042 » — le numéro est fabriqué par le back, jamais envoyé par le front. */
const nextNumero = () => `DBZ-${String(db.nextNumero++).padStart(4, '0')}`

const fail = (message) => {
  throw new Error(message)
}

/** Le refus commun à toutes les routes : sans jeton valable, on ne fait rien. */
function requireUser() {
  if (!currentUser) fail('Connectez-vous pour continuer.')
  return currentUser
}

function publicUser(user) {
  return { id: user.id, username: user.username, is_staff: user.is_staff }
}

/** Le billet tel que le contrat le décrit. */
function publicTicket(ticket) {
  return {
    id: ticket.id,
    numero: ticket.numero,
    role: ticket.role,
    created_at: ticket.created_at,
  }
}

/** La version courte, celle qui accompagne une place ou une visite. */
function shortTicket(ticket) {
  return {
    id: ticket.id,
    numero: ticket.numero,
    role: ticket.role,
  }
}

const peopleInside = (attractionId) =>
  db.visits.filter((v) => v.attraction_id === attractionId).length

const attractionOf = (id) => db.attractions.find((a) => a.id === id)

/** Le délai de présentation est-il dépassé ? */
function readyExpired(entry) {
  if (!entry.ready_at) return false
  const secondsSince = (Date.now() - new Date(entry.ready_at).getTime()) / 1000
  return secondsSince > attractionOf(entry.attraction_id).max_seconds_allowing_ready
}

/** Combien de personnes devant, celle-ci comprise : 1 = c'est le prochain. */
function positionOf(entry) {
  return (
    db.entries.filter(
      (e) => e.attraction_id === entry.attraction_id && e.joined_at <= entry.joined_at,
    ).length
  )
}

/**
 * Le meilleur billet utilisable du visiteur pour cette attraction, ou null :
 * un billet déjà engagé dans une file ou une visite ne compte pas.
 */
function bestTicket(attractionId) {
  const engaged = new Set([
    ...db.entries.map((e) => e.ticket_id),
    ...db.visits.map((v) => v.ticket_id),
  ])
  const mine = db.tickets.filter(
    (t) => t.user_id === currentUser?.id && !engaged.has(t.id),
  )
  mine.sort((a, b) => ROLE_PRIORITY.indexOf(a.role) - ROLE_PRIORITY.indexOf(b.role))
  return mine[0] ?? null
}

const ticketOf = (id) => db.tickets.find((t) => t.id === id)

// ── Les réponses ────────────────────────────────────────────────────────────

export const mock = {
  // Comptes
  async login({ username, password }) {
    await wait()
    const user = db.users.find((u) => u.username === username && u.password === password)
    // Un nom inconnu et un mot de passe faux donnent le même refus : la réponse
    // ne confirme jamais qu'un compte existe.
    if (!user) fail('Identifiants incorrects.')
    currentUser = user
    return { token: `faux-jeton-${user.id}`, user: publicUser(user) }
  },

  async signup({ username, email, password1, password2 }) {
    await wait()
    if (!username || !email || !password1 || !password2) fail('Tous les champs sont obligatoires.')
    if (password1 !== password2) fail('Les deux mots de passe ne correspondent pas.')
    if (db.users.some((u) => u.username === username)) fail('Ce nom est déjà pris.')
    const user = { id: nextId(), username, email, password: password1, is_staff: false }
    db.users.push(user)
    currentUser = user
    return { token: `faux-jeton-${user.id}`, user: publicUser(user) }
  },

  // Au rechargement de la page, la mémoire du faux back est repartie de zéro :
  // on retrouve le visiteur depuis son jeton, comme le vrai back le ferait.
  async me() {
    await wait()
    if (!currentUser) {
      const id = Number(getToken()?.replace('faux-jeton-', ''))
      currentUser = db.users.find((u) => u.id === id) ?? null
    }
    if (!currentUser) fail('Non connecté.')
    return publicUser(currentUser)
  },

  // Billets
  /** Les billets d'un visiteur : les siens, ou n'importe lesquels pour le staff. */
  async userTickets(userId) {
    await wait()
    const user = requireUser()
    // Le billet d'un autre et un compte inconnu donnent le même refus : la
    // route ne sert pas à savoir quels comptes existent.
    if (user.id !== userId && !user.is_staff) fail('Ces billets ne sont pas les vôtres.')
    if (!db.users.some((u) => u.id === userId)) fail('Ces billets ne sont pas les vôtres.')
    return db.tickets.filter((t) => t.user_id === userId).map(publicTicket)
  },

  /** Tous les billets du parc, avec leur détenteur. Réservé au staff. */
  async allTickets() {
    await wait()
    const user = requireUser()
    if (!user.is_staff) fail('Connectez-vous pour continuer.')
    return db.tickets.map((ticket) => {
      const owner = db.users.find((u) => u.id === ticket.user_id)
      return {
        ...publicTicket(ticket),
        user: owner ? { id: owner.id, username: owner.username } : null,
      }
    })
  },

  /** L'achat : le billet est aussitôt au visiteur, et utilisable. */
  async buyTicket({ role }) {
    await wait()
    requireUser()
    if (!ROLE_KEYS.includes(role)) fail("Ce type de billet n'existe pas.")
    const ticket = {
      id: nextId(),
      user_id: currentUser.id,
      numero: nextNumero(),
      role,
      created_at: new Date().toISOString(),
    }
    db.tickets.push(ticket)
    return publicTicket(ticket)
  },

  async assignTicket({ numero }) {
    await wait()
    requireUser()
    if (!numero) fail('Saisissez un numéro de billet.')
    const ticket = db.tickets.find((t) => t.numero === numero)
    // Un numéro inconnu et un numéro déjà pris donnent la même réponse : on ne
    // dit pas à qui appartient un billet.
    if (!ticket || ticket.user_id !== null) fail('Ce numéro de billet est introuvable.')
    ticket.user_id = currentUser.id
    return publicTicket(ticket)
  },

  // Attractions
  /** Le catalogue seul : ce que le visiteur a en cours n'est pas ici. */
  async attractions() {
    await wait()
    requireUser()
    return db.attractions.map((attraction) => ({
      id: attraction.id,
      name: attraction.name,
      photo_url: attraction.photo_url,
      max_people: attraction.max_people,
      people_inside: peopleInside(attraction.id),
      avg_duration: attraction.avg_duration,
    }))
  },

  async joinQueue(attractionId) {
    await wait()
    requireUser()
    if (!attractionOf(attractionId)) fail("Cette attraction n'existe pas.")
    // Une place et une seule par attraction : on ne double pas la file en
    // jouant un deuxième billet, et on ne s'y remet pas en étant à l'intérieur.
    const here = (row) =>
      row.attraction_id === attractionId && ticketOf(row.ticket_id)?.user_id === currentUser.id
    if (db.entries.some(here)) fail('Vous avez déjà une place dans cette file.')
    if (db.visits.some(here)) fail('Vous êtes déjà à l\'intérieur de cette attraction.')
    const ticket = bestTicket(attractionId)
    if (!ticket) fail('Aucun de vos billets ne peut rejoindre cette file.')
    const alone = db.entries.filter((e) => e.attraction_id === attractionId).length === 0
    db.entries.push({
      id: nextId(),
      attraction_id: attractionId,
      ticket_id: ticket.id,
      joined_at: new Date().toISOString(),
      // Pour la maquette, le premier de la file est appelé tout de suite ; côté
      // back, c'est l'attraction qui décidera.
      is_ready: alone,
      ready_at: alone ? new Date().toISOString() : null,
    })
    return null
  },

  /** Les places et présences du visiteur, comme `GET /queue/`. */
  async myQueue() {
    await wait()
    const user = requireUser()
    const mine = (row) => ticketOf(row.ticket_id)?.user_id === user.id
    return {
      entries: db.entries.filter(mine).map((entry) => ({
        id: entry.id,
        attraction_id: entry.attraction_id,
        ticket: publicTicket(ticketOf(entry.ticket_id)),
        joined_at: entry.joined_at,
        is_ready: entry.is_ready,
        ready_at: entry.ready_at,
        max_seconds_allowing_ready: attractionOf(entry.attraction_id).max_seconds_allowing_ready,
        ready_expired: readyExpired(entry),
        // Comme le back : une place déjà appelée n'a plus de rang.
        position: entry.is_ready ? 0 : positionOf(entry),
      })),
      visits: db.visits.filter(mine).map((visit) => ({
        attraction_id: visit.attraction_id,
        ticket: publicTicket(ticketOf(visit.ticket_id)),
        entered_at: visit.entered_at,
      })),
    }
  },

  /** Le rang seul, celui que le front réinterroge pendant l'attente. */
  async queuePosition(entryId) {
    requireUser()
    const entry = db.entries.find((e) => e.id === entryId)
    // Place inconnue et place d'un autre : même refus, un rang dit à quel point
    // une file est chargée.
    if (!entry || ticketOf(entry.ticket_id)?.user_id !== currentUser.id) {
      fail("Cette place n'existe plus.")
    }
    return { position: positionOf(entry) }
  },

  async leaveQueue(entryId) {
    await wait()
    requireUser()
    db.entries = db.entries.filter((e) => e.id !== entryId)
    return null
  },

  async validateQueue(entryId) {
    await wait()
    requireUser()
    const entry = db.entries.find((e) => e.id === entryId)
    if (!entry) fail("Cette place n'existe plus.")
    if (!entry.is_ready) fail("Votre tour n'est pas encore venu.")
    if (readyExpired(entry)) fail('Votre tour est passé : la place a été rendue à la file.')
    db.visits.push({
      id: nextId(),
      attraction_id: entry.attraction_id,
      ticket_id: entry.ticket_id,
      entered_at: new Date().toISOString(),
    })
    db.entries = db.entries.filter((e) => e.id !== entryId)
    return null
  },

  // Console
  async console() {
    await wait()
    const user = requireUser()
    if (!user.is_staff) fail('Connectez-vous pour continuer.')
    return db.attractions.map((attraction) => ({
      attraction: {
        id: attraction.id,
        name: attraction.name,
        max_people: attraction.max_people,
      },
      inside: peopleInside(attraction.id),
      waiting: db.entries.filter((e) => e.attraction_id === attraction.id && !e.is_ready).length,
      ready: db.entries
        .filter((e) => e.attraction_id === attraction.id && e.is_ready)
        .map((entry) => {
          const ticket = ticketOf(entry.ticket_id)
          return {
            id: entry.id,
            username: db.users.find((u) => u.id === ticket.user_id)?.username ?? '—',
            ticket: shortTicket(ticket),
            ready_at: entry.ready_at,
            max_seconds_allowing_ready: attraction.max_seconds_allowing_ready,
            ready_expired: readyExpired(entry),
          }
        }),
    }))
  },

  // L'admin fait entrer le visiteur. Contrairement à la validation côté
  // visiteur, une place au délai dépassé peut être acceptée : c'est le sens du
  // poste, l'admin décide en sachant que le visiteur s'est fait attendre.
  async acceptEntry(entryId) {
    await wait()
    const user = requireUser()
    if (!user.is_staff) fail('Connectez-vous pour continuer.')
    const entry = db.entries.find((e) => e.id === entryId)
    if (!entry) fail("Cette place n'existe plus.")
    const attraction = attractionOf(entry.attraction_id)
    if (peopleInside(attraction.id) >= attraction.max_people) {
      fail("L'attraction est pleine : attendez une sortie.")
    }
    db.visits.push({
      id: nextId(),
      attraction_id: entry.attraction_id,
      ticket_id: entry.ticket_id,
      entered_at: new Date().toISOString(),
    })
    db.entries = db.entries.filter((e) => e.id !== entryId)
    return null
  },

  // L'admin retire la place : le visiteur n'entre pas, et sa place est rendue.
  async refuseEntry(entryId) {
    await wait()
    const user = requireUser()
    if (!user.is_staff) fail('Connectez-vous pour continuer.')
    db.entries = db.entries.filter((e) => e.id !== entryId)
    return null
  },
}
