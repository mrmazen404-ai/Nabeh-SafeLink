import Logo from './Logo';
import { useAuth } from '../context/AuthContext';
import { ShieldCheckIcon, ShieldIcon, BarChartIcon, InfoIcon } from './Icons';

export default function Header({ activeTab, setActiveTab, onNavigateAuth }) {
  const { user, isGuest, logout } = useAuth();
  const navItems = isGuest
    ? [{ id: 'scan', label: 'الفحص', icon: ShieldIcon }]
    : [
      { id: 'home', label: 'الرئيسية', icon: ShieldIcon },
      { id: 'scan', label: 'الفحص', icon: ShieldIcon },
      { id: 'history', label: 'السجل', icon: BarChartIcon },
      { id: 'stats', label: 'الإحصائيات', icon: InfoIcon },
    ];

  return (
    <header className="app-header">
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

        <nav className="header-nav-desktop" aria-label="التنقل الرئيسي">
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
                <Icon size={18} color={isActive ? '#1E90FF' : '#4B5563'} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {!isGuest && user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-primary)' }}>
                {user.display_name || user.email}
              </span>
              <button
                type="button"
                onClick={logout}
                style={{ background: 'none', border: '1px solid var(--color-border)', padding: '4px 10px', borderRadius: 'var(--radius-sm)', fontSize: '12px', color: 'var(--color-danger)', cursor: 'pointer', fontWeight: 600 }}
              >
                خروج
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => onNavigateAuth && onNavigateAuth('login')}
              style={{ background: 'var(--color-primary)', color: '#FFFFFF', border: 'none', padding: '6px 14px', borderRadius: 'var(--radius-sm)', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
            >
              تسجيل الدخول
            </button>
          )}
          <div className="header-badge">
            <ShieldCheckIcon size={16} color="#16A34A" />
            <span>الحماية نشطة</span>
          </div>
        </div>
      </div>
    </header>
  );
}
