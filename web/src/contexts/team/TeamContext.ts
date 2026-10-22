import { createContext, useContext } from "react";
import type {
  Option,
  Team,
  TeamMembership,
  TeamMembershipRequest,
  TeamMembershipStatus,
} from "../../types/Team";

export interface TeamContextType {
  teams: Team[];
  teamsOptions: Option[];
  getTeams: () => Promise<void>;
  team: Team | null;
  setTeam: (team: Team | null) => void;
  approvedTeamMemberships: TeamMembership[];
  approvedTeamMembershipsOptions: Option[];
  requestedTeamMemberships: TeamMembership[];
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
  teamMembership: TeamMembership | null;
  setTeamMembership: (membership: TeamMembership | null) => void;
}

export const TeamContext = createContext<TeamContextType | null>(null);

export function useTeam() {
  const context = useContext(TeamContext);

  if (!context) {
    throw new Error("useTeam must be used within TeamProvider");
  }

  return context;
}
