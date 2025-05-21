import { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Layouts
import DashboardLayout from '../components/layout/DashboardLayout';

// Auth
const Login = lazy(() => import('../pages/auth/Login'));

// Customer
const CustomerDashboard = lazy(() => import('../pages/customer/Dashboard'));
const CustomerApplications = lazy(() => import('../pages/customer/Applications'));
const CustomerNewApplication = lazy(() => import('../pages/customer/NewApplication'));
const CustomerApplicationDetails = lazy(() => import('../pages/customer/ApplicationDetails'));

// Staff
const StaffDashboard = lazy(() => import('../pages/staff/Dashboard'));
const StaffApplications = lazy(() => import('../pages/staff/Applications'));
const StaffApplicationDetails = lazy(() => import('../pages/staff/ApplicationDetails'));

// Manager
const ManagerDashboard = lazy(() => import('../pages/manager/Dashboard'));
const ManagerApplications = lazy(() => import('../pages/manager/Applications'));
const ManagerApplicationDetails = lazy(() => import('../pages/manager/ApplicationDetails'));
const ManagerTeam = lazy(() => import('../pages/manager/Team'));
const ManagerReports = lazy(() => import('../pages/manager/Reports'));

// Admin
const AdminDashboard = lazy(() => import('../pages/admin/Dashboard'));
const AdminApplications = lazy(() => import('../pages/admin/Applications'));
const AdminApplicationDetails = lazy(() => import('../pages/admin/ApplicationDetails'));
const AdminUsers = lazy(() => import('../pages/admin/Users'));
const AdminDepartments = lazy(() => import('../pages/admin/Departments'));
const AdminReports = lazy(() => import('../pages/admin/Reports'));
const AdminSettings = lazy(() => import('../pages/admin/Settings'));

// Loading component
const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
  </div>
);

// Auth guard component
interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: Array<string>;
}

const ProtectedRoute = ({ children, allowedRoles }: ProtectedRouteProps) => {
  const { isAuthenticated, user, isLoading } = useAuth();
  
  if (isLoading) {
    return <LoadingFallback />;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    // Redirect to the appropriate dashboard based on role
    if (user.role === 'customer') return <Navigate to="/customer" replace />;
    if (user.role === 'staff') return <Navigate to="/staff" replace />;
    if (user.role === 'manager') return <Navigate to="/manager" replace />;
    if (user.role === 'admin') return <Navigate to="/admin" replace />;
  }
  
  return <>{children}</>;
};

export default function AppRoutes() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        {/* Auth routes */}
        <Route path="/login" element={<Login />} />
        
        {/* Customer routes */}
        <Route path="/customer" element={
          <ProtectedRoute allowedRoles={['customer']}>
            <DashboardLayout>
              <CustomerDashboard />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/customer/applications" element={
          <ProtectedRoute allowedRoles={['customer']}>
            <DashboardLayout>
              <CustomerApplications />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/customer/applications/new" element={
          <ProtectedRoute allowedRoles={['customer']}>
            <DashboardLayout>
              <CustomerNewApplication />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/customer/applications/:id" element={
          <ProtectedRoute allowedRoles={['customer']}>
            <DashboardLayout>
              <CustomerApplicationDetails />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        
        {/* Staff routes */}
        <Route path="/staff" element={
          <ProtectedRoute allowedRoles={['staff']}>
            <DashboardLayout>
              <StaffDashboard />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/staff/applications" element={
          <ProtectedRoute allowedRoles={['staff']}>
            <DashboardLayout>
              <StaffApplications />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/staff/applications/:id" element={
          <ProtectedRoute allowedRoles={['staff']}>
            <DashboardLayout>
              <StaffApplicationDetails />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        
        {/* Manager routes */}
        <Route path="/manager" element={
          <ProtectedRoute allowedRoles={['manager']}>
            <DashboardLayout>
              <ManagerDashboard />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/manager/applications" element={
          <ProtectedRoute allowedRoles={['manager']}>
            <DashboardLayout>
              <ManagerApplications />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/manager/applications/:id" element={
          <ProtectedRoute allowedRoles={['manager']}>
            <DashboardLayout>
              <ManagerApplicationDetails />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/manager/team" element={
          <ProtectedRoute allowedRoles={['manager']}>
            <DashboardLayout>
              <ManagerTeam />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/manager/reports" element={
          <ProtectedRoute allowedRoles={['manager']}>
            <DashboardLayout>
              <ManagerReports />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        
        {/* Admin routes */}
        <Route path="/admin" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <DashboardLayout>
              <AdminDashboard />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/admin/applications" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <DashboardLayout>
              <AdminApplications />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/admin/applications/:id" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <DashboardLayout>
              <AdminApplicationDetails />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/admin/users" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <DashboardLayout>
              <AdminUsers />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/admin/departments" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <DashboardLayout>
              <AdminDepartments />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/admin/reports" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <DashboardLayout>
              <AdminReports />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/admin/settings" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <DashboardLayout>
              <AdminSettings />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        
        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Suspense>
  );
}