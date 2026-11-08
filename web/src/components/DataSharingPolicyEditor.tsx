import type React from "react";
import { useState } from "react";
import type {
  DataSharingField,
  DataSharingValues,
  MembershipDataSharingPolicy,
  Team,
  TeamDataSharingRequirements,
} from "../types/Team";
import { DATA_SHARING_FIELDS } from "../utils/dataSharing";
import DataSharingRequirementsList from "./DataSharingRequirementsList";

interface DataSharingPolicyEditorProps {
  team: Team;
  requirements: TeamDataSharingRequirements | undefined;
  policy: MembershipDataSharingPolicy | null | undefined;
  onSave: (teamId: number, policy: DataSharingValues) => Promise<void>;
}

const DataSharingPolicyEditor: React.FC<DataSharingPolicyEditorProps> = ({
  team,
  requirements,
  policy,
  onSave,
}) => {
  const [fieldOverrides, setFieldOverrides] = useState<
    Partial<Record<DataSharingField, boolean>>
  >({});
  const [saving, setSaving] = useState(false);

  const selectedFields = {
    ...createSelectedFields(requirements, policy),
    ...fieldOverrides,
  };

  const toggleField = (field: DataSharingField) => {
    if (requirements?.[field] === true) return;

    setFieldOverrides((current) => ({
      ...current,
      [field]: !selectedFields[field],
    }));
  };

  const onSaveClick = async () => {
    setSaving(true);
    try {
      const payload = Object.fromEntries(
        DATA_SHARING_FIELDS.map(({ field }) => [field, selectedFields[field]]),
      ) as DataSharingValues;
      await onSave(team.id, payload);
      setFieldOverrides({});
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="data-sharing-policy-editor">
      <div className="data-sharing-policy-heading">
        <div>
          <h3>{team.name}</h3>
          <p>Choose which metrics this team can access from your data.</p>
        </div>
        <DataSharingRequirementsList
          requirements={requirements}
          invalidFields={policy?.invalid_fields}
          policyAccepted={policy !== null && policy !== undefined}
        />
      </div>

      {policy === null && (
        <div className="data-sharing-pending-banner">
          This policy has not been accepted yet. Required fields are checked
          below to show what the team requires; saving will record your choice.
        </div>
      )}

      <div className="metric-request-fields" aria-label={`${team.name} sharing policy`}>
        {DATA_SHARING_FIELDS.map(({ field, label, description }) => {
          const isRequired = requirements?.[field] === true;
          const isSelected = selectedFields[field];
          const isConflicting = policy?.invalid_fields.includes(field) ?? false;

          return (
            <button
              className={`metric-request-field${isSelected ? " is-selected" : ""}${isRequired ? " is-required" : ""}${isConflicting ? " is-conflicting" : ""}`}
              key={field}
              type="button"
              aria-pressed={isSelected}
              aria-label={`${label}${isRequired ? ", required" : ""}${isConflicting ? ", needs update" : ""}`}
              disabled={isRequired}
              onClick={() => toggleField(field)}
            >
              <span className="metric-request-field-copy">
                <span className="metric-request-field-label">
                  {label}
                  {isRequired && (
                    <span className="required-metric-label">Required</span>
                  )}
                  {isConflicting && (
                    <span className="conflicting-metric-label">Needs update</span>
                  )}
                </span>
                <span className="metric-request-field-description">
                  {description}
                </span>
                {isConflicting && (
                  <span className="data-sharing-alert">
                    Your previous choice does not meet the team requirement.
                  </span>
                )}
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
        disabled={saving}
        onClick={onSaveClick}
      >
        {saving ? "Saving..." : "Save sharing policy"}
      </button>
    </div>
  );
};

const createSelectedFields = (
  requirements: TeamDataSharingRequirements | undefined,
  policy: MembershipDataSharingPolicy | null | undefined,
) =>
  Object.fromEntries(
    DATA_SHARING_FIELDS.map(({ field }) => [
      field,
      requirements?.[field] === true || policy?.[field] !== false,
    ]),
  ) as Record<DataSharingField, boolean>;

export default DataSharingPolicyEditor;
