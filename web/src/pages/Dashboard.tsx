import type React from "react";
import { useRef, useState } from "react";
import type { SingleValue } from "react-select";
import { useNavigate } from "react-router-dom";
import MetricSquare from "../components/MetricSquare";
import SelectInput from "../components/SelectInput";
import { useBiometrics } from "../contexts/biometrics/BiometricsContext";
import { useTeam } from "../contexts/team/TeamContext";
import { useUser } from "../contexts/user/UserContext";
import Nav from "../Nav";
import type { GraphData } from "../types/Biometrics";
import type { Option } from "../types/Team";
import { alertUser } from "../utils/alerts";
import "./Dashboard.css";

const Dashboard: React.FC = () => {
  const { user, logout } = useUser();
  const { uploadCsv, skinTempDelta, bpmGraph, getMetrics } = useBiometrics();
  const {
    teams,
    teamsOptions,
    team,
    setTeam,
    approvedTeamMemberships,
    approvedTeamMembershipsOptions,
    teamMembership,
    setTeamMembership,
  } = useTeam();
  const navigate = useNavigate();

  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleTeamChange = (option: SingleValue<Option>) => {
    setTeam(
      teams.find((candidate) => candidate.id === Number(option?.value)) ?? null,
    );
  };

  const handleMembershipChange = (option: SingleValue<Option>) => {
    setTeamMembership(
      approvedTeamMemberships.find(
        (membership) => membership.id === Number(option?.value),
      ) ?? null,
    );
  };

  const handleUploadChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploading(true);
    try {
      if (!user) {
        throw new Error("No user is logged in at this time");
      }

      const files = e.target.files;
      if (!files || files.length !== 1) {
        throw new Error("Can only upload one CSV file at a time.");
      }

      const file = files[0];
      if (!file.name.toLowerCase().endsWith(".csv")) {
        throw new Error("File chosen must be a CSV file.");
      }

      const response = await uploadCsv(file, user?.id);
      getMetrics(user.id);
      alertUser(response.detail);
    } catch (error) {
      alertUser(error instanceof Error ? error.message : String(error));
    }
    setUploading(false);
  };

  return (
    <>
      <Nav>
        <div className="nav-button-container">
          {user?.is_staff && (
            <SelectInput
              options={approvedTeamMembershipsOptions}
              value={
                teamMembership
                  ? {
                      value: String(teamMembership.id),
                      label: String(teamMembership.user_id),
                    }
                  : null
              }
              onChange={handleMembershipChange}
              placeholder="Select player..."
            />
          )}
          {user?.is_staff && (
            <SelectInput
              options={teamsOptions}
              value={
                team
                  ? {
                      value: String(team.id),
                      label: team.name,
                    }
                  : null
              }
              onChange={handleTeamChange}
              placeholder="Select team..."
            />
          )}
          <button onClick={() => navigate("/requests")}>Requests</button>
          <button onClick={() => navigate("/profile")}>Profile</button>
          <button onClick={logout}>Log out</button>
        </div>
      </Nav>
      <div className="page-container">
        <div className="title-container">
          <h1 className="page-header">Metrics</h1>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            style={{ display: "none" }}
            onChange={handleUploadChange}
          />
          <button
            style={{ marginLeft: "auto" }}
            onClick={() => fileInputRef.current?.click()}
          >
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </div>
        <div className="metrics-container">
          <MetricSquare
            type="text"
            title="Skin Temperature Delta"
            value={getValueRepresentation(skinTempDelta)}
          />
          <MetricSquare
            type="text"
            title="Skin Temperature Delta"
            value={getValueRepresentation(skinTempDelta)}
          />
          <MetricSquare
            type="text"
            title="Skin Temperature Delta"
            value={getValueRepresentation(skinTempDelta)}
          />
          <MetricSquare
            type="graph"
            title="Beats Per Minute"
            data={getGraphRepresentation(bpmGraph)}
          />
          <MetricSquare
            type="graph"
            title="Beats Per Minute"
            data={getGraphRepresentation(bpmGraph)}
          />
          <MetricSquare
            type="graph"
            title="Beats Per Minute"
            data={getGraphRepresentation(bpmGraph)}
          />
        </div>
      </div>
    </>
  );
};

export default Dashboard;

const getValueRepresentation = (value: number | null) => {
  return value ? String(value) : "...";
};

const getGraphRepresentation = (graph: GraphData | null) => {
  return graph ?? { start: new Date(), end: new Date(), points: [] };
};
