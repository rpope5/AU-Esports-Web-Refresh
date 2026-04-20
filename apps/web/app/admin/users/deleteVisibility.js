/**
 * Delete Account must only render for true admin staff users.
 * @param {string | null | undefined} role
 * @returns {boolean}
 */
export function canRenderDeleteAccountAction(role) {
  return role === "admin";
}

