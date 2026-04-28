import { Player } from "@/types/Player";
import { resolveContentImageUrl } from "@/lib/contentImages";
import { formatRosterGameDetails, normalizeRosterRank, normalizeRosterRole } from "@/lib/rosterDisplay";

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
  const gameProfiles = Array.isArray(player.game_profiles) ? player.game_profiles : [];
  const legacyRole = normalizeRosterRole(player.role);
  const legacyRank = normalizeRosterRank(player.rank);
  const orderedProfiles = [...gameProfiles].sort((a, b) => {
    if (a.is_primary === b.is_primary) return 0;
    return a.is_primary ? -1 : 1;
  });

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
        {orderedProfiles.length > 0 ? (
          <>
            {orderedProfiles.map((profile) => {
              const details = formatRosterGameDetails(profile.role, profile.rank);
              const gameLabel = `${profile.game_name || profile.game_slug}${profile.is_primary ? " (Primary)" : ""}`;
              return (
                <p key={`${player.id}-${profile.game_slug}`}>
                  <strong>{gameLabel}{details ? ":" : ""}</strong>
                  {details ? ` ${details}` : ""}
                </p>
              );
            })}
          </>
        ) : (
          <>
            <p><strong>Game:</strong> {primaryGameName}</p>
            {secondaryGameNames.length > 0 && (
              <p><strong>Additional Games:</strong> {secondaryGameNames.join(", ")}</p>
            )}
            {legacyRole && <p><strong>Role:</strong> {legacyRole}</p>}
            {legacyRank && <p><strong>Rank:</strong> {legacyRank}</p>}
          </>
        )}
        <p><strong>Year:</strong> {player.year || "N/A"}</p>
        <p><strong>Major:</strong> {player.major || "N/A"}</p>
      </div>
    </div>
  );
}
