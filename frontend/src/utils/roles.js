/**
 * Les rôles de billet. Le back n'envoie que la clé (`role`) : le libellé
 * s'écrit ici, une seule fois, pour toutes les pages.
 */

export const ROLE_LABELS = {
  normal: 'Normal',
  sayan: 'Saiyan',
  super_sayan: 'Super Saiyan',
}

// Les trois rôles vendus, dans l'ordre de la liste d'achat. Le back refera le
// contrôle : ici, c'est seulement ce que le visiteur peut choisir.
export const ROLES = Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }))
