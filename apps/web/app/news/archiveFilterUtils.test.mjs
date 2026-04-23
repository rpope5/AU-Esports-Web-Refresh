import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const {
  ALL_ARCHIVE_FILTER,
  GENERAL_ARCHIVE_FILTER,
  NEWEST_ARCHIVE_SORT,
  OLDEST_ARCHIVE_SORT,
  filterAndSortArchiveAnnouncements,
  normalizeArchiveFilterParam,
} = require("./archiveFilterUtils.js");

const announcements = [
  {
    id: 1,
    title: "Single game",
    created_at: "2026-04-20 08:00:00",
    game_slugs: ["valorant"],
    is_general: false,
  },
  {
    id: 2,
    title: "Multi game",
    created_at: "2026-04-18 08:00:00",
    game_slugs: ["valorant", "overwatch"],
    is_general: false,
  },
  {
    id: 3,
    title: "General only",
    created_at: "2026-04-19 08:00:00",
    game_slugs: [],
    is_general: true,
  },
  {
    id: 4,
    title: "General and game tagged",
    created_at: "2026-04-17 08:00:00",
    game_slugs: ["valorant"],
    is_general: true,
  },
  {
    id: 5,
    title: "Legacy game_slug",
    created_at: "2026-04-16 08:00:00",
    game_slug: "cod",
    is_general: false,
  },
  {
    id: 6,
    title: "Unscoped",
    created_at: "2026-04-15 08:00:00",
    game_slugs: [],
    is_general: false,
  },
];

function ids(items) {
  return items.map((item) => item.id);
}

assert.equal(normalizeArchiveFilterParam("valorant", ["valorant", "overwatch"]), "valorant");
assert.equal(normalizeArchiveFilterParam("unknown", ["valorant", "overwatch"]), ALL_ARCHIVE_FILTER);

const allAnnouncements = filterAndSortArchiveAnnouncements(
  announcements,
  ALL_ARCHIVE_FILTER,
  NEWEST_ARCHIVE_SORT,
);
assert.deepEqual(ids(allAnnouncements), [1, 3, 2, 4, 5, 6]);

const generalAnnouncements = filterAndSortArchiveAnnouncements(
  announcements,
  GENERAL_ARCHIVE_FILTER,
  NEWEST_ARCHIVE_SORT,
);
assert.deepEqual(ids(generalAnnouncements), [3, 4]);

const valorantAnnouncements = filterAndSortArchiveAnnouncements(
  announcements,
  "valorant",
  NEWEST_ARCHIVE_SORT,
);
assert.deepEqual(ids(valorantAnnouncements), [1, 2, 4]);
assert.equal(ids(valorantAnnouncements).filter((id) => id === 2).length, 1);
assert.ok(ids(valorantAnnouncements).includes(4));

const overwatchAnnouncements = filterAndSortArchiveAnnouncements(
  announcements,
  "overwatch",
  NEWEST_ARCHIVE_SORT,
);
assert.deepEqual(ids(overwatchAnnouncements), [2]);

const codAnnouncements = filterAndSortArchiveAnnouncements(
  announcements,
  "cod",
  NEWEST_ARCHIVE_SORT,
);
assert.deepEqual(ids(codAnnouncements), [5]);

const valorantOldestFirst = filterAndSortArchiveAnnouncements(
  announcements,
  "valorant",
  OLDEST_ARCHIVE_SORT,
);
assert.deepEqual(ids(valorantOldestFirst), [4, 2, 1]);

const noMatches = filterAndSortArchiveAnnouncements(
  announcements,
  "hearthstone",
  NEWEST_ARCHIVE_SORT,
);
assert.deepEqual(noMatches, []);
