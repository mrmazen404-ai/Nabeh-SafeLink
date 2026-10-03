import { useState } from 'react';
import Logo from '../../components/Logo';
import { useAuth } from '../../context/AuthContext';

export default function ForgotPassword({ onNavigate }) {
  const { forgotPassword } = useAuth();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;

    setLoading(true);
    try {
      const res = await forgotPassword(email.trim());
      setMessage(res.message || 'إذا كان البريد المسجل صحيحاً، فستصلك تعليمات إعادة ضبط كلمة المرور');
      setSubmitted(true);
    } catch (err) {
      setMessage('إذا كان البريد المسجل صحيحاً، فستصلك تعليمات إعادة ضبط كلمة المرور');
      setSubmitted(true);
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
          استعادة كلمة المرور
        </h1>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)', textAlign: 'center' }}>
          أدخل بريدك الإلكتروني ليصلك رابط إعادة ضبط كلمة المرور
        </p>

        {submitted ? (
          <div style={{ textAlign: 'center', padding: '16px', background: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: '8px', color: '#16A34A', fontSize: '14px', fontWeight: 600, marginBottom: 'var(--space-6)' }}>
            {message}
          </div>
        ) : (
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

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !email.trim()}
              style={{ width: '100%' }}
            >
              <span>{loading ? 'جاري الإرسال...' : 'إرسال التعليمات'}</span>
            </button>
          </form>
        )}

        <div style={{ marginTop: 'var(--space-6)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border)', textAlign: 'center' }}>
          <button
            type="button"
            onClick={() => onNavigate('login')}
            style={{ background: 'none', border: 'none', color: 'var(--color-secondary)', fontWeight: 700, cursor: 'pointer', fontSize: 'var(--text-sm)' }}
          >
            ← العودة لتسجيل الدخول
          </button>
        </div>
      </div>
    </div>
  );
}
