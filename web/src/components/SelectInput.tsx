import type { SingleValue, StylesConfig } from "react-select";
import Select, { mergeStyles } from "react-select";
import { selectStyles } from "../styles/select";
import type { Option } from "../types/Team";

interface SelectInputProps {
  options: Option[];
  value: Option | null;
  onChange: (option: SingleValue<Option>) => void;
  placeholder: string;
  styles?: StylesConfig<Option, false>;
  className?: string;
}

const SelectInput: React.FC<SelectInputProps> = ({
  options,
  value,
  onChange,
  placeholder,
  styles,
  className,
}) => {
  return (
    <Select
      classNamePrefix="role-select"
      className={className}
      options={options}
      value={value}
      onChange={onChange}
      styles={mergeStyles(selectStyles, styles)}
      isSearchable
      placeholder={placeholder}
    />
  );
};

export default SelectInput;
