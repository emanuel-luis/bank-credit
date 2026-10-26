import axios from 'axios';

export const ERROR_MESSAGES: Record<string, string> = {
  forbidden: 'Você não tem permissão para esta ação.',
  invalid_transition: 'Esta ação não é permitida no estado atual da solicitação.',
  stale_seq: 'A solicitação foi alterada por outra pessoa. Os dados foram recarregados; confira e tente de novo.',
  request_expired: 'O prazo da solicitação expirou.',
  clock_went_backwards: 'O relógio do servidor está inconsistente. Tente novamente.',
  reason_required: 'Informe o motivo.',
  invalid_amount: 'Valor inválido.',
  invalid_deliver_date: 'Data de entrega inválida.',
  missing_documents: 'Marque todos os documentos obrigatórios.',
  workflow_error: 'Não foi possível aplicar o fluxo de aprovação.',
  customers_only: 'Apenas clientes podem criar solicitações.',
  scope_not_allowed: 'Você não pode listar estas solicitações.',
  request_not_found: 'Solicitação não encontrada.',
  notification_not_found: 'Notificação não encontrada.',
  invalid_credentials: 'E-mail ou senha inválidos.',
  invalid_login: 'E-mail ou senha inválidos.',
  inactive_user: 'Usuário inativo.',
  cnpj_taken: 'Já existe um cadastro com este CNPJ.',
  email_taken: 'Já existe um cadastro com este e-mail.',
};

interface ApiErrorBody {
  detail?: unknown;
  code?: string;
}

function errorBody(err: unknown): ApiErrorBody | undefined {
  return axios.isAxiosError(err) ? (err.response?.data as ApiErrorBody | undefined) : undefined;
}

export function apiErrorCode(err: unknown): string | undefined {
  return errorBody(err)?.code;
}

/** Validation errors arrive as a list of {loc, msg}; show each as "field: message". */
function validationText(detail: unknown): string | undefined {
  if (!Array.isArray(detail)) return undefined;
  const parts = detail.map((d: { loc?: unknown[]; msg?: string }) => {
    const field = (d.loc ?? []).filter((p) => p !== 'body').join('.');
    return field ? `${field}: ${d.msg ?? ''}` : (d.msg ?? '');
  });
  return parts.join('; ') || undefined;
}

/** pt-BR message for any thrown value: known code first, then the API detail, then a generic text. */
export function errorMessage(err: unknown): string {
  const body = errorBody(err);
  if (body?.code && ERROR_MESSAGES[body.code]) return ERROR_MESSAGES[body.code];
  if (body?.code === 'validation_error') {
    return validationText(body.detail) ?? 'Dados inválidos.';
  }
  if (typeof body?.detail === 'string') return body.detail;
  if (axios.isAxiosError(err) && !err.response) return 'Não foi possível conectar ao servidor.';
  return 'Ocorreu um erro inesperado.';
}
