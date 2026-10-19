import type React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";
import type { GraphData } from "../types/Biometrics";
import "./MetricSquare.css";

interface BaseMetricSquareProps {
  type: "text" | "graph";
  title: string;
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
        <h5 className="metric-title">{props.title}</h5>
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

                      <YAxis width={30} domain={[0, "auto"]} />

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

export default MetricSquare;
