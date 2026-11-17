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
  name: string;
  team_name: string;
}

export interface TeamMember extends TeamMembership {
  name: string;
}

export type DataSharingField =
  | "bpm_shared"
  | "rhr_shared"
  | "calories_shared"
  | "respiratory_rate_shared"
  | "hrv_shared"
  | "effort_shared"
  | "skin_temp_delta_shared";

export type DataSharingValues = Partial<
  Record<DataSharingField, boolean | null>
>;

export interface TeamDataSharingRequirements extends DataSharingValues {
  team_id: number;
}

export interface MembershipDataSharingPolicy extends DataSharingValues {
  membership_id: number;
  invalid_fields: string[];
}

export type TeamsResponse = Team[];
export type MyTeamsResponse = MyTeam[];
export type TeamMembersResponse = TeamMember[];

export interface Option {
  value: string;
  label: string;
}
