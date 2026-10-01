import Logo from './Logo';
import { ShieldCheckIcon, HelpCircleIcon, MailIcon, BookOpenIcon, InfoIcon } from './Icons';
import { useLanguage } from '../context/LanguageContext';

export default function Footer({ activeTab, setActiveTab }) {
  const { t } = useLanguage();
  const currentYear = new Date().getFullYear();

  const supportLinks = [
    { id: 'faq', label: t('nav.faq'), icon: HelpCircleIcon },
    { id: 'guide', label: t('nav.guide'), icon: BookOpenIcon },
    { id: 'contact', label: t('nav.contact'), icon: MailIcon },
    { id: 'about', label: t('nav.about'), icon: InfoIcon },
  ];

  const quickLinks = [
    { id: 'home', label: t('nav.home') },
    { id: 'scan', label: t('nav.scan') },
    { id: 'history', label: t('nav.history') },
    { id: 'stats', label: t('nav.stats') },
  ];

  return (
    <footer className="app-footer" role="contentinfo">
      <div className="footer-container">
        {/* Brand & Mission */}
        <div className="footer-brand-section">
          <button
            type="button"
            className="footer-logo-btn"
            onClick={() => setActiveTab('home')}
            aria-label={t('nav.goHome')}
          >
            <Logo size="sm" showTagline={false} />
          </button>
          <p className="footer-tagline">{t('footer.tagline')}</p>
          <div className="footer-version-badge">
            <ShieldCheckIcon size={14} color="var(--color-success)" />
            <span>v1.0.0 MVP Stable</span>
          </div>
        </div>

        {/* Support Links */}
        <div className="footer-links-column">
          <h3 className="footer-column-title">{t('footer.supportSection')}</h3>
          <ul className="footer-links-list">
            {supportLinks.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    className={`footer-link-btn ${isActive ? 'active' : ''}`}
                    onClick={() => setActiveTab(item.id)}
                  >
                    <Icon size={15} />
                    <span>{item.label}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Quick System Nav Links */}
        <div className="footer-links-column">
          <h3 className="footer-column-title">{t('footer.quickLinksSection')}</h3>
          <ul className="footer-links-list">
            {quickLinks.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    className={`footer-link-btn ${isActive ? 'active' : ''}`}
                    onClick={() => setActiveTab(item.id)}
                  >
                    <span>{item.label}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Security Notice */}
        <div className="footer-notice-card">
          <p className="footer-notice-text">
            {t('footer.securityNotice')}
          </p>
        </div>
      </div>

      <div className="footer-bottom-bar">
        <p className="footer-copyright">
          {t('footer.rights', { year: currentYear })}
        </p>
      </div>

      <style>{`
        .app-footer {
          background: var(--color-surface);
          border-top: 1px solid var(--color-border);
          margin-top: var(--space-8, 48px);
          padding: var(--space-8, 48px) var(--space-4, 16px) var(--space-6, 24px);
          color: var(--color-text-secondary);
          font-size: 14px;
        }

        .footer-container {
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: 1.5fr 1fr 1fr 1.2fr;
          gap: var(--space-6, 24px);
        }

        .footer-brand-section {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: var(--space-3, 12px);
        }

        .footer-logo-btn {
          background: none;
          border: none;
          padding: 0;
          cursor: pointer;
          display: inline-flex;
        }

        .footer-tagline {
          color: var(--color-text-secondary);
          font-size: 13px;
          line-height: 1.5;
          margin: 0;
        }

        .footer-version-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          background: var(--color-bg);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-full);
          font-size: 12px;
          font-weight: 500;
          color: var(--color-text-muted);
        }

        .footer-links-column {
          display: flex;
          flex-direction: column;
          gap: var(--space-3, 12px);
        }

        .footer-column-title {
          font-size: 15px;
          font-weight: 600;
          color: var(--color-text);
          margin: 0;
        }

        .footer-links-list {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .footer-link-btn {
          background: none;
          border: none;
          padding: 0;
          font-family: inherit;
          font-size: 13px;
          color: var(--color-text-secondary);
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          transition: color var(--transition-fast);
        }

        .footer-link-btn:hover,
        .footer-link-btn.active {
          color: var(--color-secondary);
        }

        .footer-notice-card {
          background: var(--color-bg);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          padding: var(--space-4, 16px);
          display: flex;
          align-items: center;
        }

        .footer-notice-text {
          margin: 0;
          font-size: 12px;
          line-height: 1.6;
          color: var(--color-text-muted);
        }

        .footer-bottom-bar {
          max-width: 1200px;
          margin: var(--space-6, 24px) auto 0;
          padding-top: var(--space-4, 16px);
          border-top: 1px solid var(--color-border);
          text-align: center;
        }

        .footer-copyright {
          margin: 0;
          font-size: 12px;
          color: var(--color-text-muted);
        }

        @media (max-width: 900px) {
          .footer-container {
            grid-template-columns: 1fr 1fr;
          }
        }

        @media (max-width: 600px) {
          .footer-container {
            grid-template-columns: 1fr;
            gap: var(--space-6, 24px);
          }
          .app-footer {
            padding-bottom: 80px; /* space for mobile bottom nav */
          }
        }
      `}</style>
    </footer>
  );
}
