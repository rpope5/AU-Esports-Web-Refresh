import Link from "next/link";

import { resolveContentImageUrl } from "@/lib/contentImages";
import { StaffProfileSummary } from "@/types/StaffProfile";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STAFF_CATEGORY_LABELS: Record<string, string> = {
  coach: "Coach",
  captain: "Captain",
  faculty: "Faculty",
  advisor: "Advisor",
  staff: "Staff",
  other: "Other",
};

function resolveStaffImage(imageUrl: string | null): string {
  return resolveContentImageUrl(imageUrl, API_URL, "staff");
}

function normalizeEmailHref(email: string): string | null {
  const trimmed = email.trim();
  if (!trimmed || !trimmed.includes("@")) return null;
  return `mailto:${encodeURIComponent(trimmed)}`;
}

function gameScopeLabel(gameScope: string[]): string {
  if (!Array.isArray(gameScope) || gameScope.length === 0) return "All Teams";
  return gameScope.join(", ");
}

interface StaffCardProps {
  profile: StaffProfileSummary;
}

export default function StaffCard({ profile }: StaffCardProps) {
  const categoryLabel = STAFF_CATEGORY_LABELS[profile.category] || "Other";
  const emailHref = profile.email ? normalizeEmailHref(profile.email) : null;
  return (
    <article className="rounded-xl border border-gray-700 bg-gray-900 p-4 shadow-lg">
      <div className="flex items-start gap-4">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={resolveStaffImage(profile.image_url)}
          alt={profile.full_name}
          className="h-20 w-20 flex-none rounded-full border border-gray-600 object-cover"
        />
        <div className="min-w-0 flex-1">
          <h2 className="text-lg font-bold text-white">{profile.full_name}</h2>
          <p className="text-sm font-semibold text-[#FFC72C]">{profile.title}</p>
          <p className="mt-1 text-xs uppercase tracking-wide text-gray-300">{categoryLabel}</p>
          <p className="mt-1 text-sm text-gray-300">{gameScopeLabel(profile.game_scope)}</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {emailHref && profile.email && (
          <a
            href={emailHref}
            className="rounded-md border border-[#FFC72C]/70 px-3 py-1 text-xs font-semibold text-[#FFC72C] transition-colors hover:bg-[#FFC72C]/10"
          >
            Email
          </a>
        )}
        <Link
          href={`/staff/${profile.slug}`}
          className="rounded-md border border-gray-600 px-3 py-1 text-xs font-semibold text-gray-200 transition-colors hover:border-[#FFC72C] hover:text-[#FFC72C]"
        >
          View Profile
        </Link>
      </div>
    </article>
  );
}
