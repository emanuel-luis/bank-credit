import api from './client';
import type { components } from './schema';

type S = components['schemas'];

export type SlaBreachRateResponse = S['SlaBreachRateResponse'];
export type SlaBreachRateRow = S['SlaBreachRateRow'];
export type TimeInStageResponse = S['TimeInStageResponse'];
export type TimeInStageRow = S['TimeInStageRow'];
export type ThroughputResponse = S['ThroughputResponse'];
export type ThroughputRow = S['ThroughputRow'];

/** Dates are YYYY-MM-DD; an omitted field uses the API default window. */
export interface AnalyticsParams {
  from?: string;
  to?: string;
  sector?: string;
}

const clean = (p: AnalyticsParams) => ({ from: p.from || undefined, to: p.to || undefined, sector: p.sector || undefined });

export const getSlaBreachRate = async (p: AnalyticsParams): Promise<SlaBreachRateResponse> =>
  (await api.get<SlaBreachRateResponse>('/analytics/sla-breach-rate', { params: clean(p) })).data;

export const getTimeInStage = async (p: AnalyticsParams): Promise<TimeInStageResponse> =>
  (await api.get<TimeInStageResponse>('/analytics/time-in-stage', { params: clean(p) })).data;

export const getThroughput = async (p: AnalyticsParams): Promise<ThroughputResponse> =>
  (await api.get<ThroughputResponse>('/analytics/throughput', { params: clean(p) })).data;
