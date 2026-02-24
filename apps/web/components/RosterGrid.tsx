import RosterCard from "./RosterCard";
import { Player } from "@/types/Player";

interface RosterGridProps {
  players: Player[];
}


export default function RosterGrid({ players }: RosterGridProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 px-6 pb-16">
      {players.map((player, i) => (
        <RosterCard key={i} player={player} />
      ))}
    </div>
  );
}