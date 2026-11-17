export const formatMetricValue = (value: number) => {
  if (Math.abs(value) < 1) {
    const formatted = value.toFixed(2);
    return formatted.startsWith("-0")
      ? `-${formatted.slice(2)}`
      : formatted;
  }

  if (Math.abs(value) < 1000) {
    const oneDecimal = value.toFixed(1);
    return oneDecimal.length <= 4 ? oneDecimal : String(Math.round(value));
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 1,
    notation: "compact",
  })
    .format(value)
    .replace("K", "k");
};
