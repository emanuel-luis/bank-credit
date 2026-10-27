import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  type ChartData,
  type ChartOptions,
} from 'chart.js';
import { Bar, Chart, Line } from 'react-chartjs-2';
import { SERIES_COLORS, THROUGHPUT_LABELS } from './theme';
import { dayLabel, THROUGHPUT_EXITS, weekLabel, type BreachSeries, type StageBar, type ThroughputField } from '../../lib/reports';

// Only what the three charts use, to keep the bundle small.
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend);

const SURFACE = '#ffffff';
const INK = '#374151'; // gray-700
const MUTED = '#6b7280'; // gray-500
const GRID = '#e5e7eb'; // gray-200


const legend = { position: 'bottom' as const, labels: { color: INK, usePointStyle: true, boxWidth: 8, boxHeight: 8 } };
const tooltip = { backgroundColor: '#111827', padding: 10, boxPadding: 4 };

const axis = (title?: string) => ({
  grid: { color: GRID },
  border: { display: false },
  ticks: { color: MUTED },
  title: { display: !!title, text: title ?? '', color: MUTED },
});
const xAxis = { grid: { display: false }, ticks: { color: MUTED, maxRotation: 0, autoSkipPadding: 12 } };

export function BreachChart({
  weeks,
  series,
  sectorNames,
  colorOf,
}: {
  weeks: string[];
  series: BreachSeries[];
  sectorNames: Record<string, string>;
  colorOf: (sector: string) => string;
}) {
  const data: ChartData<'line', (number | null)[], string> = {
    labels: weeks.map(weekLabel),
    datasets: series.map((s) => ({
      label: sectorNames[s.sector] ?? s.sector,
      data: s.rate,
      borderColor: colorOf(s.sector),
      backgroundColor: colorOf(s.sector),
      pointBorderColor: SURFACE,
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6,
      borderWidth: 2,
      tension: 0,
      spanGaps: true,
    })),
  };
  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    scales: { x: xAxis, y: { ...axis('Violação do SLA (%)'), min: 0, max: 100, ticks: { color: MUTED, callback: (v) => `${v}%` } } },
    plugins: {
      legend,
      tooltip: {
        ...tooltip,
        callbacks: {
          label: (ctx) => {
            const s = series[ctx.datasetIndex];
            const i = ctx.dataIndex;
            if (s.rate[i] === null) return `${ctx.dataset.label}: sem encerramentos`;
            return `${ctx.dataset.label}: ${(s.rate[i] as number).toFixed(1).replace('.', ',')}% (${s.breached[i]} de ${s.closed[i]} encerradas)`;
          },
        },
      },
    },
  };
  return <Line data={data} options={options} role="img" aria-label="Linha com a taxa semanal de violação do SLA por setor" />;
}

export function StageChart({ bars }: { bars: StageBar[] }) {
  const data: ChartData<'bar', number[], string> = {
    labels: bars.map((b) => b.label),
    datasets: [
      { label: 'Mediana (p50)', data: bars.map((b) => b.p50), backgroundColor: SERIES_COLORS[0], borderColor: SURFACE, borderWidth: 2, borderRadius: 4 },
      { label: 'p90', data: bars.map((b) => b.p90), backgroundColor: SERIES_COLORS[1], borderColor: SURFACE, borderWidth: 2, borderRadius: 4 },
    ],
  };
  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: { x: xAxis, y: { ...axis('Horas'), beginAtZero: true } },
    plugins: {
      legend,
      tooltip: {
        ...tooltip,
        callbacks: {
          label: (ctx) => {
            // chart.js 4.6 types parsed values as number | null (gaps in the data).
            const hours = ctx.parsed.y;
            if (hours === null) return `${ctx.dataset.label}: sem dados`;
            return `${ctx.dataset.label}: ${hours.toFixed(1).replace('.', ',')} h`;
          },
          afterBody: (items) => `${bars[items[0].dataIndex].n} etapas concluídas`,
        },
      },
    },
  };
  return <Bar data={data} options={options} role="img" aria-label="Barras agrupadas com mediana e percentil 90 de horas por etapa" />;
}


export function ThroughputChart({ days, totals }: { days: string[]; totals: Record<ThroughputField, number[]> }) {
  const data: ChartData<'bar' | 'line', number[], string> = {
    labels: days.map(dayLabel),
    datasets: [
      ...THROUGHPUT_EXITS.map((f, i) => ({
        type: 'bar' as const,
        label: THROUGHPUT_LABELS[f],
        data: totals[f],
        backgroundColor: SERIES_COLORS[i],
        borderColor: SURFACE,
        borderWidth: 1,
        stack: 'exits',
        order: 2,
      })),
      {
        type: 'line' as const,
        label: THROUGHPUT_LABELS.entered,
        data: totals.entered,
        borderColor: INK,
        backgroundColor: INK,
        borderWidth: 2,
        pointRadius: 2,
        pointHoverRadius: 5,
        tension: 0,
        order: 1,
      },
    ],
  };
  const options: ChartOptions<'bar' | 'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    scales: { x: { ...xAxis, stacked: true }, y: { ...axis('Solicitações'), stacked: true, beginAtZero: true, ticks: { color: MUTED, precision: 0 } } },
    plugins: { legend, tooltip },
  };
  return <Chart<'bar' | 'line', number[], string> type="bar" data={data} options={options} role="img" aria-label="Barras empilhadas com as saídas diárias e linha com as entradas" />;
}
