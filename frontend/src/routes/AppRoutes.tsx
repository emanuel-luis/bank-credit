import { Suspense, lazy, type ReactNode } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth, type UserRole } from '../contexts/AuthContext';

import DashboardLayout from '../components/layout/DashboardLayout';
import RegisterClient from '../pages/auth/RegisterClient';

const Login = lazy(() => import('../pages/auth/Login'));

const CustomerDashboard = lazy(() => import('../pages/customer/Dashboard'));
const CustomerApplications = lazy(() => import('../pages/customer/Applications'));
const CustomerNewApplication = lazy(() => import('../pages/customer/NewApplication'));
const CustomerApplicationDetails = lazy(() => import('../pages/customer/ApplicationDetails'));

// Staff, manager and admin share the queue pages; the scope follows the role.
const StaffDashboard = lazy(() => import('../pages/staff/Dashboard'));
const StaffApplications = lazy(() => import('../pages/staff/Applications'));
const StaffApplicationDetails = lazy(() => import('../pages/staff/ApplicationDetails'));

const ManagerReports = lazy(() => import('../pages/manager/Reports'));
const AdminReports = lazy(() => import('../pages/admin/Reports'));
const AdminSettings = lazy(() => import('../pages/admin/Settings'));

const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
  </div>
);

const ProtectedRoute = ({ children, role }: { children: ReactNode; role: UserRole }) => {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) return <LoadingFallback />;
  if (!isAuthenticated || !user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={`/${user.role}`} replace />;

  return <DashboardLayout>{children}</DashboardLayout>;
};

const page = (role: UserRole, path: string, element: ReactNode) => (
  <Route key={`${role}${path}`} path={`/${role}${path}`} element={<ProtectedRoute role={role}>{element}</ProtectedRoute>} />
);

const queuePages = (role: 'staff' | 'manager' | 'admin') => [
  page(role, '', <StaffDashboard />),
  page(role, '/applications', <StaffApplications />),
  page(role, '/applications/:id', <StaffApplicationDetails />),
];

export default function AppRoutes() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register-client" element={<RegisterClient />} />

        {page('customer', '', <CustomerDashboard />)}
        {page('customer', '/applications', <CustomerApplications />)}
        {page('customer', '/applications/new', <CustomerNewApplication />)}
        {page('customer', '/applications/:id', <CustomerApplicationDetails />)}

        {queuePages('staff')}
        {queuePages('manager')}
        {page('manager', '/reports', <ManagerReports />)}
        {queuePages('admin')}
        {page('admin', '/reports', <AdminReports />)}
        {page('admin', '/settings', <AdminSettings />)}

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Suspense>
  );
}
