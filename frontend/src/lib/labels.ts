import type { DocumentType, EventType, Role, Status } from '../api/types';

export const STATUS_LABELS: Record<Status, string> = {
  IN_REVIEW: 'Em análise',
  RETURNED: 'Devolvida',
  APPROVED: 'Aprovada',
  REJECTED: 'Rejeitada',
  CANCELLED: 'Cancelada',
  EXPIRED: 'Expirada',
};

export const EVENT_LABELS: Record<EventType, string> = {
  SUBMITTED: 'Solicitação enviada',
  STAGE_APPROVED: 'Etapa aprovada',
  RETURNED: 'Devolvida ao cliente',
  RESUBMITTED: 'Reenviada',
  REJECTED: 'Rejeitada',
  CANCELLED: 'Cancelada',
  EXPIRED: 'Expirada',
  SLA_BREACHED: 'Prazo (SLA) estourado',
};

export const DOCUMENT_LABELS: Record<DocumentType, string> = {
  company_registration: 'Contrato social ou registro da empresa',
  financial_statements: 'Demonstrações financeiras',
  business_plan: 'Plano de negócios',
  tax_clearance: 'Certidão negativa de débitos',
  collateral: 'Garantia (opcional)',
};

export const REQUIRED_DOCUMENTS: DocumentType[] = [
  'company_registration',
  'financial_statements',
  'business_plan',
  'tax_clearance',
];

export const ALL_DOCUMENTS: DocumentType[] = [...REQUIRED_DOCUMENTS, 'collateral'];

export const ROLE_LABELS: Record<Role, string> = {
  customer: 'Cliente',
  staff: 'Analista',
  manager: 'Gerente',
  admin: 'Administrador',
};

export const STATUSES = Object.keys(STATUS_LABELS) as Status[];
