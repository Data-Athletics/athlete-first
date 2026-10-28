export const twoMonthsBack = (date: Date = new Date()) => {
  const start = new Date(date);
  start.setMonth(start.getMonth() - 2);
  return start;
};
