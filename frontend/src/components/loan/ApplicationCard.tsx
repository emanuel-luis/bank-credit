import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { FileClock, Calendar, DollarSign, Building, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardFooter } from '../ui/Card';
import ApplicationStatusBadge, { ApplicationStatus } from './ApplicationStatusBadge';
import Button from '../ui/Button';

export interface ApplicationCardProps {
  id: string;
  title: string;
  status: ApplicationStatus;
  amount: number;
  department: string;
  submittedAt: Date;
  deadline?: Date;
  hasSlaWarning?: boolean;
  onViewDetails: (id: string) => void;
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
};

const formatDate = (date: Date | string | number) => {
  try {
    const dateObj = date instanceof Date ? date : new Date(date);
    if (isNaN(dateObj.getTime())) {
      return 'Invalid date';
    }
    return formatDistanceToNow(dateObj, { addSuffix: true, locale: ptBR });
  } catch {
    return 'Invalid date';
  }
};

export default function ApplicationCard({
  id,
  title,
  status,
  amount,
  department,
  submittedAt,
  deadline,
  hasSlaWarning = false,
  onViewDetails,
}: ApplicationCardProps) {
  return (
    <Card className="h-full transition-shadow hover:shadow-md">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between mb-4">
          <h3 className="font-medium text-gray-900 line-clamp-1">{title}</h3>
          <ApplicationStatusBadge status={status} />
        </div>
        
        <div className="space-y-3">
          <div className="flex items-center text-gray-500">
            <DollarSign className="h-4 w-4 mr-2 flex-shrink-0" />
            <span className="font-medium text-gray-700">{formatCurrency(amount)}</span>
          </div>
          
          <div className="flex items-center text-gray-500">
            <Building className="h-4 w-4 mr-2 flex-shrink-0" />
            <span>{department}</span>
          </div>
          
          <div className="flex items-center text-gray-500">
            <Calendar className="h-4 w-4 mr-2 flex-shrink-0" />
            <span>Submitted {formatDate(submittedAt)}</span>
          </div>
          
          {deadline && (
            <div className="flex items-center text-gray-500">
              <FileClock className="h-4 w-4 mr-2 flex-shrink-0" />
              <span className={hasSlaWarning ? 'text-error-600 font-medium' : ''}>
                Due {formatDate(deadline)}
              </span>
            </div>
          )}
          
          {hasSlaWarning && (
            <div className="flex items-center text-error-600">
              <AlertCircle className="h-4 w-4 mr-2 flex-shrink-0" />
              <span className="text-sm font-medium">SLA breach warning</span>
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
          View Details
        </Button>
      </CardFooter>
    </Card>
  );
}

export { ApplicationCard }