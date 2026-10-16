import { useEffect, useState, type ReactNode } from "react";
import { api } from "../../api/axios";
import type { UploadResponse } from "../../types/Biometrics";
import { BiometricsContext } from "./BiometricsContext";

export function BiometricsProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);

  const uploadCsv = async (file: File, user_id: number) => {
    const formData = new FormData();
    formData.append("file", file);

    const { data } = await api.post<UploadResponse>(
      `/biometrics/${user_id}`,
      formData,
    );
    console.log(data);

    return data;
  };

  useEffect(() => {
    setLoading(true);
    setLoading(false);
  }, []);

  return (
    <BiometricsContext.Provider
      value={{
        loading,
        uploadCsv,
      }}
    >
      {children}
    </BiometricsContext.Provider>
  );
}
