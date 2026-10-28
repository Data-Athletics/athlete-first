import type React from "react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { SingleValue } from "react-select";
import Request from "../components/Request";
import SelectInput from "../components/SelectInput";
import { useTeam } from "../contexts/team/TeamContext";
import { useUser } from "../contexts/user/UserContext";
import Nav from "../Nav";
import type { Option, Team, TeamMember } from "../types/Team";
import { alertUser } from "../utils/alerts";
import "./Team.css";

const TeamPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useUser();
  const {
    teams,
    myTeams,
    teamsOptions,
    getTeamMembers,
    leaveTeam,
    createTeamMembershipRequest,
    teamMembershipRequests,
    updateTeamMembershipStatus,
    deleteTeamMembership,
  } = useTeam();

  const [username, setUsername] = useState("");
  const [requestTeam, setRequestTeam] = useState<Team | null>(null);
  const [requesting, setRequesting] = useState(false);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [teamMembers, setTeamMembers] = useState<Record<number, TeamMember[]>>(
    {},
  );
  const requestTeamOptions = teamsOptions;
  const acceptedTeams = myTeams.filter(
    ({ membership }) => membership.status === "approve",
  );

  useEffect(() => {
    if (!user?.is_staff) return;

    const loadTeamMembers = async () => {
      const acceptedTeamIds = myTeams
        .filter(({ membership }) => membership.status === "approve")
        .map(({ id }) => id);
      const entries = await Promise.all(
        acceptedTeamIds.map(async (id) => [id, await getTeamMembers(id)] as const),
      );
      setTeamMembers(Object.fromEntries(entries));
    };

    void loadTeamMembers();
  }, [myTeams, user?.is_staff]);

  const handleTeamChange = (option: SingleValue<Option>) => {
    setRequestTeam(
      teams.find((candidate) => candidate.id === Number(option?.value)) ?? null,
    );
  };

  const onRequestClick = async () => {
    if (!requestTeam || username.trim() === "") return;

    setRequesting(true);
    try {
      await createTeamMembershipRequest(requestTeam.id, username.trim());
      alertUser("Membership request sent!");
      setUsername("");
    } catch (error) {
      console.error(error);
      const errorMessage =
        error instanceof Error ? error.message : String(error);

      alertUser(/user/i.test(errorMessage) ? "User not found." : "Membership request could not be sent.");
    } finally {
      setRequesting(false);
    }
  };

  const onRemovePlayer = async (teamId: number, membershipId: number) => {
    const actionKey = `remove:${teamId}:${membershipId}`;
    setLoadingAction(actionKey);
    try {
      await deleteTeamMembership(teamId, membershipId);
      const members = await getTeamMembers(teamId);
      setTeamMembers((current) => ({ ...current, [teamId]: members }));
      alertUser("Player removed from the team.");
    } catch (error) {
      console.error(error);
      alertUser("Player could not be removed.");
    } finally {
      setLoadingAction(null);
    }
  };

  const onUpdateRequestStatus = async (
    teamId: number,
    membershipId: number,
    status: "approve" | "reject",
  ) => {
    const actionKey = `${status}:${teamId}:${membershipId}`;
    setLoadingAction(actionKey);
    try {
      await updateTeamMembershipStatus(teamId, membershipId, status);
      alertUser(
        status === "approve"
          ? "Membership request accepted."
          : "Membership request rejected.",
      );
    } catch (error) {
      console.error(error);
      alertUser("Membership request could not be updated.");
    } finally {
      setLoadingAction(null);
    }
  };

  const onDeleteRequest = async (teamId: number, membershipId: number) => {
    const actionKey = `delete:${teamId}:${membershipId}`;
    setLoadingAction(actionKey);
    try {
      await deleteTeamMembership(teamId, membershipId);
      alertUser("Membership request deleted.");
    } catch (error) {
      console.error(error);
      alertUser("Membership request could not be deleted.");
    } finally {
      setLoadingAction(null);
    }
  };

  const onLeaveTeam = async (teamId: number, membershipId: number) => {
    const actionKey = `leave:${teamId}:${membershipId}`;
    setLoadingAction(actionKey);
    try {
      await leaveTeam(teamId, membershipId);
      alertUser("You left the team.");
    } catch (error) {
      console.error(error);
      alertUser("You could not leave the team.");
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <>
      <Nav>
        <div className="nav-button-container">
          <button onClick={() => navigate("/dashboard")}>Dashboard</button>
          <button onClick={() => navigate("/profile")}>Profile</button>
          <button onClick={logout}>Log out</button>
        </div>
      </Nav>
      <div className="page-container team-page-container">
        <div className="title-container">
          <h1 className="page-header">Team</h1>
        </div>
        <div className="team-sections">
          <section className="team-section team-list-section">
            <h2>Your Teams</h2>
            {acceptedTeams.length === 0 ? (
              <p>No teams at this time.</p>
            ) : (
              acceptedTeams.map(({ id, name, membership }) => {
                const players = (teamMembers[id] ?? []).filter(
                  (member) =>
                    member.role === "athlete" && member.status === "approve",
                );

                return (
                  <div className="team-item" key={id}>
                    <div className="team-item-details">
                      <span className="team-name">{name}</span>
                      {user?.is_staff ? (
                        players.length === 0 ? (
                          <span>No players on this team.</span>
                        ) : (
                          players.map((player) => (
                            <div className="team-player" key={player.id}>
                              <span>{player.name}</span>
                              <button
                                disabled={
                                  loadingAction === `remove:${id}:${player.id}`
                                }
                                onClick={() =>
                                  onRemovePlayer(id, player.id)
                                }
                              >
                                {loadingAction === `remove:${id}:${player.id}`
                                  ? "Removing..."
                                  : "Remove"}
                              </button>
                            </div>
                          ))
                        )
                      ) : (
                        <span>{membership.role}</span>
                      )}
                    </div>
                    {!user?.is_staff && (
                      <button
                        disabled={
                          loadingAction === `leave:${id}:${membership.id}`
                        }
                        onClick={() => onLeaveTeam(id, membership.id)}
                      >
                        {loadingAction === `leave:${id}:${membership.id}`
                          ? "Leaving..."
                          : "Leave"}
                      </button>
                    )}
                  </div>
                );
              })
            )}
          </section>

          <section className="team-section team-requests-section">
            <h2>Team Requests</h2>
            {user?.is_staff && (
              <div className="team-request-form">
                <h3 className="input-title">Username</h3>
                <input
                  className="text-input"
                  type="text"
                  placeholder="Username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                />
                <h3 className="input-title">Team</h3>
                <SelectInput
                  className="team-select"
                  options={requestTeamOptions}
                  value={
                    requestTeam
                      ? {
                          value: String(requestTeam.id),
                          label: requestTeam.name,
                        }
                      : null
                  }
                  onChange={handleTeamChange}
                  placeholder="Select team..."
                  styles={{
                    control: (base) => ({
                      ...base,
                      width: "100%",
                    }),
                  }}
                />
                <button disabled={requesting} onClick={onRequestClick}>
                  {requesting ? "Requesting..." : "Request"}
                </button>
              </div>
            )}
            {teamMembershipRequests.length === 0 ? (
              <p>No requests at this time.</p>
            ) : (
              teamMembershipRequests.map((request) => (
                <Request
                  key={request.id}
                  request={request}
                  isStaff={Boolean(user?.is_staff)}
                  onAccept={() =>
                    onUpdateRequestStatus(
                      request.team_id,
                      request.id,
                      "approve",
                    )
                  }
                  onReject={() =>
                    onUpdateRequestStatus(
                      request.team_id,
                      request.id,
                      "reject",
                    )
                  }
                  onDelete={() =>
                    onDeleteRequest(request.team_id, request.id)
                  }
                  loadingAction={
                    loadingAction?.endsWith(`:${request.team_id}:${request.id}`)
                      ? (loadingAction.split(":")[0] as
                          | "accept"
                          | "reject"
                          | "delete")
                      : null
                  }
                />
              ))
            )}
          </section>

          <section className="team-section">
            <h2>Metrics Requests</h2>
            <p>No requests at this time.</p>
          </section>
        </div>
      </div>
    </>
  );
};

export default TeamPage;
