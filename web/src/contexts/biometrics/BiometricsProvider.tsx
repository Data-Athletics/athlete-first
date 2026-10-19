import { useEffect, useState, type ReactNode } from "react";
import { api } from "../../api/axios";
import type {
  CaloriesResponse,
  DataPoint,
  GraphData,
  GraphResponse,
  SkinTempDeltaResponse,
  UploadResponse,
} from "../../types/Biometrics";
import { twoMonthsBack } from "../../utils/dates";
import { useUser } from "../user/UserContext";
import { BiometricsContext } from "./BiometricsContext";

export function BiometricsProvider({ children }: { children: ReactNode }) {
  const { user } = useUser();

  const [loading, setLoading] = useState(true);
  const [calories, setCalories] = useState<number | null>(null);
  const [skinTempDelta, setSkinTempDelta] = useState<number | null>(null);
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
    getCalories(user_id);
    getSkinTempDelta(user_id);
    getBpmGraph(user_id);
  };

  useEffect(() => {
    setLoading(true);
    setLoading(false);
  }, []);

  useEffect(() => {
    if (user) {
      getMetrics(user.id);
    }
  }, [user]);

  return (
    <BiometricsContext.Provider
      value={{
        loading,
        calories,
        skinTempDelta,
        bpmGraph,
        uploadCsv,
        getCalories,
        getSkinTempDelta,
        getBpmGraph,
        getMetrics,
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
