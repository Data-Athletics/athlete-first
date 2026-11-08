import type React from "react";
import type {
  MembershipDataSharingPolicy,
  TeamDataSharingRequirements,
  TeamMembershipRequest,
} from "../types/Team";
import DataSharingRequirementsList from "./DataSharingRequirementsList";

interface RequestProps {
  request: TeamMembershipRequest;
  isStaff: boolean;
  onAccept: () => void;
  onReject: () => void;
  onDelete: () => void;
  loadingAction: "accept" | "reject" | "delete" | null;
  requirements?: TeamDataSharingRequirements;
  policy?: MembershipDataSharingPolicy | null;
}

const Request: React.FC<RequestProps> = ({
  request,
  isStaff,
  onAccept,
  onReject,
  onDelete,
  loadingAction,
  requirements,
  policy,
}) => (
  <div className="request-row">
    <div className="request-details">
      <span className="request-username">
        {isStaff ? request.name : request.team_name}
      </span>
      {isStaff && <span className="request-team">{request.team_name}</span>}
      <DataSharingRequirementsList
        requirements={requirements}
        invalidFields={isStaff ? undefined : policy?.invalid_fields}
        policyAccepted={
          isStaff ? undefined : policy !== null && policy !== undefined
        }
      />
    </div>
    <div className="request-actions">
      {isStaff ? (
        <button disabled={loadingAction !== null} onClick={onDelete}>
          {loadingAction === "delete" ? "Deleting..." : "Delete"}
        </button>
      ) : (
        <>
          <button disabled={loadingAction !== null} onClick={onAccept}>
            {loadingAction === "accept" ? "Accepting..." : "Accept"}
          </button>
          <button disabled={loadingAction !== null} onClick={onReject}>
            {loadingAction === "reject" ? "Rejecting..." : "Reject"}
          </button>
        </>
      )}
    </div>
  </div>
);

export default Request;
