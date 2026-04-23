"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import InlineDestructiveConfirm from "../_components/InlineDestructiveConfirm";
import { clearAdminStorage, formatRoleLabel, parseAdminSession, type AdminSession } from "../_lib/session";
import { getContentPlaceholder, resolveContentImageUrl } from "@/lib/contentImages";
import type { GameOption } from "@/types/GameOption";

type AnnouncementState = "draft" | "pending_approval" | "published" | "rejected";

type Announcement = {
  id: number;
  title: string;
  body: string;
  image_url: string | null;
  state: AnnouncementState;
  game_slug: string | null;
  game_name: string | null;
  game_slugs?: string[];
  game_names?: string[];
  is_general?: boolean;
  created_at: string;
  updated_at: string | null;
  created_by_admin_id: number | null;
  created_by_username: string | null;
  approved_by_admin_id: number | null;
  approved_by_username: string | null;
  approved_at: string | null;
};

type CreateWorkflowAction = "save_draft" | "submit_for_approval" | "publish";
type UpdateWorkflowAction = CreateWorkflowAction | "reject";

type AnnouncementUpdatePayload = {
  title?: string;
  body?: string;
  workflow_action?: UpdateWorkflowAction;
  game_slugs?: string[];
  is_general?: boolean;
};

const DEFAULT_NEWS_PLACEHOLDER = getContentPlaceholder("announcement");

function resolveImageUrl(imageUrl: string | null, apiUrl: string): string {
  return resolveContentImageUrl(imageUrl, apiUrl, "announcement");
}

function formatPostedDate(rawValue: string | null): string {
  if (!rawValue) return "Unknown date";
  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(rawValue);
  const normalized = hasTimezone ? rawValue : `${rawValue}Z`;
  const parsed = new Date(normalized);
  if (Number.isNaN(parsed.getTime())) return "Unknown date";
  return parsed.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function previewBody(body: string, maxLength = 220): string {
  const normalized = body.replace(/\s+/g, " ").trim();
  if (normalized.length <= maxLength) return normalized;
  return `${normalized.slice(0, maxLength).trim()}...`;
}

function formatWorkflowState(state: AnnouncementState): string {
  if (state === "pending_approval") return "Pending Approval";
  return state.charAt(0).toUpperCase() + state.slice(1);
}

function stateBadgeClasses(state: AnnouncementState): string {
  if (state === "published") return "border-emerald-700/60 bg-emerald-950/40 text-emerald-300";
  if (state === "pending_approval") return "border-amber-700/60 bg-amber-950/40 text-amber-300";
  if (state === "rejected") return "border-red-700/60 bg-red-950/40 text-red-300";
  return "border-neutral-700 bg-neutral-900 text-neutral-300";
}

function normalizeGameSlugs(values: string[] | null | undefined): string[] {
  if (!values || values.length === 0) return [];

  const normalized: string[] = [];
  const seen = new Set<string>();
  for (const rawValue of values) {
    const value = rawValue.trim().toLowerCase();
    if (!value || seen.has(value)) continue;
    seen.add(value);
    normalized.push(value);
  }
  return normalized;
}

function toggleSelection(current: string[], slug: string, checked: boolean): string[] {
  if (checked) return normalizeGameSlugs([...current, slug]);
  return current.filter((item) => item !== slug);
}

function getAnnouncementGameSlugs(item: Announcement): string[] {
  const normalized = normalizeGameSlugs(item.game_slugs);
  if (normalized.length > 0) return normalized;
  return item.game_slug ? [item.game_slug] : [];
}

function dedupeTagLabels(labels: string[]): string[] {
  const deduped: string[] = [];
  const seen = new Set<string>();
  for (const rawLabel of labels) {
    const trimmed = rawLabel.trim();
    if (!trimmed) continue;
    const key = trimmed.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(key === "general" ? "General" : trimmed);
  }
  return deduped;
}

export default function AdminNewsPage() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [me, setMe] = useState<AdminSession | null>(null);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [allGames, setAllGames] = useState<GameOption[]>([]);
  const [loadingAnnouncements, setLoadingAnnouncements] = useState(true);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [selectedGameSlugs, setSelectedGameSlugs] = useState<string[]>([]);
  const [isGeneralSelected, setIsGeneralSelected] = useState(false);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [busyAnnouncementId, setBusyAnnouncementId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editBody, setEditBody] = useState("");
  const [editGameSlugs, setEditGameSlugs] = useState<string[]>([]);
  const [editIsGeneral, setEditIsGeneral] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const sortedAnnouncements = useMemo(
    () =>
      [...announcements].sort((a, b) => {
        const aTime = Date.parse(a.created_at);
        const bTime = Date.parse(b.created_at);
        return bTime - aTime;
      }),
    [announcements],
  );

  const canManageAnnouncements = Boolean(me?.permissions.can_manage_announcements);
  const canDeleteAnnouncements = Boolean(me?.permissions.can_delete_announcements);
  const role = me?.role || "";
  const canPublishAnnouncements = role === "coach" || role === "head_coach" || role === "admin";
  const canUseGeneralTag = Boolean(me?.has_global_game_access);

  const availableGames = useMemo(() => {
    if (!me) return [];
    if (me.has_global_game_access) return allGames;
    return allGames.filter((game) => me.allowed_game_slugs.includes(game.slug));
  }, [allGames, me]);

  const gameNameBySlug = useMemo(() => {
    const map = new Map<string, string>();
    for (const game of allGames) map.set(game.slug, game.name);
    return map;
  }, [allGames]);

  const getAnnouncementTagLabels = useCallback(
    (item: Announcement): string[] => {
      const labels: string[] = [];
      if (item.is_general) labels.push("General");

      const slugs = getAnnouncementGameSlugs(item);
      if (Array.isArray(item.game_names) && item.game_names.length > 0) {
        labels.push(...item.game_names);
      } else if (item.game_name) {
        labels.push(item.game_name);
      } else {
        labels.push(...slugs.map((slug) => gameNameBySlug.get(slug) || slug));
      }

      if (labels.length === 0) return ["Unscoped"];
      return dedupeTagLabels(labels);
    },
    [gameNameBySlug],
  );

  const loadAnnouncements = useCallback(
    async (token: string) => {
      setLoadingAnnouncements(true);
      try {
        const res = await fetch(`${apiUrl}/api/v1/admin/news`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (res.status === 401) {
          clearAdminStorage();
          router.push("/admin/login");
          return;
        }
        if (res.status === 403) {
          setError("You do not have permission to manage announcements.");
          return;
        }
        if (!res.ok) {
          const responseText = await res.text();
          throw new Error(responseText || "Failed to load announcements");
        }

        const data = (await res.json()) as Announcement[];
        setAnnouncements(Array.isArray(data) ? data : []);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load announcements");
      } finally {
        setLoadingAnnouncements(false);
      }
    },
    [apiUrl, router],
  );

  const loadGames = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/games`);
      if (!res.ok) throw new Error("Failed to load canonical games");
      const data = (await res.json()) as GameOption[];
      setAllGames(Array.isArray(data) ? data : []);
    } catch {
      setAllGames([]);
    }
  }, [apiUrl]);

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
          setError("Failed to validate admin session.");
          setLoadingAnnouncements(false);
          return;
        }

        const parsedSession = parseAdminSession(await whoamiRes.json());
        setMe(parsedSession);

        if (!parsedSession.permissions.can_manage_announcements) {
          setError("You do not have permission to manage announcements.");
          setLoadingAnnouncements(false);
          return;
        }

        await Promise.all([loadAnnouncements(token), loadGames()]);
      } catch {
        setError("Failed to initialize announcements.");
        setLoadingAnnouncements(false);
      }
    };

    void init();
  }, [apiUrl, loadAnnouncements, loadGames, router]);

  function canEditAnnouncement(item: Announcement): boolean {
    if (!me) return false;
    if (me.role === "admin" || me.role === "head_coach" || me.role === "coach") return true;
    if (me.role === "captain") {
      return item.created_by_username === me.username && item.state !== "published";
    }
    return false;
  }

  function canSubmitAnnouncement(item: Announcement): boolean {
    if (!me) return false;
    if (me.role !== "captain") return false;
    if (item.created_by_username !== me.username) return false;
    return item.state === "draft" || item.state === "rejected";
  }

  async function submitAnnouncement(action: CreateWorkflowAction): Promise<void> {
    setError(null);
    setSuccess(null);

    const cleanTitle = title.trim();
    const cleanBody = body.trim();
    if (!cleanTitle || !cleanBody) {
      setError("Title and content are required.");
      return;
    }

    const normalizedSelectedSlugs = normalizeGameSlugs(selectedGameSlugs);
    if (normalizedSelectedSlugs.length === 0 && !isGeneralSelected) {
      setError("Select at least one game or enable General.");
      return;
    }
    if (isGeneralSelected && !canUseGeneralTag) {
      setError("General announcements require global game access.");
      return;
    }

    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }
    if (!canManageAnnouncements) {
      setError("You do not have permission to create announcements.");
      return;
    }

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("title", cleanTitle);
      formData.append("body", cleanBody);
      formData.append("workflow_action", action);
      formData.append("is_general", String(isGeneralSelected));
      if (normalizedSelectedSlugs.length === 1) {
        formData.append("game_slug", normalizedSelectedSlugs[0]);
      }
      for (const slug of normalizedSelectedSlugs) {
        formData.append("game_slugs", slug);
      }
      if (imageFile) formData.append("image", imageFile);

      const res = await fetch(`${apiUrl}/api/v1/admin/news`, {
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
        setError("You do not have permission to perform that action.");
        return;
      }
      if (!res.ok) {
        const responseText = await res.text();
        throw new Error(responseText || "Failed to create announcement");
      }

      setTitle("");
      setBody("");
      setImageFile(null);
      setSelectedGameSlugs([]);
      setIsGeneralSelected(false);
      setSuccess(
        action === "publish"
          ? "Announcement published."
          : action === "submit_for_approval"
            ? "Announcement submitted for approval."
            : "Draft saved.",
      );
      await loadAnnouncements(token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create announcement");
    } finally {
      setSubmitting(false);
    }
  }

  async function updateAnnouncement(
    announcementId: number,
    payload: AnnouncementUpdatePayload,
  ): Promise<void> {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      throw new Error("Session expired");
    }

    setBusyAnnouncementId(announcementId);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`${apiUrl}/api/v1/admin/news/${announcementId}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (res.status === 401) {
        clearAdminStorage();
        router.push("/admin/login");
        throw new Error("Unauthorized");
      }
      if (res.status === 403) {
        throw new Error("You do not have permission to update this announcement.");
      }
      if (!res.ok) {
        const responseText = await res.text();
        throw new Error(responseText || "Failed to update announcement");
      }

      setSuccess("Announcement updated.");
      await loadAnnouncements(token);
    } finally {
      setBusyAnnouncementId(null);
    }
  }

  async function transitionAnnouncement(announcementId: number, action: "submit" | "publish" | "reject"): Promise<void> {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      throw new Error("Session expired");
    }

    setBusyAnnouncementId(announcementId);
    setError(null);
    setSuccess(null);
    try {
      const route =
        action === "submit"
          ? `${apiUrl}/api/v1/admin/news/${announcementId}/submit`
          : action === "publish"
            ? `${apiUrl}/api/v1/admin/news/${announcementId}/publish`
            : `${apiUrl}/api/v1/admin/news/${announcementId}/reject`;

      const res = await fetch(route, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.status === 401) {
        clearAdminStorage();
        router.push("/admin/login");
        throw new Error("Unauthorized");
      }
      if (res.status === 403) {
        throw new Error("You do not have permission to perform that workflow action.");
      }
      if (!res.ok) {
        const responseText = await res.text();
        throw new Error(responseText || "Failed to update workflow state");
      }

      setSuccess(
        action === "submit"
          ? "Announcement submitted for approval."
          : action === "publish"
            ? "Announcement published."
            : "Announcement rejected.",
      );
      await loadAnnouncements(token);
    } finally {
      setBusyAnnouncementId(null);
    }
  }

  function beginEditing(item: Announcement): void {
    setEditingId(item.id);
    setEditTitle(item.title);
    setEditBody(item.body);
    setEditGameSlugs(getAnnouncementGameSlugs(item));
    setEditIsGeneral(Boolean(item.is_general));
  }

  function cancelEditing(): void {
    setEditingId(null);
    setEditTitle("");
    setEditBody("");
    setEditGameSlugs([]);
    setEditIsGeneral(false);
  }

  async function saveEdit(item: Announcement): Promise<void> {
    const cleanTitle = editTitle.trim();
    const cleanBody = editBody.trim();
    if (!cleanTitle || !cleanBody) {
      setError("Title and content are required.");
      return;
    }

    const normalizedEditSlugs = normalizeGameSlugs(editGameSlugs);
    if (normalizedEditSlugs.length === 0 && !editIsGeneral) {
      setError("Select at least one game or enable General.");
      return;
    }
    if (editIsGeneral && !canUseGeneralTag) {
      setError("General announcements require global game access.");
      return;
    }

    try {
      await updateAnnouncement(item.id, {
        title: cleanTitle,
        body: cleanBody,
        game_slugs: normalizedEditSlugs,
        is_general: editIsGeneral,
      });
      cancelEditing();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update announcement");
    }
  }

  async function confirmDeleteAnnouncement(announcementId: number): Promise<void> {
    if (!canDeleteAnnouncements) {
      throw new Error("You do not have permission to delete announcements.");
    }

    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      throw new Error("Session expired");
    }

    setDeletingId(announcementId);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`${apiUrl}/api/v1/admin/news/${announcementId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.status === 401) {
        clearAdminStorage();
        router.push("/admin/login");
        throw new Error("Unauthorized");
      }
      if (res.status === 403) {
        throw new Error("You do not have permission to delete announcements.");
      }
      if (res.status === 404) {
        setAnnouncements((prev) => prev.filter((item) => item.id !== announcementId));
        setSuccess("Announcement was already removed.");
        return;
      }
      if (!res.ok) {
        const responseText = await res.text();
        throw new Error(responseText || "Failed to delete announcement");
      }

      setAnnouncements((prev) => prev.filter((item) => item.id !== announcementId));
      setSuccess("Announcement deleted.");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete announcement";
      setError(message);
      throw new Error(message);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Esports Announcements</h1>
          <p className="mt-1 text-sm text-neutral-400">
            {me ? `Signed in as ${me.username} - ${formatRoleLabel(me.role)}` : "Loading session..."}
          </p>
        </div>
        <Link
          href="/admin"
          className="rounded-lg border border-neutral-800 bg-neutral-950 px-4 py-2 text-sm hover:border-neutral-700"
        >
          Back to Admin
        </Link>
      </div>

      {canManageAnnouncements ? (
        <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
          <h2 className="text-xl font-medium">Create Announcement</h2>
          <p className="mt-1 text-sm text-neutral-400">
            Captains can draft and submit for review. Coaches and above can publish for authorized games.
          </p>

          <div className="mt-3 flex flex-wrap gap-2 text-xs text-neutral-400">
            <span className="rounded-full border border-neutral-700 px-2 py-0.5">
              Available games: {availableGames.length}
            </span>
            <span className="rounded-full border border-neutral-700 px-2 py-0.5">
              General access: {canUseGeneralTag ? "Enabled" : "Global roles only"}
            </span>
          </div>

          <form className="mt-4 grid gap-4">
            <div>
              <label className="text-sm text-neutral-300">Announcement Scope</label>
              <div className="mt-2 rounded-lg border border-neutral-800 bg-neutral-900 p-3">
                <label className="flex items-center gap-2 text-sm text-neutral-200">
                  <input
                    type="checkbox"
                    checked={isGeneralSelected}
                    disabled={submitting || !canUseGeneralTag}
                    onChange={(event) => setIsGeneralSelected(event.target.checked)}
                  />
                  <span>General (site-wide, not tied to one game)</span>
                </label>
                {!canUseGeneralTag && (
                  <p className="mt-1 text-xs text-neutral-500">
                    General announcements are limited to staff with global game access.
                  </p>
                )}

                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {availableGames.length === 0 ? (
                    <p className="text-xs text-neutral-500">
                      No game access assigned. Enable General or ask an admin to assign game scope.
                    </p>
                  ) : (
                    availableGames.map((game) => {
                      const isChecked = selectedGameSlugs.includes(game.slug);
                      return (
                        <label
                          key={game.slug}
                          className="flex items-center gap-2 rounded border border-neutral-800 bg-black/40 px-2 py-1.5 text-xs text-neutral-300"
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            disabled={submitting}
                            onChange={(event) =>
                              setSelectedGameSlugs((prev) => toggleSelection(prev, game.slug, event.target.checked))
                            }
                          />
                          <span>{game.name}</span>
                        </label>
                      );
                    })
                  )}
                </div>
                <p className="mt-2 text-xs text-neutral-500">
                  Choose one or more games, General, or both.
                </p>
              </div>
            </div>

            <div>
              <label className="text-sm text-neutral-300">Subject / Title</label>
              <input
                className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2 text-sm"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Example: Valorant Team Wins Spring Invitational"
                maxLength={255}
                required
              />
            </div>

            <div>
              <label className="text-sm text-neutral-300">Announcement Content</label>
              <textarea
                className="mt-1 min-h-40 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-3 text-sm"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Write the full announcement here..."
                required
              />
            </div>

            <div>
              <label className="text-sm text-neutral-300">Background Image (Optional)</label>
              <input
                className="mt-1 block w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2 text-sm file:mr-3 file:rounded file:border-0 file:bg-neutral-800 file:px-3 file:py-1.5 file:text-sm"
                type="file"
                accept="image/*"
                onChange={(e) => setImageFile(e.target.files?.[0] || null)}
              />
              <p className="mt-1 text-xs text-neutral-500">
                If omitted, the frontend uses `{DEFAULT_NEWS_PLACEHOLDER}`.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={submitting}
                onClick={() => submitAnnouncement("save_draft")}
                className="rounded-lg border border-neutral-700 px-4 py-2 text-sm disabled:opacity-60"
              >
                {submitting ? "Saving..." : "Save Draft"}
              </button>
              <button
                type="button"
                disabled={submitting}
                onClick={() => submitAnnouncement("submit_for_approval")}
                className="rounded-lg border border-amber-700/80 bg-amber-900/30 px-4 py-2 text-sm text-amber-100 disabled:opacity-60"
              >
                {submitting ? "Submitting..." : "Submit for Approval"}
              </button>
              {canPublishAnnouncements && (
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => submitAnnouncement("publish")}
                  className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-black disabled:opacity-60"
                >
                  {submitting ? "Publishing..." : "Publish Now"}
                </button>
              )}
            </div>

            {error && <p className="text-sm text-red-400">{error}</p>}
            {success && <p className="text-sm text-emerald-400">{success}</p>}
          </form>
        </section>
      ) : (
        <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
          <h2 className="text-xl font-medium">Announcement Access</h2>
          <p className="mt-2 text-sm text-neutral-400">
            This account does not have permission to create or manage announcements.
          </p>
          {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
        </section>
      )}

      <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-xl font-medium">Announcement History</h2>
          <span className="text-sm text-neutral-400">{sortedAnnouncements.length} total</span>
        </div>

        {loadingAnnouncements ? (
          <p className="mt-4 text-sm text-neutral-400">Loading announcements...</p>
        ) : sortedAnnouncements.length === 0 ? (
          <p className="mt-4 text-sm text-neutral-400">No announcements yet.</p>
        ) : (
          <div className="mt-4 grid gap-4">
            {sortedAnnouncements.map((item) => {
              const resolvedImageUrl = resolveImageUrl(item.image_url, apiUrl);
              const usingDefaultImage = !item.image_url;
              const isEditing = editingId === item.id;
              const isBusy = busyAnnouncementId === item.id || deletingId === item.id;
              const canEdit = canEditAnnouncement(item);
              const canSubmit = canSubmitAnnouncement(item);
              const canPublish = canPublishAnnouncements && item.state !== "published";
              const canReject = canPublishAnnouncements && item.state === "pending_approval";
              const tagLabels = getAnnouncementTagLabels(item);

              return (
                <article
                  key={item.id}
                  className="overflow-hidden rounded-xl border border-neutral-800 bg-black/60"
                >
                  <div className="h-32 w-full bg-neutral-900">
                    {/* Dynamic backend image URLs are rendered via img to preserve existing behavior across environments. */}
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={resolvedImageUrl}
                      alt={item.title}
                      className="h-full w-full object-cover opacity-90"
                    />
                  </div>
                  <div className="p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <h3 className="text-lg font-semibold">{item.title}</h3>
                        <span className="text-xs text-neutral-400">
                          Created {formatPostedDate(item.created_at)}
                        </span>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className={`rounded-full border px-2 py-0.5 text-xs ${stateBadgeClasses(item.state)}`}>
                          {formatWorkflowState(item.state)}
                        </span>
                        {canDeleteAnnouncements && (
                          <InlineDestructiveConfirm
                            triggerLabel="Delete"
                            confirmMessage="This announcement is about to be permanently deleted."
                            confirmLabel="Delete Permanently"
                            pendingLabel="Deleting..."
                            busy={deletingId === item.id}
                            onConfirm={() => confirmDeleteAnnouncement(item.id)}
                          />
                        )}
                      </div>
                    </div>

                    {!isEditing ? (
                      <>
                        <p className="mt-2 text-sm text-neutral-300">{previewBody(item.body)}</p>
                        <details className="mt-2 text-sm text-neutral-200">
                          <summary className="cursor-pointer text-neutral-300">
                            View full announcement
                          </summary>
                          <p className="mt-2 whitespace-pre-wrap text-neutral-300">{item.body}</p>
                        </details>
                      </>
                    ) : (
                      <div className="mt-3 grid gap-3">
                        <div>
                          <label className="text-sm text-neutral-300">Title</label>
                          <input
                            className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2 text-sm"
                            value={editTitle}
                            onChange={(event) => setEditTitle(event.target.value)}
                          />
                        </div>
                        <div>
                          <label className="text-sm text-neutral-300">Body</label>
                          <textarea
                            className="mt-1 min-h-32 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-3 text-sm"
                            value={editBody}
                            onChange={(event) => setEditBody(event.target.value)}
                          />
                        </div>
                        <div>
                          <label className="text-sm text-neutral-300">Announcement Scope</label>
                          <div className="mt-1 rounded-lg border border-neutral-800 bg-neutral-900 p-3">
                            <label className="flex items-center gap-2 text-sm text-neutral-200">
                              <input
                                type="checkbox"
                                checked={editIsGeneral}
                                disabled={isBusy || !canUseGeneralTag}
                                onChange={(event) => setEditIsGeneral(event.target.checked)}
                              />
                              <span>General (site-wide)</span>
                            </label>
                            {!canUseGeneralTag && (
                              <p className="mt-1 text-xs text-neutral-500">
                                General announcements are limited to staff with global game access.
                              </p>
                            )}
                            <div className="mt-2 grid gap-2 sm:grid-cols-2">
                              {availableGames.length === 0 ? (
                                <p className="text-xs text-neutral-500">No game access assigned.</p>
                              ) : (
                                availableGames.map((game) => {
                                  const isChecked = editGameSlugs.includes(game.slug);
                                  return (
                                    <label
                                      key={`${item.id}-${game.slug}`}
                                      className="flex items-center gap-2 rounded border border-neutral-800 bg-black/40 px-2 py-1.5 text-xs text-neutral-300"
                                    >
                                      <input
                                        type="checkbox"
                                        checked={isChecked}
                                        disabled={isBusy}
                                        onChange={(event) =>
                                          setEditGameSlugs((prev) =>
                                            toggleSelection(prev, game.slug, event.target.checked),
                                          )
                                        }
                                      />
                                      <span>{game.name}</span>
                                    </label>
                                  );
                                })
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-neutral-400">
                      <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                        ID: {item.id}
                      </span>
                      <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                        Tags: {tagLabels.join(", ")}
                      </span>
                      <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                        Author: {item.created_by_username || "Unknown"}
                      </span>
                      {item.approved_by_username && (
                        <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                          Approved by: {item.approved_by_username}
                        </span>
                      )}
                      {item.approved_at && (
                        <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                          Approved at: {formatPostedDate(item.approved_at)}
                        </span>
                      )}
                      {usingDefaultImage && (
                        <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                          Uses default image
                        </span>
                      )}
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      {canEdit && !isEditing && (
                        <button
                          type="button"
                          className="rounded-lg border border-neutral-700 px-3 py-1.5 text-xs hover:border-neutral-500"
                          onClick={() => beginEditing(item)}
                          disabled={isBusy}
                        >
                          Edit
                        </button>
                      )}
                      {isEditing && (
                        <>
                          <button
                            type="button"
                            className="rounded-lg border border-neutral-700 px-3 py-1.5 text-xs hover:border-neutral-500"
                            onClick={() => saveEdit(item)}
                            disabled={isBusy}
                          >
                            {isBusy ? "Saving..." : "Save Changes"}
                          </button>
                          <button
                            type="button"
                            className="rounded-lg border border-neutral-700 px-3 py-1.5 text-xs hover:border-neutral-500"
                            onClick={cancelEditing}
                            disabled={isBusy}
                          >
                            Cancel
                          </button>
                        </>
                      )}
                      {canSubmit && (
                        <button
                          type="button"
                          className="rounded-lg border border-amber-700/80 bg-amber-900/30 px-3 py-1.5 text-xs text-amber-100"
                          onClick={() => transitionAnnouncement(item.id, "submit")}
                          disabled={isBusy}
                        >
                          {isBusy ? "Submitting..." : "Submit for Approval"}
                        </button>
                      )}
                      {canPublish && (
                        <button
                          type="button"
                          className="rounded-lg border border-emerald-700/80 bg-emerald-900/30 px-3 py-1.5 text-xs text-emerald-100"
                          onClick={() => transitionAnnouncement(item.id, "publish")}
                          disabled={isBusy}
                        >
                          {isBusy ? "Publishing..." : "Publish"}
                        </button>
                      )}
                      {canReject && (
                        <button
                          type="button"
                          className="rounded-lg border border-red-700/80 bg-red-900/30 px-3 py-1.5 text-xs text-red-100"
                          onClick={() => transitionAnnouncement(item.id, "reject")}
                          disabled={isBusy}
                        >
                          {isBusy ? "Rejecting..." : "Reject"}
                        </button>
                      )}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
