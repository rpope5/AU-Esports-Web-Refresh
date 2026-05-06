export type StaffCategory = "coach" | "captain" | "faculty" | "advisor" | "staff" | "other";

export interface StaffProfileSummary {
  id: number;
  slug: string;
  full_name: string;
  preferred_name: string | null;
  title: string;
  category: StaffCategory;
  email: string | null;
  image_url: string | null;
  game_scope: string[];
  year_label: string | null;
  previous_college: string | null;
}

export interface StaffProfileDetail extends StaffProfileSummary {
  phone: string | null;
  bio_at_ashland: string[];
  bio_before_ashland: string[];
  responsibilities: string[];
  sort_order: number;
  created_at: string;
  updated_at: string;
}
