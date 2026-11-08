import type {
  DataSharingField,
  DataSharingValues,
  MembershipDataSharingPolicy,
  TeamDataSharingRequirements,
} from "../types/Team";

export interface DataSharingFieldDefinition {
  field: DataSharingField;
  label: string;
  description: string;
}

export const DATA_SHARING_FIELDS: DataSharingFieldDefinition[] = [
  {
    field: "bpm_shared",
    label: "Beats per minute",
    description: "Heart-rate readings and the BPM trend graph.",
  },
  {
    field: "rhr_shared",
    label: "Resting heart rate",
    description: "The athlete's resting heart-rate summary.",
  },
  {
    field: "calories_shared",
    label: "Calories",
    description: "Estimated daily calories from biometric data.",
  },
  {
    field: "respiratory_rate_shared",
    label: "Respiratory rate",
    description: "The athlete's most recent respiratory-rate value.",
  },
  {
    field: "hrv_shared",
    label: "Heart-rate variability",
    description: "HRV calculated over the recent measurement window.",
  },
  {
    field: "effort_shared",
    label: "Effort",
    description: "The athlete's recent effort and strain estimate.",
  },
  {
    field: "skin_temp_delta_shared",
    label: "Skin temperature",
    description: "Change in skin temperature compared with baseline.",
  },
];

export const getRequiredFields = (
  requirements: TeamDataSharingRequirements | null | undefined,
) =>
  DATA_SHARING_FIELDS.filter(({ field }) => requirements?.[field] === true);

export const getFieldsByName = (fieldNames: string[]) =>
  DATA_SHARING_FIELDS.filter(({ field }) => fieldNames.includes(field));

export const getPolicyAcceptancePayload = (
  requirements: TeamDataSharingRequirements | null | undefined,
  policy: MembershipDataSharingPolicy | null | undefined,
): DataSharingValues =>
  Object.fromEntries(
    DATA_SHARING_FIELDS.map(({ field }) => {
      const requiredValue = requirements?.[field];
      if (requiredValue !== null && requiredValue !== undefined) {
        return [field, requiredValue];
      }

      return [field, policy?.[field] ?? true];
    }),
  ) as DataSharingValues;
