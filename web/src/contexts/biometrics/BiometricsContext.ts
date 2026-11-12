import { createContext, useContext } from "react";
import type {
  GraphData,
  MetricSnapshot,
  UploadResponse,
} from "../../types/Biometrics";

export interface BiometricsContextType {
  loading: boolean;
  metricsRefreshing: boolean;
  metricsUpdatedAt: number | null;
  caloriesGraph: GraphData | null;
  hrv: number | null;
  rhr: number | null;
  respiratoryRate: number | null;
  effortGraph: GraphData | null;
  bpmGraph: GraphData | null;
  uploadCsv: (file: File, user_id: number) => Promise<UploadResponse>;
  getCalories: (user_id: number) => Promise<GraphData>;
  getHRV: (user_id: number) => Promise<number | null>;
  getRHR: (user_id: number) => Promise<number | null>;
  getRespiratoryRate: (user_id: number) => Promise<number | null>;
  getEffort: (user_id: number) => Promise<GraphData>;
  getBpmGraph: (
    user_id: number,
    start?: Date,
    end?: Date,
  ) => Promise<GraphData>;
  getMetricsSnapshot: (user_id: number) => Promise<MetricSnapshot>;
  getMetrics: (user_id: number) => Promise<void>;
  clearMetrics: () => void;
}

export const BiometricsContext = createContext<BiometricsContextType | null>(
  null,
);

export function useBiometrics() {
  const context = useContext(BiometricsContext);

  if (!context) {
    throw new Error("useBiometrics must be used within BiometricsProvider");
  }

  return context;
}
