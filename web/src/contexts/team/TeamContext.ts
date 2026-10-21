import { createContext, useContext } from "react";
import type { Option, Team, TeamMembership } from "../../types/Team";

export interface TeamContextType {
  teams: Team[];
  teamsOptions: Option[];
  getTeams: () => Promise<void>;
  team: Team | null;
  setTeam: (team: Team | null) => void;
  teamMemberships: TeamMembership[];
  teamMembershipsOptions: Option[];
  getTeamMemberships: () => Promise<void>;
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
