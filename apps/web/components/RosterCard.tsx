import { Player } from "@/types/Player";

interface RosterCardProps {
  player: Player;
}

const DEFAULT_HEADSHOT = "/images/esports-news-placeholder.jpg";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function resolveImageUrl(imageUrl: string | null): string {
  if (!imageUrl || !imageUrl.trim()) return DEFAULT_HEADSHOT;
  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) return imageUrl;
  if (imageUrl.startsWith("/uploads")) return `${API_URL}${imageUrl}`;
  if (imageUrl.startsWith("/")) return imageUrl;
  return `${API_URL}/${imageUrl}`;
}


export default function RosterCard({ player }: RosterCardProps) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 shadow-lg flex flex-col items-center text-center border border-gray-700">
      <img
        src={resolveImageUrl(player.headshot)}
        alt={player.name}
        className="w-32 h-32 rounded-full object-cover mb-4 border border-gray-600"
      />

      <h2 className="text-xl font-bold">{player.name}</h2>
      <p className="text-purple-400 font-semibold">{player.gamertag}</p>

      <div className="mt-3 text-sm text-gray-300 space-y-1">
        <p><strong>Game:</strong> {player.game}</p>
        <p><strong>Role:</strong> {player.role || "N/A"}</p>
        <p><strong>Rank:</strong> {player.rank || "N/A"}</p>
        <p><strong>Year:</strong> {player.year || "N/A"}</p>
        <p><strong>Major:</strong> {player.major || "N/A"}</p>
      </div>
    </div>
  );
}
