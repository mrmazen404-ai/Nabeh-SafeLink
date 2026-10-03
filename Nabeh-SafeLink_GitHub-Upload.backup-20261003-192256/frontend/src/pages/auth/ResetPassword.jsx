import { useState, useEffect } from 'react';
import Logo from '../../components/Logo';
import { useAuth } from '../../context/AuthContext';
import { AlertTriangleIcon } from '../../components/Icons';

export default function ResetPassword({ onNavigate }) {
  const { resetPassword } = useAuth();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [recoveryToken, setRecoveryToken] = useState('');

  // Extract access_token from URL query string or hash if redirected
  useEffect(() => {
    const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    const queryParams = new URLSearchParams(window.location.search);
    const token = hashParams.get('access_token') || queryParams.get('access_token') || sessionStorage.getItem('nabeh_recovery_token') || '';
    setRecoveryToken(token);
    if (token) window.history.replaceState(null, '', window.location.pathname);
    else setError('رابط الاستعادة غير صالح أو منتهي الصلاحية. اطلب رابطاً جديداً.');
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!recoveryToken) {
      setError('رابط الاستعادة غير صالح أو منتهي الصلاحية. اطلب رابطاً جديداً.');
      return;
    }
    if (newPassword.length < 12) {
      setError('كلمة المرور يجب أن تتكون من 12 حرفاً على الأقل');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('كلمتا المرور غير متطابقتين');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await resetPassword(newPassword, recoveryToken);
      setRecoveryToken('');
      window.history.replaceState(null, '', '/');
      setSuccess(true);
      setTimeout(() => {
        onNavigate('login');
      }, 2500);
    } catch (err) {
      setError('تعذر تحديث كلمة المرور. قد يكون الرابط منتهي الصلاحية.');
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
          تعيين كلمة مرور جديدة
        </h1>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)', textAlign: 'center' }}>
              أدخل كلمة مرور من 12 حرفاً على الأقل للحفاظ على أمان حسابك
        </p>

        {success ? (
          <div style={{ textAlign: 'center', padding: '16px', background: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: '8px', color: '#16A34A', fontSize: '14px', fontWeight: 600 }}>
            تم تحديث كلمة المرور بنجاح! جاري تحويلك لصفحة الدخول...
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div>
              <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
                كلمة المرور الجديدة
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  className="scanner-input"
                  style={{ direction: 'ltr', textAlign: 'left', minHeight: '44px', paddingLeft: '14px', paddingRight: '70px' }}
                  maxLength={128}
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
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
                تأكيد كلمة المرور الجديدة
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

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !newPassword}
              style={{ width: '100%' }}
            >
              <span>{loading ? 'جاري التحديث...' : 'حفظ كلمة المرور الجديدة'}</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
