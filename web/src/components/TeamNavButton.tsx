import { useNavigate } from "react-router-dom";
import { useTeam } from "../contexts/team/TeamContext";

const TeamNavButton = () => {
  const navigate = useNavigate();
  const { hasDataSharingAttention } = useTeam();

  return (
    <button
      className="team-nav-button"
      aria-label={
        hasDataSharingAttention
          ? "Team — data sharing action needed"
          : "Team"
      }
      onClick={() => navigate("/team")}
    >
      <span>Team</span>
      {hasDataSharingAttention && (
        <span className="team-attention-dot" aria-hidden="true" />
      )}
    </button>
  );
};

export default TeamNavButton;
