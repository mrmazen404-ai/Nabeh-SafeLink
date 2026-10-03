import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { MoonIcon, SunIcon, GlobeIcon } from './Icons';

export default function AuthPageControls() {
  const { lang, toggleLanguage, t } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  return (
    <div className="auth-page-controls" aria-label="Page preferences">
      <button type="button" className="auth-control auth-language-control" onClick={toggleLanguage} aria-label={t('auth.changeLanguage')} title={t('auth.changeLanguage')}>
        <GlobeIcon size={15} color="currentColor" /><span>{lang === 'ar' ? 'English' : 'العربية'}</span>
      </button>
      <button type="button" className="auth-control auth-theme-control" onClick={toggleTheme} aria-label={t('auth.toggleTheme')} title={t('auth.toggleTheme')}>
        {theme === 'dark' ? <SunIcon size={16} color="currentColor" /> : <MoonIcon size={16} color="currentColor" />}
      </button>
    </div>
  );
}
