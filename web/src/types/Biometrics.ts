export interface IntervalData {
  start: Date;
  end: Date;
}

export interface DataPoint {
  time: string;
  value: number;
}

export interface UploadResponse {
  detail: string;
  code: number;
}

export interface CaloriesResponse {
  calories: number;
}

export interface SkinTempDeltaResponse {
  skin_temp_delta: number;
}

export interface HRVResponse extends IntervalData {
  hrv: number | null;
}

export interface RHRResponse extends IntervalData {
  rhr: number | null;
}

export interface RespiratoryRateResponse {
  respiratory_rate: number | null;
}

export interface EffortResponse {
  effort: number | null;
}

export interface GraphResponse extends IntervalData {
  x: Date[];
  y: number[];
}

export interface GraphData extends IntervalData {
  points: DataPoint[];
}
