import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import Button from '../../components/ui/Button';
import { registerClient } from '../../api/auth';
import type { ClientCreate } from '../../api/types';
import { errorMessage } from '../../lib/errors';

type FormData = Omit<ClientCreate, 'cnae_secondary' | 'cnae_secondary_desc' | 'complement'> & {
  cnae_secondary: string;
  cnae_secondary_desc: string;
  complement: string;
};

type Field = { name: Exclude<keyof FormData, 'user'>; label: string; required?: boolean; max?: number };

const COMPANY_FIELDS: Field[] = [
  { name: 'cnpj', label: 'CNPJ', required: true },
  { name: 'trade_name', label: 'Nome fantasia', required: true, max: 200 },
  { name: 'legal_name', label: 'Razão social', required: true, max: 200 },
  { name: 'cnae_primary', label: 'CNAE principal', required: true, max: 16 },
  { name: 'cnae_primary_desc', label: 'Descrição do CNAE principal', required: true, max: 255 },
  { name: 'cnae_secondary', label: 'CNAE secundário', max: 16 },
  { name: 'cnae_secondary_desc', label: 'Descrição do CNAE secundário', max: 255 },
  { name: 'legal_nature_code', label: 'Código da natureza jurídica', required: true, max: 8 },
  { name: 'legal_nature_desc', label: 'Natureza jurídica', required: true, max: 255 },
  { name: 'street', label: 'Logradouro', required: true, max: 200 },
  { name: 'number', label: 'Número', required: true, max: 20 },
  { name: 'complement', label: 'Complemento', max: 100 },
  { name: 'postal_code', label: 'CEP', required: true },
  { name: 'district', label: 'Bairro', required: true, max: 100 },
  { name: 'city', label: 'Município', required: true, max: 100 },
  { name: 'state', label: 'UF', required: true },
];

const USER_FIELDS = [
  { name: 'user.full_name', label: 'Nome completo', type: 'text', max: 200 },
  { name: 'user.email', label: 'E-mail', type: 'email', max: 254 },
  { name: 'user.phone', label: 'Telefone', type: 'tel', max: 20 },
  { name: 'user.password', label: 'Senha (mínimo 8 caracteres)', type: 'password', max: 128 },
] as const;

const inputClass = 'w-full border rounded-sm px-2 py-1';
const emptyToNull = (v: string) => (v.trim() === '' ? null : v.trim());

export default function RegisterClient() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>();
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    setError(null);
    setSuccess(false);
    try {
      await registerClient({
        ...data,
        postal_code: data.postal_code.replace(/\D/g, ''),
        state: data.state.trim().toUpperCase(),
        cnae_secondary: emptyToNull(data.cnae_secondary),
        cnae_secondary_desc: emptyToNull(data.cnae_secondary_desc),
        complement: emptyToNull(data.complement),
      });
      setSuccess(true);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-8">
      <div className="max-w-2xl w-full bg-white p-8 rounded-sm shadow-sm">
        <h2 className="text-2xl font-bold mb-6">Cadastro de cliente</h2>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {COMPANY_FIELDS.map((f) => (
              <div key={f.name}>
                <label htmlFor={f.name} className="block text-sm font-medium">
                  {f.label}
                </label>
                <input
                  id={f.name}
                  maxLength={f.max}
                  className={inputClass}
                  {...register(f.name, { required: f.required })}
                />
                {errors[f.name] && <span className="text-red-500 text-xs">Campo obrigatório</span>}
              </div>
            ))}
          </div>
          <hr className="my-4" />
          <h3 className="text-lg font-semibold mb-2">Usuário responsável</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {USER_FIELDS.map((f) => (
              <div key={f.name}>
                <label htmlFor={f.name} className="block text-sm font-medium">
                  {f.label}
                </label>
                <input
                  id={f.name}
                  type={f.type}
                  maxLength={f.max}
                  className={inputClass}
                  {...register(f.name, {
                    required: true,
                    ...(f.type === 'password' && { minLength: 8 }),
                  })}
                />
                {errors.user?.[f.name.slice(5) as keyof FormData['user']] && (
                  <span className="text-red-500 text-xs">
                    {f.type === 'password' ? 'Mínimo de 8 caracteres' : 'Campo obrigatório'}
                  </span>
                )}
              </div>
            ))}
          </div>
          <div className="mt-6">
            <Button type="submit" isLoading={isLoading} className="w-full">
              Cadastrar
            </Button>
          </div>
          {success && (
            <div className="text-green-600 mt-4">
              Cadastro realizado. <Link to="/login" className="underline">Entrar</Link>
            </div>
          )}
          {error && (
            <div className="text-red-600 mt-4" role="alert">
              {error}
            </div>
          )}
          <p className="text-sm text-gray-500">
            Já tem conta? <Link to="/login" className="underline">Entrar</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
