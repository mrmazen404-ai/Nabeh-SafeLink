import { useState } from 'react';
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

import Home from './pages/Home';
import Scanner from './pages/Scanner';
import History from './pages/History';
import Statistics from './pages/Statistics';
import About from './pages/About';
import Contact from './pages/Contact';
import Faq from './pages/Faq';
import UserGuide from './pages/UserGuide';
import ErrorPage from './components/ErrorPage';
import BottomNav from './components/BottomNav';
import './styles/theme.css';

const TAB_PATHS = {
  home: '/',
  scan: '/scan',
  history: '/history',
  stats: '/stats',
  faq: '/faq',
  guide: '/guide',
  contact: '/contact',
  about: '/about',
};

function getActiveTab(pathname) {
  const match = Object.entries(TAB_PATHS)
    .filter(([, path]) => path !== '/')
    .find(([, path]) => pathname === path || pathname.startsWith(`${path}/`));
  return match?.[0] || (pathname === '/' ? 'home' : undefined);
}

function LoadingRoute() {
  return (
    <main role="status" aria-live="polite" aria-busy="true" style={{ minHeight: '100dvh', display: 'grid', placeItems: 'center', background: 'var(--color-bg-subtle)' }}>
      <span>جارٍ التحقق من الجلسة… / Checking session…</span>
    </main>
  );
}

function ProtectedRoute() {
  const { isGuest, loading } = useAuth();
  const location = useLocation();
  if (loading) return <LoadingRoute />;
  if (isGuest) return <Navigate to="/login" replace state={{ from: location }} />;
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
  return <Component {...context} {...props} />;
}

function AuthNavigation() {
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);

  return (page, data = {}) => {
    const paths = {
      login: '/login',
      register: '/register',
      'forgot-password': '/forgot-password',
      'reset-password': '/reset-password',
      'verify-otp': '/verify-otp',
      home: '/',
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
      const from = location.state?.from;
      navigate(from ? `${from.pathname}${from.search || ''}` : '/', { replace: true });
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
  return <Splash onComplete={() => navigate('/onboarding', { replace: true })} />;
}

function SettingsRedirect() {
  return <Navigate to="/" replace />;
}

function AppRoutes({ initialScanUrl, onQuickScan, onClearInitial }) {
  const navigate = useNavigate();
  const location = useLocation();
  const onNavigateAuth = AuthNavigation();
  const query = new URLSearchParams(location.search);

  const navigateFromPage = (tab) => navigate(TAB_PATHS[tab] || '/');
  const rescan = (value) => {
    onQuickScan(value || '');
    navigate('/scan');
  };

  return (
    <Routes>
      <Route element={<PublicRoute />}>
        <Route element={<NavigationLayout initialScanUrl={initialScanUrl} onQuickScan={onQuickScan} onClearInitial={onClearInitial} onNavigateAuth={onNavigateAuth} />}>
          <Route path="/scan" element={<RoutedPage component={Scanner} />} />
          <Route path="/faq" element={<RoutedPage component={Faq} />} />
          <Route path="/support" element={<RoutedPage component={Faq} />} />
          <Route path="/guide" element={<RoutedPage component={UserGuide} />} />
          <Route path="/contact" element={<RoutedPage component={Contact} />} />
          <Route path="/about" element={<RoutedPage component={About} />} />
        </Route>
        <Route path="/reset-password" element={<ResetPassword onNavigate={onNavigateAuth} />} />
        <Route path="/onboarding" element={<OnboardingRoute />} />
        <Route path="/splash" element={<SplashRoute />} />
      </Route>

      <Route element={<GuestRoute />}>
        <Route path="/login" element={<Login onNavigate={onNavigateAuth} />} />
        <Route path="/register" element={<Register onNavigate={onNavigateAuth} />} />
        <Route path="/forgot-password" element={<ForgotPassword onNavigate={onNavigateAuth} />} />
        <Route path="/verify-otp" element={<VerifyOtp onNavigate={onNavigateAuth} email={query.get('email') || ''} type={query.get('type') || 'signup'} />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<NavigationLayout initialScanUrl={initialScanUrl} onQuickScan={onQuickScan} onClearInitial={onClearInitial} onNavigateAuth={onNavigateAuth} />}>
          <Route path="/" element={<RoutedPage component={Home} onNavigate={navigateFromPage} onQuickScan={rescan} />} />
          <Route path="/history" element={<RoutedPage component={History} onQuickScan={rescan} />} />
          <Route path="/stats" element={<RoutedPage component={Statistics} />} />
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
