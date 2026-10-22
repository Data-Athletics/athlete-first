import { useEffect, useState, type ReactNode } from "react";
import { api } from "../../api/axios";
import {
  type Option,
  type Team,
  type TeamMembership,
  type TeamMembershipRequest,
  type TeamMembershipStatus,
  type TeamMembershipsResponse,
  type MyTeamsResponse,
} from "../../types/Team";
import { useUser } from "../user/UserContext";
import { TeamContext } from "./TeamContext";

const ALL_OPTION = { value: "all", label: "All" };

export function TeamProvider({ children }: { children: ReactNode }) {
  const { user } = useUser();

  const [approvedTeamMemberships, setApprovedTeamMemberships] = useState<
    TeamMembership[]
  >([]);
  const [approvedTeamMembershipsOptions, setApprovedTeamMembershipsOptions] =
    useState<Option[]>([]);
  const [requestedTeamMemberships, setRequestedTeamMemberships] = useState<
    TeamMembership[]
  >([]);
  const [requestedTeamMembershipsOptions, setRequestedTeamMembershipsOptions] =
    useState<Option[]>([]);
  const [teamMembershipRequests, setTeamMembershipRequests] = useState<
    TeamMembershipRequest[]
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
      const athleteMemberships = data.filter(
        (membership) => membership.role === "athlete",
      );
      setApprovedTeamMemberships(
        athleteMemberships.filter(
          (membership) => membership.status === "approve",
        ),
      );
      setRequestedTeamMemberships(
        athleteMemberships.filter(
          (membership) => membership.status !== "approve",
        ),
      );
    } else {
      console.error("Cannot get memberships now because no team is selected");
    }
  };

  const createTeamMembershipRequest = async (
    teamId: number,
    username: string,
  ) => {
    await api.post(`/team/teams/${teamId}/memberships/request`, {
      username,
    });
    await getTeamMembershipRequests();
  };

  const getTeamMembershipRequests = async () => {
    const responses = await Promise.all(
      teams.map(({ id }) =>
        api.get<TeamMembershipRequest[]>(
          `/team/teams/${id}/memberships/non-approved`,
        ),
      ),
    );
    setTeamMembershipRequests(responses.flatMap(({ data }) => data));
  };

  const updateTeamMembershipStatus = async (
    teamId: number,
    membershipId: number,
    status: TeamMembershipStatus,
  ) => {
    await api.patch(`/team/teams/${teamId}/memberships/${membershipId}`, {
      status,
    });
    await getTeamMembershipRequests();
  };

  const deleteTeamMembership = async (teamId: number, membershipId: number) => {
    await api.delete(`/team/teams/${teamId}/memberships/${membershipId}`);
    await getTeamMembershipRequests();
  };

  const getTeams = async () => {
    const { data } = await api.get<MyTeamsResponse>("/team/teams/me");
    setTeams(data.map(({ id, name }) => ({ id, name })));
  };

  useEffect(() => {
    getTeams();
  }, [user]);

  useEffect(() => {
    getTeamMembershipRequests();
  }, [teams]);

  useEffect(() => {
    setTeamsOptions(
      teams.map((team) => ({ value: String(team.id), label: team.name })),
    );
  }, [teams]);

  useEffect(() => {
    setApprovedTeamMembershipsOptions(
      approvedTeamMemberships
        .map((membership) => ({
          value: String(membership.id),
          label: String(membership.user_id),
        }))
        .concat(ALL_OPTION),
    );
  }, [approvedTeamMemberships]);

  useEffect(() => {
    setRequestedTeamMembershipsOptions(
      requestedTeamMemberships
        .map((membership) => ({
          value: String(membership.id),
          label: String(membership.user_id),
        }))
        .concat(ALL_OPTION),
    );
  }, [requestedTeamMemberships]);

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
        approvedTeamMemberships,
        approvedTeamMembershipsOptions,
        requestedTeamMemberships,
        requestedTeamMembershipsOptions,
        getTeamMemberships,
        teamMembershipRequests,
        getTeamMembershipRequests,
        createTeamMembershipRequest,
        updateTeamMembershipStatus,
        deleteTeamMembership,
        teamMembership,
        setTeamMembership,
      }}
    >
      {children}
    </TeamContext.Provider>
  );
}
