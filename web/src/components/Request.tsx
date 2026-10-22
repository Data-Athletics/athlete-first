import type React from "react";
import type { TeamMembershipRequest } from "../types/Team";

interface RequestProps {
  request: TeamMembershipRequest;
  isStaff: boolean;
  onAccept: () => void;
  onReject: () => void;
  onDelete: () => void;
}

const Request: React.FC<RequestProps> = ({
  request,
  isStaff,
  onAccept,
  onReject,
  onDelete,
}) => (
  <div className="request-row">
    <div className="request-details">
      <span className="request-username">
        {isStaff ? request.username : request.team_name}
      </span>
      {isStaff && <span className="request-team">{request.team_name}</span>}
    </div>
    <div className="request-actions">
      {isStaff ? (
        <button onClick={onDelete}>Delete</button>
      ) : (
        <>
          <button onClick={onAccept}>Accept</button>
          <button onClick={onReject}>Reject</button>
        </>
      )}
    </div>
  </div>
);

export default Request;
