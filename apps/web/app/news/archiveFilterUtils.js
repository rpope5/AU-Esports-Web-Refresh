const ALL_ARCHIVE_FILTER = "all";
const GENERAL_ARCHIVE_FILTER = "general";
const NEWEST_ARCHIVE_SORT = "newest";
const OLDEST_ARCHIVE_SORT = "oldest";

function parseApiDate(rawValue) {
  if (typeof rawValue !== "string" || !rawValue.trim()) return null;
  const value = rawValue.trim();
  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(value);
  const parsed = new Date(hasTimezone ? value : `${value}Z`);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
}

function normalizeGameSlugs(rawSlugs) {
  if (!Array.isArray(rawSlugs)) return [];
  const normalized = [];
  const seen = new Set();

  for (const rawSlug of rawSlugs) {
    if (typeof rawSlug !== "string") continue;
    const slug = rawSlug.trim().toLowerCase();
    if (!slug || seen.has(slug)) continue;
    seen.add(slug);
    normalized.push(slug);
  }

  return normalized;
}

function getAnnouncementGameSlugs(item) {
  const normalized = normalizeGameSlugs(item?.game_slugs);
  if (normalized.length > 0) return normalized;

  if (typeof item?.game_slug !== "string") return [];
  const legacySlug = item.game_slug.trim().toLowerCase();
  return legacySlug ? [legacySlug] : [];
}

function normalizeArchiveFilterParam(rawValue, canonicalGameSlugs) {
  const candidate = typeof rawValue === "string" ? rawValue.trim().toLowerCase() : "";
  if (!candidate || candidate === ALL_ARCHIVE_FILTER) return ALL_ARCHIVE_FILTER;
  if (candidate === GENERAL_ARCHIVE_FILTER) return GENERAL_ARCHIVE_FILTER;

  if (!Array.isArray(canonicalGameSlugs)) return ALL_ARCHIVE_FILTER;
  return canonicalGameSlugs.includes(candidate) ? candidate : ALL_ARCHIVE_FILTER;
}

function normalizeArchiveSortParam(rawValue) {
  const candidate = typeof rawValue === "string" ? rawValue.trim().toLowerCase() : "";
  if (candidate === OLDEST_ARCHIVE_SORT) return OLDEST_ARCHIVE_SORT;
  return NEWEST_ARCHIVE_SORT;
}

function matchesArchiveFilter(item, filterValue) {
  if (filterValue === ALL_ARCHIVE_FILTER) return true;
  if (filterValue === GENERAL_ARCHIVE_FILTER) return Boolean(item?.is_general);
  return getAnnouncementGameSlugs(item).includes(filterValue);
}

function parseAnnouncementTimestamp(rawValue) {
  return parseApiDate(rawValue)?.getTime() ?? Number.NaN;
}

function sortArchiveAnnouncements(items, sortOrder) {
  const normalizedSort = normalizeArchiveSortParam(sortOrder);
  const direction = normalizedSort === OLDEST_ARCHIVE_SORT ? 1 : -1;

  return [...items].sort((a, b) => {
    const aTime = parseAnnouncementTimestamp(a?.created_at);
    const bTime = parseAnnouncementTimestamp(b?.created_at);
    const aId = Number(a?.id ?? 0);
    const bId = Number(b?.id ?? 0);

    if (Number.isNaN(aTime) && Number.isNaN(bTime)) {
      return direction * (aId - bId);
    }
    if (Number.isNaN(aTime)) return 1;
    if (Number.isNaN(bTime)) return -1;

    const timeDiff = aTime - bTime;
    if (timeDiff !== 0) return direction * timeDiff;
    return direction * (aId - bId);
  });
}

function filterAndSortArchiveAnnouncements(items, filterValue, sortOrder) {
  return sortArchiveAnnouncements(
    (Array.isArray(items) ? items : []).filter((item) => matchesArchiveFilter(item, filterValue)),
    sortOrder,
  );
}

module.exports = {
  ALL_ARCHIVE_FILTER,
  GENERAL_ARCHIVE_FILTER,
  NEWEST_ARCHIVE_SORT,
  OLDEST_ARCHIVE_SORT,
  normalizeGameSlugs,
  getAnnouncementGameSlugs,
  normalizeArchiveFilterParam,
  normalizeArchiveSortParam,
  matchesArchiveFilter,
  parseAnnouncementTimestamp,
  sortArchiveAnnouncements,
  filterAndSortArchiveAnnouncements,
};
