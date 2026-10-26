import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getSlaBreachRate, getThroughput, getTimeInStage, type AnalyticsParams } from '../api/analytics';

const options = { placeholderData: keepPreviousData, staleTime: 60_000 };

/** `enabled` lets the page hold requests back while the filters are invalid. */
export const useSlaBreachRate = (params: AnalyticsParams, enabled = true) =>
  useQuery({ queryKey: ['analytics', 'sla-breach-rate', params], queryFn: () => getSlaBreachRate(params), enabled, ...options });

export const useTimeInStage = (params: AnalyticsParams, enabled = true) =>
  useQuery({ queryKey: ['analytics', 'time-in-stage', params], queryFn: () => getTimeInStage(params), enabled, ...options });

export const useThroughput = (params: AnalyticsParams, enabled = true) =>
  useQuery({ queryKey: ['analytics', 'throughput', params], queryFn: () => getThroughput(params), enabled, ...options });
