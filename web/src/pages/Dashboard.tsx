import type React from "react";
import { useEffect, useRef, useState } from "react";
import type { SingleValue } from "react-select";
import { useNavigate } from "react-router-dom";
import MetricSquare from "../components/MetricSquare";
import SelectInput from "../components/SelectInput";
import TeamNavButton from "../components/TeamNavButton";
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
  const {
    uploadCsv,
    calories,
    skinTempDelta,
    hrv,
    rhr,
    respiratoryRate,
    effort,
    bpmGraph,
    getMetrics,
    clearMetrics,
  } = useBiometrics();
  const {
    loading: teamLoading,
    teams,
    teamsOptions,
    team,
    setTeam,
    approvedTeamMemberships,
    approvedTeamMembershipsOptions,
    teamMembership,
    setTeamMembership,
    dataSharingLoading,
    ownDataSharingBlocked,
  } = useTeam();
  const navigate = useNavigate();

  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleTeamChange = (option: SingleValue<Option>) => {
    setTeam(
      teams.find((candidate) => candidate.id === Number(option?.value)) ?? null,
    );
    if (user?.is_staff) {
      setTeamMembership(null);
      clearMetrics();
    }
  };

  const handleMembershipChange = (option: SingleValue<Option>) => {
    if (!option || option.value === "all") {
      setTeamMembership(null);
      clearMetrics();
      return;
    }

    const membership = approvedTeamMemberships.find(
      (candidate) => candidate.id === Number(option.value),
    );
    setTeamMembership(membership ?? null);
  };

  useEffect(() => {
    if (user?.is_staff && teamMembership) {
      void getMetrics(teamMembership.user_id);
    }
  }, [
    teamMembership?.user_id,
    user?.is_staff,
  ]);

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

      const metricUserId = user.is_staff
        ? teamMembership?.user_id
        : user.id;
      if (!metricUserId) {
        throw new Error("Select a player before uploading biometrics.");
      }

      const response = await uploadCsv(file, metricUserId);
      await getMetrics(metricUserId);
      alertUser(response.detail);
    } catch (error) {
      alertUser(error instanceof Error ? error.message : String(error));
    }
    setUploading(false);
  };

  if (teamLoading || dataSharingLoading) {
    return (
      <>
        <Nav>
          <div className="nav-button-container">
            <TeamNavButton />
            <button onClick={() => navigate("/profile")}>Profile</button>
            <button onClick={logout}>Log out</button>
          </div>
        </Nav>
        <div className="page-container dashboard-loading">
          <p>Loading...</p>
        </div>
      </>
    );
  }

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
                      label: teamMembership.name,
                    }
                  : { value: "all", label: "All" }
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
          <TeamNavButton />
          <button onClick={() => navigate("/profile")}>Profile</button>
          <button onClick={logout}>Log out</button>
        </div>
      </Nav>
      <div className="page-container">
        <div className="title-container">
          <h1 className="page-header">Metrics</h1>
          {!user?.is_staff && (
            <>
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
            </>
          )}
        </div>
        {!user?.is_staff && ownDataSharingBlocked ? (
          <div className="metrics-access-blocked">
            <h2>Metrics sharing needs your attention</h2>
            <p>
              Review and accept the current team metric requirements before
              viewing your data.
            </p>
            <button onClick={() => navigate("/team")}>Review sharing</button>
          </div>
        ) : (
        <div className="metrics-container">
            {user?.is_staff && !teamMembership ? (
              <div className="aggregate-metrics-placeholder">
                <h2>Team Aggregated Metrics</h2>
                <p>Coming soon</p>
              </div>
            ) : (
              <>
                <MetricSquare
                  type="text"
                  title="Calories"
                  value={getValueRepresentation(calories)}
                />
                <MetricSquare
                  type="text"
                  title="Skin Temperature Delta"
                  value={getValueRepresentation(skinTempDelta)}
                />
                <MetricSquare
                  type="text"
                  title="HRV"
                  value={getValueRepresentation(hrv)}
                />
                <MetricSquare
                  type="text"
                  title="RHR"
                  value={getValueRepresentation(rhr)}
                />
                <MetricSquare
                  type="text"
                  title="Respiratory Rate"
                  value={getValueRepresentation(respiratoryRate)}
                />
                <MetricSquare
                  type="text"
                  title="Effort"
                  value={getValueRepresentation(effort)}
                />
                <MetricSquare
                  type="graph"
                  title="Beats Per Minute"
                  data={getGraphRepresentation(bpmGraph)}
                />
              </>
            )}
        </div>
        )}
      </div>
    </>
  );
};

export default Dashboard;

const getValueRepresentation = (value: number | null) => {
  if (value === null) return "...";
  if (Math.abs(value) < 1000) {
    const rounded = value.toFixed(1);
    return rounded.length <= 4 ? rounded : String(Math.round(value));
  }

  const compact = new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 1,
    notation: "compact",
  }).format(value);

  return compact.length <= 4
    ? compact
    : new Intl.NumberFormat("en-US", {
        maximumFractionDigits: 0,
        notation: "compact",
      }).format(value);
};

const getGraphRepresentation = (graph: GraphData | null) => {
  return graph ?? { start: new Date(), end: new Date(), points: [] };
};
