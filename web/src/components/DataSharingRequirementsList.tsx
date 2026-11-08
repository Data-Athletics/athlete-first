import type React from "react";
import type { TeamDataSharingRequirements } from "../types/Team";
import { getFieldsByName, getRequiredFields } from "../utils/dataSharing";

interface DataSharingRequirementsListProps {
  requirements: TeamDataSharingRequirements | null | undefined;
  invalidFields?: string[];
  policyAccepted?: boolean;
}

const DataSharingRequirementsList: React.FC<DataSharingRequirementsListProps> = ({
  requirements,
  invalidFields = [],
  policyAccepted,
}) => {
  const requiredFields = getRequiredFields(requirements);
  const conflictingFields = getFieldsByName(invalidFields);

  return (
    <div className="data-sharing-requirements">
      <span className="data-sharing-requirements-title">
        {requiredFields.length > 0
          ? "Metrics required to share"
          : "No additional metrics are required"}
      </span>
      {requiredFields.length > 0 && (
        <div className="data-sharing-requirement-chips">
          {requiredFields.map(({ field, label }) => (
            <span
              className="data-sharing-requirement-chip is-required"
              key={field}
            >
              {label}
            </span>
          ))}
        </div>
      )}
      {conflictingFields.length > 0 && (
        <div className="data-sharing-conflicts">
          <span className="data-sharing-conflicts-title">
            Fields that need updating
          </span>
          <div className="data-sharing-requirement-chips">
            {conflictingFields.map(({ field, label }) => (
              <span
                className="data-sharing-requirement-chip is-conflicting"
                key={field}
              >
                {label}
              </span>
            ))}
          </div>
        </div>
      )}
      {policyAccepted === false && requiredFields.length > 0 && (
        <span className="data-sharing-pending">
          Required metrics are shown checked for acceptance, but this policy
          has not been accepted yet.
        </span>
      )}
    </div>
  );
};

export default DataSharingRequirementsList;
