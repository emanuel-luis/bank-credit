import api from './client';
import type {
  CreateRequestBody,
  HistoryItem,
  ListParams,
  RequestDetail,
  RequestPage,
  TransitionBody,
} from './types';

export const listRequests = async (params: ListParams): Promise<RequestPage> =>
  (await api.get<RequestPage>('/requests', { params })).data;

export const getRequest = async (id: number): Promise<RequestDetail> =>
  (await api.get<RequestDetail>(`/requests/${id}`)).data;

export const getHistory = async (id: number): Promise<HistoryItem[]> =>
  (await api.get<HistoryItem[]>(`/requests/${id}/history`)).data;

export const createRequest = async (body: CreateRequestBody): Promise<RequestDetail> =>
  (await api.post<RequestDetail>('/requests', body)).data;

export const transitionRequest = async (id: number, body: TransitionBody): Promise<RequestDetail> =>
  (await api.post<RequestDetail>(`/requests/${id}/transitions`, body)).data;
