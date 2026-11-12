import { useEffect, useRef, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { api } from "../../api/axios";
import type {
  GraphData,
  GraphResponse,
  HRVResponse,
  MetricSnapshot,
  RespiratoryRateResponse,
  RHRResponse,
  UploadResponse,
} from "../../types/Biometrics";
import { useTeam } from "../team/TeamContext";
import { useUser } from "../user/UserContext";
import { BiometricsContext } from "./BiometricsContext";

interface MetricsSnapshot {
  caloriesGraph: GraphData | null;
  hrv: number | null;
  rhr: number | null;
  respiratoryRate: number | null;
  effortGraph: GraphData | null;
  bpmGraph: GraphData | null;
  updatedAt: number;
}

const getCurrentTimestamp = () => Date.now();

export function BiometricsProvider({ children }: { children: ReactNode }) {
  const { user } = useUser();
  const { dataSharingLoading, ownDataSharingBlocked } = useTeam();
  const { pathname } = useLocation();
  const loadedUserId = useRef<number | null>(null);
  const metricsCache = useRef(new Map<number, MetricsSnapshot>());
  const latestMetricsRequest = useRef(0);

  const [loading, setLoading] = useState(true);
  const [metricsRefreshing, setMetricsRefreshing] = useState(false);
  const [metricsUpdatedAt, setMetricsUpdatedAt] = useState<number | null>(null);
  const [caloriesGraph, setCaloriesGraph] = useState<GraphData | null>(null);
  const [hrv, setHrv] = useState<number | null>(null);
  const [rhr, setRhr] = useState<number | null>(null);
  const [respiratoryRate, setRespiratoryRate] = useState<number | null>(null);
  const [effortGraph, setEffortGraph] = useState<GraphData | null>(null);
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

  const fetchCalories = async (user_id: number): Promise<GraphData> => {
    const { data } = await api.get<GraphResponse>(
      `/biometrics/${user_id}/calories`,
    );

    return transformGraphData(data);
  };

  const fetchHRV = async (user_id: number): Promise<number | null> => {
    const { data } = await api.get<HRVResponse>(`/biometrics/${user_id}/hrv`);
    return data.hrv;
  };

  const fetchRHR = async (user_id: number): Promise<number | null> => {
    const { data } = await api.get<RHRResponse>(`/biometrics/${user_id}/rhr`);
    return data.rhr;
  };

  const fetchRespiratoryRate = async (
    user_id: number,
  ): Promise<number | null> => {
    const { data } = await api.get<RespiratoryRateResponse>(
      `/biometrics/${user_id}/respiratory-rate`,
    );
    return data.respiratory_rate;
  };

  const fetchEffort = async (user_id: number): Promise<GraphData> => {
    const { data } = await api.get<GraphResponse>(
      `/biometrics/${user_id}/effort`,
    );
    return transformGraphData(data);
  };

  const fetchBpmGraph = async (
    user_id: number,
    start?: Date,
    end?: Date,
  ): Promise<GraphData> => {
    const { data } = await api.get<GraphResponse>(
      `/biometrics/${user_id}/bpm`,
      {
        params: { start_time: start, end_time: end },
      },
    );

    return transformGraphData(data);
  };

  const getCalories = async (user_id: number): Promise<GraphData> => {
    const graph = await fetchCalories(user_id);
    setCaloriesGraph(graph);
    return graph;
  };

  const getHRV = async (user_id: number): Promise<number | null> => {
    const value = await fetchHRV(user_id);
    setHrv(value);
    return value;
  };

  const getRHR = async (user_id: number): Promise<number | null> => {
    const value = await fetchRHR(user_id);
    setRhr(value);
    return value;
  };

  const getRespiratoryRate = async (user_id: number): Promise<number | null> => {
    const value = await fetchRespiratoryRate(user_id);
    setRespiratoryRate(value);
    return value;
  };

  const getEffort = async (user_id: number): Promise<GraphData> => {
    const graph = await fetchEffort(user_id);
    setEffortGraph(graph);
    return graph;
  };

  const getBpmGraph = async (
    user_id: number,
    start?: Date,
    end?: Date,
  ): Promise<GraphData> => {
    const graph = await fetchBpmGraph(user_id, start, end);
    setBpmGraph(graph);
    return graph;
  };

  const getMetricsSnapshot = async (
    user_id: number,
  ): Promise<MetricSnapshot> => {
    const [caloriesResult, hrvResult, rhrResult, respiratoryResult, effortResult, bpmResult] =
      await Promise.allSettled([
        fetchCalories(user_id),
        fetchHRV(user_id),
        fetchRHR(user_id),
        fetchRespiratoryRate(user_id),
        fetchEffort(user_id),
        fetchBpmGraph(user_id),
      ]);

    return {
      caloriesGraph:
        caloriesResult.status === "fulfilled" ? caloriesResult.value : null,
      hrv: hrvResult.status === "fulfilled" ? hrvResult.value : null,
      rhr: rhrResult.status === "fulfilled" ? rhrResult.value : null,
      respiratoryRate:
        respiratoryResult.status === "fulfilled"
          ? respiratoryResult.value
          : null,
      effortGraph:
        effortResult.status === "fulfilled" ? effortResult.value : null,
      bpmGraph: bpmResult.status === "fulfilled" ? bpmResult.value : null,
    };
  };

  const applyMetricsSnapshot = (snapshot: MetricsSnapshot) => {
    setCaloriesGraph(snapshot.caloriesGraph);
    setHrv(snapshot.hrv);
    setRhr(snapshot.rhr);
    setRespiratoryRate(snapshot.respiratoryRate);
    setEffortGraph(snapshot.effortGraph);
    setBpmGraph(snapshot.bpmGraph);
    setMetricsUpdatedAt(snapshot.updatedAt);
  };

  const getMetrics = async (user_id: number) => {
    const cachedSnapshot = metricsCache.current.get(user_id);
    if (cachedSnapshot) {
      applyMetricsSnapshot(cachedSnapshot);
      setLoading(false);
    } else {
      clearMetrics();
      setLoading(true);
    }

    const requestId = latestMetricsRequest.current + 1;
    latestMetricsRequest.current = requestId;
    setMetricsRefreshing(true);

    const [caloriesResult, hrvResult, rhrResult, respiratoryResult, effortResult, bpmResult] =
      await Promise.allSettled([
      fetchCalories(user_id),
      fetchHRV(user_id),
      fetchRHR(user_id),
      fetchRespiratoryRate(user_id),
      fetchEffort(user_id),
      fetchBpmGraph(user_id),
      ]);

    const snapshot: MetricsSnapshot = {
      caloriesGraph:
        caloriesResult.status === "fulfilled" ? caloriesResult.value : null,
      hrv: hrvResult.status === "fulfilled" ? hrvResult.value : null,
      rhr: rhrResult.status === "fulfilled" ? rhrResult.value : null,
      respiratoryRate:
        respiratoryResult.status === "fulfilled"
          ? respiratoryResult.value
          : null,
      effortGraph:
        effortResult.status === "fulfilled" ? effortResult.value : null,
      bpmGraph: bpmResult.status === "fulfilled" ? bpmResult.value : null,
      updatedAt: getCurrentTimestamp(),
    };

    metricsCache.current.set(user_id, snapshot);
    if (requestId === latestMetricsRequest.current) {
      applyMetricsSnapshot(snapshot);
      setLoading(false);
      setMetricsRefreshing(false);
    }
  };

  const clearMetrics = () => {
    setCaloriesGraph(null);
    setHrv(null);
    setRhr(null);
    setRespiratoryRate(null);
    setEffortGraph(null);
    setBpmGraph(null);
    setMetricsUpdatedAt(null);
  };

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
        metricsRefreshing,
        metricsUpdatedAt,
        caloriesGraph,
        hrv,
        rhr,
        respiratoryRate,
        effortGraph,
        bpmGraph,
        uploadCsv,
        getCalories,
        getHRV,
        getRHR,
        getRespiratoryRate,
        getEffort,
        getBpmGraph,
        getMetricsSnapshot,
        getMetrics,
        clearMetrics,
      }}
    >
      {children}
    </BiometricsContext.Provider>
  );
}

const transformGraphData = (graphData: GraphResponse): GraphData => {
  return {
    start: new Date(graphData.start),
    end: new Date(graphData.end),
    points: graphData.x.map((xValue, index) => ({
      time: new Date(xValue).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }),
      value: graphData.y[index] ?? 0,
    })),
  };
};
