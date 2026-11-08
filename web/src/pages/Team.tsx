import type React from "react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { SingleValue } from "react-select";
import DataSharingPolicyEditor from "../components/DataSharingPolicyEditor";
import DataSharingRequirementsList from "../components/DataSharingRequirementsList";
import MetricRequestEditor from "../components/MetricRequestEditor";
import Request from "../components/Request";
import SelectInput from "../components/SelectInput";
import { useTeam } from "../contexts/team/TeamContext";
import { useUser } from "../contexts/user/UserContext";
import Nav from "../Nav";
import type { DataSharingValues, Option, Team, TeamMember } from "../types/Team";
import { alertUser } from "../utils/alerts";
import { getPolicyAcceptancePayload } from "../utils/dataSharing";
import "./Team.css";

type TeamSectionKey = "teams" | "requests" | "metrics";

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
    dataSharingRequirements,
    dataSharingPolicies,
    dataSharingLoading,
    updateTeamDataSharingRequirements,
    updateMembershipDataSharingPolicy,
  } = useTeam();

  const [username, setUsername] = useState("");
  const [requestTeam, setRequestTeam] = useState<Team | null>(null);
  const [requesting, setRequesting] = useState(false);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [teamMembers, setTeamMembers] = useState<Record<number, TeamMember[]>>(
    {},
  );
  const [openSections, setOpenSections] = useState<
    Record<TeamSectionKey, boolean>
  >({ teams: true, requests: true, metrics: true });
  const [selectedPolicyTeamId, setSelectedPolicyTeamId] = useState<number | null>(
    null,
  );
  const requestTeamOptions = teamsOptions;
  const acceptedTeams = myTeams.filter(
    ({ membership }) => membership.status === "approve",
  );
  const metricRequests = acceptedTeams.filter(({ id, membership }) => {
    if (user?.is_staff || membership.role !== "athlete") return false;

    const policy = dataSharingPolicies[id];
    return policy === null || policy === undefined || policy.invalid_fields.length > 0;
  });
  const athleteTeams = acceptedTeams.filter(
    ({ membership }) => membership.role === "athlete",
  );
  const activePolicyTeamId =
    selectedPolicyTeamId ?? athleteTeams[0]?.id ?? null;
  const activePolicyTeam =
    athleteTeams.find(({ id }) => id === activePolicyTeamId) ?? null;

  const toggleSection = (section: TeamSectionKey) => {
    setOpenSections((current) => ({
      ...current,
      [section]: !current[section],
    }));
  };

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

  const onAcceptTeamRequest = async (
    teamId: number,
    membershipId: number,
  ) => {
    const actionKey = `accept:${teamId}:${membershipId}`;
    setLoadingAction(actionKey);
    try {
      await updateMembershipDataSharingPolicy(
        teamId,
        getPolicyAcceptancePayload(
          dataSharingRequirements[teamId],
          dataSharingPolicies[teamId],
        ),
      );
      await updateTeamMembershipStatus(teamId, membershipId, "approve");
      alertUser("Team request accepted and metrics sharing confirmed.");
    } catch (error) {
      console.error(error);
      alertUser("Team request could not be accepted.");
    } finally {
      setLoadingAction(null);
    }
  };

  const onAcceptMetricRequest = async (teamId: number) => {
    const actionKey = `metrics:${teamId}`;
    setLoadingAction(actionKey);
    try {
      await updateMembershipDataSharingPolicy(
        teamId,
        getPolicyAcceptancePayload(
          dataSharingRequirements[teamId],
          dataSharingPolicies[teamId],
        ),
      );
      alertUser("Metric request accepted.");
    } catch (error) {
      console.error(error);
      alertUser("Metric request could not be accepted.");
    } finally {
      setLoadingAction(null);
    }
  };

  const onSaveAthletePolicy = async (
    teamId: number,
    policy: DataSharingValues,
  ) => {
    try {
      await updateMembershipDataSharingPolicy(teamId, policy);
      alertUser("Your sharing policy was updated.");
    } catch (error) {
      console.error(error);
      alertUser("Your sharing policy could not be updated.");
      throw error;
    }
  };

  const onSaveMetricRequest = async (
    teamId: number,
    requirements: DataSharingValues,
  ) => {
    try {
      await updateTeamDataSharingRequirements(teamId, requirements);
      alertUser("Metric request updated for the team.");
    } catch (error) {
      console.error(error);
      alertUser("Metric request could not be updated.");
      throw error;
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
          <section
            className={`team-section team-accordion team-list-section${
              openSections.teams ? " is-open" : ""
            }`}
          >
            <button
              className="team-section-toggle"
              type="button"
              aria-expanded={openSections.teams}
              onClick={() => toggleSection("teams")}
            >
              <span className="team-section-toggle-title">Your Teams</span>
              <span className="team-section-toggle-icon" aria-hidden="true" />
            </button>
            <div className="team-section-panel">
              <div className="team-section-panel-inner">
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
                        <>
                          <span>{membership.role}</span>
                          {(dataSharingPolicies[id] === null ||
                            dataSharingPolicies[id] === undefined ||
                            dataSharingPolicies[id]?.invalid_fields.length > 0) && (
                            <span className="data-sharing-alert">
                              Data sharing needs your attention
                            </span>
                          )}
                        </>
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
              </div>
            </div>
          </section>

          <section
            className={`team-section team-accordion team-requests-section${
              openSections.requests ? " is-open" : ""
            }`}
          >
            <button
              className="team-section-toggle"
              type="button"
              aria-expanded={openSections.requests}
              onClick={() => toggleSection("requests")}
            >
              <span className="team-section-toggle-title">Team Requests</span>
              <span className="team-section-toggle-icon" aria-hidden="true" />
            </button>
            <div className="team-section-panel">
              <div className="team-section-panel-inner">
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
                    user?.is_staff
                      ? onUpdateRequestStatus(
                          request.team_id,
                          request.id,
                          "approve",
                        )
                      : onAcceptTeamRequest(request.team_id, request.id)
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
                  requirements={dataSharingRequirements[request.team_id]}
                  policy={dataSharingPolicies[request.team_id]}
                />
              ))
            )}
              </div>
            </div>
          </section>

          <section
            className={`team-section team-accordion metrics-requests-section${
              openSections.metrics ? " is-open" : ""
            }`}
          >
            <button
              className="team-section-toggle"
              type="button"
              aria-expanded={openSections.metrics}
              onClick={() => toggleSection("metrics")}
            >
              <span className="team-section-toggle-title">Metrics Requests</span>
              <span className="team-section-toggle-icon" aria-hidden="true" />
            </button>
            <div className="team-section-panel">
              <div className="team-section-panel-inner">
            {dataSharingLoading ? (
              <p>Loading...</p>
            ) : user?.is_staff ? (
              <MetricRequestEditor
                teams={acceptedTeams}
                requirements={dataSharingRequirements}
                onSave={onSaveMetricRequest}
              />
            ) : (
              <>
                <div className="policy-editor-list">
                  <div className="policy-editor-list-heading">
                    <div>
                      <h3>Your sharing policies</h3>
                      <p>
                        Required metrics stay enabled. You can change any other
                        sharing choice at any time.
                      </p>
                    </div>
                    <SelectInput
                      className="policy-team-select"
                      options={athleteTeams.map(({ id, name }) => ({
                        value: String(id),
                        label: name,
                      }))}
                      value={
                        activePolicyTeam
                          ? {
                              value: String(activePolicyTeam.id),
                              label: activePolicyTeam.name,
                            }
                          : null
                      }
                      onChange={(option) =>
                        setSelectedPolicyTeamId(
                          option ? Number(option.value) : null,
                        )
                      }
                      placeholder="Select team..."
                    />
                  </div>
                  {activePolicyTeam ? (
                    <DataSharingPolicyEditor
                      team={activePolicyTeam}
                      requirements={dataSharingRequirements[activePolicyTeam.id]}
                      policy={dataSharingPolicies[activePolicyTeam.id]}
                      onSave={onSaveAthletePolicy}
                    />
                  ) : (
                    <p>No approved teams have a sharing policy yet.</p>
                  )}
                </div>
                <div className="metric-request-list">
                  <h3>Requests to review</h3>
                  {metricRequests.length === 0 ? (
                    <p>No new metric requests at this time.</p>
                  ) : (
                    metricRequests.map(({ id, name }) => {
                      const policy = dataSharingPolicies[id];
                      const invalidFields = policy?.invalid_fields ?? [];
                      const actionKey = `metrics:${id}`;

                      return (
                        <div className="metric-request-row request-row" key={id}>
                          <div className="request-details">
                            <span className="request-username">{name}</span>
                            <span className="request-team">
                              Confirm the metrics you share with this team.
                            </span>
                            {invalidFields.length > 0 && (
                              <span className="data-sharing-alert">
                                Review the fields marked below before accepting.
                              </span>
                            )}
                            <DataSharingRequirementsList
                              requirements={dataSharingRequirements[id]}
                              invalidFields={invalidFields}
                              policyAccepted={policy !== null && policy !== undefined}
                            />
                          </div>
                          <div className="request-actions">
                            <button
                              disabled={loadingAction === actionKey}
                              onClick={() => onAcceptMetricRequest(id)}
                            >
                              {loadingAction === actionKey
                                ? "Accepting..."
                                : "Accept metrics"}
                            </button>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </>
            )}
              </div>
            </div>
          </section>
        </div>
      </div>
    </>
  );
};

export default TeamPage;
