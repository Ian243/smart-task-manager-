import React, { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, CheckSquare, LogOut, CheckCircle, Bot, Repeat } from 'lucide-react';
import AIChat from './AIChat';

const Layout = () => {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Tasks', path: '/tasks', icon: CheckSquare },
    { name: 'Recurring', path: '/recurring', icon: Repeat },
  ];

  return (
    <div className="flex h-screen bg-surface">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col hidden md:flex">
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <CheckCircle className="h-6 w-6 text-primary-500 mr-2" />
          <span className="text-xl font-bold text-gray-900">Smart Tasks</span>
        </div>
        
        <div className="flex-1 overflow-y-auto py-6 px-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                  isActive 
                    ? 'bg-primary-50 text-primary-600' 
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon className={`h-5 w-5 mr-3 ${isActive ? 'text-primary-500' : 'text-gray-400'}`} />
                {item.name}
              </Link>
            );
          })}
        </div>

        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex flex-col">
              <span className="text-sm font-medium text-gray-900 truncate">{user?.name}</span>
              <span className="text-xs text-gray-500">{user?.role}</span>
            </div>
            <button onClick={handleLogout} className="text-gray-400 hover:text-gray-600">
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 md:hidden">
          <div className="flex items-center">
            <CheckCircle className="h-6 w-6 text-primary-500 mr-2" />
            <span className="text-xl font-bold text-gray-900">Smart Tasks</span>
          </div>
          <button onClick={handleLogout} className="text-gray-500">
            <LogOut className="h-6 w-6" />
          </button>
        </header>

        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <Outlet />
        </main>
        
        {/* Floating AI Agent */}
        <AIChat />
      </div>
    </div>
  );
};

export default Layout;
