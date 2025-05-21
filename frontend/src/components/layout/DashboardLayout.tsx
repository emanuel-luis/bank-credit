import { ReactNode, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  FileText, 
  Home, 
  Users, 
  Settings, 
  Bell, 
  LogOut, 
  Menu, 
  X, 
  ChevronDown, 
  Building2
} from 'lucide-react';
import { useAuth, UserRole } from '../../contexts/AuthContext';
import Button from '../ui/Button';

// Define navigation based on user roles
const navigationByRole: Record<UserRole, Array<{ name: string; href: string; icon: typeof Home }>> = {
  customer: [
    { name: 'Dashboard', href: '/customer', icon: Home },
    { name: 'Applications', href: '/customer/applications', icon: FileText },
  ],
  staff: [
    { name: 'Dashboard', href: '/staff', icon: Home },
    { name: 'Applications', href: '/staff/applications', icon: FileText },
  ],
  manager: [
    { name: 'Dashboard', href: '/manager', icon: Home },
    { name: 'Applications', href: '/manager/applications', icon: FileText },
    { name: 'Team', href: '/manager/team', icon: Users },
    { name: 'Reports', href: '/manager/reports', icon: BarChart3 },
  ],
  admin: [
    { name: 'Dashboard', href: '/admin', icon: Home },
    { name: 'Applications', href: '/admin/applications', icon: FileText },
    { name: 'Users', href: '/admin/users', icon: Users },
    { name: 'Departments', href: '/admin/departments', icon: Building2 },
    { name: 'Reports', href: '/admin/reports', icon: BarChart3 },
    { name: 'Settings', href: '/admin/settings', icon: Settings },
  ],
};

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // If no user or role is not defined, don't render the layout
  if (!user || !navigationByRole[user.role]) {
    return null;
  }

  const navigation = navigationByRole[user.role];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-gray-600 bg-opacity-75"
            onClick={() => setSidebarOpen(false)}
          />
          
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ ease: 'easeOut', duration: 0.3 }}
            className="relative flex flex-col flex-1 w-full max-w-xs bg-white"
          >
            <div className="absolute top-0 right-0 -mr-12 pt-2">
              <button
                className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                onClick={() => setSidebarOpen(false)}
              >
                <span className="sr-only">Close sidebar</span>
                <X className="h-6 w-6 text-white" aria-hidden="true" />
              </button>
            </div>
            
            <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
              <div className="flex-shrink-0 flex items-center px-4">
                <Building2 className="h-8 w-8 text-primary-600" />
                <span className="ml-2 text-xl font-bold text-primary-600">
                  Banco do Nordeste
                </span>
              </div>
              <nav className="mt-5 px-2 space-y-1">
                {navigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`${
                      location.pathname === item.href
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    } group flex items-center px-2 py-2 text-base font-medium rounded-md`}
                  >
                    <item.icon
                      className={`${
                        location.pathname === item.href
                          ? 'text-primary-600'
                          : 'text-gray-400 group-hover:text-gray-500'
                      } mr-4 h-6 w-6`}
                      aria-hidden="true"
                    />
                    {item.name}
                  </Link>
                ))}
              </nav>
            </div>
            
            <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
              <div className="flex-shrink-0 group block">
                <div className="flex items-center">
                  <div className="bg-gray-200 rounded-full h-10 w-10 flex items-center justify-center">
                    <span className="text-gray-600 font-medium">
                      {user.name.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <div className="ml-3">
                    <p className="text-base font-medium text-gray-700 group-hover:text-gray-900">
                      {user.name}
                    </p>
                    <p className="text-sm font-medium text-gray-500 group-hover:text-gray-700">
                      {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                      {user.department && ` - ${user.department}`}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Static sidebar for desktop */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
        <div className="flex-1 flex flex-col min-h-0 bg-white border-r border-gray-200">
          <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
            <div className="flex items-center flex-shrink-0 px-4">
              <Building2 className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-bold text-primary-600">
                Banco do Nordeste
              </span>
            </div>
            <nav className="mt-5 flex-1 px-2 space-y-1">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`${
                    location.pathname === item.href
                      ? 'bg-primary-50 text-primary-600'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  } group flex items-center px-2 py-2 text-sm font-medium rounded-md`}
                >
                  <item.icon
                    className={`${
                      location.pathname === item.href
                        ? 'text-primary-600'
                        : 'text-gray-400 group-hover:text-gray-500'
                    } mr-3 h-5 w-5`}
                    aria-hidden="true"
                  />
                  {item.name}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
            <div className="flex-shrink-0 w-full group block">
              <div className="flex items-center">
                <div className="bg-gray-200 rounded-full h-9 w-9 flex items-center justify-center">
                  <span className="text-gray-600 font-medium">
                    {user.name.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
                <div className="ml-3 flex flex-col flex-grow min-w-0">
                  <p className="text-sm font-medium text-gray-700 group-hover:text-gray-900 truncate">
                    {user.name}
                  </p>
                  <p className="text-xs font-medium text-gray-500 group-hover:text-gray-700">
                    {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                    {user.department && ` - ${user.department}`}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="ml-2"
                  onClick={handleLogout}
                  aria-label="Logout"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="md:pl-64 flex flex-col flex-1">
        <div className="sticky top-0 z-10 bg-white pl-1 pt-1 sm:pl-3 sm:pt-3 md:hidden">
          <button
            type="button"
            className="-ml-0.5 -mt-0.5 h-12 w-12 inline-flex items-center justify-center rounded-md text-gray-500 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
            onClick={() => setSidebarOpen(true)}
          >
            <span className="sr-only">Open sidebar</span>
            <Menu className="h-6 w-6" aria-hidden="true" />
          </button>
        </div>

        <main className="flex-1">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              <header className="bg-white shadow-sm mb-6 rounded-lg">
                <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
                  <div className="flex items-center justify-between">
                    <h1 className="text-lg font-semibold text-gray-900">
                      {navigation.find(item => item.href === location.pathname)?.name || 'Dashboard'}
                    </h1>
                    <div className="flex items-center space-x-4">
                      <button className="relative p-1 rounded-full text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                        <span className="sr-only">View notifications</span>
                        <Bell className="h-6 w-6" aria-hidden="true" />
                        <span className="absolute top-0 right-0 block h-2 w-2 rounded-full bg-error-500 ring-2 ring-white"></span>
                      </button>
                      <div className="md:hidden">
                        <Button variant="outline" size="sm" onClick={handleLogout}>
                          <LogOut className="h-4 w-4 mr-2" />
                          Logout
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </header>
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}