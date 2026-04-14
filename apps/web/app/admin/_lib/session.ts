export type AdminPermissionKey =
  | "can_view_recruits"
  | "can_manage_recruits"
  | "can_delete_recruits"
  | "can_manage_announcements"
  | "can_delete_announcements"
  | "can_manage_users";

export type AdminPermissions = Record<AdminPermissionKey, boolean>;

export type AdminSession = {
  username: string;
  role: string;
  permissions: AdminPermissions;
  has_global_game_access: boolean;
  allowed_game_slugs: string[];
};

const DEFAULT_PERMISSIONS: AdminPermissions = {
  can_view_recruits: false,
  can_manage_recruits: false,
  can_delete_recruits: false,
  can_manage_announcements: false,
  can_delete_announcements: false,
  can_manage_users: false,
};

const PERMISSIONS_BY_ROLE: Record<string, AdminPermissions> = {
  captain: {
    can_view_recruits: true,
    can_manage_recruits: false,
    can_delete_recruits: false,
    can_manage_announcements: false,
    can_delete_announcements: false,
    can_manage_users: false,
  },
  coach: {
    can_view_recruits: true,
    can_manage_recruits: true,
    can_delete_recruits: false,
    can_manage_announcements: false,
    can_delete_announcements: false,
    can_manage_users: false,
  },
  head_coach: {
    can_view_recruits: true,
    can_manage_recruits: true,
    can_delete_recruits: true,
    can_manage_announcements: true,
    can_delete_announcements: true,
    can_manage_users: false,
  },
  admin: {
    can_view_recruits: true,
    can_manage_recruits: true,
    can_delete_recruits: true,
    can_manage_announcements: true,
    can_delete_announcements: true,
    can_manage_users: true,
  },
};

function normalizeRole(rawRole: unknown): string {
  if (typeof rawRole !== "string") return "coach";
  const normalized = rawRole.trim().toLowerCase().replace(/[-\s]+/g, "_");
  if (normalized === "headcoach") return "head_coach";
  if (normalized === "administrator") return "admin";
  if (normalized === "admin" || normalized === "head_coach" || normalized === "captain" || normalized === "coach") {
    return normalized;
  }
  return "coach";
}

function parsePermissions(raw: unknown, role: string): AdminPermissions {
  const roleDefaults = PERMISSIONS_BY_ROLE[role] || DEFAULT_PERMISSIONS;
  if (!raw || typeof raw !== "object") return roleDefaults;

  return {
    can_view_recruits: Boolean((raw as Partial<AdminPermissions>).can_view_recruits ?? roleDefaults.can_view_recruits),
    can_manage_recruits: Boolean((raw as Partial<AdminPermissions>).can_manage_recruits ?? roleDefaults.can_manage_recruits),
    can_delete_recruits: Boolean((raw as Partial<AdminPermissions>).can_delete_recruits ?? roleDefaults.can_delete_recruits),
    can_manage_announcements: Boolean(
      (raw as Partial<AdminPermissions>).can_manage_announcements ?? roleDefaults.can_manage_announcements,
    ),
    can_delete_announcements: Boolean(
      (raw as Partial<AdminPermissions>).can_delete_announcements ?? roleDefaults.can_delete_announcements,
    ),
    can_manage_users: Boolean((raw as Partial<AdminPermissions>).can_manage_users ?? roleDefaults.can_manage_users),
  };
}

export function parseAdminSession(raw: unknown): AdminSession {
  const role = normalizeRole((raw as { role?: unknown })?.role);
  const permissions = parsePermissions((raw as { permissions?: unknown })?.permissions, role);

  const allowed_game_slugs_raw = (raw as { allowed_game_slugs?: unknown })?.allowed_game_slugs;
  const allowed_game_slugs = Array.isArray(allowed_game_slugs_raw)
    ? allowed_game_slugs_raw.filter((value): value is string => typeof value === "string")
    : [];

  const has_global_game_access = Boolean(
    (raw as { has_global_game_access?: unknown })?.has_global_game_access || role === "head_coach" || role === "admin",
  );

  return {
    username: typeof (raw as { username?: unknown })?.username === "string" ? String((raw as { username: unknown }).username) : "",
    role,
    permissions,
    has_global_game_access,
    allowed_game_slugs,
  };
}

export function canAccessGame(session: AdminSession | null, gameSlug: string): boolean {
  if (!session) return false;
  if (session.has_global_game_access) return true;
  return session.allowed_game_slugs.includes(gameSlug);
}

export function clearAdminStorage(): void {
  localStorage.removeItem("au_admin_token");
  localStorage.removeItem("au_admin_role");
  localStorage.removeItem("au_admin_username");
}

export function formatRoleLabel(role: string): string {
  return role
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
