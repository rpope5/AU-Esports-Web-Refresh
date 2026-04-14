"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const gameCards = [
  {
    name: "Announcements",
    href: "/admin/news",
    description: "Create and manage esports news announcements",
  },
  {
    name: "Schedule",
    href: "/admin/schedule",
    description: "Create and manage public calendar events",
  },
  {
    name: "Valorant",
    href: "/admin/recruits/valorant",
    description: "View and manage Valorant recruits",
  },
  {
    name: "CS2",
    href: "/admin/recruits/cs2",
    description: "View and manage Counter-Strike 2 recruits",
  },
  {
    name: "Fortnite",
    href: "/admin/recruits/fortnite",
    description: "View and manage Fortnite recruits",
  },
  {
    name: "Rainbow Six Siege",
    href: "/admin/recruits/r6",
    description: "View and manage Rainbow Six Siege recruits",
  },
  {
    name: "Rocket League",
    href: "/admin/recruits/rocket-league",
    description: "View and manage Rocket League recruits",
  },
  {
    name: "Overwatch",
    href: "/admin/recruits/overwatch",
    description: "View and manage Overwatch recruits",
  },
  {
    name: "Call of Duty",
    href: "/admin/recruits/cod",
    description: "View and manage Call of Duty recruits",
  },
  {
    name: "Hearthstone",
    href: "/admin/recruits/hearthstone",
    description: "View and manage Hearthstone recruits",
  },

  {
    name: "Smash",
    href: "/admin/recruits/smash",
    description: "View and manage Smash recruits",
  },

  {
    name: "Mario Kart",
    href: "/admin/recruits/mario-kart",
    description: "View and manage Mario Kart recruits",
  }
];

export default function AdminHome() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [me, setMe] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }

    (async () => {
      const res = await fetch(`${apiUrl}/api/v1/admin/whoami`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        localStorage.removeItem("au_admin_token");
        router.push("/admin/login");
        return;
      }

      setMe(await res.json());
    })();
  }, [apiUrl, router]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Admin Portal</h1>
          {me ? (
            <p className="mt-1 text-sm text-neutral-400">
              Signed in as {me.username} • {me.role}
            </p>
          ) : (
            <p className="mt-1 text-sm text-neutral-400">Loading session...</p>
          )}
        </div>

        <button
          onClick={() => {
            localStorage.removeItem("au_admin_token");
            localStorage.removeItem("au_admin_role");
            localStorage.removeItem("au_admin_username");
            router.push("/admin/login");
          }}
          className="rounded-lg border border-neutral-800 bg-neutral-950 px-4 py-2 text-sm hover:border-neutral-700"
        >
          Log Out
        </button>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-2">
        {gameCards.map((game) =>
          game.href === "#" ? (
            <div
              key={game.name}
              className="rounded-2xl border border-neutral-800 bg-neutral-950 p-5 opacity-70"
            >
              <h2 className="text-xl font-medium">{game.name}</h2>
              <p className="mt-2 text-sm text-neutral-400">{game.description}</p>
            </div>
          ) : (
            <Link
              key={game.name}
              href={game.href}
              className="rounded-2xl border border-neutral-800 bg-neutral-950 p-5 transition hover:border-neutral-700"
            >
              <h2 className="text-xl font-medium">{game.name}</h2>
              <p className="mt-2 text-sm text-neutral-400">{game.description}</p>
            </Link>
          )
        )}
      </div>
    </div>
  );
}
