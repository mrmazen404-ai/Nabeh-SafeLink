import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import axios from 'axios';
import './style.css';

const api = axios.create({ baseURL: import.meta.env.VITE_ADMIN_API_URL || '/api/v1/admin', timeout: 20000 });
const accessKey = 'nabeh_admin_access_token';
const refreshKey = 'nabeh_admin_refresh_token';
const getAccess = () => sessionStorage.getItem(accessKey);
const clearTokens = () => { sessionStorage.removeItem(accessKey); localStorage.removeItem(refreshKey); };

async function refreshSession() {
  const refreshToken = localStorage.getItem(refreshKey);
  if (!refreshToken) throw new Error('No administrator refresh token');
  const { data } = await api.post('/auth/refresh', { refresh_token: refreshToken });
  sessionStorage.setItem(accessKey, data.data.access_token);
  localStorage.setItem(refreshKey, data.data.refresh_token);
  return data.data.access_token;
}

api.interceptors.request.use((config) => {
  const token = getAccess();
  if (token && !config.headers?.Authorization) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use((response) => response, async (error) => {
  const original = error.config;
  const authEndpoint = original?.url?.startsWith('/auth/');
  if (error.response?.status !== 401 || !original || original._retry || authEndpoint) return Promise.reject(error);
  original._retry = true;
  try {
    const token = await refreshSession();
    original.headers = { ...(original.headers || {}), Authorization: `Bearer ${token}` };
    return api(original);
  } catch {
    clearTokens();
    window.dispatchEvent(new Event('admin-session-expired'));
    return Promise.reject(error);
  }
});

const navItems = [
  { path: '/dashboard', label: 'الرئيسية', icon: '⌂', permission: 'dashboard.read' },
  { path: '/users', label: 'المستخدمون', icon: '◎', permission: 'users.read' },
  { path: '/scans', label: 'الفحوصات', icon: '⌁', permission: 'scans.read' },
  { path: '/audit-logs', label: 'سجل التدقيق', icon: '≡', permission: 'audit.read' },
  { path: '/sessions', label: 'الجلسات', icon: '◌', permission: 'sessions.read' },
  { path: '/statistics', label: 'الإحصائيات', icon: '▥', permission: 'dashboard.read' },
];

function currentPath() { return window.location.pathname || '/dashboard'; }

function useNavigation() {
  const [path, setPath] = useState(currentPath());
  useEffect(() => { const onPop = () => setPath(currentPath()); window.addEventListener('popstate', onPop); return () => window.removeEventListener('popstate', onPop); }, []);
  const go = (next) => { window.history.pushState({}, '', next); setPath(next); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  return { path, go };
}

function Login({ onComplete, initialMessage = '' }) {
  const [stage, setStage] = useState('login');
  const [form, setForm] = useState({ email: '', password: '', code: '' });
  const [challenge, setChallenge] = useState('');
  const [message, setMessage] = useState(initialMessage);
  const [busy, setBusy] = useState(false);
  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const submit = stage === 'login' ? login : stage === '2fa' ? verify2fa : stage === 'setup' ? setup2fa : confirm2fa;

  async function login(e) {
    e.preventDefault(); setBusy(true); setMessage('');
    try {
      const { data } = await api.post('/auth/login', { email: form.email, password: form.password });
      if (data.status === '2FA_REQUIRED') { setChallenge(data.challenge_token); setStage('2fa'); }
      else if (data.status === '2FA_SETUP_REQUIRED') { setChallenge(data.setup_token); setStage('setup'); }
      else onComplete(data.data);
    } catch (error) { setMessage(error.response?.data?.detail || 'تعذر تسجيل الدخول'); }
    finally { setBusy(false); }
  }
  async function verify2fa(e) {
    e.preventDefault(); setBusy(true); setMessage('');
    try { const { data } = await api.post('/auth/2fa/verify', { code: form.code }, { headers: { Authorization: `Bearer ${challenge}` } }); onComplete(data.data); }
    catch (error) { setMessage(error.response?.data?.detail || 'رمز التحقق غير صحيح'); }
    finally { setBusy(false); }
  }
  async function setup2fa(e) {
    e.preventDefault(); setBusy(true); setMessage('');
    try { const { data } = await api.post('/auth/2fa/setup', {}, { headers: { Authorization: `Bearer ${challenge}` } }); setMessage(`امسح QR في Google Authenticator. السر المؤقت: ${data.data.secret}`); setStage('confirm'); }
    catch (error) { setMessage(error.response?.data?.detail || 'تعذر بدء إعداد 2FA'); }
    finally { setBusy(false); }
  }
  async function confirm2fa(e) {
    e.preventDefault(); setBusy(true); setMessage('');
    try { await api.post('/auth/2fa/confirm', { code: form.code }, { headers: { Authorization: `Bearer ${challenge}` } }); setMessage('تم تفعيل 2FA. سجّل الدخول مرة أخرى.'); setStage('login'); }
    catch (error) { setMessage(error.response?.data?.detail || 'رمز التحقق غير صحيح'); }
    finally { setBusy(false); }
  }

  return <main className="auth-page"><section className="auth-card">
    <div className="brand"><span className="brand-mark">N</span><div><small>Nabeh SafeLink</small><h1>Admin Control</h1></div></div>
    <div className="eyebrow">منطقة الإدارة المحمية</div>
    <h2>{stage === 'login' ? 'تسجيل دخول المسؤول' : stage === 'setup' ? 'إعداد المصادقة الثنائية' : 'التحقق من الهوية'}</h2>
    <p className="muted">هذه المنطقة مخصصة لمسؤولي Nabeh SafeLink فقط.</p>
    <form onSubmit={submit}>
      {stage === 'login' && <><label>البريد الإلكتروني<input name="email" type="email" autoComplete="username" value={form.email} onChange={change} required /></label><label>كلمة المرور<input name="password" type="password" autoComplete="current-password" value={form.password} onChange={change} required minLength="12" /></label></>}
      {stage !== 'login' && <label>رمز Authenticator<input name="code" inputMode="numeric" autoComplete="one-time-code" value={form.code} onChange={change} required minLength="6" maxLength="8" /></label>}
      <button className="primary" disabled={busy}>{busy ? 'جارٍ التحقق...' : stage === 'login' ? 'دخول آمن' : stage === 'setup' ? 'بدء إعداد 2FA' : 'تأكيد الهوية'}</button>
    </form>
    {message && <div className="notice">{message}</div>}
    <div className="auth-foot"><span className="status-dot" /> الاتصال الإداري مشفر ومراقب</div>
  </section></main>;
}

function Shell({ profile, path, go, onLogout, children }) {
  const [dark, setDark] = useState(document.documentElement.dataset.theme === 'dark');
  const [menuOpen, setMenuOpen] = useState(false);
  const allowed = navItems.filter((item) => !profile?.permissions || profile.permissions.includes(item.permission));
  const active = allowed.find((item) => path === item.path) || allowed[0];
  const toggleTheme = () => { const next = !dark; setDark(next); document.documentElement.dataset.theme = next ? 'dark' : 'light'; };
  const toggleLanguage = () => { const next = document.documentElement.dir === 'rtl' ? 'ltr' : 'rtl'; document.documentElement.dir = next; document.documentElement.lang = next === 'rtl' ? 'ar' : 'en'; };
  const navigate = (next) => { go(next); setMenuOpen(false); };
  return <div className="admin-app">
    <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
      <div className="sidebar-brand"><span className="brand-mark">N</span><div><strong>Nabeh</strong><small>SafeLink Admin</small></div></div>
      <div className="workspace"><span className="status-dot" /> بيئة الإدارة <strong>نشطة</strong></div>
      <nav className="side-nav" aria-label="التنقل الإداري">{allowed.map((item) => <button key={item.path} className={active?.path === item.path ? 'active' : ''} onClick={() => navigate(item.path)}><span>{item.icon}</span>{item.label}</button>)}</nav>
      <div className="sidebar-footer"><button onClick={() => navigate('/profile')}>الملف الإداري</button><button className="danger-link" onClick={onLogout}>تسجيل الخروج</button></div>
    </aside>
    {menuOpen && <button className="scrim" aria-label="إغلاق القائمة" onClick={() => setMenuOpen(false)} />}
    <section className="main-area">
      <header className="topbar"><button className="menu-button" onClick={() => setMenuOpen(!menuOpen)} aria-label="فتح القائمة">☰</button><div><p className="top-kicker">Nabeh SafeLink / Admin</p><h1>{active?.label || 'لوحة التحكم'}</h1></div><div className="top-actions"><button className="icon-button" onClick={toggleLanguage} aria-label="تغيير اللغة">ع / E</button><button className="icon-button" onClick={toggleTheme} aria-label="تبديل الثيم">{dark ? '☀' : '☾'}</button><div className="admin-avatar" title={profile?.email}>{(profile?.display_name || 'A').slice(0, 1)}</div></div></header>
      <main className="content">{children}</main>
      <nav className="bottom-nav" aria-label="التنقل السريع">{allowed.slice(0, 4).map((item) => <button key={item.path} className={active?.path === item.path ? 'active' : ''} onClick={() => navigate(item.path)}><span>{item.icon}</span>{item.label}</button>)}</nav>
    </section>
  </div>;
}

function StatCard({ label, value, tone = '' }) { return <article className={`stat-card ${tone}`}><span>{label}</span><strong>{value}</strong><small>بيانات محمية</small></article>; }
function Dashboard({ profile, go }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => { api.get('/dashboard/overview?range_days=30').then(({ data }) => setMetrics(data.data)).catch((e) => setError(e.response?.data?.detail || 'تعذر تحميل مؤشرات Dashboard')).finally(() => setLoading(false)); }, []);
  if (loading) return <div className="loading-state dashboard-loading"><div className="loader" /> جارٍ تحميل المؤشرات من Supabase...</div>;
  if (error) return <section className="empty-state"><div className="empty-icon">!</div><span className="eyebrow">فشل مصدر البيانات</span><h2>تعذر تحميل Dashboard</h2><p>{error}</p><small>لم يتم عرض أرقام بديلة أو وهمية.</small></section>;
  const users = metrics.users; const scans = metrics.scans; const support = metrics.support; const feedback = metrics.feedback;
  return <div className="page-stack"><section className="hero-card"><div><span className="eyebrow">مركز التحكم الآمن · آخر {metrics.range_days} يوماً</span><h2>مرحباً، {profile?.display_name || 'مسؤول النظام'}</h2><p>الأرقام التالية مقروءة مباشرة من جداول Supabase التشغيلية.</p></div><div className="hero-shield">✓</div></section><section className="stats-grid"><StatCard label="المستخدمون" value={users.total} /><StatCard label="الفحوصات" value={scans.total} /><StatCard label="خطرة" value={scans.dangerous} tone={scans.dangerous ? 'warning' : 'success'} /><StatCard label="دعم مفتوح" value={support.open} /></section><section className="panel-grid"><article className="panel"><div className="panel-heading"><div><span className="eyebrow">توزيع نتائج الفحص</span><h3>نتائج حقيقية</h3></div><span className="count-badge">30 يوم</span></div><div className="metric-list"><div><span>آمنة</span><strong>{scans.safe}</strong></div><div><span>مشبوهة</span><strong>{scans.suspicious}</strong></div><div><span>خطرة</span><strong className="danger-number">{scans.dangerous}</strong></div><div><span>تحتاج مراجعة</span><strong>{scans.needs_review}</strong></div></div></article><article className="panel security-panel"><span className="eyebrow">التشغيل</span><h3>{scans.processing} فحص قيد المعالجة</h3><p>{feedback.new} بلاغ جديد و{support.urgent_open} طلب دعم عاجل مفتوح.</p><span className="security-badge"><i /> {metrics.audit.period_events} حدث تدقيق خلال الفترة</span></article></section><article className="panel"><div className="panel-heading"><div><span className="eyebrow">إجراءات سريعة</span><h3>الوصول التشغيلي</h3></div></div><div className="quick-actions"><button onClick={() => go('/users')}>استعراض المستخدمين <span>←</span></button><button onClick={() => go('/scans')}>مراجعة الفحوصات <span>←</span></button><button onClick={() => go('/audit-logs')}>فتح سجل التدقيق <span>←</span></button></div></article></div>;
}

function ComingSoon({ title, description, permission }) { return <section className="empty-state"><div className="empty-icon">◌</div><span className="eyebrow">وحدة محمية</span><h2>{title}</h2><p>{description}</p><code>{permission}</code><small>سيتم توصيل هذه الوحدة بـ Admin API في المرحلة التالية.</small></section>; }
function SessionsPage() { const [rows, setRows] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState(''); useEffect(() => { api.get('/sessions').then(({ data }) => setRows(data.data || [])).catch((e) => setError(e.response?.data?.detail || 'تعذر تحميل الجلسات')).finally(() => setLoading(false)); }, []); return <section className="panel table-panel"><div className="panel-heading"><div><span className="eyebrow">جلسات Admin</span><h2>الجلسات النشطة والسابقة</h2></div><span className="count-badge">{rows.length}</span></div>{loading ? <div className="loading-state">جارٍ تحميل الجلسات...</div> : error ? <div className="notice">{error}</div> : rows.length === 0 ? <div className="inline-empty">لا توجد جلسات مسجلة.</div> : <div className="table-wrap"><table><thead><tr><th>تاريخ الإنشاء</th><th>آخر استخدام</th><th>الانتهاء</th><th>الحالة</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><td>{new Date(row.created_at).toLocaleString('ar')}</td><td>{row.last_used_at ? new Date(row.last_used_at).toLocaleString('ar') : '—'}</td><td>{new Date(row.expires_at).toLocaleDateString('ar')}</td><td><span className={row.revoked_at ? 'table-status muted-status' : 'table-status'}>{row.revoked_at ? 'ملغاة' : 'نشطة'}</span></td></tr>)}</tbody></table></div>}</section>; }
function AuditPage() {
  const [rows, setRows] = useState([]); const [meta, setMeta] = useState({ total: 0 }); const [security, setSecurity] = useState(null); const [selected, setSelected] = useState(null); const [action, setAction] = useState(''); const [resource, setResource] = useState(''); const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [offset, setOffset] = useState(0); const limit = 25;
  const load = () => { setLoading(true); setError(''); const params = { limit, offset }; if (action.trim()) params.action = action.trim(); if (resource.trim()) params.resource_type = resource.trim(); api.get('/audit-logs', { params }).then(({ data }) => { setRows(data.data || []); setMeta(data.meta || { total: 0 }); }).catch((e) => setError(e.response?.data?.detail || 'تعذر تحميل السجل')).finally(() => setLoading(false)); };
  useEffect(() => { load(); api.get('/security/overview?range_days=7').then(({ data }) => setSecurity(data.data)).catch(() => {}); }, [offset]);
  const filter = (e) => { e.preventDefault(); setOffset(0); load(); };
  const openDetails = async (id) => { try { const { data } = await api.get(`/audit-logs/${id}`); setSelected(data.data); } catch (e) { setError(e.response?.data?.detail || 'تعذر تحميل تفاصيل الحدث'); } };
  return <div className="page-stack">{security && <section className="security-grid"><article className={`security-stat ${security.risk_level.toLowerCase()}`}><span>مستوى الخطر</span><strong>{security.risk_level}</strong><small>آخر {security.range_days} أيام</small></article><article className="security-stat"><span>محاولات فاشلة</span><strong>{security.login_attempts.failed}</strong><small>من {security.login_attempts.total} محاولة</small></article><article className="security-stat"><span>محاولات محجوبة</span><strong>{security.login_attempts.rate_limited}</strong><small>Rate limited</small></article><article className="security-stat"><span>جلسات نشطة</span><strong>{security.sessions.active}</strong><small>{security.admins.suspended} مسؤول موقوف</small></article></section>}<section className="panel table-panel"><div className="panel-heading"><div><span className="eyebrow">Audit Center</span><h2>سجل التدقيق الإداري</h2></div><span className="count-badge">{meta.total || 0}</span></div><form className="filters" onSubmit={filter}><input value={action} onChange={(e) => setAction(e.target.value)} placeholder="الإجراء مثل ADMIN_LOGIN" aria-label="فلترة الإجراء" /><input value={resource} onChange={(e) => setResource(e.target.value)} placeholder="نوع المورد" aria-label="فلترة المورد" /><button className="filter-button">تصفية</button></form>{loading ? <div className="loading-state">جارٍ تحميل سجل التدقيق...</div> : error ? <div className="notice">{error}</div> : rows.length === 0 ? <div className="inline-empty">لا توجد أحداث مطابقة.</div> : <div className="table-wrap"><table><thead><tr><th>الإجراء</th><th>المورد</th><th>المعرّف</th><th>التاريخ</th><th>تفاصيل</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><td><strong>{row.action}</strong></td><td>{row.resource_type || '—'}</td><td className="mono">{row.resource_id || '—'}</td><td>{new Date(row.created_at).toLocaleString('ar')}</td><td><button className="row-action" onClick={() => openDetails(row.id)}>عرض</button></td></tr>)}</tbody></table></div>}<div className="pagination"><button disabled={offset === 0 || loading} onClick={() => setOffset(Math.max(0, offset - limit))}>السابق</button><span>{meta.total ? `${offset + 1}–${Math.min(offset + limit, meta.total)} من ${meta.total}` : '0 حدث'}</span><button disabled={offset + limit >= (meta.total || 0) || loading} onClick={() => setOffset(offset + limit)}>التالي</button></div></section>{selected && <section className="panel detail-panel"><div className="panel-heading"><div><span className="eyebrow">تفاصيل مقنّعة</span><h3>{selected.action}</h3></div><button className="icon-button" onClick={() => setSelected(null)}>إغلاق</button></div><div className="detail-grid"><div><span>المورد</span><strong>{selected.resource_type || '—'}</strong></div><div><span>التاريخ</span><strong>{new Date(selected.created_at).toLocaleString('ar')}</strong></div></div><pre className="audit-json">{JSON.stringify({ before_data: selected.before_data, after_data: selected.after_data, metadata_masked: selected.metadata_masked }, null, 2)}</pre></section>}</div>;
}
function UsersPage() {
  const [rows, setRows] = useState([]); const [meta, setMeta] = useState({ total: 0 }); const [search, setSearch] = useState(''); const [status, setStatus] = useState(''); const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [offset, setOffset] = useState(0); const limit = 25;
  const load = () => { setLoading(true); setError(''); const params = { limit, offset }; if (search.trim()) params.search = search.trim(); if (status) params.status = status; api.get('/users', { params }).then(({ data }) => { setRows(data.data || []); setMeta(data.meta || { total: 0 }); }).catch((e) => setError(e.response?.data?.detail || 'تعذر تحميل المستخدمين')).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, [offset, status]);
  const submitSearch = (e) => { e.preventDefault(); setOffset(0); load(); };
  const changeStatus = async (user) => { const next = user.status === 'SUSPENDED' ? 'ACTIVE' : 'SUSPENDED'; const reason = window.prompt(next === 'SUSPENDED' ? 'سبب إيقاف المستخدم:' : 'سبب إعادة تفعيل المستخدم:', 'مراجعة إدارية'); if (!reason?.trim()) return; try { await api.patch(`/users/${user.id}/status`, { status: next, reason: reason.trim() }); load(); } catch (e) { setError(e.response?.data?.detail || 'تعذر تغيير حالة المستخدم'); } };
  return <section className="panel table-panel"><div className="panel-heading"><div><span className="eyebrow">إدارة المستخدمين</span><h2>المستخدمون</h2></div><span className="count-badge">{meta.total || 0}</span></div><form className="filters" onSubmit={submitSearch}><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="بحث بالبريد أو الاسم" aria-label="بحث بالمستخدمين" /><select value={status} onChange={(e) => { setStatus(e.target.value); setOffset(0); }}><option value="">كل الحالات</option><option value="ACTIVE">نشط</option><option value="SUSPENDED">موقوف</option><option value="DELETED">محذوف</option></select><button className="filter-button">بحث</button></form>{loading ? <div className="loading-state">جارٍ تحميل المستخدمين...</div> : error ? <div className="notice">{error}</div> : rows.length === 0 ? <div className="inline-empty">لا توجد نتائج مطابقة.</div> : <div className="table-wrap"><table><thead><tr><th>المستخدم</th><th>الدور</th><th>الحالة</th><th>آخر دخول</th><th>إجراء</th></tr></thead><tbody>{rows.map((user) => <tr key={user.id}><td><strong>{user.display_name}</strong><small className="table-sub">{user.email}</small></td><td>{user.role}</td><td><span className={`table-status ${user.status !== 'ACTIVE' ? 'muted-status' : ''}`}>{user.status}</span></td><td>{user.last_login_at ? new Date(user.last_login_at).toLocaleDateString('ar') : '—'}</td><td>{user.status !== 'DELETED' && <button className="row-action" onClick={() => changeStatus(user)}>{user.status === 'SUSPENDED' ? 'تفعيل' : 'إيقاف'}</button>}</td></tr>)}</tbody></table></div>}<div className="pagination"><button disabled={offset === 0 || loading} onClick={() => setOffset(Math.max(0, offset - limit))}>السابق</button><span>{meta.total ? `${offset + 1}–${Math.min(offset + limit, meta.total)} من ${meta.total}` : '0 نتيجة'}</span><button disabled={offset + limit >= (meta.total || 0) || loading} onClick={() => setOffset(offset + limit)}>التالي</button></div></section>;
}

function ProtectedPage({ profile, path, go }) {
  if (path === '/dashboard' || path === '/') return <Dashboard profile={profile} go={go} />;
  if (path === '/sessions') return <SessionsPage />;
  if (path === '/audit-logs') return <AuditPage />;
  if (path === '/users') return <UsersPage />;
  if (path === '/scans') return <ComingSoon title="إدارة الفحوصات" description="وحدة الفحوصات ستعرض نتائج الفحص والإشارات دون كشف البيانات الحساسة افتراضياً." permission="scans.read" />;
  if (path === '/statistics') return <ComingSoon title="الإحصائيات" description="سيتم توصيل مؤشرات المنصة واستعلامات الإحصائيات في المرحلة التالية." permission="dashboard.read" />;
  if (path === '/profile') return <ComingSoon title="الملف الإداري" description="إدارة بيانات المسؤول وطرق المصادقة والجلسات ستضاف ضمن وحدة Admin Management." permission="admins.read" />;
  return <ComingSoon title="الصفحة غير موجودة" description="المسار المطلوب غير متاح في لوحة التحكم." permission="—" />;
}

function App() {
  const { path, go } = useNavigation();
  const [stage, setStage] = useState(getAccess() && localStorage.getItem(refreshKey) ? 'loading' : 'login');
  const [profile, setProfile] = useState(null);
  const [initialMessage, setInitialMessage] = useState('');
  const loadProfile = async () => { try { const { data } = await api.get('/auth/me', { headers: { Authorization: `Bearer ${getAccess()}` } }); setProfile(data.data); setStage('shell'); } catch { clearTokens(); setStage('login'); setInitialMessage('انتهت جلسة الإدارة. يرجى تسجيل الدخول من جديد.'); } };
  useEffect(() => { const expired = () => { clearTokens(); setProfile(null); setStage('login'); setInitialMessage('انتهت جلسة الإدارة. يرجى تسجيل الدخول من جديد.'); }; window.addEventListener('admin-session-expired', expired); if (stage === 'loading') loadProfile(); return () => window.removeEventListener('admin-session-expired', expired); }, [stage]);
  const complete = (data) => { sessionStorage.setItem(accessKey, data.access_token); localStorage.setItem(refreshKey, data.refresh_token); setInitialMessage(''); loadProfile(); };
  const logout = async () => { try { if (getAccess()) await api.post('/auth/logout', {}, { headers: { Authorization: `Bearer ${getAccess()}` } }); } catch {} clearTokens(); setProfile(null); setStage('login'); go('/'); };
  const title = useMemo(() => stage === 'shell' ? 'Admin Shell' : 'Admin Login', [stage]);
  useEffect(() => { document.title = `Nabeh ${title}`; }, [title]);
  if (stage === 'loading') return <main className="loading-page"><div className="loader" /><p>جارٍ تأمين جلسة الإدارة...</p></main>;
  if (stage === 'login') return <Login onComplete={complete} initialMessage={initialMessage} />;
  return <Shell profile={profile} path={path} go={go} onLogout={logout}><ProtectedPage profile={profile} path={path} go={go} /></Shell>;
}

createRoot(document.getElementById('root')).render(<App />);
