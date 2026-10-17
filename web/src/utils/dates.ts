export const twoMonthsBack = (date: Date = new Date()) => {
  return new Date(new Date(date).setMonth(new Date().getMonth() - 2));
};
