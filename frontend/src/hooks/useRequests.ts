import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createRequest, getHistory, getRequest, listRequests, transitionRequest } from '../api/requests';
import type { CreateRequestBody, ListParams, TransitionBody } from '../api/types';
import { apiErrorCode } from '../lib/errors';

export const useRequests = (params: ListParams) =>
  useQuery({
    queryKey: ['requests', 'list', params],
    queryFn: () => listRequests(params),
    placeholderData: keepPreviousData,
  });

export const useRequest = (id: number) =>
  useQuery({ queryKey: ['requests', 'detail', id], queryFn: () => getRequest(id) });

export const useHistory = (id: number) =>
  useQuery({ queryKey: ['requests', 'history', id], queryFn: () => getHistory(id) });

export function useCreateRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateRequestBody) => createRequest(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['requests'] }),
  });
}

/** On a stale_seq conflict (HTTP 409) the request queries refetch; errorMessage explains it. */
export function useTransition(id: number) {
  const qc = useQueryClient();
  const refresh = () => qc.invalidateQueries({ queryKey: ['requests'] });
  return useMutation({
    mutationFn: (body: TransitionBody) => transitionRequest(id, body),
    onSuccess: refresh,
    onError: (err) => {
      if (apiErrorCode(err) === 'stale_seq') void refresh();
    },
  });
}
