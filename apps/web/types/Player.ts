export interface PlayerGameProfile {
  game_slug: string;
  game_name: string | null;
  role: string | null;
  rank: string | null;
  is_primary: boolean;
}

export interface Player {
  id: number;
  name: string;
  gamertag: string;
  game: string;
  primary_game_slug: string | null;
  primary_game_name: string | null;
  secondary_game_slugs: string[];
  secondary_game_names: string[];
  role: string | null;
  rank: string | null;
  game_profiles: PlayerGameProfile[];
  year: string | null;
  major: string | null;
  headshot: string | null;
}
