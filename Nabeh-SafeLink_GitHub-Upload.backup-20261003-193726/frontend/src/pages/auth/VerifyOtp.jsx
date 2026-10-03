import { useState, useEffect } from 'react';
import Logo from '../../components/Logo';
import { useAuth } from '../../context/AuthContext';
import { AlertTriangleIcon } from '../../components/Icons';

export default function VerifyOtp({ onNavigate, email = '', type = 'signup' }) {
  const { verifyOtp } = useAuth();
  const [otpToken, setOtpToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [cooldown, setCooldown] = useState(60);

  useEffect(() => {
    if (cooldown > 0) {
      const timer = setInterval(() => setCooldown((prev) => prev - 1), 1000);
      return () => clearInterval(timer);
    }
  }, [cooldown]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!otpToken.trim() || otpToken.trim().length < 6) {
      setError('الرجاء إدخال رمز التحقق المكون من 6 أرقام');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await verifyOtp(email, otpToken.trim(), type);
      onNavigate(type === 'recovery' ? 'reset-password' : 'home');
    } catch (err) {
      setError('رمز التحقق غير صحيح أو منتهي الصلاحية');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg-subtle)', padding: '20px' }}>
      <div className="card" style={{ maxWidth: '440px', width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 'var(--space-6)' }}>
          <Logo size="lg" showTagline={true} />
        </div>

        <h1 style={{ fontSize: 'var(--text-xl)', fontWeight: 700, color: 'var(--color-primary)', marginBottom: 'var(--space-2)', textAlign: 'center' }}>
          تأكيد بريدك الإلكتروني
        </h1>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)', textAlign: 'center' }}>
          تم إرسال رمز تحقق مكون من 6 أرقام إلى: <strong dir="ltr">{email || 'بريدك المسجل'}</strong>
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div>
            <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)', textAlign: 'center' }}>
              رمز التحقق (OTP)
            </label>
            <input
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              className="scanner-input"
              style={{
                direction: 'ltr',
                textAlign: 'center',
                letterSpacing: '8px',
                fontSize: '24px',
                fontWeight: 700,
                minHeight: '52px'
              }}
              placeholder="123456"
              value={otpToken}
              onChange={(e) => setOtpToken(e.target.value.replace(/\D/g, ''))}
              required
            />
          </div>

          {error && (
            <div className="scanner-error" style={{ marginBottom: 0 }}>
              <AlertTriangleIcon size={16} color="var(--color-danger)" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || otpToken.length < 6}
            style={{ width: '100%' }}
          >
            <span>{loading ? 'جاري التحقق...' : 'تأكيد الحساب'}</span>
          </button>
        </form>

        <div style={{ marginTop: 'var(--space-6)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border)', textAlign: 'center', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
          {cooldown > 0 ? (
            <span>إعادة إرسال الرمز متاح بعد {cooldown} ثانية</span>
          ) : (
            <button
              type="button"
              onClick={() => setCooldown(60)}
              style={{ background: 'none', border: 'none', color: 'var(--color-secondary)', fontWeight: 700, cursor: 'pointer' }}
            >
              إعادة إرسال الرمز الآن
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
