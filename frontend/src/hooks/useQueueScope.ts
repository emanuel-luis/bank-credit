import { useAuth } from '../contexts/AuthContext';
import type { Scope } from '../api/types';

/** Staff and manager see their sector's queue, admin sees everything; the API enforces the same rule. */
export function useQueueScope(): { scope: Scope; basePath: string } {
  const { user } = useAuth();
  const role = user?.role ?? 'staff';
  return { scope: role === 'admin' ? 'all' : 'queue', basePath: `/${role}/applications` };
}
