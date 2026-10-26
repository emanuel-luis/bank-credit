import RequestDetailPage from '../../components/loan/RequestDetailPage';
import { useQueueScope } from '../../hooks/useQueueScope';

export default function StaffApplicationDetails() {
  const { basePath } = useQueueScope();
  return <RequestDetailPage listPath={basePath} showClient />;
}
