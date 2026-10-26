import { AxiosError } from 'axios';
import { describe, expect, it } from 'vitest';
import { apiErrorCode, errorMessage } from './errors';

function apiError(data: unknown, status = 400) {
  const err = new AxiosError('failed');
  err.response = { data, status, statusText: '', headers: {}, config: {} as never };
  return err;
}

describe('errorMessage', () => {
  it('maps a known code to pt-BR', () => {
    expect(errorMessage(apiError({ detail: 'x', code: 'cnpj_taken' }))).toBe('Já existe um cadastro com este CNPJ.');
    expect(apiErrorCode(apiError({ detail: 'x', code: 'stale_seq' }, 409))).toBe('stale_seq');
  });

  it('falls back to the detail for an unknown code', () => {
    expect(errorMessage(apiError({ detail: 'Algo novo', code: 'http_418' }))).toBe('Algo novo');
  });

  it('joins validation errors as field: message', () => {
    const detail = [{ loc: ['body', 'user', 'email'], msg: 'value is not a valid email address' }];
    expect(errorMessage(apiError({ detail, code: 'validation_error' }, 422))).toBe(
      'user.email: value is not a valid email address',
    );
  });

  it('handles a network error and non-API values', () => {
    expect(errorMessage(new AxiosError('Network Error'))).toBe('Não foi possível conectar ao servidor.');
    expect(errorMessage(new Error('boom'))).toBe('Ocorreu um erro inesperado.');
  });
});
