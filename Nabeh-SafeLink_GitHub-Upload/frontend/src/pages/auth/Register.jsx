import { useState } from 'react';
import Logo from '../../components/Logo';
import { useAuth } from '../../context/AuthContext';
import { AlertTriangleIcon, ArrowLeftIcon, ArrowRightIcon, UserIcon } from '../../components/Icons';
import { useLanguage } from '../../context/LanguageContext';
import AuthPageControls from '../../components/AuthPageControls';
import './login.css';
import './register.css';

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

export default function Register({ onNavigate }) {
  const { register } = useAuth();
  const { t, dir } = useLanguage();
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!email.trim() || !password || !displayName.trim() || !confirmPassword) {
      setError(t('auth.requiredFields'));
      return;
    }
    if (password !== confirmPassword) {
      setError(t('auth.passwordMismatch'));
      return;
    }
    if (password.length < 12) {
      setError(t('auth.passwordLength'));
      return;
    }

    setError('');
    setLoading(true);
    try {
      const response = await register(email.trim(), password, displayName.trim());
      setSuccessMsg(response.message || 'إذا كان البريد الإلكتروني صحيحاً، فستصلك تعليمات تأكيد الحساب');
      setTimeout(() => onNavigate('verify-otp', { email: email.trim() }), 2000);
    } catch {
      setError('تعذر إنشاء الحساب. تأكد من البيانات أو حاول مجدداً.');
    } finally {
      setLoading(false);
    }
  };

  const BackIcon = dir === 'rtl' ? ArrowRightIcon : ArrowLeftIcon;

  return (
    <main className="login-page register-page" dir={dir}>
      <AuthPageControls />
      <div className="login-shell">
        <div className="login-branding"><Logo size="lg" showTagline={false} /></div>

        <section className="login-welcome" aria-labelledby="register-title">
          <h1 id="register-title">{t('auth.createAccount')}</h1>
          <p>{t('auth.registerSubtitle')}</p>
        </section>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <label className="login-field"><span className="login-field-icon"><UserIcon size={19} color="currentColor" /></span><input type="text" autoComplete="name" placeholder={t('auth.fullName')} value={displayName} onChange={(event) => setDisplayName(event.target.value)} aria-label={t('auth.fullName')} /></label>
          <label className="login-field"><span className="login-field-icon"><UserIcon size={19} color="currentColor" /></span><input type="email" autoComplete="email" placeholder={t('auth.emailAddress')} value={email} onChange={(event) => setEmail(event.target.value)} aria-label={t('auth.emailAddress')} /></label>
          <label className="login-field"><span className="login-field-icon"><LockIcon size={19} color="currentColor" /></span><input type={showPassword ? 'text' : 'password'} autoComplete="new-password" maxLength={128} placeholder={t('auth.password')} value={password} onChange={(event) => setPassword(event.target.value)} aria-label={t('auth.password')} /><button type="button" className="login-password-toggle" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? t('auth.hidePassword') : t('auth.showPassword')}>{showPassword ? <EyeOffIcon size={19} /> : <EyeIcon size={19} />}</button></label>
          <label className="login-field"><span className="login-field-icon"><LockIcon size={19} color="currentColor" /></span><input type={showConfirmPassword ? 'text' : 'password'} autoComplete="new-password" maxLength={128} placeholder={t('auth.confirmPassword')} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} aria-label={t('auth.confirmPassword')} /><button type="button" className="login-password-toggle" onClick={() => setShowConfirmPassword((value) => !value)} aria-label={showConfirmPassword ? t('auth.hidePassword') : t('auth.showPassword')}>{showConfirmPassword ? <EyeOffIcon size={19} /> : <EyeIcon size={19} />}</button></label>

          {error && <div className="login-error" role="alert"><AlertTriangleIcon size={17} color="currentColor" /><span>{error}</span></div>}
          {successMsg && <div className="register-success" role="status">{successMsg}</div>}

          <button className="login-submit" type="submit" disabled={loading}><span>{loading ? '…' : t('auth.registerAction')}</span><BackIcon size={17} /></button>
        </form>

        <div className="login-divider"><span>{t('auth.socialDivider')}</span></div>
        <div className="login-social" aria-label="Social registration options"><button type="button" className="login-social-button" aria-label="Continue with Google"><GoogleIcon /></button><button type="button" className="login-social-button" aria-label="Continue with Apple"><AppleIcon /></button></div>

        <p className="register-footer">{t('auth.alreadyAccount')} <button type="button" onClick={() => onNavigate('login')}>{t('auth.login')}</button></p>
      </div>
    </main>
  );
}
