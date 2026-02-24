
import { Player } from "@/types/Player";

interface RosterCardProps {
  player: Player;
}




export default function RosterCard({ player }: RosterCardProps) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 shadow-lg flex flex-col items-center text-center border border-gray-700">
      <img
        src={player.headshot}
        alt={player.name}
        className="w-32 h-32 rounded-full object-cover mb-4 border border-gray-600"
      />

      <h2 className="text-xl font-bold">{player.name}</h2>
      <p className="text-purple-400 font-semibold">{player.gamertag}</p>

      <div className="mt-3 text-sm text-gray-300 space-y-1">
        <p><strong>Game:</strong> {player.game}</p>
        <p><strong>Rank:</strong> {player.rank}</p>
        <p><strong>Year:</strong> {player.year}</p>
        <p><strong>Major:</strong> {player.major}</p>
      </div>
    </div>
  );
}