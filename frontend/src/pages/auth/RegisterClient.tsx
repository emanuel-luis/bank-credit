import { useForm } from 'react-hook-form';
import { useState } from 'react';
import Button from '../../components/ui/Button';

type UserData = {
  email: string;
  full_name: string;
  phone: string;
  password: string;
  is_superuser: boolean;
  groups: string[];
};

type FormData = {
  cnpj: string;
  nome_fantasia: string;
  razao_social: string;
  cnae_principal: string;
  cnae_principal_desc: string;
  cnae_secundario: string;
  cnae_secundario_desc: string;
  natureza_juridica: string;
  natureza_juridica_desc: string;
  logradouro: string;
  numero: string;
  complemento: string;
  cep: string;
  bairro: string;
  municipio: string;
  uf: string;
  user: UserData;
};

export default function RegisterClient() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>();
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    try {
      // Adiciona valores padrão para campos obrigatórios do usuário
      data.user.is_superuser = false;
      data.user.groups = [];
      const res = await fetch('http://127.0.0.1:8000/auth/register/client', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('Erro ao cadastrar cliente');
      setSuccess('Cadastro realizado com sucesso!');
    } catch (err: any) {
      setError(err.message || 'Erro desconhecido');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-2xl w-full bg-white p-8 rounded shadow">
        <h2 className="text-2xl font-bold mb-6">Cadastro de Cliente</h2>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium">CNPJ</label>
              <input {...register('cnpj', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.cnpj && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Nome Fantasia</label>
              <input {...register('nome_fantasia', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.nome_fantasia && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Razão Social</label>
              <input {...register('razao_social', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.razao_social && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">CNAE Principal</label>
              <input {...register('cnae_principal', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.cnae_principal && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Descrição CNAE Principal</label>
              <input {...register('cnae_principal_desc', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.cnae_principal_desc && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">CNAE Secundário</label>
              <input {...register('cnae_secundario', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.cnae_secundario && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Descrição CNAE Secundário</label>
              <input {...register('cnae_secundario_desc', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.cnae_secundario_desc && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Natureza Jurídica</label>
              <input {...register('natureza_juridica', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.natureza_juridica && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Descrição Natureza Jurídica</label>
              <input {...register('natureza_juridica_desc', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.natureza_juridica_desc && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Logradouro</label>
              <input {...register('logradouro', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.logradouro && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Número</label>
              <input {...register('numero', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.numero && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Complemento</label>
              <input {...register('complemento')} className="input w-full border rounded px-2 py-1" />
            </div>
            <div>
              <label className="block text-sm font-medium">CEP</label>
              <input {...register('cep', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.cep && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Bairro</label>
              <input {...register('bairro', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.bairro && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Município</label>
              <input {...register('municipio', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.municipio && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">UF</label>
              <input {...register('uf', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.uf && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
          </div>
          <hr className="my-4" />
          <h3 className="text-lg font-semibold mb-2">Usuário Responsável</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium">Email</label>
              <input {...register('user.email', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.user?.email && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Nome Completo</label>
              <input {...register('user.full_name', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.user?.full_name && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Telefone</label>
              <input {...register('user.phone', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.user?.phone && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
            <div>
              <label className="block text-sm font-medium">Senha</label>
              <input type="password" {...register('user.password', { required: true })} className="input w-full border rounded px-2 py-1" />
              {errors.user?.password && <span className="text-red-500 text-xs">Campo obrigatório</span>}
            </div>
          </div>
          <div className="mt-6">
            <Button type="submit" isLoading={isLoading} className="w-full">
              Cadastrar
            </Button>
          </div>
          {success && <div className="text-green-600 mt-4">{success}</div>}
          {error && <div className="text-red-600 mt-4">{error}</div>}
        </form>
      </div>
    </div>
  );
}