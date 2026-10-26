import { useState } from 'react';
import Button from '../ui/Button';

interface ReasonDialogProps {
  title: string;
  confirmLabel: string;
  /** When true the confirm button stays disabled until a reason is typed. */
  required: boolean;
  busy: boolean;
  error: string | null;
  onConfirm: (reason: string) => void;
  onClose: () => void;
}

export default function ReasonDialog({ title, confirmLabel, required, busy, error, onConfirm, onClose }: ReasonDialogProps) {
  const [reason, setReason] = useState('');
  const canConfirm = !busy && (!required || reason.trim() !== '');
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-label={title}>
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <label htmlFor="reason" className="mt-4 block text-sm font-medium text-gray-700">
          Motivo{required ? '' : ' (opcional)'}
        </label>
        <textarea
          id="reason"
          rows={4}
          maxLength={1000}
          autoFocus
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
        {error && (
          <p className="mt-3 text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={busy}>
            Voltar
          </Button>
          <Button variant="danger" onClick={() => onConfirm(reason.trim())} disabled={!canConfirm} isLoading={busy}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
