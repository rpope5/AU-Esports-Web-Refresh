import { Player } from "@/types/Player";
import { resolveContentImageUrl } from "@/lib/contentImages";

interface RosterCardProps {
  player: Player;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function resolveRosterHeadshot(imageUrl: string | null): string {
  return resolveContentImageUrl(imageUrl, API_URL, "roster");
}


export default function RosterCard({ player }: RosterCardProps) {
  const primaryGameName = player.primary_game_name || player.game;
  const secondaryGameNames = Array.isArray(player.secondary_game_names) ? player.secondary_game_names : [];

  return (
    <div className="bg-gray-900 rounded-xl p-4 shadow-lg flex flex-col items-center text-center border border-gray-700">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={resolveRosterHeadshot(player.headshot)}
        alt={player.name}
        className="w-32 h-32 rounded-full object-cover mb-4 border border-gray-600"
      />

      <h2 className="text-xl font-bold">{player.name}</h2>
      <p className="text-purple-400 font-semibold">{player.gamertag}</p>

      <div className="mt-3 text-sm text-gray-300 space-y-1">
        <p><strong>Game:</strong> {primaryGameName}</p>
        {secondaryGameNames.length > 0 && (
          <p><strong>Additional Games:</strong> {secondaryGameNames.join(", ")}</p>
        )}
        <p><strong>Role:</strong> {player.role || "N/A"}</p>
        <p><strong>Rank:</strong> {player.rank || "N/A"}</p>
        <p><strong>Year:</strong> {player.year || "N/A"}</p>
        <p><strong>Major:</strong> {player.major || "N/A"}</p>
      </div>
    </div>
  );
}
