"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import RosterCard from "@/components/RosterCard";
import type { Player } from "@/types/Player";
import InlineDestructiveConfirm from "../_components/InlineDestructiveConfirm";
import { clearAdminStorage, formatRoleLabel, parseAdminSession, type AdminSession } from "../_lib/session";

type RosterFormState = {
  name: string;
  gamertag: string;
  game: string;
  role: string;
  rank: string;
  year: string;
  major: string;
  headshot_url: string;
};

const EMPTY_FORM: RosterFormState = {
  name: "",
  gamertag: "",
  game: "",
  role: "",
  rank: "",
  year: "",
  major: "",
  headshot_url: "",
};

function normalizeField(value: string): string {
  return value.trim();
}

function appendOptional(formData: FormData, key: keyof RosterFormState, value: string): void {
  formData.append(key, normalizeField(value));
}

export default function AdminRosterPage() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [session, setSession] = useState<AdminSession | null>(null);
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [createForm, setCreateForm] = useState<RosterFormState>(EMPTY_FORM);
  const [createHeadshot, setCreateHeadshot] = useState<File | null>(null);
  const [creating, setCreating] = useState(false);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<RosterFormState>(EMPTY_FORM);
  const [editHeadshot, setEditHeadshot] = useState<File | null>(null);
  const [removeEditHeadshot, setRemoveEditHeadshot] = useState(false);
  const [busyPlayerId, setBusyPlayerId] = useState<number | null>(null);
  const [deletingPlayerId, setDeletingPlayerId] = useState<number | null>(null);

  const canViewRoster = Boolean(session?.permissions.can_view_roster);
  const canManageRoster = Boolean(session?.permissions.can_manage_roster);
  const canDeleteRoster = Boolean(session?.permissions.can_delete_roster);

  function updateCreateField<K extends keyof RosterFormState>(field: K, value: RosterFormState[K]): void {
    setCreateForm((prev) => ({ ...prev, [field]: value }));
  }

  function updateEditField<K extends keyof RosterFormState>(field: K, value: RosterFormState[K]): void {
    setEditForm((prev) => ({ ...prev, [field]: value }));
  }

  const loadRoster = useCallback(
    async (token: string) => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${apiUrl}/api/v1/admin/roster`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (res.status === 401) {
          clearAdminStorage();
          router.push("/admin/login");
          return;
        }
        if (res.status === 403) {
          setError("You do not have permission to view roster members.");
          return;
        }
        if (!res.ok) {
          const responseText = await res.text();
          throw new Error(responseText || "Failed to load roster");
        }

        const data = (await res.json()) as Player[];
        setPlayers(Array.isArray(data) ? data : []);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load roster");
      } finally {
        setLoading(false);
      }
    },
    [apiUrl, router],
  );

  useEffect(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }

    const init = async () => {
      try {
        const whoamiRes = await fetch(`${apiUrl}/api/v1/admin/whoami`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (whoamiRes.status === 401) {
          clearAdminStorage();
          router.push("/admin/login");
          return;
        }
        if (!whoamiRes.ok) {
          const responseText = await whoamiRes.text();
          throw new Error(responseText || "Failed to validate admin session");
        }

        const parsedSession = parseAdminSession(await whoamiRes.json());
        setSession(parsedSession);

        if (!parsedSession.permissions.can_view_roster) {
          setError("You do not have permission to view roster members.");
          setLoading(false);
          return;
        }

        await loadRoster(token);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to initialize roster editor");
        setLoading(false);
      }
    };

    void init();
  }, [apiUrl, loadRoster, router]);

  function beginEdit(player: Player): void {
    setEditingId(player.id);
    setEditForm({
      name: player.name ?? "",
      gamertag: player.gamertag ?? "",
      game: player.game ?? "",
      role: player.role ?? "",
      rank: player.rank ?? "",
      year: player.year ?? "",
      major: player.major ?? "",
      headshot_url: player.headshot ?? "",
    });
    setEditHeadshot(null);
    setRemoveEditHeadshot(false);
  }

  function cancelEdit(): void {
    setEditingId(null);
    setEditForm(EMPTY_FORM);
    setEditHeadshot(null);
    setRemoveEditHeadshot(false);
  }

  async function createPlayer(): Promise<void> {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }
    if (!canManageRoster) {
      setError("You do not have permission to create roster members.");
      return;
    }

    const name = normalizeField(createForm.name);
    const gamertag = normalizeField(createForm.gamertag);
    const game = normalizeField(createForm.game);
    if (!name || !gamertag || !game) {
      setError("Name, gamertag, and game are required.");
      return;
    }

    setCreating(true);
    setError(null);
    setSuccess(null);
    try {
      const formData = new FormData();
      formData.append("name", name);
      formData.append("gamertag", gamertag);
      formData.append("game", game);
      appendOptional(formData, "role", createForm.role);
      appendOptional(formData, "rank", createForm.rank);
      appendOptional(formData, "year", createForm.year);
      appendOptional(formData, "major", createForm.major);
      appendOptional(formData, "headshot_url", createForm.headshot_url);
      if (createHeadshot) formData.append("headshot", createHeadshot);

      const res = await fetch(`${apiUrl}/api/v1/admin/roster`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (res.status === 401) {
        clearAdminStorage();
        router.push("/admin/login");
        return;
      }
      if (res.status === 403) {
        setError("You do not have permission to create roster members.");
        return;
      }
      if (!res.ok) {
        const responseText = await res.text();
        throw new Error(responseText || "Failed to create roster member");
      }

      setCreateForm(EMPTY_FORM);
      setCreateHeadshot(null);
      setSuccess("Roster member created.");
      await loadRoster(token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create roster member");
    } finally {
      setCreating(false);
    }
  }

  async function saveEdit(playerId: number): Promise<void> {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }
    if (!canManageRoster) {
      setError("You do not have permission to edit roster members.");
      return;
    }

    const name = normalizeField(editForm.name);
    const gamertag = normalizeField(editForm.gamertag);
    const game = normalizeField(editForm.game);
    if (!name || !gamertag || !game) {
      setError("Name, gamertag, and game are required.");
      return;
    }

    setBusyPlayerId(playerId);
    setError(null);
    setSuccess(null);
    try {
      const formData = new FormData();
      formData.append("name", name);
      formData.append("gamertag", gamertag);
      formData.append("game", game);
      appendOptional(formData, "role", editForm.role);
      appendOptional(formData, "rank", editForm.rank);
      appendOptional(formData, "year", editForm.year);
      appendOptional(formData, "major", editForm.major);
      appendOptional(formData, "headshot_url", editForm.headshot_url);
      if (removeEditHeadshot) formData.append("remove_headshot", "true");
      if (editHeadshot) formData.append("headshot", editHeadshot);

      const res = await fetch(`${apiUrl}/api/v1/admin/roster/${playerId}`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (res.status === 401) {
        clearAdminStorage();
        router.push("/admin/login");
        return;
      }
      if (res.status === 403) {
        setError("You do not have permission to edit roster members.");
        return;
      }
      if (!res.ok) {
        const responseText = await res.text();
        throw new Error(responseText || "Failed to update roster member");
      }

      setSuccess("Roster member updated.");
      cancelEdit();
      await loadRoster(token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update roster member");
    } finally {
      setBusyPlayerId(null);
    }
  }

  async function deletePlayer(playerId: number): Promise<void> {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      throw new Error("Session expired");
    }
    if (!canDeleteRoster) {
      throw new Error("You do not have permission to delete roster members.");
    }

    setDeletingPlayerId(playerId);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`${apiUrl}/api/v1/admin/roster/${playerId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.status === 401) {
        clearAdminStorage();
        router.push("/admin/login");
        throw new Error("Unauthorized");
      }
      if (res.status === 403) {
        throw new Error("You do not have permission to delete roster members.");
      }
      if (res.status === 404) {
        setPlayers((prev) => prev.filter((player) => player.id !== playerId));
        setSuccess("Roster member was already removed.");
        return;
      }
      if (res.status !== 204) {
        const responseText = await res.text();
        throw new Error(responseText || "Failed to delete roster member");
      }

      setPlayers((prev) => prev.filter((player) => player.id !== playerId));
      setSuccess("Roster member deleted.");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete roster member";
      setError(message);
      throw new Error(message);
    } finally {
      setDeletingPlayerId(null);
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Roster Editor</h1>
          <p className="mt-1 text-sm text-neutral-400">
            {session ? `Signed in as ${session.username} - ${formatRoleLabel(session.role)}` : "Loading session..."}
          </p>
        </div>
        <Link
          href="/admin"
          className="rounded-lg border border-neutral-800 bg-neutral-950 px-4 py-2 text-sm hover:border-neutral-700"
        >
          Back to Admin
        </Link>
      </div>

      {canViewRoster && canManageRoster ? (
        <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
          <h2 className="text-xl font-medium">Add Roster Member</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <input
              className="rounded-lg border border-neutral-800 bg-neutral-900 p-2 text-sm"
              placeholder="Name"
              value={createForm.name}
              onChange={(event) => updateCreateField("name", event.target.value)}
            />
            <input
              className="rounded-lg border border-neutral-800 bg-neutral-900 p-2 text-sm"
              placeholder="Gamertag"
              value={createForm.gamertag}
              onChange={(event) => updateCreateField("gamertag", event.target.value)}
            />
            <input
              className="rounded-lg border border-neutral-800 bg-neutral-900 p-2 text-sm"
              placeholder="Game"
              value={createForm.game}
              onChange={(event) => updateCreateField("game", event.target.value)}
            />
            <input
              className="rounded-lg border border-neutral-800 bg-neutral-900 p-2 text-sm"
              placeholder="Role"
              value={createForm.role}
              onChange={(event) => updateCreateField("role", event.target.value)}
            />
            <input
              className="rounded-lg border border-neutral-800 bg-neutral-900 p-2 text-sm"
              placeholder="Rank"
              value={createForm.rank}
              onChange={(event) => updateCreateField("rank", event.target.value)}
            />
            <input
              className="rounded-lg border border-neutral-800 bg-neutral-900 p-2 text-sm"
              placeholder="Year"
              value={createForm.year}
              onChange={(event) => updateCreateField("year", event.target.value)}
            />
            <input
              className="rounded-lg border border-neutral-800 bg-neutral-900 p-2 text-sm"
              placeholder="Major"
              value={createForm.major}
              onChange={(event) => updateCreateField("major", event.target.value)}
            />
            <input
              className="rounded-lg border border-neutral-800 bg-neutral-900 p-2 text-sm"
              placeholder="Headshot URL (optional)"
              value={createForm.headshot_url}
              onChange={(event) => updateCreateField("headshot_url", event.target.value)}
            />
          </div>

          <div className="mt-3">
            <label className="text-sm text-neutral-300">Upload Headshot (Optional)</label>
            <input
              className="mt-1 block w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2 text-sm file:mr-3 file:rounded file:border-0 file:bg-neutral-800 file:px-3 file:py-1.5 file:text-sm"
              type="file"
              accept="image/*"
              onChange={(event) => setCreateHeadshot(event.target.files?.[0] || null)}
            />
            <p className="mt-1 text-xs text-neutral-500">
              Uploaded headshots are stored under `/uploads/roster`, separate from announcement images.
            </p>
          </div>

          <div className="mt-4">
            <button
              type="button"
              disabled={creating}
              onClick={() => void createPlayer()}
              className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-black disabled:opacity-60"
            >
              {creating ? "Creating..." : "Create Roster Member"}
            </button>
          </div>
        </section>
      ) : canViewRoster ? (
        <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
          <h2 className="text-xl font-medium">Roster Access</h2>
          <p className="mt-2 text-sm text-neutral-400">
            This account can view roster members but cannot edit them.
          </p>
        </section>
      ) : null}

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
      {success && <p className="mt-4 text-sm text-emerald-400">{success}</p>}

      <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-xl font-medium">Roster Members</h2>
          <span className="text-sm text-neutral-400">{players.length} total</span>
        </div>

        {loading ? (
          <p className="mt-4 text-sm text-neutral-400">Loading roster...</p>
        ) : !canViewRoster ? (
          <p className="mt-4 text-sm text-red-400">You do not have permission to view roster members.</p>
        ) : players.length === 0 ? (
          <p className="mt-4 text-sm text-neutral-400">No roster members yet.</p>
        ) : (
          <div className="mt-6 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {players.map((player) => {
              const isEditing = editingId === player.id;
              const isBusy = busyPlayerId === player.id || deletingPlayerId === player.id;

              return (
                <article key={player.id} className="rounded-xl border border-neutral-800 bg-black/50 p-4">
                  <RosterCard player={player} />

                  <div className="mt-4 flex flex-wrap gap-2">
                    {canManageRoster && (
                      <button
                        type="button"
                        className="rounded-lg border border-neutral-700 px-3 py-1.5 text-xs hover:border-neutral-500"
                        onClick={() => (isEditing ? cancelEdit() : beginEdit(player))}
                        disabled={isBusy}
                      >
                        {isEditing ? "Cancel Edit" : "Edit"}
                      </button>
                    )}
                    {canDeleteRoster && (
                      <InlineDestructiveConfirm
                        triggerLabel="Delete"
                        confirmMessage="This roster member is about to be permanently deleted."
                        confirmLabel="Delete Permanently"
                        pendingLabel="Deleting..."
                        busy={deletingPlayerId === player.id}
                        onConfirm={() => deletePlayer(player.id)}
                      />
                    )}
                  </div>

                  {isEditing && canManageRoster && (
                    <div className="mt-4 grid gap-2">
                      <input
                        className="rounded border border-neutral-700 bg-neutral-900 p-2 text-xs"
                        value={editForm.name}
                        onChange={(event) => updateEditField("name", event.target.value)}
                        placeholder="Name"
                      />
                      <input
                        className="rounded border border-neutral-700 bg-neutral-900 p-2 text-xs"
                        value={editForm.gamertag}
                        onChange={(event) => updateEditField("gamertag", event.target.value)}
                        placeholder="Gamertag"
                      />
                      <input
                        className="rounded border border-neutral-700 bg-neutral-900 p-2 text-xs"
                        value={editForm.game}
                        onChange={(event) => updateEditField("game", event.target.value)}
                        placeholder="Game"
                      />
                      <input
                        className="rounded border border-neutral-700 bg-neutral-900 p-2 text-xs"
                        value={editForm.role}
                        onChange={(event) => updateEditField("role", event.target.value)}
                        placeholder="Role"
                      />
                      <input
                        className="rounded border border-neutral-700 bg-neutral-900 p-2 text-xs"
                        value={editForm.rank}
                        onChange={(event) => updateEditField("rank", event.target.value)}
                        placeholder="Rank"
                      />
                      <input
                        className="rounded border border-neutral-700 bg-neutral-900 p-2 text-xs"
                        value={editForm.year}
                        onChange={(event) => updateEditField("year", event.target.value)}
                        placeholder="Year"
                      />
                      <input
                        className="rounded border border-neutral-700 bg-neutral-900 p-2 text-xs"
                        value={editForm.major}
                        onChange={(event) => updateEditField("major", event.target.value)}
                        placeholder="Major"
                      />
                      <input
                        className="rounded border border-neutral-700 bg-neutral-900 p-2 text-xs"
                        value={editForm.headshot_url}
                        onChange={(event) => updateEditField("headshot_url", event.target.value)}
                        placeholder="Headshot URL"
                      />
                      <input
                        className="block w-full rounded border border-neutral-700 bg-neutral-900 p-2 text-xs file:mr-3 file:rounded file:border-0 file:bg-neutral-800 file:px-3 file:py-1.5 file:text-xs"
                        type="file"
                        accept="image/*"
                        onChange={(event) => setEditHeadshot(event.target.files?.[0] || null)}
                      />
                      <label className="flex items-center gap-2 text-xs text-neutral-300">
                        <input
                          type="checkbox"
                          checked={removeEditHeadshot}
                          onChange={(event) => setRemoveEditHeadshot(event.target.checked)}
                        />
                        Remove existing headshot
                      </label>
                      <button
                        type="button"
                        className="rounded-lg border border-neutral-700 px-3 py-1.5 text-xs hover:border-neutral-500 disabled:opacity-60"
                        onClick={() => void saveEdit(player.id)}
                        disabled={isBusy}
                      >
                        {isBusy ? "Saving..." : "Save Changes"}
                      </button>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
