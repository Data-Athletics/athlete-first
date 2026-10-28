import { useEffect, useRef, useState, type ReactNode } from "react";
import { api } from "../../api/axios";
import {
  type Option,
  type Team,
  type TeamMember,
  type TeamMembership,
  type TeamMembershipRequest,
  type TeamMembershipStatus,
  type MyTeam,
  type MyTeamsResponse,
  type TeamMembersResponse,
} from "../../types/Team";
import { useUser } from "../user/UserContext";
import { TeamContext } from "./TeamContext";

const ALL_OPTION = { value: "all", label: "All" };

export function TeamProvider({ children }: { children: ReactNode }) {
  const { user } = useUser();

  const [approvedTeamMemberships, setApprovedTeamMemberships] = useState<
    TeamMember[]
  >([]);
  const [approvedTeamMembershipsOptions, setApprovedTeamMembershipsOptions] =
    useState<Option[]>([]);
  const [requestedTeamMemberships, setRequestedTeamMemberships] = useState<
    TeamMember[]
  >([]);
  const [requestedTeamMembershipsOptions, setRequestedTeamMembershipsOptions] =
    useState<Option[]>([]);
  const [teamMembershipRequests, setTeamMembershipRequests] = useState<
    TeamMembershipRequest[]
  >([]);
  const [teamMembership, setTeamMembership] = useState<TeamMember | null>(
    null,
  );
  const [teams, setTeams] = useState<Team[]>([]);
  const [myTeams, setMyTeams] = useState<MyTeam[]>([]);
  const [teamsOptions, setTeamsOptions] = useState<Option[]>([]);
  const [team, setTeam] = useState<Team | null>(null);
  const loadedUserId = useRef<number | null>(null);

  const getTeamMemberships = async () => {
    if (team) {
      const { data } = await api.get<TeamMember[]>(
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

  const loadTeamMembershipRequests = async (
    currentTeams: Team[],
    currentMyTeams: MyTeam[],
  ) => {
    if (!user) return;

    if (!user.is_staff) {
      setTeamMembershipRequests(
        currentMyTeams
          .filter(({ membership }) => membership.status !== "approve")
          .map(({ name, membership }) => ({
            ...membership,
            name: user.name,
            team_name: name,
          })),
      );
      return;
    }

    const responses = await Promise.all(
      currentTeams.map(({ id }) =>
        api.get<TeamMembershipRequest[]>(
          `/team/teams/${id}/memberships/non-approved`,
        ),
      ),
    );
    setTeamMembershipRequests(responses.flatMap(({ data }) => data));
  };

  const getTeamMembershipRequests = async () => {
    await loadTeamMembershipRequests(teams, myTeams);
  };

  const updateTeamMembershipStatus = async (
    teamId: number,
    membershipId: number,
    status: TeamMembershipStatus,
  ) => {
    const { data: updatedMembership } = await api.patch<TeamMembership>(
      `/team/teams/${teamId}/memberships/${membershipId}`,
      { status },
    );

    if (user?.is_staff) {
      await getTeamMembershipRequests();
      return;
    }

    const updatedTeams = myTeams.map((currentTeam) =>
      currentTeam.membership.id === membershipId
        ? { ...currentTeam, membership: updatedMembership }
        : currentTeam,
    );
    setMyTeams(updatedTeams);
    setTeams(
      updatedTeams
        .filter(({ membership }) => membership.status === "approve")
        .map(({ id, name }) => ({ id, name })),
    );
    setTeamMembershipRequests((requests) =>
      status === "approve"
        ? requests.filter((request) => request.id !== membershipId)
        : requests.map((request) =>
            request.id === membershipId
              ? { ...request, status: updatedMembership.status }
              : request,
          ),
    );
  };

  const deleteTeamMembership = async (teamId: number, membershipId: number) => {
    await api.delete(`/team/teams/${teamId}/memberships/${membershipId}`);
    await getTeams();
  };

  const getTeams = async () => {
    const { data } = await api.get<MyTeamsResponse>("/team/teams/me");
    const approvedTeams = data
      .filter(({ membership }) => membership.status === "approve")
      .map(({ id, name }) => ({ id, name }));
    setMyTeams(data);
    setTeams(approvedTeams);
    await loadTeamMembershipRequests(approvedTeams, data);
  };

  const getTeamMembers = async (teamId: number): Promise<TeamMember[]> => {
    const { data } = await api.get<TeamMembersResponse>(
      `/team/teams/${teamId}/memberships`,
    );
    return data;
  };

  const leaveTeam = async (teamId: number, membershipId: number) => {
    await api.delete(`/team/teams/${teamId}/memberships/${membershipId}`);
    if (team?.id === teamId) {
      setTeam(null);
    }
    await getTeams();
  };

  useEffect(() => {
    if (!user) {
      loadedUserId.current = null;
      return;
    }

    if (loadedUserId.current === user.id) return;

    loadedUserId.current = user.id;
    void getTeams();
  }, [user?.id]);

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
          label: membership.name,
        }))
        .concat(ALL_OPTION),
    );
  }, [approvedTeamMemberships]);

  useEffect(() => {
    setRequestedTeamMembershipsOptions(
      requestedTeamMemberships
        .map((membership) => ({
          value: String(membership.id),
          label: membership.name,
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
        myTeams,
        teamsOptions,
        getTeams,
        getTeamMembers,
        leaveTeam,
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
