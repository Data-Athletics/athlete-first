import { useEffect, useRef, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
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

const selectedTeamStorageKey = (userId: number) =>
  `selected-team-${userId}`;
const selectedMembershipStorageKey = (userId: number) =>
  `selected-membership-${userId}`;

export function TeamProvider({ children }: { children: ReactNode }) {
  const { user } = useUser();
  const location = useLocation();

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
  const [teamMembership, setTeamMembershipState] = useState<TeamMember | null>(
    null,
  );
  const [teams, setTeams] = useState<Team[]>([]);
  const [myTeams, setMyTeams] = useState<MyTeam[]>([]);
  const [teamsOptions, setTeamsOptions] = useState<Option[]>([]);
  const [team, setTeamState] = useState<Team | null>(null);
  const [loading, setLoading] = useState(true);
  const loadedUserId = useRef<number | null>(null);
  const lastTeamPageLoad = useRef<string | null>(null);

  const setTeam = (selectedTeam: Team | null) => {
    setTeamState(selectedTeam);
    if (!user) return;

    if (selectedTeam) {
      localStorage.setItem(
        selectedTeamStorageKey(user.id),
        String(selectedTeam.id),
      );
    } else {
      localStorage.removeItem(selectedTeamStorageKey(user.id));
    }

    setTeamMembershipState(null);
    localStorage.removeItem(selectedMembershipStorageKey(user.id));
  };

  const setTeamMembership = (membership: TeamMember | null) => {
    setTeamMembershipState(membership);
    if (!user) return;

    if (membership) {
      localStorage.setItem(
        selectedMembershipStorageKey(user.id),
        String(membership.id),
      );
    } else {
      localStorage.removeItem(selectedMembershipStorageKey(user.id));
    }
  };

  const getTeamMemberships = async () => {
    if (team) {
      const { data } = await api.get<TeamMember[]>(
        `/team/teams/${team.id}/memberships`,
      );
      const athleteMemberships = data.filter(
        (membership) => membership.role === "athlete",
      );
      const approvedMemberships = athleteMemberships.filter(
        (membership) => membership.status === "approve",
      );
      setApprovedTeamMemberships(approvedMemberships);
      setRequestedTeamMemberships(
        athleteMemberships.filter(
          (membership) => membership.status !== "approve",
        ),
      );

      const savedMembershipId = Number(
        localStorage.getItem(selectedMembershipStorageKey(user?.id ?? 0)),
      );
      setTeamMembershipState(
        approvedMemberships.find(
          (membership) => membership.id === savedMembershipId,
        ) ?? null,
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
    setLoading(true);
    const { data } = await api.get<MyTeamsResponse>("/team/teams/me");
    const approvedTeams = data
      .filter(({ membership }) => membership.status === "approve")
      .map(({ id, name }) => ({ id, name }));
    setMyTeams(data);
    setTeams(approvedTeams);
    setTeamsOptions(
      approvedTeams.map((currentTeam) => ({
        value: String(currentTeam.id),
        label: currentTeam.name,
      })),
    );
    const savedTeamId = Number(
      localStorage.getItem(selectedTeamStorageKey(user?.id ?? 0)),
    );
    const savedTeam =
      approvedTeams.find((candidate) => candidate.id === savedTeamId) ?? null;
    setTeamState(savedTeam);
    void loadTeamMembershipRequests(approvedTeams, data).catch((error) =>
      console.error("Failed to load team requests:", error),
    );
    if (!savedTeam) setLoading(false);
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
      lastTeamPageLoad.current = null;
      return;
    }

    if (location.pathname === "/team") {
      const loadKey = `${user.id}:${location.key}`;
      if (lastTeamPageLoad.current === loadKey) return;

      lastTeamPageLoad.current = loadKey;
      loadedUserId.current = user.id;
      void getTeams().catch((error) => {
        console.error("Failed to refresh teams:", error);
        setLoading(false);
      });
      return;
    }

    if (loadedUserId.current === user.id) return;

    loadedUserId.current = user.id;
    void getTeams().catch((error) => {
      console.error("Failed to load teams:", error);
      setLoading(false);
    });
  }, [location.key, location.pathname, user?.id]);

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
    if (!user || !team) return;

    const savedMembershipId = Number(
      localStorage.getItem(selectedMembershipStorageKey(user.id)),
    );
    const savedMembership = approvedTeamMemberships.find(
      (membership) =>
        membership.id === savedMembershipId && membership.team_id === team.id,
    );

    setTeamMembershipState(savedMembership ?? null);
  }, [approvedTeamMemberships, team?.id, user?.id]);

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
      void getTeamMemberships()
        .catch((error) => console.error("Failed to load team memberships:", error))
        .finally(() => setLoading(false));
    }
  }, [team]);

  return (
    <TeamContext.Provider
      value={{
        loading,
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
