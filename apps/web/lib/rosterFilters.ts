import type { Player } from "@/types/Player";
import type { GameOption } from "@/types/GameOption";

export const ALL_GAMES_FILTER_VALUE = "all";

export function filterPlayerByGame(player: Player, selectedGameSlug: string): boolean {
  if (selectedGameSlug === ALL_GAMES_FILTER_VALUE) return true;
  const profiles = Array.isArray(player.game_profiles) ? player.game_profiles : [];
  if (profiles.some((profile) => profile.game_slug === selectedGameSlug)) {
    return true;
  }
  if (player.primary_game_slug === selectedGameSlug) return true;
  return Array.isArray(player.secondary_game_slugs) && player.secondary_game_slugs.includes(selectedGameSlug);
}

export function deriveGameOptions(games: GameOption[], players: Player[]): GameOption[] {
  if (games.length > 0) return games;

  const bySlug = new Map<string, GameOption>();
  for (const player of players) {
    const profiles = Array.isArray(player.game_profiles) ? player.game_profiles : [];
    for (const profile of profiles) {
      const slug = profile.game_slug;
      const name = profile.game_name || profile.game_slug;
      if (!slug || !name || bySlug.has(slug)) continue;
      bySlug.set(slug, { id: -1, slug, name });
    }

    const slug = player.primary_game_slug;
    const name = player.primary_game_name || player.game;
    if (!slug || !name || bySlug.has(slug)) continue;
    bySlug.set(slug, { id: -1, slug, name });
  }
  return Array.from(bySlug.values()).sort((a, b) => a.name.localeCompare(b.name));
}
