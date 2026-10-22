import type React from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { SingleValue } from "react-select";
import Request from "../components/Request";
import SelectInput from "../components/SelectInput";
import { useTeam } from "../contexts/team/TeamContext";
import { useUser } from "../contexts/user/UserContext";
import Nav from "../Nav";
import type { Option, Team } from "../types/Team";
import { alertUser } from "../utils/alerts";
import "./Requests.css";

const Requests: React.FC = () => {
  const navigate = useNavigate();

  const { user, logout } = useUser();
  const {
    teams,
    teamsOptions,
    createTeamMembershipRequest,
    teamMembershipRequests,
    updateTeamMembershipStatus,
    deleteTeamMembership,
  } = useTeam();

  const [username, setUsername] = useState("");
  const [requestTeam, setRequestTeam] = useState<Team | null>(null);
  const requestTeamOptions = teamsOptions.filter(
    (option) => option.value !== "all",
  );

  const handleTeamChange = (option: SingleValue<Option>) => {
    setRequestTeam(
      teams.find((candidate) => candidate.id === Number(option?.value)) ?? null,
    );
  };

  const onRequestClick = async () => {
    if (!requestTeam || username.trim() === "") {
      return;
    }

    try {
      await createTeamMembershipRequest(requestTeam.id, username.trim());
      alertUser("Membership request sent!");
      setUsername("");
    } catch (error) {
      console.error(error);

      const errorMessage =
        error instanceof Error ? error.message : String(error);

      if (/user/i.test(errorMessage)) {
        alertUser("User not found.");
        return;
      }

      alertUser("Membership request could not be sent.");
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
      <div className="page-container">
        <div className="title-container">
          <h1 className="page-header">Requests</h1>
        </div>
        <div
          className={`requests-layout${user?.is_staff ? "" : " requests-layout-single"}`}
        >
          {user?.is_staff && (
            <div className="request-container">
              <h2>Make a Request</h2>
              <h3 className="input-title">Username</h3>
              <input
                className="text-input"
                type="text"
                placeholder="Username"
                value={username}
                style={{ width: "100%", boxSizing: "border-box" }}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
              <h3 className="input-title">Team</h3>
              <SelectInput
                className="request-team-select"
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
              <button
                onClick={onRequestClick}
                style={{ marginTop: "30px", width: "100%" }}
              >
                Request
              </button>
            </div>
          )}
          <div className="request-container membership-requests-container">
            <h2>{user?.is_staff ? "Outgoing Requests" : "Team Requests"}</h2>
            {teamMembershipRequests.length === 0 ? (
              <p>No requests at this time.</p>
            ) : (
              teamMembershipRequests.map((request) => (
                <Request
                  key={request.id}
                  request={request}
                  isStaff={Boolean(user?.is_staff)}
                  onAccept={() =>
                    updateTeamMembershipStatus(
                      request.team_id,
                      request.id,
                      "approve",
                    )
                  }
                  onReject={() =>
                    updateTeamMembershipStatus(
                      request.team_id,
                      request.id,
                      "reject",
                    )
                  }
                  onDelete={() =>
                    deleteTeamMembership(request.team_id, request.id)
                  }
                />
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default Requests;
