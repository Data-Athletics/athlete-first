export type TeamRole = "coach" | "athlete";
export type TeamMembershipStatus = "approve" | "reject" | "pending";

export interface TeamMembership {
  id: number;
  role: TeamRole;
  status: TeamMembershipStatus;
  user_id: number;
  team_id: number;
}

export type TeamMembershipsResponse = TeamMembership[];

export interface Team {
  id: number;
  name: string;
}

export interface MyTeam extends Team {
  membership: TeamMembership;
}

export interface TeamMembershipRequest extends TeamMembership {
  username: string;
  team_name: string;
}

export type TeamsResponse = Team[];
export type MyTeamsResponse = MyTeam[];

export interface Option {
  value: string;
  label: string;
}
