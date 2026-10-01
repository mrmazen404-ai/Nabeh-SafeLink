import { useEffect, useState } from 'react';
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
import BottomNav from './components/BottomNav';
import './styles/theme.css';

function MainApp() {
  const { isGuest, loading } = useAuth();
  const initialResetRoute = window.location.pathname.replace(/\/$/, '') === '/reset-password';
  const [viewState, setViewState] = useState(initialResetRoute ? 'auth_page' : 'splash');
  const [authPage, setAuthPage] = useState(initialResetRoute ? 'reset-password' : 'login');
  const [activeTab, setActiveTab] = useState('home');
  const [initialScanUrl, setInitialScanUrl] = useState('');
  const [verifyEmail, setVerifyEmail] = useState('');

  useEffect(() => {
    if (!loading && isGuest) {
      setActiveTab('scan');
      setInitialScanUrl('');
    }
  }, [isGuest, loading]);

  const handleNavigateAuth = (page, data = {}) => {
    if (page !== 'reset-password' && window.location.pathname.replace(/\/$/, '') === '/reset-password') {
      window.history.replaceState(null, '', '/');
    }
    if (data.email) setVerifyEmail(data.email);
    setAuthPage(page);
    setViewState('auth_page');
  };

  const handleQuickScan = (url) => {
    setInitialScanUrl(url);
    setActiveTab('scan');
  };

  const handleSplashComplete = () => {
    setViewState('onboarding');
  };

  const handleOnboardingComplete = () => {
    setViewState('main');
  };

  if (loading) {
    return (
      <main role="status" aria-live="polite" aria-busy="true" style={{ minHeight: '100dvh', display: 'grid', placeItems: 'center', background: 'var(--color-bg-subtle)' }}>
        <span>جارٍ التحقق من الجلسة… / Checking session…</span>
      </main>
    );
  }

  if (viewState === 'splash') {
    return <Splash onComplete={handleSplashComplete} />;
  }

  if (viewState === 'onboarding') {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }

  if (viewState === 'auth_page') {
    if (authPage === 'login') return <Login onNavigate={handleNavigateAuth} />;
    if (authPage === 'register') return <Register onNavigate={handleNavigateAuth} />;
    if (authPage === 'forgot-password') return <ForgotPassword onNavigate={handleNavigateAuth} />;
    if (authPage === 'reset-password') return <ResetPassword onNavigate={handleNavigateAuth} />;
    if (authPage === 'verify-otp') return <VerifyOtp onNavigate={handleNavigateAuth} email={verifyEmail} />;
  }

  return (
    <div className="app-container">
      {!isGuest && activeTab === 'home' && (
        <Home
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onNavigate={(tab) => setActiveTab(tab)}
          onQuickScan={handleQuickScan}
          onNavigateAuth={handleNavigateAuth}
        />
      )}

      {activeTab === 'scan' && (
        <Scanner
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          initialUrl={initialScanUrl}
          onClearInitial={() => setInitialScanUrl('')}
          isGuest={isGuest}
          onNavigateAuth={handleNavigateAuth}
        />
      )}

      {!isGuest && activeTab === 'history' && (
        <History
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onQuickScan={handleQuickScan}
          isGuest={isGuest}
          onNavigateAuth={handleNavigateAuth}
        />
      )}

      {!isGuest && activeTab === 'stats' && (
        <Statistics
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          isGuest={isGuest}
          onNavigateAuth={handleNavigateAuth}
        />
      )}

      <BottomNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isGuest={isGuest}
      />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <AuthProvider>
          <MainApp />
        </AuthProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}
