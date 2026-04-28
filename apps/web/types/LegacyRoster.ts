import type { Player } from "@/types/Player";

export interface LegacyRosterListItem {
  id: number;
  name: string;
  slug: string;
  created_at: string;
  player_count: number;
}

export interface LegacyRosterDetail {
  id: number;
  name: string;
  slug: string;
  created_at: string;
  players: Player[];
}
