/**
 * LA liste des adresses de l'API. Un seul fichier à corriger le jour où le back
 * nomme ses routes autrement : rien d'autre dans le front ne connaît une URL.
 *
 * Les noms reprennent mot pour mot ceux du contrat (`API.md`), y compris en
 * anglais : une URL qui se lit pareil des deux côtés est une URL qu'on ne se
 * trompe pas à écrire.
 */

export const endpoints = {
  // ── Comptes ─────────────────────────────────────────────────────────────
  signup: '/auth/signup/', //   POST  crée le compte et renvoie un jeton
  login: '/auth/login/', //     POST  échange identifiants contre jeton
  me: '/auth/me/', //           GET   qui est connecté, d'après le jeton

  // ── Billets ─────────────────────────────────────────────────────────────
  tickets: '/tickets/', //      GET   tous les billets (staff)  ·  POST  en acheter un
  userTickets: (userId) => `/user/${userId}/tickets/`, //   GET   les billets d'un visiteur
  assignTicket: '/tickets/assign/', //                      POST  en rattacher un

  // ── Attractions & files ─────────────────────────────────────────────────
  attractions: '/attractions/', // GET   le catalogue, rien sur le visiteur
  myQueue: '/queue/', //           GET   ses places et ses présences
  joinQueue: (attractionId) => `/attractions/${attractionId}/queue/join/`, // POST
  queuePosition: (entryId) => `/queue/${entryId}/position/`, //               GET
  leaveQueue: (entryId) => `/queue/${entryId}/leave/`, //                     POST
  validateQueue: (entryId) => `/queue/${entryId}/validate/`, //               POST

  // ── Console admin ───────────────────────────────────────────────────────
  console: '/console/', //      GET
  acceptEntry: (entryId) => `/console/entries/${entryId}/accept/`, // POST
  refuseEntry: (entryId) => `/console/entries/${entryId}/refuse/`, // POST
}
