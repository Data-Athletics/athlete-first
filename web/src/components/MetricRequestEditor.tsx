import type React from "react";
import { useState } from "react";
import type {
  DataSharingField,
  DataSharingValues,
  Team,
  TeamDataSharingRequirements,
} from "../types/Team";
import { DATA_SHARING_FIELDS } from "../utils/dataSharing";
import SelectInput from "./SelectInput";
import type { Option } from "../types/Team";

interface MetricRequestEditorProps {
  teams: Team[];
  requirements: Record<number, TeamDataSharingRequirements>;
  onSave: (teamId: number, requirements: DataSharingValues) => Promise<void>;
}

const MetricRequestEditor: React.FC<MetricRequestEditorProps> = ({
  teams,
  requirements,
  onSave,
}) => {
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(
    null,
  );
  const [fieldOverrides, setFieldOverrides] = useState<
    Partial<Record<DataSharingField, boolean>>
  >({});
  const [saving, setSaving] = useState(false);

  const activeTeamId = selectedTeamId ?? teams[0]?.id ?? null;
  const selectedTeam = teams.find(({ id }) => id === activeTeamId) ?? null;
  const selectedFields = {
    ...createSelectedFields(activeTeamId ? requirements[activeTeamId] : undefined),
    ...fieldOverrides,
  };

  const toggleField = (field: DataSharingField) => {
    setFieldOverrides((current) => ({
      ...current,
      [field]: !selectedFields[field],
    }));
  };

  const onSaveClick = async () => {
    if (!selectedTeam) return;

    setSaving(true);
    try {
      const payload = Object.fromEntries(
        DATA_SHARING_FIELDS.map(({ field }) => [
          field,
          selectedFields[field] ? true : undefined,
        ]).filter(([, value]) => value !== undefined),
      ) as DataSharingValues;
      await onSave(selectedTeam.id, payload);
    } finally {
      setSaving(false);
    }
  };

  const teamOptions: Option[] = teams.map(({ id, name }) => ({
    value: String(id),
    label: name,
  }));

  return (
    <div className="metric-request-editor">
      <div className="metric-request-editor-heading">
        <div>
          <h3>Request metrics from a team</h3>
          <p>
            Select the metrics athletes must share. Their team agreement will
            update when you save this request.
          </p>
        </div>
        <SelectInput
          className="metric-request-team-select"
          options={teamOptions}
          value={selectedTeam ? { value: String(selectedTeam.id), label: selectedTeam.name } : null}
          onChange={(option) => {
            setSelectedTeamId(option ? Number(option.value) : null);
            setFieldOverrides({});
          }}
          placeholder="Select team..."
        />
      </div>

      <div className="metric-request-fields" aria-label="Metrics to request">
        {DATA_SHARING_FIELDS.map(({ field, label, description }) => {
          const isSelected = selectedFields[field];

          return (
            <button
              className={`metric-request-field${isSelected ? " is-selected" : ""}`}
              key={field}
              type="button"
              aria-pressed={isSelected}
              onClick={() => toggleField(field)}
            >
              <span className="metric-request-field-copy">
                <span className="metric-request-field-label">{label}</span>
                <span className="metric-request-field-description">
                  {description}
                </span>
              </span>
              <span className="metric-request-toggle" aria-hidden="true">
                <span />
              </span>
            </button>
          );
        })}
      </div>

      <button
        className="metric-request-save"
        disabled={!selectedTeam || saving}
        onClick={onSaveClick}
      >
        {saving ? "Saving..." : "Save metric request"}
      </button>
    </div>
  );
};

const createSelectedFields = (
  requirements: TeamDataSharingRequirements | undefined,
) =>
  Object.fromEntries(
    DATA_SHARING_FIELDS.map(({ field }) => [field, requirements?.[field] === true]),
  ) as Record<DataSharingField, boolean>;

export default MetricRequestEditor;
