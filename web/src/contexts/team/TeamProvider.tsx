import { useEffect, useState, type ReactNode } from "react";
import { api } from "../../api/axios";
import {
  type Option,
  type Team,
  type TeamMembership,
  type TeamMembershipsResponse,
  type TeamsResponse,
} from "../../types/Team";
import { useUser } from "../user/UserContext";
import { TeamContext } from "./TeamContext";

export function TeamProvider({ children }: { children: ReactNode }) {
  const { user } = useUser();

  const [teamMemberships, setTeamMemberships] = useState<TeamMembership[]>([]);
  const [teamMembershipsOptions, setTeamMembershipsOptions] = useState<
    Option[]
  >([]);
  const [teamMembership, setTeamMembership] = useState<TeamMembership | null>(
    null,
  );
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamsOptions, setTeamsOptions] = useState<Option[]>([]);
  const [team, setTeam] = useState<Team | null>(null);

  const getTeamMemberships = async () => {
    if (team) {
      const { data } = await api.get<TeamMembershipsResponse>(
        `/team/teams/${team.id}/memberships`,
      );
      setTeamMemberships(
        data.filter((membership) => membership.role === "athlete"),
      );
    } else {
      console.error("Cannot get memberships now because no team is selected");
    }
  };

  const getTeams = async () => {
    const { data } = await api.get<TeamsResponse>("/team/teams");
    setTeams(data);
  };

  useEffect(() => {
    getTeams();
  }, [user]);

  useEffect(() => {
    setTeamsOptions(
      teams.map((team) => ({ value: String(team.id), label: team.name })),
    );
  }, [teams]);

  useEffect(() => {
    setTeamMembershipsOptions(
      teamMemberships.map((membership) => ({
        value: String(membership.id),
        label: String(membership.user_id),
      })),
    );
  }, [teamMemberships]);

  useEffect(() => {
    if (team) {
      getTeamMemberships();
    }
    setTeamMembership(null);
  }, [team]);

  return (
    <TeamContext.Provider
      value={{
        teams,
        teamsOptions,
        getTeams,
        team,
        setTeam,
        teamMemberships,
        teamMembershipsOptions,
        getTeamMemberships,
        teamMembership,
        setTeamMembership,
      }}
    >
      {children}
    </TeamContext.Provider>
  );
}
