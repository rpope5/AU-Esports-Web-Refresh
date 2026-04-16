"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { canAccessGame, clearAdminStorage, formatRoleLabel, parseAdminSession, type AdminSession } from "./_lib/session";

type RecruitGameCard = {
  name: string;
  slug?: string;
  href: string;
  description: string;
  requiredPermission?: keyof AdminSession["permissions"];
};

const RECRUIT_GAME_CARDS: RecruitGameCard[] = [
  {
    name: "Schedule",
    href: "/admin/schedule",
    description: "Create and manage public calendar events",
    requiredPermission: "can_manage_schedule",
  },
  {
    name: "Valorant",
    slug: "valorant",
    href: "/admin/recruits/valorant",
    description: "View and manage Valorant recruits",
  },
  {
    name: "CS2",
    slug: "cs2",
    href: "/admin/recruits/cs2",
    description: "View and manage Counter-Strike 2 recruits",
  },
  {
    name: "Fortnite",
    slug: "fortnite",
    href: "/admin/recruits/fortnite",
    description: "View and manage Fortnite recruits",
  },
  {
    name: "Rainbow Six Siege",
    slug: "r6",
    href: "/admin/recruits/r6",
    description: "View and manage Rainbow Six Siege recruits",
  },
  {
    name: "Rocket League",
    slug: "rocket-league",
    href: "/admin/recruits/rocket-league",
    description: "View and manage Rocket League recruits",
  },
  {
    name: "Overwatch",
    slug: "overwatch",
    href: "/admin/recruits/overwatch",
    description: "View and manage Overwatch recruits",
  },
  {
    name: "Call of Duty",
    slug: "cod",
    href: "/admin/recruits/cod",
    description: "View and manage Call of Duty recruits",
  },
  {
    name: "Hearthstone",
    slug: "hearthstone",
    href: "/admin/recruits/hearthstone",
    description: "View and manage Hearthstone recruits",
  },
  {
    name: "Smash",
    slug: "smash",
    href: "/admin/recruits/smash",
    description: "View and manage Smash recruits",
  },
  {
    name: "Mario Kart",
    slug: "mario-kart",
    href: "/admin/recruits/mario-kart",
    description: "View and manage Mario Kart recruits",
  },
];

export default function AdminHome() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [me, setMe] = useState<AdminSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const visibleRecruitCards = useMemo(() => {
    if (!me) return [];
    return RECRUIT_GAME_CARDS.filter((game) => {
      if (game.requiredPermission && !me.permissions[game.requiredPermission]) {
        return false;
      }
      if (!game.slug) return true;
      return canAccessGame(me, game.slug);
    });
  }, [me]);

  useEffect(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }

    (async () => {
      try {
        const res = await fetch(`${apiUrl}/api/v1/admin/whoami`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (res.status === 401) {
          clearAdminStorage();
          router.push("/admin/login");
          return;
        }

        if (!res.ok) {
          const text = await res.text();
          setError(text || "Failed to load session");
          return;
        }

        setMe(parseAdminSession(await res.json()));
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load session");
      } finally {
        setLoading(false);
      }
    })();
  }, [apiUrl, router]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Admin Portal</h1>
          {me ? (
            <p className="mt-1 text-sm text-neutral-400">
              Signed in as {me.username} - {formatRoleLabel(me.role)}
            </p>
          ) : loading ? (
            <p className="mt-1 text-sm text-neutral-400">Loading session...</p>
          ) : (
            <p className="mt-1 text-sm text-red-400">{error || "Session unavailable"}</p>
          )}
        </div>

        <button
          onClick={() => {
            clearAdminStorage();
            router.push("/admin/login");
          }}
          className="rounded-lg border border-neutral-800 bg-neutral-950 px-4 py-2 text-sm hover:border-neutral-700"
        >
          Log Out
        </button>
      </div>

      {me?.permissions.can_manage_announcements && (
        <div className="mt-8">
          <Link
            href="/admin/news"
            className="block rounded-2xl border border-neutral-800 bg-neutral-950 p-5 transition hover:border-neutral-700"
          >
            <h2 className="text-xl font-medium">Announcements</h2>
            <p className="mt-2 text-sm text-neutral-400">Create and manage esports news announcements</p>
          </Link>
        </div>
      )}

      {me?.permissions.can_view_roster && (
        <div className="mt-4">
          <Link
            href="/admin/roster"
            className="block rounded-2xl border border-neutral-800 bg-neutral-950 p-5 transition hover:border-neutral-700"
          >
            <h2 className="text-xl font-medium">Roster</h2>
            <p className="mt-2 text-sm text-neutral-400">Create, edit, and manage public roster members</p>
          </Link>
        </div>
      )}

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {visibleRecruitCards.map((game) => (
          <Link
            key={game.href}
            href={game.href}
            className="rounded-2xl border border-neutral-800 bg-neutral-950 p-5 transition hover:border-neutral-700"
          >
            <h2 className="text-xl font-medium">{game.name}</h2>
            <p className="mt-2 text-sm text-neutral-400">{game.description}</p>
          </Link>
        ))}
      </div>

      {!loading && me && visibleRecruitCards.length === 0 && (
        <div className="mt-8 rounded-xl border border-neutral-800 bg-neutral-950 p-4 text-sm text-neutral-300">
          No recruit game assignments are currently available for this account.
        </div>
      )}
    </div>
  );
}
