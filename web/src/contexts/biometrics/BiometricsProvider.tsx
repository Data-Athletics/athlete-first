import { useEffect, useRef, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { api } from "../../api/axios";
import type {
  CaloriesResponse,
  DataPoint,
  EffortResponse,
  GraphData,
  GraphResponse,
  HRVResponse,
  RespiratoryRateResponse,
  RHRResponse,
  SkinTempDeltaResponse,
  UploadResponse,
} from "../../types/Biometrics";
import { twoMonthsBack } from "../../utils/dates";
import { useTeam } from "../team/TeamContext";
import { useUser } from "../user/UserContext";
import { BiometricsContext } from "./BiometricsContext";

export function BiometricsProvider({ children }: { children: ReactNode }) {
  const { user } = useUser();
  const { dataSharingLoading, ownDataSharingBlocked } = useTeam();
  const { pathname } = useLocation();
  const loadedUserId = useRef<number | null>(null);

  const [loading, setLoading] = useState(true);
  const [calories, setCalories] = useState<number | null>(null);
  const [skinTempDelta, setSkinTempDelta] = useState<number | null>(null);
  const [hrv, setHrv] = useState<number | null>(null);
  const [rhr, setRhr] = useState<number | null>(null);
  const [respiratoryRate, setRespiratoryRate] = useState<number | null>(null);
  const [effort, setEffort] = useState<number | null>(null);
  const [bpmGraph, setBpmGraph] = useState<GraphData | null>(null);

  const uploadCsv = async (file: File, user_id: number) => {
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    const { data } = await api.post<UploadResponse>(
      `/biometrics/${user_id}`,
      formData,
    );

    setLoading(false);
    return data;
  };

  const getCalories = async (user_id: number) => {
    const { data } = await api.get<CaloriesResponse>(
      `/biometrics/${user_id}/calories`,
    );

    setCalories(data.calories);
  };

  const getSkinTempDelta = async (user_id: number) => {
    const { data } = await api.get<SkinTempDeltaResponse>(
      `/biometrics/${user_id}/skin-temp-delta`,
    );

    setSkinTempDelta(data.skin_temp_delta);
  };

  const getHRV = async (user_id: number) => {
    const { data } = await api.get<HRVResponse>(`/biometrics/${user_id}/hrv`, {
      params: { end_time: new Date() },
    });
    setHrv(data.hrv);
  };

  const getRHR = async (user_id: number) => {
    const end = new Date();
    const start = twoMonthsBack(end);
    const { data } = await api.get<RHRResponse>(`/biometrics/${user_id}/rhr`, {
      params: { start_time: start, end_time: end },
    });
    setRhr(data.rhr);
  };

  const getRespiratoryRate = async (user_id: number) => {
    const { data } = await api.get<RespiratoryRateResponse>(
      `/biometrics/${user_id}/respiratory-rate`,
    );
    setRespiratoryRate(data.respiratory_rate);
  };

  const getEffort = async (user_id: number) => {
    const { data } = await api.get<EffortResponse>(
      `/biometrics/${user_id}/effort`,
    );
    setEffort(data.effort);
  };

  const getBpmGraph = async (
    user_id: number,
    start: Date = twoMonthsBack(),
    end: Date = new Date(),
  ) => {
    const { data } = await api.get<GraphResponse>(
      `/biometrics/${user_id}/bpm`,
      {
        params: {
          start_time: start,
          end_time: end,
        },
      },
    );

    setBpmGraph({ start: start, end: end, points: transformGraphData(data) });
    console.log(data);
  };

  const getMetrics = async (user_id: number) => {
    clearMetrics();
    setLoading(true);
    await Promise.allSettled([
      getCalories(user_id),
      getSkinTempDelta(user_id),
      getHRV(user_id),
      getRHR(user_id),
      getRespiratoryRate(user_id),
      getEffort(user_id),
      getBpmGraph(user_id),
    ]);
    setLoading(false);
  };

  const clearMetrics = () => {
    setCalories(null);
    setSkinTempDelta(null);
    setHrv(null);
    setRhr(null);
    setRespiratoryRate(null);
    setEffort(null);
    setBpmGraph(null);
  };

  useEffect(() => {
    setLoading(true);
    setLoading(false);
  }, []);

  useEffect(() => {
    if (
      pathname !== "/dashboard" ||
      !user ||
      user.is_staff ||
      dataSharingLoading ||
      ownDataSharingBlocked
    ) {
      loadedUserId.current = null;
      return;
    }

    if (loadedUserId.current === user.id) return;

    loadedUserId.current = user.id;
    void getMetrics(user.id).catch((error) => {
      console.error("Failed to load metrics:", error);
    });
  }, [
    dataSharingLoading,
    ownDataSharingBlocked,
    pathname,
    user?.id,
    user?.is_staff,
  ]);

  return (
    <BiometricsContext.Provider
      value={{
        loading,
        calories,
        skinTempDelta,
        hrv,
        rhr,
        respiratoryRate,
        effort,
        bpmGraph,
        uploadCsv,
        getCalories,
        getSkinTempDelta,
        getHRV,
        getRHR,
        getRespiratoryRate,
        getEffort,
        getBpmGraph,
        getMetrics,
        clearMetrics,
      }}
    >
      {children}
    </BiometricsContext.Provider>
  );
}

const transformGraphData = (graphData: GraphResponse): DataPoint[] => {
  return graphData.x.map((xValue, index) => ({
    time: new Date(xValue).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    value: graphData.y[index] ?? 0,
  }));
};
