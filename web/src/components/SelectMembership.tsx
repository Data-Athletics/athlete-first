import type React from "react";
import type { SingleValue } from "react-select";
import Select from "react-select";
import { useTeam } from "../contexts/team/TeamContext";
import { useUser } from "../contexts/user/UserContext";
import { selectStyles } from "../styles/select";
import type { Option } from "../types/Team";

const SelectMembership: React.FC = () => {
  const { user } = useUser();
  const {
    teamMemberships,
    setTeamMembership,
    teamMembership,
    teamMembershipsOptions,
  } = useTeam();

  const handleTeamMembershipChange = (option: SingleValue<Option>) => {
    if (option) {
      setTeamMembership(
        teamMemberships.find(
          (membership) => membership.id === Number(option.value),
        ) ?? null,
      );
    }
  };

  return (
    <>
      {user?.is_staff && (
        <Select
          classNamePrefix="role-select"
          options={teamMembershipsOptions}
          value={
            teamMembership
              ? {
                  value: String(teamMembership.id),
                  label: String(teamMembership.user_id),
                }
              : null
          }
          onChange={handleTeamMembershipChange}
          styles={selectStyles}
          isSearchable
          placeholder="Select player..."
        />
      )}
    </>
  );
};

export default SelectMembership;
