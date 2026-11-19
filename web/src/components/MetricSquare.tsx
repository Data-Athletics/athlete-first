import type React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { GraphData } from "../types/Biometrics";
import { formatMetricValue } from "../utils/metric";
import "./MetricSquare.css";

interface BaseMetricSquareProps {
  type: "text" | "graph";
  title: string;
  unit?: string;
  description: string;
  playerName?: string;
  compactHeader?: boolean;
}

interface MetricSquareValueProps extends BaseMetricSquareProps {
  type: "text";
  value: string;
}

interface MetricSquareGraphProps extends BaseMetricSquareProps {
  type: "graph";
  data: GraphData;
}

type MetricSquareProps = MetricSquareValueProps | MetricSquareGraphProps;

const MetricSquare: React.FC<MetricSquareProps> = (props) => {
  return (
    <>
      <div className="metric-container">
        <div
          className={`metric-heading${
            props.compactHeader ? " is-compact" : ""
          }`}
        >
          <span className="metric-title-row">
            {props.playerName ? (
              <span className="metric-player">{props.playerName}</span>
            ) : (
                <h5 className="metric-title">{props.title}</h5>
            )}
            <MetricInfo title={props.title} description={props.description} />
          </span>
          {!props.compactHeader && props.unit && (
            <span className="metric-details">({props.unit})</span>
          )}
        </div>
        <div className="value-container">
          {(() => {
            switch (props.type) {
              case "text":
                return <h1 className="metric-value">{props.value}</h1>;
              case "graph":
                return (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={props.data.points}
                      margin={{ top: 10, right: 10, left: 10, bottom: 5 }}
                      barCategoryGap="25%"
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        vertical={false}
                        stroke="#374151"
                      />

                      <XAxis
                        dataKey="time"
                        tick={{ fontSize: 11, fill: "#9ca3af" }}
                        tickLine={false}
                        axisLine={false}
                        interval={Math.max(
                          0,
                          Math.ceil(props.data.points.length / 5) - 1,
                        )}
                        angle={-45} // Rotates labels 45 degrees counter-clockwise
                        textAnchor="end" // Anchors the end of the text string to the tick mark
                        dx={8}
                        dy={-8}
                      />

                      <YAxis
                        width={30}
                        tick={{ fontSize: 15, fill: "#9ca3af" }}
                        domain={[0, "auto"]}
                        tickFormatter={formatMetricValue}
                      />

                      <Tooltip
                        formatter={(value) => formatMetricValue(Number(value))}
                      />

                      <Bar
                        dataKey="value"
                        fill="#3b82f6"
                        radius={[5, 5, 0, 0]}
                        maxBarSize={20}
                        isAnimationActive={false}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                );
            }
          })()}
        </div>
      </div>
    </>
  );
};

const MetricInfo: React.FC<{ title: string; description: string }> = ({
  title,
  description,
}) => (
  <span className="metric-info-wrapper">
    <button
      className="metric-info"
      type="button"
      aria-label={`About ${title}`}
    >
      i
    </button>
    <span className="metric-info-tooltip" role="tooltip">
      {description}
    </span>
  </span>
);

export default MetricSquare;
