import { createContext, useContext } from "react";
import type { GraphData, UploadResponse } from "../../types/Biometrics";

export interface BiometricsContextType {
  loading: boolean;
  calories: number | null;
  skinTempDelta: number | null;
  bpmGraph: GraphData | null;
  uploadCsv: (file: File, user_id: number) => Promise<UploadResponse>;
  getCalories: (user_id: number) => Promise<void>;
  getSkinTempDelta: (user_id: number) => Promise<void>;
  getBpmGraph: (user_id: number, start: Date, end: Date) => Promise<void>;
  getMetrics: (user_id: number) => Promise<void>;
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
