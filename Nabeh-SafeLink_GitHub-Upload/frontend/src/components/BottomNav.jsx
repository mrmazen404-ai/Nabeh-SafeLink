import { ShieldIcon, BarChartIcon, InfoIcon } from './Icons';
import { useLanguage } from '../context/LanguageContext';

export default function BottomNav({ activeTab, setActiveTab, isGuest = false }) {
  const { t } = useLanguage();
  if (isGuest) return null;
  const tabs = [
    { id: 'home', label: t('nav.home'), icon: ShieldIcon },
    { id: 'scan', label: t('nav.scan'), icon: ShieldIcon },
    { id: 'history', label: t('nav.history'), icon: BarChartIcon },
    { id: 'stats', label: t('nav.stats'), icon: InfoIcon },
  ];
  return (
    <nav className="mobile-bottom-nav" aria-label={t('nav.home')}>
      {tabs.map((item) => {
        const IconComponent = item.icon;
        const isActive = activeTab === item.id;
        return (
          <button
            key={item.id}
            type="button"
            className={`mobile-nav-item ${isActive ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
            aria-current={isActive ? 'page' : undefined}
          >
            <IconComponent size={20} color={isActive ? 'var(--color-secondary)' : 'var(--color-text-muted)'} />
            <span>{item.label}</span>
          </button>
        );
      })}
      <style>{`
        .mobile-bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: var(--color-bg); border-top: 1px solid var(--color-border); display: flex; justify-content: space-around; padding: 8px 0 10px; box-shadow: var(--shadow-sm); z-index: 100; }
        .mobile-nav-item { background: none; border: none; border-top: 2px solid transparent; display: flex; flex-direction: column; align-items: center; gap: 4px; font-family: inherit; font-size: 12px; font-weight: 500; color: var(--color-text-muted); cursor: pointer; padding: 6px 16px; border-radius: 6px; transition: all 150ms ease; }
        .mobile-nav-item.active { background: var(--color-bg-subtle); border-top-color: var(--color-secondary); color: var(--color-text); font-weight: 600; }
        @media (min-width: 768px) { .mobile-bottom-nav { display: none !important; } }
      `}</style>
    </nav>
  );
}
