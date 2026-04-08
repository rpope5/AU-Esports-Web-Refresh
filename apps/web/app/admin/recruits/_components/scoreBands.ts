export type ScoreBandKey =
  | "very_high_confidence"
  | "high_priority"
  | "review_soon"
  | "low_priority";

export type ScoreBandResult = {
  key: ScoreBandKey;
  label: string;
  coachGuidance: string;
  badgeClassName: string;
};

type ScoreBandPolicy = {
  highPriorityMin: number;
  reviewSoonMin: number;
  veryHighConfidenceMin: number | null;
};

const GLOBAL_POLICY: ScoreBandPolicy = {
  highPriorityMin: 80,
  reviewSoonMin: 70,
  veryHighConfidenceMin: 90,
};

const SMASH_POLICY: ScoreBandPolicy = {
  highPriorityMin: 60,
  reviewSoonMin: 50,
  veryHighConfidenceMin: null,
};

const SCORE_BAND_META: Record<ScoreBandKey, Omit<ScoreBandResult, "key">> = {
  very_high_confidence: {
    label: "Very high confidence",
    coachGuidance: "Shortlist candidates when coach bandwidth is limited.",
    badgeClassName: "border-emerald-700 bg-emerald-900/40 text-emerald-200",
  },
  high_priority: {
    label: "High priority",
    coachGuidance: "Strong fit indicators; review first for immediate outreach/tryout consideration.",
    badgeClassName: "border-blue-700 bg-blue-900/40 text-blue-200",
  },
  review_soon: {
    label: "Review soon",
    coachGuidance: "Promising but mixed signal; review after high-priority queue.",
    badgeClassName: "border-amber-700 bg-amber-900/40 text-amber-200",
  },
  low_priority: {
    label: "Low priority / backlog",
    coachGuidance: "Lower current fit signal; keep in backlog and revisit as team needs shift.",
    badgeClassName: "border-neutral-700 bg-neutral-900 text-neutral-300",
  },
};

export function usesSmashScoreBands(gameSlug?: string | null): boolean {
  return (gameSlug || "").trim().toLowerCase() === "smash";
}

function getScoreBandPolicy(gameSlug?: string | null): ScoreBandPolicy {
  return usesSmashScoreBands(gameSlug) ? SMASH_POLICY : GLOBAL_POLICY;
}

export function getScoreBand(score?: number | null, gameSlug?: string | null): ScoreBandResult | null {
  if (typeof score !== "number") return null;

  const policy = getScoreBandPolicy(gameSlug);
  let key: ScoreBandKey;

  if (policy.veryHighConfidenceMin !== null && score >= policy.veryHighConfidenceMin) {
    key = "very_high_confidence";
  } else if (score >= policy.highPriorityMin) {
    key = "high_priority";
  } else if (score >= policy.reviewSoonMin) {
    key = "review_soon";
  } else {
    key = "low_priority";
  }

  return { key, ...SCORE_BAND_META[key] };
}

export function getScoreBandLegend(gameSlug?: string | null): Array<{ label: string; range: string }> {
  if (usesSmashScoreBands(gameSlug)) {
    return [
      { label: "High priority", range: ">= 60" },
      { label: "Review soon", range: "50-59" },
      { label: "Low priority / backlog", range: "< 50" },
    ];
  }

  return [
    { label: "Very high confidence", range: ">= 90" },
    { label: "High priority", range: "80-89" },
    { label: "Review soon", range: "70-79" },
    { label: "Low priority / backlog", range: "< 70" },
  ];
}

