const HIDDEN_RANK_TOKENS = new Set(["na", "n/a"]);

function normalizeText(value: string | null | undefined): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

export function normalizeRosterRole(value: string | null | undefined): string | null {
  return normalizeText(value);
}

export function normalizeRosterRank(value: string | null | undefined): string | null {
  const normalized = normalizeText(value);
  if (!normalized) return null;
  return HIDDEN_RANK_TOKENS.has(normalized.toLowerCase()) ? null : normalized;
}

export function rankInputValue(value: string | null | undefined): string {
  return normalizeRosterRank(value) ?? "";
}

export function formatRosterGameDetails(
  role: string | null | undefined,
  rank: string | null | undefined,
): string | null {
  const parts: string[] = [];
  const normalizedRole = normalizeRosterRole(role);
  const normalizedRank = normalizeRosterRank(rank);
  if (normalizedRole) parts.push(normalizedRole);
  if (normalizedRank) parts.push(normalizedRank);
  return parts.length > 0 ? parts.join(" / ") : null;
}
