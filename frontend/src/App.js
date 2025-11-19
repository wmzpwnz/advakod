import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { AdminProvider } from './contexts/AdminContext';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import ConnectionStatus from './components/ConnectionStatus';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import AdminLogin from './pages/AdminLogin';
import { 
  LazyChat, 
  LazyProfile, 
  LazyPricing 
} from './components/LazyComponent';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';
import Admin from './pages/Admin';
import AdminDashboard from './pages/AdminDashboard';
import IntegratedAdminPanel from './pages/IntegratedAdminPanel';
import RoleManagement from './pages/RoleManagement';
import ModerationPanel from './pages/ModerationPanel';
import ModerationDashboard from './pages/ModerationDashboard';
import usePerformanceOptimization from './hooks/usePerformanceOptimization';

function App() {
  // Initialize performance optimizations
  usePerformanceOptimization();
  
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <AdminProvider>
            <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
              <div className="App">
                <ConnectionStatus />
                <Routes>
                  <Route path="/" element={<Layout />}>
                    <Route index element={<Home />} />
                    <Route path="login" element={<Login />} />
                    <Route path="register" element={<Register />} />
                    <Route path="admin-login" element={<AdminLogin />} />
                    <Route path="pricing" element={<LazyPricing />} />
                    <Route 
                      path="chat" 
                      element={
                        <ProtectedRoute>
                          <ErrorBoundary>
                            <LazyChat />
                          </ErrorBoundary>
                        </ProtectedRoute>
                      } 
                    />
                    <Route 
                      path="profile" 
                      element={
                        <ProtectedRoute>
                          <ErrorBoundary>
                            <LazyProfile />
                          </ErrorBoundary>
                        </ProtectedRoute>
                      } 
                    />
                    <Route 
                      path="admin" 
                      element={
                        <AdminRoute>
                          <ErrorBoundary>
                            <IntegratedAdminPanel />
                          </ErrorBoundary>
                        </AdminRoute>
                      } 
                    />
                    <Route 
                      path="admin-legacy" 
                      element={
                        <AdminRoute>
                          <ErrorBoundary>
                            <Admin />
                          </ErrorBoundary>
                        </AdminRoute>
                      } 
                    />
                    <Route 
                      path="admin-dashboard" 
                      element={
                        <AdminRoute>
                          <ErrorBoundary>
                            <AdminDashboard />
                          </ErrorBoundary>
                        </AdminRoute>
                      } 
                    />
                    <Route 
                      path="role-management" 
                      element={
                        <AdminRoute>
                          <ErrorBoundary>
                            <RoleManagement />
                          </ErrorBoundary>
                        </AdminRoute>
                      } 
                    />
                    <Route 
                      path="moderation" 
                      element={
                        <ProtectedRoute>
                          <ErrorBoundary>
                            <ModerationPanel />
                          </ErrorBoundary>
                        </ProtectedRoute>
                      } 
                    />
                    <Route 
                      path="moderation-dashboard" 
                      element={
                        <ProtectedRoute>
                          <ErrorBoundary>
                            <ModerationDashboard />
                          </ErrorBoundary>
                        </ProtectedRoute>
                      } 
                    />
                  </Route>
                </Routes>
              </div>
            </Router>
          </AdminProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
