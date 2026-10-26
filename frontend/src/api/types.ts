import type { components } from './schema';

type S = components['schemas'];

export type Status = S['RequestStatus'];
export type EventType = S['EventType'];
export type DocumentType = S['DocumentType'];
export type Action = S['Action'];
export type Role = S['UserRole'];
export type RequestSummary = S['RequestSummary'];
export type RequestDetail = S['RequestDetail'];
export type RequestPage = S['RequestPage'];
export type HistoryItem = S['HistoryItem'];
export type CreateRequestBody = S['CreditRequestCreate'];
export type TransitionBody = S['TransitionIn'];
export type Me = S['Me'];
export type ClientCreate = S['ClientCreate'];
export type Workflow = S['WorkflowRead'];
export type Scope = S['Scope'];

export interface ListParams {
  scope?: Scope;
  status?: Status;
  stage?: string;
  overdue?: boolean;
  limit?: number;
  offset?: number;
}
