import Logo from './Logo';
import { useAuth } from '../context/AuthContext';
import { ShieldCheckIcon, ShieldIcon, BarChartIcon, InfoIcon } from './Icons';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { GlobeIcon, MoonIcon, SunIcon } from './Icons';

export default function Header({ activeTab, setActiveTab, onNavigateAuth }) {
  const { user, isGuest, logout } = useAuth();
  const { lang, dir, toggleLanguage, t } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const navItems = isGuest
    ? [{ id: 'scan', label: t('nav.scan'), icon: ShieldIcon }]
    : [
      { id: 'home', label: t('nav.home'), icon: ShieldIcon },
      { id: 'scan', label: t('nav.scan'), icon: ShieldIcon },
      { id: 'history', label: t('nav.history'), icon: BarChartIcon },
      { id: 'stats', label: t('nav.stats'), icon: InfoIcon },
    ];

  return (
    <header className="app-header" dir={dir}>
      <div className="app-header-container">
        <button
          type="button"
          className="header-brand"
          onClick={() => setActiveTab(isGuest ? 'scan' : 'home')}
          aria-label="Nabeh SafeLink"
          style={{ cursor: 'pointer', background: 'none', border: 0, padding: 0 }}
        >
          <Logo size="md" showTagline={true} />
        </button>

        <nav className="header-nav-desktop" aria-label={t('nav.home')}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`desktop-nav-btn ${isActive ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                <Icon size={18} color={isActive ? 'var(--color-secondary)' : 'var(--color-text-muted)'} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

          <div className="header-actions">
          <button type="button" className="header-preference-btn" onClick={toggleLanguage} aria-label={t('nav.changeLanguage')} title={t('nav.changeLanguage')}><GlobeIcon size={15} /><span>{lang === 'ar' ? 'English' : 'العربية'}</span></button>
          <button type="button" className="header-preference-btn header-theme-btn" onClick={toggleTheme} aria-label={t('auth.toggleTheme')} title={t('auth.toggleTheme')}>{theme === 'dark' ? <SunIcon size={16} /> : <MoonIcon size={16} />}</button>
          {!isGuest && user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-primary)' }}>
                {user.display_name || user.email}
              </span>
              <button
                type="button"
                onClick={async () => {
                  await logout();
                  navigate('/login', { replace: true });
                }}
                className="header-logout-btn"
              >
                {t('auth.logout')}
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => onNavigateAuth && onNavigateAuth('login')}
              className="header-login-btn"
            >
              {t('auth.login')}
            </button>
          )}
          <div className="header-badge">
            <ShieldCheckIcon size={16} color="#16A34A" />
            <span>{t('nav.protectionActive')}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
