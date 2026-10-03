import { createContext, useContext, useEffect, useState } from 'react';
import api from '../services/api';
import { clearAccessToken, getAccessToken, setAccessToken } from '../services/authToken';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => getAccessToken());
  const [loading, setLoading] = useState(() => Boolean(getAccessToken()));
  const isGuest = !user || !token;

  const logout = () => {
    clearAccessToken();
    setUser(null);
    setToken(null);
    setLoading(false);
  };

  const checkAuth = async (candidateToken = getAccessToken()) => {
    if (!candidateToken) {
      logout();
      return null;
    }
    setLoading(true);
    try {
      const res = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${candidateToken}` },
      });
      if (!res.data?.success || !res.data?.data?.user_id) {
        logout();
        return null;
      }
      setUser(res.data.data);
      setToken(candidateToken);
      return res.data.data;
    } catch (error) {
      logout();
      throw error;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const currentToken = getAccessToken();
    if (currentToken) checkAuth(currentToken).catch(() => {});
    else setLoading(false);
    // The memory-only token can only be populated by this app's auth actions.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const accessToken = res.data?.data?.access_token;
    if (!res.data?.success || !accessToken) throw new Error('فشل تسجيل الدخول');
    setAccessToken(accessToken);
    setToken(accessToken);
    await checkAuth(accessToken);
    return res.data;
  };

  const register = async (email, password, displayName) => {
    const res = await api.post('/auth/register', { email, password, display_name: displayName });
    return res.data;
  };

  const forgotPassword = async (email) => {
    const res = await api.post('/auth/forgot-password', { email });
    return res.data;
  };

  const resetPassword = async (newPassword, recoveryToken) => {
    if (!recoveryToken) throw new Error('رمز استعادة كلمة المرور مفقود');
    const res = await api.post(
      '/auth/reset-password',
      { new_password: newPassword },
      { headers: { Authorization: `Bearer ${recoveryToken}` } },
    );
    sessionStorage.removeItem('nabeh_recovery_token');
    return res.data;
  };

  const verifyOtp = async (email, otpToken, type = 'signup') => {
    const res = await api.post('/auth/verify-otp', { email, token: otpToken, type });
    const accessToken = res.data?.data?.access_token;
    if (res.data?.success && accessToken && type === 'signup') {
      setAccessToken(accessToken);
      setToken(accessToken);
      await checkAuth(accessToken);
    } else if (res.data?.success && accessToken && type === 'recovery') {
      sessionStorage.setItem('nabeh_recovery_token', accessToken);
    }
    return res.data;
  };

  return (
    <AuthContext.Provider value={{ user, token, isGuest, loading, login, register, forgotPassword, resetPassword, verifyOtp, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
