import type React from "react";
import type { SingleValue } from "react-select";
import Select from "react-select";
import { useTeam } from "../contexts/team/TeamContext";
import { selectStyles } from "../styles/select";
import type { Option } from "../types/Team";

const SelectTeam: React.FC = () => {
  const { teams, setTeam, team, teamsOptions } = useTeam();

  const handleTeamChange = (option: SingleValue<Option>) => {
    if (option) {
      setTeam(teams.find((team) => team.id === Number(option.value)) ?? null);
    }
  };

  return (
    <Select
      classNamePrefix="role-select"
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
      styles={selectStyles}
      isSearchable
      placeholder="Select team..."
    />
  );
};

export default SelectTeam;
