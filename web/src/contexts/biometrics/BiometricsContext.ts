import { createContext, useContext } from "react";
import type { UploadResponse } from "../../types/Biometrics";

export interface BiometricsContextType {
  loading: boolean;
  uploadCsv: (file: File, user_id: number) => Promise<UploadResponse>;
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
