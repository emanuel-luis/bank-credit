import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { FileClock, Calendar, DollarSign, Building, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardFooter } from '../ui/Card';
import ApplicationStatusBadge, { ApplicationStatus } from './ApplicationStatusBadge';
import Button from '../ui/Button';

export interface ApplicationCardProps {
  id: string | number;
  title?: string;
  status: ApplicationStatus | string;
  amount: number;
  department?: string;
  companyName?: string;
  submittedAt?: Date | string;
  deadline?: Date | string;
  hasSlaWarning?: boolean;
  onViewDetails: (id: string | number) => void;
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
};

const formatDate = (date?: Date | string | number) => {
  if (!date) return '-';
  try {
    const dateObj = date instanceof Date ? date : new Date(date);
    if (isNaN(dateObj.getTime())) {
      return '-';
    }
    // Exibe a data formatada: 21/05/2025
    return format(dateObj, 'P', { locale: ptBR });
  } catch {
    return '-';
  }
};

export default function ApplicationCard({
  id,
  title,
  status,
  companyName,
  amount,
  department,
  central, // Adicione se quiser receber central como prop
  submittedAt,
  deadline,
  hasSlaWarning = false,
  onViewDetails,
}: ApplicationCardProps & { central?: string }) {
  return (
    <Card className="h-full transition-shadow hover:shadow-md">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between mb-4">
          <h3 className="font-medium text-gray-900 line-clamp-1">
            {companyName || title || '-'}
          </h3>
          <ApplicationStatusBadge status={status} />
        </div>
        
        <div className="space-y-3">
          <div className="flex items-center text-gray-500">
            <DollarSign className="h-4 w-4 mr-2 flex-shrink-0" />
            <span className="font-medium text-gray-700">{formatCurrency(amount)}</span>
          </div>
          
          {department && (
            <div className="flex items-center text-gray-500">
              <Building className="h-4 w-4 mr-2 flex-shrink-0" />
              <span>Departamento: {department}</span>
            </div>
          )}

          {central && (
            <div className="flex items-center text-gray-500">
              <Building className="h-4 w-4 mr-2 flex-shrink-0" />
              <span>Central: {central}</span>
            </div>
          )}
          
          <div className="flex items-center text-gray-500">
            <Calendar className="h-4 w-4 mr-2 flex-shrink-0" />
            <span>Enviado em {formatDate(submittedAt)}</span>
          </div>
          
          {deadline && (
            <div className="flex items-center text-gray-500">
              <FileClock className="h-4 w-4 mr-2 flex-shrink-0" />
              <span className={hasSlaWarning ? 'text-error-600 font-medium' : ''}>
                Prazo {formatDate(deadline)}
              </span>
            </div>
          )}
          
          {hasSlaWarning && (
            <div className="flex items-center text-error-600">
              <AlertCircle className="h-4 w-4 mr-2 flex-shrink-0" />
              <span className="text-sm font-medium">Aviso de estouro de SLA</span>
            </div>
          )}
        </div>
      </CardContent>
      
      <CardFooter>
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={() => onViewDetails(id)}
        >
          Ver detalhes
        </Button>
      </CardFooter>
    </Card>
  );
}

export { ApplicationCard };