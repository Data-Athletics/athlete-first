import type { StylesConfig } from "react-select";

export const selectStyles: StylesConfig<
  { value: string; label: string },
  false
> = {
  control: (base, state) => ({
    ...base,
    backgroundColor: "var(--text)",
    border: "none",
    borderRadius: "20px",
    width: "240px",
    minHeight: "43px",
    fontSize: "16px",
    boxShadow: state.isFocused
      ? "0 0 6px color-mix(in srgb, var(--container-bg), var(--text) 90%)"
      : "none",
    cursor: "pointer",
  }),
  valueContainer: (base) => ({
    ...base,
    padding: "0 10px",
  }),
  singleValue: (base) => ({
    ...base,
    color: "black",
  }),
  input: (base) => ({
    ...base,
    color: "black",
  }),
  placeholder: (base) => ({
    ...base,
    color: "#777",
  }),
  menu: (base) => ({
    ...base,
    backgroundColor: "var(--text)",
    borderRadius: "10px",
    overflow: "hidden",
  }),
  option: (base, state) => ({
    ...base,
    backgroundColor: state.isSelected
      ? "var(--container-bg)"
      : state.isFocused
        ? "#e5e5e5"
        : "transparent",
    color: state.isSelected ? "var(--text)" : "black",
    cursor: "pointer",
    fontSize: "16px",
  }),
  indicatorSeparator: () => ({
    display: "none",
  }),
  dropdownIndicator: (base) => ({
    ...base,
    color: "black",
    "&:hover": {
      color: "black",
    },
  }),
};
