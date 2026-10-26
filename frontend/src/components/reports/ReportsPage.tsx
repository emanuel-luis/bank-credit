import { useMemo, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useSlaBreachRate, useThroughput, useTimeInStage } from '../../hooks/useAnalytics';
import { useWorkflow } from '../../hooks/useRequests';
import {
  pivotBreachRate,
  sectorOrder,
  stageBars,
  throughputByDay,
  THROUGHPUT_EXITS,
  weekLabel,
  weeksOf,
  defaultWeek,
} from '../../lib/reports';
import { BreachChart, StageChart, ThroughputChart } from './Charts';
import { seriesColor, THROUGHPUT_LABELS } from './theme';
import Panel from './Panel';

const field = 'rounded-md border border-gray-300 bg-white px-2 py-1 text-sm text-gray-900';

/** Shared by the manager and admin routes; the API pins a manager to their own sector. */
export default function ReportsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const ownSector = user?.employee?.sector ?? null;

  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [adminSector, setAdminSector] = useState('');
  const [pickedWeek, setPickedWeek] = useState('');

  const invalidRange = !!from && !!to && from > to;
  const params = { from, to, sector: isAdmin ? adminSector : (ownSector?.code ?? '') };
  const enabled = !invalidRange;

  const breach = useSlaBreachRate(params, enabled);
  const stages = useTimeInStage(params, enabled);
  const flow = useThroughput(params, enabled);
  const workflow = useWorkflow();

  const { sectorNames, stageNames, stageCodes, knownSectors } = useMemo(() => {
    const sectorNames: Record<string, string> = {};
    const stageNames: Record<string, string> = {};
    const list = workflow.data?.stages ?? [];
    for (const st of list) {
      stageNames[st.code] = st.name;
      for (const r of st.routes) sectorNames[r.sector.code] = r.sector.name;
    }
    return {
      sectorNames,
      stageNames,
      stageCodes: [...list].sort((a, b) => a.position - b.position).map((s) => s.code),
      knownSectors: Object.keys(sectorNames),
    };
  }, [workflow.data]);

  const breachData = useMemo(() => pivotBreachRate(breach.data?.data ?? []), [breach.data]);
  const order = sectorOrder(knownSectors, breachData.series.map((s) => s.sector));
  const colorOf = (sector: string) => seriesColor(order.indexOf(sector));

  const stageRows = useMemo(() => stages.data?.data ?? [], [stages.data]);
  const weeks = useMemo(() => weeksOf(stageRows), [stageRows]);
  const week = weeks.includes(pickedWeek)
    ? pickedWeek
    : defaultWeek(weeks, new Date().toISOString().slice(0, 10));
  const bars = useMemo(
    () => stageBars(stageRows, week, stageNames, sectorNames, stageCodes),
    [stageRows, week, stageNames, sectorNames, stageCodes],
  );

  const flowData = useMemo(() => throughputByDay(flow.data?.data ?? []), [flow.data]);

  const sectorOptions = [...knownSectors].sort();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end gap-4 rounded-lg bg-white p-4 shadow-card">
        <label className="text-sm text-gray-700">
          <span className="mb-1 block">De</span>
          <input type="date" className={field} value={from} max={to || undefined} onChange={(e) => setFrom(e.target.value)} />
        </label>
        <label className="text-sm text-gray-700">
          <span className="mb-1 block">Até</span>
          <input type="date" className={field} value={to} min={from || undefined} onChange={(e) => setTo(e.target.value)} />
        </label>
        {isAdmin ? (
          <label className="text-sm text-gray-700">
            <span className="mb-1 block">Setor</span>
            <select className={field} value={adminSector} onChange={(e) => setAdminSector(e.target.value)}>
              <option value="">Todos os setores</option>
              {sectorOptions.map((code) => (
                <option key={code} value={code}>
                  {sectorNames[code] ?? code}
                </option>
              ))}
            </select>
          </label>
        ) : (
          <p className="text-sm text-gray-700">
            <span className="mb-1 block">Setor</span>
            <span className="inline-block py-1 font-medium">{ownSector?.name ?? '-'}</span>
          </p>
        )}
        {(from || to) && (
          <button type="button" className="text-sm text-primary-600 hover:underline" onClick={() => { setFrom(''); setTo(''); }}>
            Limpar datas
          </button>
        )}
        <p className="text-xs text-gray-500">Sem datas: últimas 12 semanas (SLA e tempo por etapa) e 90 dias (fluxo).</p>
        {invalidRange && (
          <p role="alert" className="w-full text-sm text-error-600">A data inicial é posterior à data final.</p>
        )}
      </div>

      <Panel
        title="Violação do SLA por semana"
        note="Parcela das etapas concluídas na semana que passaram do prazo, por setor; a semana é a da saída da etapa."
        isLoading={breach.isLoading}
        error={breach.error}
        isEmpty={breachData.weeks.length === 0}
        sourceView={breach.data?.source_view}
        generatedAt={breach.data?.generated_at}
        table={{
          head: ['Semana', 'Setor', 'Encerradas', 'Violadas', 'Taxa'],
          rows: (breach.data?.data ?? []).map((r) => [
            weekLabel(r.week_start),
            sectorNames[r.sector_code] ?? r.sector_code,
            r.closed,
            r.breached,
            `${(Number(r.breach_rate) * 100).toFixed(1).replace('.', ',')}%`,
          ]),
        }}
      >
        <BreachChart weeks={breachData.weeks} series={breachData.series} sectorNames={sectorNames} colorOf={colorOf} />
      </Panel>

      <Panel
        title="Tempo em cada etapa"
        note="Mediana e p90 em horas da semana escolhida (por padrão, a última semana completa). Percentis não se somam nem se tiram a média entre semanas, por isso mostramos uma semana por vez."
        isLoading={stages.isLoading}
        error={stages.error}
        isEmpty={weeks.length === 0}
        sourceView={stages.data?.source_view}
        generatedAt={stages.data?.generated_at}
        actions={
          weeks.length > 0 && (
            <label className="text-sm text-gray-700">
              <span className="mr-2">Semana</span>
              <select className={field} value={week} onChange={(e) => setPickedWeek(e.target.value)}>
                {weeks.map((w) => (
                  <option key={w} value={w}>
                    {weekLabel(w)}
                  </option>
                ))}
              </select>
            </label>
          )
        }
        table={{
          head: ['Etapa', 'Mediana (h)', 'p90 (h)', 'Etapas concluídas'],
          rows: bars.map((b) => [b.label, b.p50.toFixed(1).replace('.', ','), b.p90.toFixed(1).replace('.', ','), b.n]),
        }}
      >
        <StageChart bars={bars} />
      </Panel>

      <Panel
        title="Entradas e saídas por dia"
        note="Barras: saídas do dia por resultado (empilhadas). Linha: solicitações que entraram, reenvios incluídos. Setores somados."
        isLoading={flow.isLoading}
        error={flow.error}
        isEmpty={flowData.days.length === 0}
        sourceView={flow.data?.source_view}
        generatedAt={flow.data?.generated_at}
        table={{
          head: ['Dia', 'Entradas', ...THROUGHPUT_EXITS.map((f) => THROUGHPUT_LABELS[f])],
          rows: flowData.days.map((d, i) => [
            d,
            flowData.totals.entered[i],
            ...THROUGHPUT_EXITS.map((f) => flowData.totals[f][i]),
          ]),
        }}
      >
        <ThroughputChart days={flowData.days} totals={flowData.totals} />
      </Panel>
    </div>
  );
}
