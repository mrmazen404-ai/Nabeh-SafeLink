import { useState } from 'react';
import Logo from '../../components/Logo';
import { useAuth } from '../../context/AuthContext';
import { AlertTriangleIcon, ArrowLeftIcon, ArrowRightIcon, MailIcon } from '../../components/Icons';
import { useLanguage } from '../../context/LanguageContext';
import AuthPageControls from '../../components/AuthPageControls';
import './login.css';

function LockIcon({ size = 20, color = 'currentColor' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg>;
}

function EyeIcon({ size = 20, color = 'currentColor' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" /><circle cx="12" cy="12" r="2.5" /></svg>;
}

function EyeOffIcon({ size = 20, color = 'currentColor' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m3 3 18 18M10.6 6.2A10.6 10.6 0 0 1 12 6c6.5 0 10 6 10 6a18.7 18.7 0 0 1-3.1 3.8M6.3 6.3C3.6 8.1 2 12 2 12s3.5 6 10 6c1.2 0 2.3-.2 3.3-.6" /><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" /></svg>;
}

function GoogleIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285F4" d="M21.6 12.23c0-.7-.06-1.37-.18-2.02H12v3.83h5.38a4.6 4.6 0 0 1-1.99 3.02v2.5h3.22c1.89-1.74 2.99-4.3 2.99-7.33Z"/><path fill="#34A853" d="M12 22c2.7 0 4.96-.9 6.61-2.44l-3.22-2.5c-.9.6-2.05.96-3.39.96-2.61 0-4.82-1.76-5.61-4.13H3.06v2.58A10 10 0 0 0 12 22Z"/><path fill="#FBBC05" d="M6.39 13.89A6.02 6.02 0 0 1 6.08 12c0-.66.11-1.3.31-1.89V7.53H3.06A10 10 0 0 0 2 12c0 1.61.38 3.13 1.06 4.47l3.33-2.58Z"/><path fill="#EA4335" d="M12 5.98c1.47 0 2.8.5 3.84 1.49l2.88-2.88C16.95 2.93 14.7 2 12 2a10 10 0 0 0-8.94 5.53l3.33 2.58C7.18 7.74 9.39 5.98 12 5.98Z"/></svg>;
}

function AppleIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M17.05 12.54c-.02-2.1 1.72-3.12 1.8-3.17a3.87 3.87 0 0 0-3.05-1.65c-1.29-.13-2.53.77-3.18.77-.66 0-1.68-.75-2.76-.73a4.06 4.06 0 0 0-3.42 2.08c-1.48 2.56-.38 6.34 1.04 8.41.7 1.01 1.52 2.14 2.6 2.1 1.04-.04 1.43-.67 2.68-.67 1.25 0 1.6.67 2.7.65 1.12-.02 1.82-1.02 2.5-2.04a8.37 8.37 0 0 0 1.14-2.35 3.64 3.64 0 0 1-2.05-3.4ZM14.96 6.36a3.7 3.7 0 0 0 .85-2.66 3.76 3.76 0 0 0-2.45 1.27 3.53 3.53 0 0 0-.88 2.56 3.1 3.1 0 0 0 2.48-1.17Z"/></svg>;
}

function getLoginError(error, isArabic) {
  const status = error?.response?.status;
  if (status === 401) return isArabic ? 'البريد الإلكتروني أو كلمة المرور غير صحيحة.' : 'The email or password is incorrect.';
  if (status === 403) return isArabic ? 'هذا الحساب موقوف. تواصل مع الدعم.' : 'This account is suspended. Contact support.';
  if (status === 422) return isArabic ? 'أدخل بريداً إلكترونياً صحيحاً وكلمة مرور صالحة.' : 'Enter a valid email and password.';
  if (status === 429) return isArabic ? 'تم تجاوز عدد محاولات الدخول. انتظر قليلاً ثم حاول مجدداً.' : 'Too many login attempts. Wait a moment and try again.';
  if (status >= 500) return isArabic ? 'خدمة تسجيل الدخول غير متاحة مؤقتاً. حاول لاحقاً.' : 'Login service is temporarily unavailable. Try again later.';
  if (!error?.response) return isArabic ? 'تعذر الاتصال بالخادم. تحقق من تشغيل النظام والاتصال.' : 'Unable to reach the server. Check the service and your connection.';
  return isArabic ? 'تعذر تسجيل الدخول. تحقق من البيانات وحاول مجدداً.' : 'Unable to sign in. Check your details and try again.';
}

export default function Login({ onNavigate }) {
  const { login } = useAuth();
  const { t, dir } = useLanguage();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail || !password) {
      setError(t('auth.requiredFields'));
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setError(dir === 'rtl' ? 'أدخل عنوان بريد إلكتروني صحيحاً.' : 'Enter a valid email address.');
      return;
    }

    setError('');
    setLoading(true);
    try {
      await login(normalizedEmail, password);
      onNavigate('home');
    } catch (err) {
      setError(getLoginError(err, dir === 'rtl'));
    } finally {
      setLoading(false);
    }
  };

  const SubmitArrow = dir === 'rtl' ? ArrowLeftIcon : ArrowRightIcon;
  const BackArrow = dir === 'rtl' ? ArrowRightIcon : ArrowLeftIcon;

  return (
    <main className="login-page" dir={dir}>
      <AuthPageControls />
      <div className="login-shell">
        <div className="login-branding">
          <Logo size="lg" showTagline={false} />
        </div>

        <section className="login-welcome" aria-labelledby="login-title">
          <h1 id="login-title">{t('auth.loginTitle')}</h1>
          <p>{t('auth.loginSubtitle')}</p>
        </section>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <label className="login-field">
            <span className="login-field-icon"><MailIcon size={19} color="currentColor" /></span>
            <input
              type="email"
              dir={dir}
              autoComplete="email"
              placeholder={t('auth.emailOrUsername')}
              value={email}
              onChange={(event) => { setEmail(event.target.value); setError(''); }}
              aria-label={t('auth.emailOrUsername')}
              required
            />
          </label>

          <label className="login-field">
            <span className="login-field-icon"><LockIcon size={19} color="currentColor" /></span>
            <input
              type={showPassword ? 'text' : 'password'}
              dir={dir}
              autoComplete="current-password"
              placeholder={t('auth.password')}
              value={password}
              onChange={(event) => { setPassword(event.target.value); setError(''); }}
              aria-label={t('auth.password')}
              required
            />
            <button type="button" className="login-password-toggle" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? t('auth.hidePassword') : t('auth.showPassword')}>
              {showPassword ? <EyeOffIcon size={19} color="currentColor" /> : <EyeIcon size={19} color="currentColor" />}
            </button>
          </label>

          <div className="login-utilities">
            <label className="login-remember"><input type="checkbox" checked={rememberMe} onChange={(event) => setRememberMe(event.target.checked)} /><span className="login-checkmark" /> <span>{t('auth.rememberMe')}</span></label>
            <button type="button" className="login-forgot" onClick={() => onNavigate('forgot-password')}>{t('auth.forgotPassword')}</button>
          </div>

          {error && <div className="login-error" role="alert" aria-live="polite"><AlertTriangleIcon size={17} color="currentColor" /><span>{error}</span></div>}

          <button className="login-submit" type="submit" disabled={loading}>
            <span>{loading ? '…' : t('auth.login')}</span>
            <SubmitArrow size={17} color="currentColor" />
          </button>
        </form>

        <div className="login-divider"><span>{t('auth.socialDivider')}</span></div>
        <div className="login-social" aria-label="Social login options">
          <button type="button" className="login-social-button" aria-label={t('auth.socialGoogle')} title={t('auth.socialGoogle')}><GoogleIcon /></button>
          <button type="button" className="login-social-button" aria-label={t('auth.socialApple')} title={t('auth.socialApple')}><AppleIcon /></button>
        </div>

        <p className="login-register">{t('auth.noAccount')} <button type="button" onClick={() => onNavigate('register')}>{t('auth.register')}</button></p>
        <button type="button" className="login-guest" onClick={() => onNavigate('scan')}><BackArrow size={15} /> {t('auth.continueGuest')}</button>
      </div>
    </main>
  );
}
