import { useState, useEffect, lazy, Suspense } from 'react';
import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useOutletContext,
} from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import { ThemeProvider } from './context/ThemeContext';

import Splash from './pages/auth/Splash';
import Onboarding from './pages/auth/Onboarding';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import ForgotPassword from './pages/auth/ForgotPassword';
import ResetPassword from './pages/auth/ResetPassword';
import VerifyOtp from './pages/auth/VerifyOtp';
import WelcomePage from './pages/WelcomePage';
import SessionCheckScreen from './components/SessionCheckScreen';
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Scanner = lazy(() => import('./pages/Scanner'));
const History = lazy(() => import('./pages/History'));
const Statistics = lazy(() => import('./pages/Statistics'));
const ScanDetails = lazy(() => import('./pages/ScanDetails'));
const Comparison = lazy(() => import('./pages/Comparison'));
const ExportReport = lazy(() => import('./pages/ExportReport'));
const Notifications = lazy(() => import('./pages/Notifications'));
const AlertSettings = lazy(() => import('./pages/AlertSettings'));
const About = lazy(() => import('./pages/About'));
const Contact = lazy(() => import('./pages/Contact'));
const Faq = lazy(() => import('./pages/Faq'));
const UserGuide = lazy(() => import('./pages/UserGuide'));
import ErrorPage from './components/ErrorPage';
import BottomNav from './components/BottomNav';
import './styles/theme.css';
const TAB_PATHS = {
  home: '/dashboard',
  scan: '/scan',
  history: '/history',
  stats: '/stats',
  faq: '/faq',
  guide: '/guide',
  contact: '/contact',
  about: '/about',
};

function getActiveTab(pathname) {
  if (pathname === '/home') return 'home';
  const match = Object.entries(TAB_PATHS)
    .filter(([, path]) => path !== '/')
    .find(([, path]) => pathname === path || pathname.startsWith(`${path}/`));
  return match?.[0] || (pathname === '/' ? 'home' : undefined);
}

function LoadingRoute() {
  return <SessionCheckScreen />;
}

function ProtectedRoute() {
  const { isGuest, loading } = useAuth();
  const location = useLocation();
  if (loading) return <LoadingRoute />;
  if (isGuest) {
    const next = `${location.pathname}${location.search || ''}`;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace state={{ from: location }} />;
  }
  return <Outlet />;
}

function GuestRoute() {
  const { isGuest, loading } = useAuth();
  if (loading) return <LoadingRoute />;
  if (!isGuest) return <Navigate to="/" replace />;
  return <Outlet />;
}

function PublicRoute() {
  const { loading } = useAuth();
  return loading ? <LoadingRoute /> : <Outlet />;
}

function NavigationLayout({ initialScanUrl, onQuickScan, onClearInitial, onNavigateAuth }) {
  const { isGuest } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const activeTab = getActiveTab(location.pathname);

  const setActiveTab = (tab) => {
    const path = TAB_PATHS[tab];
    if (path) navigate(path);
  };

  const handleQuickScan = (value) => {
    onQuickScan(value || '');
    navigate('/scan');
  };

  return (
    <div className="app-container">
      <Outlet context={{ activeTab, setActiveTab, isGuest, onNavigateAuth, onQuickScan: handleQuickScan, initialScanUrl, onClearInitial }} />
      <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} isGuest={isGuest} />
    </div>
  );
}

function RoutedPage({ component: Component, ...props }) {
  const context = useOutletContext();
  return (
    <Suspense fallback={<LoadingRoute />}>
      <Component {...context} {...props} />
    </Suspense>
  );
}

function AuthNavigation() {
  const navigate = useNavigate();

  return (page, data = {}) => {
    const paths = {
      login: '/login',
      register: '/register',
      'forgot-password': '/forgot-password',
      'reset-password': '/reset-password',
      'verify-otp': '/verify-otp',
      home: '/dashboard',
      scan: '/scan',
    };
    const path = paths[page];
    if (!path) return;

    if (page === 'verify-otp') {
      const params = new URLSearchParams({ email: data.email || '', type: data.type || 'signup' });
      navigate(`${path}?${params.toString()}`);
      return;
    }

    if (page === 'home') {
      // Authentication always lands in the official workspace, never the public welcome screen.
      navigate('/dashboard', { replace: true });
      return;
    }

    navigate(path);
  };
}

function OnboardingRoute() {
  const navigate = useNavigate();
  return <Onboarding onComplete={() => navigate('/login', { replace: true })} />;
}

function SplashRoute() {
  const navigate = useNavigate();
  const { isGuest, user } = useAuth();

  const handleComplete = () => {
    if (!isGuest && user) {
      navigate('/dashboard', { replace: true });
    } else {
      navigate('/welcome', { replace: true });
    }
  };

  return <Splash onComplete={handleComplete} />;
}

function SettingsRedirect() {
  return <Navigate to="/dashboard" replace />;
}

function AppRoutes({ initialScanUrl, onQuickScan, onClearInitial }) {
  const navigate = useNavigate();
  const location = useLocation();
  const onNavigateAuth = AuthNavigation();
  const query = new URLSearchParams(location.search);
  const { isSecuringSession, finishSecuringSession } = useAuth();

  const navigateFromPage = (tab) => navigate(TAB_PATHS[tab] || '/');
  const rescan = (value) => {
    onQuickScan(value || '');
    navigate('/scan');
  };

  if (isSecuringSession) {
    return <SessionCheckScreen onComplete={finishSecuringSession} />;
  }

  return (
    <Routes>
      {/* The public entry point initializes through Splash before WelcomePage. */}
      <Route path="/" element={<SplashRoute />} />

      <Route element={<PublicRoute />}>
        <Route element={<NavigationLayout initialScanUrl={initialScanUrl} onQuickScan={onQuickScan} onClearInitial={onClearInitial} onNavigateAuth={onNavigateAuth} />}>
          <Route path="/scan" element={<RoutedPage component={Scanner} />} />
          <Route path="/faq" element={<RoutedPage component={Faq} />} />
          <Route path="/support" element={<RoutedPage component={Faq} />} />
          <Route path="/guide" element={<RoutedPage component={UserGuide} />} />
          <Route path="/contact" element={<RoutedPage component={Contact} />} />
          <Route path="/about" element={<RoutedPage component={About} />} />
        </Route>
        <Route path="/welcome" element={<WelcomePage />} />
        <Route path="/onboarding" element={<OnboardingRoute />} />
        <Route path="/splash" element={<SplashRoute />} />
      </Route>

      <Route element={<GuestRoute />}>
        <Route path="/login" element={<Login onNavigate={onNavigateAuth} />} />
        <Route path="/register" element={<Register onNavigate={onNavigateAuth} />} />
        <Route path="/forgot-password" element={<ForgotPassword onNavigate={onNavigateAuth} />} />
        <Route path="/reset-password" element={<ResetPassword onNavigate={onNavigateAuth} />} />
        <Route path="/verify-otp" element={<VerifyOtp onNavigate={onNavigateAuth} email={query.get('email') || ''} type={query.get('type') || 'signup'} />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<NavigationLayout initialScanUrl={initialScanUrl} onQuickScan={onQuickScan} onClearInitial={onClearInitial} onNavigateAuth={onNavigateAuth} />}>
          <Route path="/dashboard" element={<RoutedPage component={Dashboard} />} />
          <Route path="/notifications" element={<RoutedPage component={Notifications} />} />
          <Route path="/settings/alerts" element={<RoutedPage component={AlertSettings} />} />
          {/* /home remains a backwards-compatible alias; Dashboard is the single workspace. */}
          <Route path="/home" element={<RoutedPage component={Dashboard} />} />
          <Route path="/history" element={<RoutedPage component={History} onQuickScan={rescan} />} />
          <Route path="/stats" element={<RoutedPage component={Statistics} />} />
          <Route path="/scan-details/:scanId" element={<RoutedPage component={ScanDetails} />} />
          <Route path="/compare" element={<RoutedPage component={Comparison} />} />
          <Route path="/export-report" element={<RoutedPage component={ExportReport} />} />
          <Route path="/settings" element={<SettingsRedirect />} />
        </Route>
      </Route>

      <Route path="/404" element={<ErrorPage type="404" onNavigate={navigateFromPage} />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
}

export default function App() {
  const [initialScanUrl, setInitialScanUrl] = useState('');

  return (
    <ThemeProvider>
      <LanguageProvider>
        <BrowserRouter>
          <AuthProvider>
            <AppRoutes
              initialScanUrl={initialScanUrl}
              onQuickScan={(value) => setInitialScanUrl(value || '')}
              onClearInitial={() => setInitialScanUrl('')}
            />
          </AuthProvider>
        </BrowserRouter>
      </LanguageProvider>
    </ThemeProvider>
  );
}