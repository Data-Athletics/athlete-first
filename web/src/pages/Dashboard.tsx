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
import type { GraphData, MetricSnapshot } from "../types/Biometrics";
import type { Option } from "../types/Team";
import { alertUser } from "../utils/alerts";
import { formatMetricValue } from "../utils/metric";
import "./Dashboard.css";

const METRIC_DEFINITIONS = [
  {
    key: "calories",
    categoryLabel: "Calories",
    title: "Per-day Average Calories",
    unit: "kcal/day",
    type: "graph",
  },
  {
    key: "hrv",
    categoryLabel: "HRV",
    title: "HRV Deviation",
    unit: "ms",
    type: "text",
  },
  {
    key: "rhr",
    categoryLabel: "RHR",
    title: "RHR Deviation",
    unit: "bpm",
    type: "text",
  },
  {
    key: "respiratoryRate",
    categoryLabel: "Respiratory rate",
    title: "Respiratory Rate Deviation",
    unit: "breaths/min",
    type: "text",
  },
  {
    key: "effort",
    categoryLabel: "Effort",
    title: "Per-day Average Effort",
    unit: "strain",
    type: "graph",
  },
  {
    key: "bpm",
    categoryLabel: "BPM",
    title: "Per-day Average BPM",
    unit: "bpm",
    type: "graph",
  },
] as const;

type MetricKey = (typeof METRIC_DEFINITIONS)[number]["key"];

interface PlayerMetricRow {
  id: number;
  name: string;
  snapshot: MetricSnapshot;
}

const Dashboard: React.FC = () => {
  const { user, logout } = useUser();
  const {
    loading: metricsLoading,
    metricsRefreshing,
    metricsUpdatedAt,
    uploadCsv,
    caloriesGraph,
    hrv,
    rhr,
    respiratoryRate,
    effortGraph,
    bpmGraph,
    getMetricsSnapshot,
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
  const [visibleMetricKeys, setVisibleMetricKeys] = useState<MetricKey[]>(
    METRIC_DEFINITIONS.map(({ key }) => key),
  );
  const [allPlayerMetricsState, setAllPlayerMetricsState] = useState<{
    requestKey: string;
    rows: PlayerMetricRow[];
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const metricUserId = user?.is_staff
    ? teamMembership?.user_id
    : user?.id;

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

  useEffect(() => {
    if (!user?.is_staff || !team || teamMembership) {
      return;
    }

    if (approvedTeamMemberships.length === 0) {
      return;
    }

    let cancelled = false;
    const requestKey = `${team.id}:${approvedTeamMemberships
      .map(({ id }) => id)
      .join(",")}`;

    void Promise.all(
      approvedTeamMemberships.map(async (membership) => ({
        id: membership.id,
        name: membership.name,
        snapshot: await getMetricsSnapshot(membership.user_id),
      })),
    )
      .then((rows) => {
        if (!cancelled) setAllPlayerMetricsState({ requestKey, rows });
      })
      .catch((error) => {
        if (!cancelled) {
          console.error("Failed to load all player metrics:", error);
          setAllPlayerMetricsState({ requestKey, rows: [] });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [
    approvedTeamMemberships,
    team?.id,
    teamMembership?.id,
    user?.is_staff,
  ]);

  const allPlayerMetricsRequestKey =
    team && !teamMembership
      ? `${team.id}:${approvedTeamMemberships.map(({ id }) => id).join(",")}`
      : null;
  const allPlayerMetricsLoading =
    Boolean(allPlayerMetricsRequestKey) &&
    approvedTeamMemberships.length > 0 &&
    allPlayerMetricsState?.requestKey !== allPlayerMetricsRequestKey;
  const allPlayerMetrics =
    allPlayerMetricsState?.requestKey === allPlayerMetricsRequestKey
      ? allPlayerMetricsState.rows
      : [];

  const toggleMetric = (key: MetricKey) => {
    setVisibleMetricKeys((current) =>
      current.includes(key)
        ? current.filter((currentKey) => currentKey !== key)
        : [...current, key],
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
          {user?.is_staff &&
            !teamMembership &&
            team &&
            approvedTeamMemberships.length > 0 && (
              <div className="metric-category-toggles metrics-title-categories">
                {METRIC_DEFINITIONS.map((definition) => (
                  <button
                    className={`metric-category-toggle${
                      visibleMetricKeys.includes(definition.key)
                        ? " is-selected"
                        : ""
                    }`}
                    key={definition.key}
                    type="button"
                    aria-pressed={visibleMetricKeys.includes(definition.key)}
                    onClick={() => toggleMetric(definition.key)}
                  >
                    {definition.categoryLabel}
                  </button>
                ))}
              </div>
            )}
          {metricUserId && !ownDataSharingBlocked && !dataSharingLoading && (
            <div className="metrics-refresh-controls">
              <span
                className={`metrics-refresh-status${
                  metricsRefreshing ? " is-refreshing" : ""
                }`}
                aria-live="polite"
              >
                {metricsRefreshing
                  ? "Updating..."
                  : metricsUpdatedAt
                    ? `Updated ${formatMetricsTime(metricsUpdatedAt)}`
                    : ""}
              </span>
              <button
                className="metrics-refresh-button"
                type="button"
                disabled={metricsRefreshing}
                onClick={() => void getMetrics(metricUserId)}
              >
                {metricsRefreshing ? "Updating..." : "Refresh"}
              </button>
            </div>
          )}
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
        ) : metricsLoading && !(user?.is_staff && !teamMembership) ? (
          <div className="dashboard-loading">
            <p>Loading...</p>
          </div>
        ) : (
          <div className="metrics-container">
            {user?.is_staff && !teamMembership ? (
              <>
                {!team ? (
                  <div className="aggregate-metrics-placeholder">
                    <h2>Select a team</h2>
                    <p>Choose a team above to view player metrics.</p>
                  </div>
                ) : approvedTeamMemberships.length === 0 ? (
                  <div className="aggregate-metrics-placeholder">
                    <h2>No approved players</h2>
                    <p>This team does not have any approved athletes yet.</p>
                  </div>
                ) : (
                  <>
                {allPlayerMetricsLoading ? (
                  <div className="dashboard-loading">
                    <p>Loading player metrics...</p>
                  </div>
                ) : visibleMetricKeys.length === 0 ? (
                  <div className="aggregate-metrics-placeholder">
                    <h2>No metric categories selected</h2>
                    <p>Choose a category above to show player metrics.</p>
                  </div>
                ) : (
                  <div className="aggregate-metric-groups">
                    {METRIC_DEFINITIONS.filter(({ key }) =>
                      visibleMetricKeys.includes(key),
                    ).map((definition) => (
                      <section
                        className="aggregate-metric-group"
                        key={definition.key}
                      >
                        <div className="aggregate-metric-group-heading">
                          <div>
                            <h2>{definition.title}</h2>
                            <p>({definition.unit})</p>
                          </div>
                          <span>
                            {allPlayerMetrics.length} player
                            {allPlayerMetrics.length === 1 ? "" : "s"}
                          </span>
                        </div>
                        <div className="aggregate-metric-grid">
                          {allPlayerMetrics.map(({ id, name, snapshot }) =>
                            renderMetricSquare(
                              definition,
                              snapshot,
                              name,
                              `${definition.key}-${id}`,
                            ),
                          )}
                        </div>
                      </section>
                    ))}
                  </div>
                )}
                  </>
                )}
              </>
            ) : (
              <>
                {METRIC_DEFINITIONS.map((definition) =>
                  renderMetricSquare(
                    definition,
                    {
                      caloriesGraph,
                      hrv,
                      rhr,
                      respiratoryRate,
                      effortGraph,
                      bpmGraph,
                    },
                    undefined,
                    definition.key,
                  ),
                )}
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
  if (value === null) return "—";
  return formatMetricValue(value);
};

const renderMetricSquare = (
  definition: (typeof METRIC_DEFINITIONS)[number],
  snapshot: MetricSnapshot,
  playerName?: string,
  key?: string,
) => {
  const commonProps = {
    title: definition.title,
    unit: definition.unit,
    playerName,
    compactHeader: Boolean(playerName),
  };

  if (definition.type === "graph") {
    const graph =
      definition.key === "calories"
        ? snapshot.caloriesGraph
        : definition.key === "effort"
          ? snapshot.effortGraph
          : snapshot.bpmGraph;

    return (
      <MetricSquare
        {...commonProps}
        key={key}
        type="graph"
        data={getGraphRepresentation(graph)}
      />
    );
  }

  const value =
    definition.key === "hrv"
      ? snapshot.hrv
      : definition.key === "rhr"
        ? snapshot.rhr
        : snapshot.respiratoryRate;

  return (
    <MetricSquare
      {...commonProps}
      key={key}
      type="text"
      value={getValueRepresentation(value)}
    />
  );
};

const formatMetricsTime = (timestamp: number) =>
  new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  }).format(timestamp);

const getGraphRepresentation = (graph: GraphData | null) => {
  return graph ?? { start: new Date(), end: new Date(), points: [] };
};
