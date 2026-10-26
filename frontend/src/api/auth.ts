import api from './client';
import type { ClientCreate, Me } from './types';
import type { components } from './schema';

export async function login(email: string, password: string): Promise<string> {
  const form = new URLSearchParams({ username: email, password });
  const { data } = await api.post<components['schemas']['Token']>('/auth/token', form);
  return data.access_token;
}

export const fetchMe = async (): Promise<Me> => (await api.get<Me>('/auth/me')).data;

export const registerClient = async (body: ClientCreate): Promise<void> => {
  await api.post('/auth/register/client', body);
};
