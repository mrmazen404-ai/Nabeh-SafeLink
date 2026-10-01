import { useState } from 'react';
import Logo from '../../components/Logo';
import { useAuth } from '../../context/AuthContext';
import { AlertTriangleIcon } from '../../components/Icons';

export default function Register({ onNavigate }) {
  const { register } = useAuth();
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password || !displayName.trim()) {
      setError('الرجاء إكمال كافة الحقول الإلزامية');
      return;
    }

    if (password !== confirmPassword) {
      setError('كلمتا المرور غير متطابقتين');
      return;
    }

    if (password.length < 12) {
      setError('يجب أن تتكون كلمة المرور من 12 حرفاً على الأقل');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const res = await register(email.trim(), password, displayName.trim());
      setSuccessMsg(res.message || 'إذا كان البريد إلكترونياً صحيحاً، فستصلك تعليمات تأكيد الحساب');
      setTimeout(() => {
        onNavigate('verify-otp', { email: email.trim() });
      }, 2000);
    } catch (err) {
      setError('تعذر إنشاء الحساب. تأكد من البيانات أو حاول مجدداً.');
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
          إنشاء حساب جديد
        </h1>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)', textAlign: 'center' }}>
          سجل للانضمام إلى منصة نابه وحفظ سجل الفحوصات
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div>
            <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
              الاسم / اسم العرض
            </label>
            <input
              type="text"
              className="scanner-input"
              style={{ minHeight: '44px', paddingLeft: '14px' }}
              placeholder="مثال: أحمد العتيبي"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
            />
          </div>

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
            <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
              كلمة المرور
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                className="scanner-input"
                style={{ direction: 'ltr', textAlign: 'left', minHeight: '44px', paddingLeft: '14px', paddingRight: '70px' }}
                maxLength={128}
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

          <div>
            <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
              تأكيد كلمة المرور
            </label>
            <input
              type="password"
              autoComplete="new-password"
              className="scanner-input"
              style={{ direction: 'ltr', textAlign: 'left', minHeight: '44px', paddingLeft: '14px' }}
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          {error && (
            <div className="scanner-error" style={{ marginBottom: 0 }}>
              <AlertTriangleIcon size={16} color="var(--color-danger)" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div style={{ padding: '10px', background: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: '8px', color: '#16A34A', fontSize: '13px', fontWeight: 600 }}>
              {successMsg}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !email.trim() || !password}
            style={{ width: '100%', marginTop: 'var(--space-2)' }}
          >
            <span>{loading ? 'جاري التسجيل...' : 'إنشاء الحساب'}</span>
          </button>
        </form>

        <div style={{ marginTop: 'var(--space-6)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border)', textAlign: 'center', fontSize: 'var(--text-sm)' }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>لديك حساب بالفعل؟ </span>
          <button
            type="button"
            onClick={() => onNavigate('login')}
            style={{ background: 'none', border: 'none', color: 'var(--color-secondary)', fontWeight: 700, cursor: 'pointer' }}
          >
            تسجيل الدخول
          </button>
        </div>
      </div>
    </div>
  );
}
