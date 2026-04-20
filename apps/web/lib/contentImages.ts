export type ContentImageKind = "announcement" | "roster";

const CONTENT_IMAGE_PLACEHOLDERS: Record<ContentImageKind, string> = {
  announcement: "/images/esports-news-placeholder.jpg",
  roster: "/placeholders/roster-member-placeholder.svg",
};

function trimTrailingSlashes(value: string): string {
  return value.replace(/\/+$/, "");
}

export function getContentPlaceholder(kind: ContentImageKind): string {
  return CONTENT_IMAGE_PLACEHOLDERS[kind];
}

export function resolveContentImageUrl(
  imageUrl: string | null | undefined,
  apiUrl: string,
  kind: ContentImageKind,
): string {
  const normalizedImageUrl = imageUrl?.trim();
  if (!normalizedImageUrl) return getContentPlaceholder(kind);
  if (normalizedImageUrl.startsWith("http://") || normalizedImageUrl.startsWith("https://")) {
    return normalizedImageUrl;
  }
  if (normalizedImageUrl.startsWith("/uploads")) {
    return `${trimTrailingSlashes(apiUrl)}${normalizedImageUrl}`;
  }
  if (normalizedImageUrl.startsWith("/")) {
    return normalizedImageUrl;
  }
  return `${trimTrailingSlashes(apiUrl)}/${normalizedImageUrl}`;
}
