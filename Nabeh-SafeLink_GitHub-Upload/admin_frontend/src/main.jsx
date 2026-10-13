import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import axios from 'axios';
import './style.css';

const api = axios.create({ baseURL: import.meta.env.VITE_ADMIN_API_URL || '/api/v1/admin', timeout: 20000 });
const tokenKey = 'nabeh_admin_access_token';
const refreshKey = 'nabeh_admin_refresh_token';
const getAccess = () => localStorage.getItem(tokenKey);

function App() {
  const [stage, setStage] = useState('login');
  const [form, setForm] = useState({ email: '', password: '', code: '' });
  const [challenge, setChallenge] = useState('');
  const [message, setMessage] = useState('');
  const [profile, setProfile] = useState(null);
  const [busy, setBusy] = useState(false);
  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const auth = (config = {}) => ({ ...config, headers: { ...(config.headers || {}), Authorization: `Bearer ${getAccess()}` } });
  async function login(e) {
    e.preventDefault(); setBusy(true); setMessage('');
    try {
      const { data } = await api.post('/auth/login', { email: form.email, password: form.password });
      if (data.status === '2FA_REQUIRED') { setChallenge(data.challenge_token); setStage('2fa'); }
      else if (data.status === '2FA_SETUP_REQUIRED') { setChallenge(data.setup_token); setStage('setup'); }
      else complete(data.data);
    } catch (error) { setMessage(error.response?.data?.detail || 'تعذر تسجيل الدخول'); }
    finally { setBusy(false); }
  }
  async function verify2fa(e) {
    e.preventDefault(); setBusy(true); setMessage('');
    try { const { data } = await api.post('/auth/2fa/verify', { code: form.code }, { headers: { Authorization: `Bearer ${challenge}` } }); complete(data.data); }
    catch (error) { setMessage(error.response?.data?.detail || 'رمز التحقق غير صحيح'); }
    finally { setBusy(false); }
  }
  async function setup2fa(e) {
    e.preventDefault(); setBusy(true); setMessage('');
    try {
      const { data } = await api.post('/auth/2fa/setup', {}, { headers: { Authorization: `Bearer ${challenge}` } });
      setMessage(`امسح QR في Google Authenticator. السر المؤقت: ${data.data.secret}`); setStage('confirm');
    } catch (error) { setMessage(error.response?.data?.detail || 'تعذر بدء إعداد 2FA'); }
    finally { setBusy(false); }
  }
  async function confirm2fa(e) {
    e.preventDefault(); setBusy(true); setMessage('');
    try { await api.post('/auth/2fa/confirm', { code: form.code }, { headers: { Authorization: `Bearer ${challenge}` } }); setMessage('تم تفعيل 2FA. سجّل الدخول مرة أخرى.'); setStage('login'); }
    catch (error) { setMessage(error.response?.data?.detail || 'رمز التحقق غير صحيح'); }
    finally { setBusy(false); }
  }
  async function loadProfile() { try { const { data } = await api.get('/auth/me', auth()); setProfile(data.data); } catch { logout(); } }
  function complete(data) { localStorage.setItem(tokenKey, data.access_token); localStorage.setItem(refreshKey, data.refresh_token); setStage('dashboard'); loadProfile(); }
  async function logout() { try { await api.post('/auth/logout', {}, auth()); } catch {} localStorage.removeItem(tokenKey); localStorage.removeItem(refreshKey); setProfile(null); setStage('login'); }
  if (stage === 'dashboard') return <main className="shell"><header><div><small>Nabeh SafeLink</small><h1>لوحة الإدارة</h1></div><button onClick={logout}>تسجيل الخروج</button></header><section className="card"><p className="eyebrow">الجلسة الإدارية</p><h2>{profile?.display_name || 'جارٍ التحميل...'}</h2><p>{profile?.email || ''}</p><span className="badge">{profile?.role || 'ADMIN'}</span><div className="grid"><a href="/users">إدارة المستخدمين</a><a href="/audit-logs">سجل التدقيق</a><a href="/sessions">الجلسات</a><a href="/statistics">الإحصائيات</a></div></section></main>;
  const submit = stage === 'login' ? login : stage === '2fa' ? verify2fa : stage === 'setup' ? setup2fa : confirm2fa;
  return <main className="shell"><section className="card auth"><div className="brand"><span className="mark">N</span><div><small>Nabeh SafeLink</small><h1>Admin Panel</h1></div></div><p className="eyebrow">منطقة الإدارة المحمية</p><h2>{stage === 'login' ? 'تسجيل دخول المسؤول' : stage === 'setup' ? 'إعداد المصادقة الثنائية' : 'التحقق من الهوية'}</h2><p className="muted">لا تستخدم هذه الصفحة بحسابات المستخدمين العادية.</p><form onSubmit={submit}>{stage === 'login' && <><label>البريد الإلكتروني<input name="email" type="email" autoComplete="username" value={form.email} onChange={change} required /></label><label>كلمة المرور<input name="password" type="password" autoComplete="current-password" value={form.password} onChange={change} required minLength="12" /></label></>}{stage !== 'login' && <label>رمز Authenticator<input name="code" inputMode="numeric" autoComplete="one-time-code" value={form.code} onChange={change} required minLength="6" maxLength="8" /></label>}<button className="primary" disabled={busy}>{busy ? 'جارٍ المعالجة...' : stage === 'login' ? 'دخول آمن' : stage === 'setup' ? 'بدء إعداد 2FA' : 'تأكيد'}</button></form>{message && <div className="notice">{message}</div>}</section></main>;
}

createRoot(document.getElementById('root')).render(<App />);
