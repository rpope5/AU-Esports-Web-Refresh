"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import InlineDestructiveConfirm from "../_components/InlineDestructiveConfirm";
import { clearAdminStorage, formatRoleLabel, parseAdminSession, type AdminSession } from "../_lib/session";

type Announcement = {
  id: number;
  title: string;
  body: string;
  image_url: string | null;
  created_at: string;
  updated_at: string | null;
  created_by_admin_id: number | null;
  created_by_username: string | null;
};

const DEFAULT_NEWS_PLACEHOLDER = "/images/esports-news-placeholder.jpg";

function resolveImageUrl(imageUrl: string | null, apiUrl: string): string {
  if (!imageUrl || !imageUrl.trim()) return DEFAULT_NEWS_PLACEHOLDER;
  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) return imageUrl;
  if (imageUrl.startsWith("/uploads")) return `${apiUrl}${imageUrl}`;
  if (imageUrl.startsWith("/")) return imageUrl;
  return `${apiUrl}/${imageUrl}`;
}

function formatPostedDate(rawValue: string): string {
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

export default function AdminNewsPage() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [me, setMe] = useState<AdminSession | null>(null);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loadingAnnouncements, setLoadingAnnouncements] = useState(true);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
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
        setAnnouncements(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load announcements");
      } finally {
        setLoadingAnnouncements(false);
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

        await loadAnnouncements(token);
      } catch {
        setError("Failed to initialize announcements.");
        setLoadingAnnouncements(false);
      }
    };

    init();
  }, [apiUrl, loadAnnouncements, router]);

  async function submitAnnouncement(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    const cleanTitle = title.trim();
    const cleanBody = body.trim();
    if (!cleanTitle || !cleanBody) {
      setError("Title and content are required.");
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
      if (imageFile) {
        formData.append("image", imageFile);
      }

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
        setError("You do not have permission to create announcements.");
        return;
      }
      if (!res.ok) {
        const responseText = await res.text();
        throw new Error(responseText || "Failed to create announcement");
      }

      setTitle("");
      setBody("");
      setImageFile(null);
      setSuccess("Announcement posted.");
      await loadAnnouncements(token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create announcement");
    } finally {
      setSubmitting(false);
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
            Publish latest team news for the public `/news` page.
          </p>

          <form className="mt-4 grid gap-4" onSubmit={submitAnnouncement}>
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
                If omitted, the frontend uses `/images/esports-news-placeholder.jpg`.
              </p>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-fit rounded-lg bg-white px-4 py-2 text-sm font-medium text-black disabled:opacity-60"
            >
              {submitting ? "Posting..." : "Post Announcement"}
            </button>

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
              return (
                <article
                  key={item.id}
                  className="overflow-hidden rounded-xl border border-neutral-800 bg-black/60"
                >
                  <div className="h-32 w-full bg-neutral-900">
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
                          Posted {formatPostedDate(item.created_at)}
                        </span>
                      </div>
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
                    <p className="mt-2 text-sm text-neutral-300">{previewBody(item.body)}</p>
                    <details className="mt-2 text-sm text-neutral-200">
                      <summary className="cursor-pointer text-neutral-300">
                        View full announcement
                      </summary>
                      <p className="mt-2 whitespace-pre-wrap text-neutral-300">{item.body}</p>
                    </details>

                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-neutral-400">
                      <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                        ID: {item.id}
                      </span>
                      <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                        Author: {item.created_by_username || "Unknown"}
                      </span>
                      {usingDefaultImage && (
                        <span className="rounded-full border border-neutral-700 px-2 py-0.5">
                          Uses default image
                        </span>
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
