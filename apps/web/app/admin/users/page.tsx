"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import InlineDestructiveConfirm from "../_components/InlineDestructiveConfirm";
import { clearAdminStorage, formatRoleLabel, parseAdminSession, type AdminSession } from "../_lib/session";
import { canRenderDeleteAccountAction } from "./deleteVisibility";

type StaffRole = "admin" | "head_coach" | "coach" | "captain";

type UserScope = {
  game_id: number;
  game_slug: string;
  game_name: string;
};

type ManagedUser = {
  id: number;
  username: string;
  email: string | null;
  role: StaffRole;
  is_active: boolean;
  must_change_password: boolean;
  has_global_game_access: boolean;
  scopes: UserScope[];
  created_at: string | null;
  updated_at: string | null;
  manageable: boolean;
};

type UserManagementOptions = {
  viewer_role: StaffRole;
  assignable_roles: StaffRole[];
  scope_game_ids: number[];
  scope_game_slugs: string[];
  games: UserScope[];
};

type CreateUserForm = {
  username: string;
  email: string;
  password: string;
  role: StaffRole;
  game_ids: number[];
  is_active: boolean;
  must_change_password: boolean;
};

type EditUserForm = {
  email: string;
  role: StaffRole;
  game_ids: number[];
  is_active: boolean;
  must_change_password: boolean;
};

const ALL_ROLE_OPTIONS: StaffRole[] = ["admin", "head_coach", "coach", "captain"];

function formatTimestamp(raw: string | null): string {
  if (!raw) return "N/A";
  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(raw);
  const parsed = new Date(hasTimezone ? raw : `${raw}Z`);
  if (Number.isNaN(parsed.getTime())) return "N/A";
  return parsed.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function buildInitialCreateForm(options: UserManagementOptions | null): CreateUserForm {
  const assignableRoles = options?.assignable_roles ?? ["coach", "captain"];
  const defaultRole = assignableRoles[0] ?? "coach";
  return {
    username: "",
    email: "",
    password: "",
    role: defaultRole,
    game_ids: [],
    is_active: true,
    must_change_password: true,
  };
}

function normalizeOptional(value: string): string {
  return value.trim();
}

export default function AdminUsersPage() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [session, setSession] = useState<AdminSession | null>(null);
  const [options, setOptions] = useState<UserManagementOptions | null>(null);
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<"all" | StaffRole>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [gameFilter, setGameFilter] = useState<"all" | number>("all");

  const [createForm, setCreateForm] = useState<CreateUserForm>(buildInitialCreateForm(null));
  const [creating, setCreating] = useState(false);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<EditUserForm | null>(null);
  const [busyUserId, setBusyUserId] = useState<number | null>(null);

  const canManageUsers = Boolean(session?.permissions.can_manage_users);
  const canDeleteAccounts = canRenderDeleteAccountAction(session?.role);
  const assignableRoles = useMemo(() => options?.assignable_roles ?? [], [options?.assignable_roles]);
  const availableScopeGames = options?.games ?? [];

  const filteredRoleOptions = useMemo(
    () => ALL_ROLE_OPTIONS.filter((role) => assignableRoles.includes(role)),
    [assignableRoles],
  );
  const roleFilterOptions = useMemo(() => {
    if (session?.role === "admin") return ALL_ROLE_OPTIONS;
    return ALL_ROLE_OPTIONS.filter((role) => assignableRoles.includes(role));
  }, [assignableRoles, session?.role]);

  const clearAndRedirectToLogin = useCallback(() => {
    clearAdminStorage();
    router.push("/admin/login");
  }, [router]);

  const getToken = useCallback(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) router.push("/admin/login");
    return token;
  }, [router]);

  const loadUsers = useCallback(
    async (token: string) => {
      if (!canManageUsers) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (search.trim()) params.set("search", search.trim());
        if (roleFilter !== "all") params.set("role", roleFilter);
        if (statusFilter === "active") params.set("is_active", "true");
        if (statusFilter === "inactive") params.set("is_active", "false");
        if (gameFilter !== "all") params.set("game_id", String(gameFilter));
        params.set("limit", "500");

        const response = await fetch(`${apiUrl}/api/v1/admin/users?${params.toString()}`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.status === 401) {
          clearAndRedirectToLogin();
          return;
        }
        if (response.status === 403) {
          setError("You do not have permission to manage users.");
          return;
        }
        if (!response.ok) {
          throw new Error((await response.text()) || "Failed to load users");
        }

        const data = (await response.json()) as ManagedUser[];
        setUsers(Array.isArray(data) ? data : []);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load users");
      } finally {
        setLoading(false);
      }
    },
    [apiUrl, canManageUsers, clearAndRedirectToLogin, gameFilter, roleFilter, search, statusFilter],
  );

  const initializePage = useCallback(async () => {
    const token = getToken();
    if (!token) return;

    try {
      const whoamiResponse = await fetch(`${apiUrl}/api/v1/admin/whoami`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (whoamiResponse.status === 401) {
        clearAndRedirectToLogin();
        return;
      }
      if (!whoamiResponse.ok) {
        throw new Error((await whoamiResponse.text()) || "Failed to validate session");
      }

      const parsedSession = parseAdminSession(await whoamiResponse.json());
      setSession(parsedSession);

      if (!parsedSession.permissions.can_manage_users) {
        setError("You do not have permission to manage users.");
        setLoading(false);
        return;
      }

      const optionsResponse = await fetch(`${apiUrl}/api/v1/admin/users/options`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (optionsResponse.status === 401) {
        clearAndRedirectToLogin();
        return;
      }
      if (!optionsResponse.ok) {
        throw new Error((await optionsResponse.text()) || "Failed to load user-management options");
      }

      const parsedOptions = (await optionsResponse.json()) as UserManagementOptions;
      setOptions(parsedOptions);
      setCreateForm(buildInitialCreateForm(parsedOptions));

      await loadUsers(token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to initialize user management");
      setLoading(false);
    }
  }, [apiUrl, clearAndRedirectToLogin, getToken, loadUsers]);

  useEffect(() => {
    void initializePage();
  }, [initializePage]);

  useEffect(() => {
    if (!session?.permissions.can_manage_users) return;
    const token = localStorage.getItem("au_admin_token");
    if (!token) return;
    void loadUsers(token);
  }, [loadUsers, session?.permissions.can_manage_users]);

  useEffect(() => {
    if (roleFilter === "all") return;
    if (!roleFilterOptions.includes(roleFilter)) {
      setRoleFilter("all");
    }
  }, [roleFilter, roleFilterOptions]);

  function toggleGameSelection(selectedIds: number[], gameId: number): number[] {
    if (selectedIds.includes(gameId)) return selectedIds.filter((id) => id !== gameId);
    return [...selectedIds, gameId];
  }

  function beginEdit(user: ManagedUser): void {
    setEditingUserId(user.id);
    setEditForm({
      email: user.email || "",
      role: user.role,
      game_ids: user.scopes.map((scope) => scope.game_id),
      is_active: user.is_active,
      must_change_password: user.must_change_password,
    });
    setError(null);
    setSuccess(null);
  }

  function cancelEdit(): void {
    setEditingUserId(null);
    setEditForm(null);
  }

  async function createUser(): Promise<void> {
    const token = getToken();
    if (!token) return;

    const payload = {
      username: createForm.username.trim(),
      email: normalizeOptional(createForm.email) || null,
      password: createForm.password,
      role: createForm.role,
      game_ids: createForm.game_ids,
      is_active: createForm.is_active,
      must_change_password: createForm.must_change_password,
    };

    if (!payload.username || !payload.password) {
      setError("Username and password are required.");
      return;
    }

    setCreating(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch(`${apiUrl}/api/v1/admin/users`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (response.status === 401) {
        clearAndRedirectToLogin();
        return;
      }
      if (!response.ok) {
        throw new Error((await response.text()) || "Failed to create user");
      }

      setCreateForm(buildInitialCreateForm(options));
      setSuccess("User account created.");
      await loadUsers(token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create user");
    } finally {
      setCreating(false);
    }
  }

  async function saveEdit(userId: number): Promise<void> {
    const token = getToken();
    if (!token || !editForm) return;

    setBusyUserId(userId);
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch(`${apiUrl}/api/v1/admin/users/${userId}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: normalizeOptional(editForm.email) || null,
          role: editForm.role,
          game_ids: editForm.game_ids,
          is_active: editForm.is_active,
          must_change_password: editForm.must_change_password,
        }),
      });

      if (response.status === 401) {
        clearAndRedirectToLogin();
        return;
      }
      if (!response.ok) {
        throw new Error((await response.text()) || "Failed to update user");
      }

      setSuccess("User updated.");
      cancelEdit();
      await loadUsers(token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update user");
    } finally {
      setBusyUserId(null);
    }
  }

  async function toggleUserActive(user: ManagedUser): Promise<void> {
    const token = getToken();
    if (!token) return;

    setBusyUserId(user.id);
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch(`${apiUrl}/api/v1/admin/users/${user.id}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ is_active: !user.is_active }),
      });

      if (response.status === 401) {
        clearAndRedirectToLogin();
        return;
      }
      if (!response.ok) {
        throw new Error((await response.text()) || "Failed to update active status");
      }

      setSuccess(user.is_active ? "User deactivated." : "User reactivated.");
      await loadUsers(token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update active status");
    } finally {
      setBusyUserId(null);
    }
  }

  async function resetPassword(user: ManagedUser): Promise<void> {
    const token = getToken();
    if (!token) return;

    const newPassword = window.prompt(`Set temporary password for ${user.username}`);
    if (!newPassword) return;

    const mustChange = window.confirm("Force password change on next login?");

    setBusyUserId(user.id);
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch(`${apiUrl}/api/v1/admin/users/${user.id}/reset-password`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          new_password: newPassword,
          must_change_password: mustChange,
        }),
      });

      if (response.status === 401) {
        clearAndRedirectToLogin();
        return;
      }
      if (!response.ok) {
        throw new Error((await response.text()) || "Failed to reset password");
      }

      setSuccess(`Password reset for ${user.username}.`);
      await loadUsers(token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to reset password");
    } finally {
      setBusyUserId(null);
    }
  }

  async function deleteUserAccount(user: ManagedUser): Promise<void> {
    if (!canDeleteAccounts) {
      throw new Error("You do not have permission to delete accounts.");
    }

    const token = getToken();
    if (!token) throw new Error("Session expired");

    setBusyUserId(user.id);
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch(`${apiUrl}/api/v1/admin/users/${user.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.status === 401) {
        clearAndRedirectToLogin();
        throw new Error("Unauthorized");
      }
      if (!response.ok) {
        throw new Error((await response.text()) || "Failed to delete account");
      }

      if (editingUserId === user.id) {
        cancelEdit();
      }
      setSuccess(`Deleted account for ${user.username}.`);
      await loadUsers(token);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete account";
      setError(message);
      throw new Error(message);
    } finally {
      setBusyUserId(null);
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">User Management</h1>
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

      {!canManageUsers ? (
        <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
          <p className="text-sm text-red-400">You do not have permission to manage users.</p>
        </section>
      ) : (
        <>
          <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
            <h2 className="text-xl font-medium">Create Staff Account</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <input
                className="rounded border border-neutral-700 bg-black p-2 text-sm"
                placeholder="Username"
                value={createForm.username}
                onChange={(event) => setCreateForm((prev) => ({ ...prev, username: event.target.value }))}
              />
              <input
                className="rounded border border-neutral-700 bg-black p-2 text-sm"
                placeholder="Email (optional)"
                value={createForm.email}
                onChange={(event) => setCreateForm((prev) => ({ ...prev, email: event.target.value }))}
              />
              <input
                className="rounded border border-neutral-700 bg-black p-2 text-sm"
                type="password"
                placeholder="Temporary password"
                value={createForm.password}
                onChange={(event) => setCreateForm((prev) => ({ ...prev, password: event.target.value }))}
              />
              <select
                className="rounded border border-neutral-700 bg-black p-2 text-sm"
                value={createForm.role}
                onChange={(event) => setCreateForm((prev) => ({ ...prev, role: event.target.value as StaffRole }))}
              >
                {filteredRoleOptions.map((role) => (
                  <option key={role} value={role}>
                    {formatRoleLabel(role)}
                  </option>
                ))}
              </select>
            </div>

            <div className="mt-4 rounded border border-neutral-800 bg-neutral-900/40 p-3">
              <p className="text-sm text-neutral-300">Game scope</p>
              <div className="mt-2 grid gap-2 md:grid-cols-2">
                {availableScopeGames.map((game) => (
                  <label key={game.game_id} className="flex items-center gap-2 text-sm text-neutral-200">
                    <input
                      type="checkbox"
                      checked={createForm.game_ids.includes(game.game_id)}
                      onChange={() =>
                        setCreateForm((prev) => ({
                          ...prev,
                          game_ids: toggleGameSelection(prev.game_ids, game.game_id),
                        }))
                      }
                    />
                    {game.game_name}
                  </label>
                ))}
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-4 text-sm">
              <label className="flex items-center gap-2 text-neutral-200">
                <input
                  type="checkbox"
                  checked={createForm.is_active}
                  onChange={(event) => setCreateForm((prev) => ({ ...prev, is_active: event.target.checked }))}
                />
                Active account
              </label>
              <label className="flex items-center gap-2 text-neutral-200">
                <input
                  type="checkbox"
                  checked={createForm.must_change_password}
                  onChange={(event) =>
                    setCreateForm((prev) => ({ ...prev, must_change_password: event.target.checked }))
                  }
                />
                Force password change on next login
              </label>
            </div>

            <div className="mt-4">
              <button
                type="button"
                disabled={creating}
                onClick={() => void createUser()}
                className="rounded bg-white px-4 py-2 text-sm font-medium text-black disabled:opacity-60"
              >
                {creating ? "Creating..." : "Create Account"}
              </button>
            </div>
          </section>

          <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
            <h2 className="text-xl font-medium">Staff Accounts</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-4">
              <input
                className="rounded border border-neutral-700 bg-black p-2 text-sm"
                placeholder="Search username/email"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <select
                className="rounded border border-neutral-700 bg-black p-2 text-sm"
                value={roleFilter}
                onChange={(event) => setRoleFilter(event.target.value as "all" | StaffRole)}
              >
                <option value="all">All roles</option>
                {roleFilterOptions.map((role) => (
                  <option key={role} value={role}>
                    {formatRoleLabel(role)}
                  </option>
                ))}
              </select>
              <select
                className="rounded border border-neutral-700 bg-black p-2 text-sm"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as "all" | "active" | "inactive")}
              >
                <option value="all">All statuses</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
              <select
                className="rounded border border-neutral-700 bg-black p-2 text-sm"
                value={gameFilter === "all" ? "all" : String(gameFilter)}
                onChange={(event) =>
                  setGameFilter(event.target.value === "all" ? "all" : Number(event.target.value))
                }
              >
                <option value="all">All games</option>
                {availableScopeGames.map((game) => (
                  <option key={game.game_id} value={String(game.game_id)}>
                    {game.game_name}
                  </option>
                ))}
              </select>
            </div>

            {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
            {success && <p className="mt-4 text-sm text-emerald-400">{success}</p>}

            {loading ? (
              <p className="mt-4 text-sm text-neutral-400">Loading users...</p>
            ) : users.length === 0 ? (
              <p className="mt-4 text-sm text-neutral-400">No users found for the current filters.</p>
            ) : (
              <div className="mt-4 grid gap-3">
                {users.map((user) => {
                  const isEditing = editingUserId === user.id && editForm;
                  const isBusy = busyUserId === user.id;
                  return (
                    <article key={user.id} className="rounded-xl border border-neutral-800 bg-black/60 p-4">
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0 lg:flex-1">
                          <h3 className="text-lg font-semibold">{user.username}</h3>
                          <p className="text-sm text-neutral-400">{user.email || "No email"}</p>
                          <div className="mt-2 flex flex-wrap gap-2 text-xs">
                            <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                              Role: {formatRoleLabel(user.role)}
                            </span>
                            <span
                              className={`rounded-full border px-2 py-0.5 ${
                                user.is_active
                                  ? "border-emerald-700/70 bg-emerald-950/30 text-emerald-200"
                                  : "border-red-700/70 bg-red-950/30 text-red-200"
                              }`}
                            >
                              {user.is_active ? "Active" : "Inactive"}
                            </span>
                            <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                              Must change password: {user.must_change_password ? "Yes" : "No"}
                            </span>
                            <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                              Created: {formatTimestamp(user.created_at)}
                            </span>
                            <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                              Updated: {formatTimestamp(user.updated_at)}
                            </span>
                          </div>
                          <p className="mt-2 text-xs text-neutral-400">
                            Scope:{" "}
                            {user.scopes.length > 0
                              ? user.scopes.map((scope) => scope.game_name).join(", ")
                              : user.has_global_game_access
                                ? "Global"
                                : "No game scope assigned"}
                          </p>
                        </div>

                        <div className="flex w-full flex-col items-start gap-2 lg:w-auto lg:items-end">
                          <div className="flex flex-wrap items-start gap-2 lg:justify-end">
                            <button
                              type="button"
                              disabled={isBusy || !user.manageable}
                              onClick={() => (isEditing ? cancelEdit() : beginEdit(user))}
                              className="rounded border border-neutral-700 px-3 py-1 text-xs hover:border-neutral-500 disabled:opacity-50"
                            >
                              {isEditing ? "Cancel" : "Edit"}
                            </button>
                            <button
                              type="button"
                              disabled={isBusy || !user.manageable}
                              onClick={() => void toggleUserActive(user)}
                              className="rounded border border-neutral-700 px-3 py-1 text-xs hover:border-neutral-500 disabled:opacity-50"
                            >
                              {user.is_active ? "Deactivate" : "Activate"}
                            </button>
                            {canDeleteAccounts && user.manageable && (
                              <InlineDestructiveConfirm
                                triggerLabel="Delete Account"
                                confirmMessage={`Delete ${user.username}'s account permanently? This cannot be undone.`}
                                confirmLabel="Delete Permanently"
                                pendingLabel="Deleting..."
                                busy={isBusy}
                                onConfirm={() => deleteUserAccount(user)}
                              />
                            )}
                            <button
                              type="button"
                              disabled={isBusy || !user.manageable}
                              onClick={() => void resetPassword(user)}
                              className="rounded border border-amber-700/80 bg-amber-950/30 px-3 py-1 text-xs text-amber-100 disabled:opacity-50"
                            >
                              Reset Password
                            </button>
                          </div>
                        </div>
                      </div>

                      {isEditing && (
                        <div className="mt-4 rounded border border-neutral-800 bg-neutral-900/40 p-3">
                          <div className="grid gap-3 md:grid-cols-2">
                            <input
                              className="rounded border border-neutral-700 bg-black p-2 text-sm"
                              value={editForm.email}
                              onChange={(event) =>
                                setEditForm((prev) => (prev ? { ...prev, email: event.target.value } : prev))
                              }
                              placeholder="Email (optional)"
                            />
                            <select
                              className="rounded border border-neutral-700 bg-black p-2 text-sm"
                              value={editForm.role}
                              onChange={(event) =>
                                setEditForm((prev) => (prev ? { ...prev, role: event.target.value as StaffRole } : prev))
                              }
                            >
                              {filteredRoleOptions.map((role) => (
                                <option key={role} value={role}>
                                  {formatRoleLabel(role)}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div className="mt-3 grid gap-2 md:grid-cols-2">
                            {availableScopeGames.map((game) => (
                              <label key={game.game_id} className="flex items-center gap-2 text-sm text-neutral-200">
                                <input
                                  type="checkbox"
                                  checked={editForm.game_ids.includes(game.game_id)}
                                  onChange={() =>
                                    setEditForm((prev) =>
                                      prev
                                        ? { ...prev, game_ids: toggleGameSelection(prev.game_ids, game.game_id) }
                                        : prev,
                                    )
                                  }
                                />
                                {game.game_name}
                              </label>
                            ))}
                          </div>

                          <div className="mt-3 flex flex-wrap gap-4 text-sm">
                            <label className="flex items-center gap-2 text-neutral-200">
                              <input
                                type="checkbox"
                                checked={editForm.is_active}
                                onChange={(event) =>
                                  setEditForm((prev) => (prev ? { ...prev, is_active: event.target.checked } : prev))
                                }
                              />
                              Active account
                            </label>
                            <label className="flex items-center gap-2 text-neutral-200">
                              <input
                                type="checkbox"
                                checked={editForm.must_change_password}
                                onChange={(event) =>
                                  setEditForm((prev) =>
                                    prev ? { ...prev, must_change_password: event.target.checked } : prev,
                                  )
                                }
                              />
                              Must change password
                            </label>
                          </div>

                          <div className="mt-3">
                            <button
                              type="button"
                              className="rounded bg-white px-3 py-1.5 text-xs font-medium text-black disabled:opacity-60"
                              disabled={isBusy}
                              onClick={() => void saveEdit(user.id)}
                            >
                              {isBusy ? "Saving..." : "Save Changes"}
                            </button>
                          </div>
                        </div>
                      )}
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
