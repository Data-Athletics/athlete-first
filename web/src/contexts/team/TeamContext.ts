import { createContext, useContext } from "react";
import type {
  Option,
  Team,
  TeamMember,
  TeamMembershipRequest,
  TeamMembershipStatus,
  MyTeam,
  DataSharingValues,
  MembershipDataSharingPolicy,
  TeamDataSharingRequirements,
} from "../../types/Team";

export interface TeamContextType {
  loading: boolean;
  teams: Team[];
  myTeams: MyTeam[];
  teamsOptions: Option[];
  getTeams: () => Promise<void>;
  getTeamMembers: (teamId: number) => Promise<TeamMember[]>;
  leaveTeam: (teamId: number, membershipId: number) => Promise<void>;
  team: Team | null;
  setTeam: (team: Team | null) => void;
  approvedTeamMemberships: TeamMember[];
  approvedTeamMembershipsOptions: Option[];
  requestedTeamMemberships: TeamMember[];
  requestedTeamMembershipsOptions: Option[];
  getTeamMemberships: () => Promise<void>;
  teamMembershipRequests: TeamMembershipRequest[];
  getTeamMembershipRequests: () => Promise<void>;
  createTeamMembershipRequest: (
    teamId: number,
    username: string,
  ) => Promise<void>;
  updateTeamMembershipStatus: (
    teamId: number,
    membershipId: number,
    status: TeamMembershipStatus,
  ) => Promise<void>;
  deleteTeamMembership: (teamId: number, membershipId: number) => Promise<void>;
  teamMembership: TeamMember | null;
  setTeamMembership: (membership: TeamMember | null) => void;
  dataSharingRequirements: Record<number, TeamDataSharingRequirements>;
  dataSharingPolicies: Record<number, MembershipDataSharingPolicy | null>;
  dataSharingLoading: boolean;
  ownDataSharingBlocked: boolean;
  hasDataSharingAttention: boolean;
  updateTeamDataSharingRequirements: (
    teamId: number,
    requirements: DataSharingValues,
  ) => Promise<TeamDataSharingRequirements>;
  updateMembershipDataSharingPolicy: (
    teamId: number,
    policy: DataSharingValues,
  ) => Promise<MembershipDataSharingPolicy>;
}

export const TeamContext = createContext<TeamContextType | null>(null);

export function useTeam() {
  const context = useContext(TeamContext);

  if (!context) {
    throw new Error("useTeam must be used within TeamProvider");
  }

  return context;
}
