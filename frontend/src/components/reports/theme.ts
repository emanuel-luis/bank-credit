import type { ThroughputField } from '../../lib/reports';

// Light theme, categorical slots 1 to 8 in fixed order (validated: adjacent CVD and normal-vision gates pass).
// Slots 3 to 5 sit under 3:1 on white, so every chart ships a legend and a table view.
export const SERIES_COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948'];

export const THROUGHPUT_LABELS: Record<ThroughputField, string> = {
  entered: 'Entradas',
  approved: 'Aprovadas',
  returned: 'Devolvidas',
  rejected: 'Rejeitadas',
  cancelled: 'Canceladas',
  expired: 'Expiradas',
};

export const seriesColor = (index: number): string => SERIES_COLORS[index % SERIES_COLORS.length];
