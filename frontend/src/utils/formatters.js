export const formatNumber = (num) => {
  if (typeof num !== 'number') return num;
  return num.toFixed(2);
};

export const formatPercent = (num) => {
  if (typeof num !== 'number') return num;
  return (num * 100).toFixed(2);
};

export const formatScore = (num) => {
  if (typeof num !== 'number') return num;
  return num.toFixed(2);
};

export const formatCoefficient = (num) => {
  if (typeof num !== 'number' || num === null || num === undefined) return '0.00';
  return num.toFixed(3);
};
