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

export interface GraphResponse extends IntervalData {
  x: Date[];
  y: number[];
}

export interface GraphData extends IntervalData {
  points: DataPoint[];
}
