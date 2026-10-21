export type TeamRole = "coach" | "athlete";

export interface TeamMembership {
  id: number;
  role: TeamRole;
  user_id: number;
  team_id: number;
}

export type TeamMembershipsResponse = TeamMembership[];

export interface Team {
  id: number;
  name: string;
}

export type TeamsResponse = Team[];

export interface Option {
  value: string;
  label: string;
}
