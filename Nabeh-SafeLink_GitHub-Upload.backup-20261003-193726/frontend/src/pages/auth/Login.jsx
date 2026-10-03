import { useState } from 'react';
import Logo from '../../components/Logo';
import { useAuth } from '../../context/AuthContext';
import { AlertTriangleIcon } from '../../components/Icons';

export default function Login({ onNavigate }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('الرجاء إدخال البريد الإلكتروني وكلمة المرور');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await login(email.trim(), password);
      onNavigate('home');
    } catch (err) {
      setError(err?.response?.data?.detail || 'اسم المستخدم أو كلمة المرور غير صحيحة');
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
          تسجيل الدخول إلى حسابك
        </h1>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)', textAlign: 'center' }}>
          أدخل بياناتك للوصول إلى سجل الفحوصات والإحصائيات المخصصة
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div>
            <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
              البريد الإلكتروني
            </label>
            <input
              type="email"
              autoComplete="email"
              className="scanner-input"
              style={{ direction: 'ltr', textAlign: 'left', minHeight: '44px', paddingLeft: '14px' }}
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-1)' }}>
              <label style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                كلمة المرور
              </label>
              <button
                type="button"
                onClick={() => onNavigate('forgot-password')}
                style={{ background: 'none', border: 'none', color: 'var(--color-secondary)', fontSize: 'var(--text-xs)', fontWeight: 600, cursor: 'pointer' }}
              >
                نسيت كلمة المرور؟
              </button>
            </div>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                className="scanner-input"
                style={{ direction: 'ltr', textAlign: 'left', minHeight: '44px', paddingLeft: '14px', paddingRight: '70px' }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--color-text-secondary)',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {showPassword ? 'إخفاء' : 'إظهار'}
              </button>
            </div>
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
            disabled={loading || !email.trim() || !password}
            style={{ width: '100%', marginTop: 'var(--space-2)' }}
          >
            <span>{loading ? 'جاري التحقق...' : 'تسجيل الدخول'}</span>
          </button>
        </form>

        <div style={{ marginTop: 'var(--space-6)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border)', textAlign: 'center', fontSize: 'var(--text-sm)' }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>ليس لديك حساب؟ </span>
          <button
            type="button"
            onClick={() => onNavigate('register')}
            style={{ background: 'none', border: 'none', color: 'var(--color-secondary)', fontWeight: 700, cursor: 'pointer' }}
          >
            إنشاء حساب جديد
          </button>
        </div>

        <div style={{ marginTop: 'var(--space-4)', textAlign: 'center' }}>
          <button
            type="button"
            onClick={() => onNavigate('scan')}
            style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)', fontWeight: 600, cursor: 'pointer' }}
          >
            ← الاستمرار كضيف دون تسجيل الدخول
          </button>
        </div>
      </div>
    </div>
  );
}
