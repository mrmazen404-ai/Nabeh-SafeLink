import { useState, useEffect, useRef } from 'react';
import Header from '../components/Header';
import { scanURL, getScans } from '../services/api';
import LoadingScreen from '../components/LoadingScreen';
import ResultScreen from '../components/ResultScreen';
import {
  LinkIcon,
  SearchIcon,
  ClipboardIcon,
  CheckCircleIcon,
  AlertTriangleIcon,
  XCircleIcon,
  HelpCircleIcon,
  InfoIcon
} from '../components/Icons';
import '../styles/scanner.css';

const STATUS_CFG = {
  SAFE: { icon: CheckCircleIcon, className: 'recent-safe', label: 'آمن' },
  SUSPICIOUS: { icon: AlertTriangleIcon, className: 'recent-suspicious', label: 'مشبوه' },
  DANGEROUS: { icon: XCircleIcon, className: 'recent-dangerous', label: 'خطر' },
  UNKNOWN: { icon: HelpCircleIcon, className: 'recent-unknown', label: 'غير معروف' },
};

export default function Scanner({ initialUrl = '', onClearInitial, activeTab, setActiveTab, isGuest = true, onNavigateAuth }) {
  const [url, setUrl] = useState(initialUrl);
  const [scanType, setScanType] = useState('URL');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [recentScans, setRecentScans] = useState([]);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isGuest) {
      setRecentScans([]);
      setResult(null);
      setUrl('');
      setError('');
    } else {
      fetchScans();
    }
    if (initialUrl) {
      setUrl(initialUrl);
      handleScan(initialUrl);
      if (onClearInitial) onClearInitial();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialUrl, isGuest]);

  const fetchScans = async () => {
    try {
      const res = await getScans();
      setRecentScans(res && res.success && Array.isArray(res.data) ? res.data.slice(0, 5) : []);
    } catch (e) {
      setRecentScans([]);
    }
  };

  const handleScan = async (targetUrl = url) => {
    const textToScan = targetUrl || url;
    if (!textToScan || !textToScan.trim()) {
      setError('الرجاء إدخال رابط أو نص صحيح للتحقق منه');
      return;
    }

    if (loading) return;

    setError('');
    setLoading(true);
    setResult(null);

    try {
      const response = await scanURL(textToScan.trim(), 'ar', isGuest, scanType);
      if (response && response.success) {
        setResult(response.data);
        if (!isGuest) fetchScans();
      } else {
        setError('حدث خطأ أثناء الفحص، حاول مرة أخرى');
      }
    } catch (err) {
      setError('تعذر الاتصال بالخادم. تأكد من تشغيل خادم FastAPI Backend.');
    } finally {
      setLoading(false);
    }
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text);
        setError('');
        if (inputRef.current) inputRef.current.focus();
      }
    } catch (e) {
      setError('تعذر القراءة من المحافظة تلقائياً');
    }
  };

  const handleClear = () => {
    setUrl('');
    setError('');
    if (inputRef.current) inputRef.current.focus();
  };

  const handleReset = () => {
    setUrl('');
    setResult(null);
    setError('');
  };

  if (loading) {
    return <LoadingScreen url={url} />;
  }

  if (result) {
    return (
      <ResultScreen
        result={result}
        onReset={handleReset}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isGuest={isGuest}
        onNavigateAuth={onNavigateAuth}
      />
    );
  }

  return (
    <div style={{ minHeight: '100dvh', background: 'var(--color-bg-subtle)' }}>
      <Header activeTab={activeTab} setActiveTab={setActiveTab} onNavigateAuth={onNavigateAuth} />

      <main className="page-container">
        {/* Guest Mode Privacy Notice (Strict PRD Compliance) */}
        {isGuest && (
          <div
            style={{
              padding: '12px 16px',
              background: '#F0FDF4',
              border: '1px solid #BBF7D0',
              borderRadius: 'var(--radius-md)',
              marginBottom: 'var(--space-4)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontSize: '13px',
              color: '#16A34A',
              fontWeight: 500
            }}
          >
            <InfoIcon size={18} color="#16A34A" />
            <span>
              <strong>فحص كضيف:</strong> يمكنك فحص رابط أو رسالة وعرض النتيجة الحالية دون الحاجة لحساب. لا تُحفظ نتائج وضع الضيف في قاعدة البيانات ولا تظهر كسجل.
            </span>
          </div>
        )}

        {/* Desktop 2-Column Grid */}
        <div className="scanner-desktop-grid">
          {/* Main Input Panel */}
          <div>
            {/* Toggle Mode URL vs TEXT */}
            <div style={{ display: 'flex', background: 'var(--color-bg)', padding: '4px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', marginBottom: 'var(--space-4)' }}>
              <button
                type="button"
                onClick={() => setScanType('URL')}
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  background: scanType === 'URL' ? 'var(--color-primary)' : 'transparent',
                  color: scanType === 'URL' ? '#FFFFFF' : 'var(--color-text-secondary)',
                  fontWeight: 600,
                  fontSize: 'var(--text-sm)',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px'
                }}
              >
                <LinkIcon size={16} color={scanType === 'URL' ? '#FFFFFF' : 'var(--color-text-secondary)'} />
                <span>فحص رابط (URL)</span>
              </button>
              <button
                type="button"
                onClick={() => setScanType('TEXT')}
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  background: scanType === 'TEXT' ? 'var(--color-primary)' : 'transparent',
                  color: scanType === 'TEXT' ? '#FFFFFF' : 'var(--color-text-secondary)',
                  fontWeight: 600,
                  fontSize: 'var(--text-sm)',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px'
                }}
              >
                <span>فحص نص / رسالة (SMS)</span>
              </button>
            </div>

            <div className="scanner-input-card">
              <h1 className="scanner-title">فحص وكشف التهديدات</h1>
              <p className="scanner-subtitle">
                {scanType === 'URL'
                  ? 'ضع الرابط المطلوب تحليله للكشف عن محاولات التصيد والروابط الخبيثة'
                  : 'أدخل نص الرسالة المشبوهة أو البريد الإلكتروني لفحص مؤشرات الاحتيال'}
              </p>

              <div className="scanner-input-wrapper">
                <span className="scanner-input-icon">
                  <LinkIcon size={18} color="var(--color-primary)" />
                </span>
                <input
                  ref={inputRef}
                  type="text"
                  className="scanner-input"
                  placeholder={scanType === 'URL' ? 'ضع الرابط هنا... e.g. https://example.com' : 'ضع نص الرسالة هنا...'}
                  value={url}
                  onChange={(e) => {
                    setUrl(e.target.value);
                    if (error) setError('');
                  }}
                  onKeyDown={(e) => e.key === 'Enter' && handleScan()}
                  dir="ltr"
                />
                {url ? (
                  <button
                    className="input-action-btn clear-btn"
                    onClick={handleClear}
                    title="مسح الخانة"
                    type="button"
                  >
                    <span>مسح</span>
                  </button>
                ) : (
                  <button
                    className="input-action-btn paste-btn"
                    onClick={handlePaste}
                    title="لصق من الحافظة"
                    type="button"
                  >
                    <ClipboardIcon size={14} color="currentColor" />
                    <span>لصق</span>
                  </button>
                )}
              </div>

              {error && (
                <div className="scanner-error">
                  <AlertTriangleIcon size={16} color="var(--color-danger)" />
                  <span>{error}</span>
                </div>
              )}

              <button
                className="btn btn-primary scanner-button"
                onClick={() => handleScan()}
                disabled={!url.trim() || loading}
                type="button"
              >
                <SearchIcon size={18} color="#FFFFFF" />
                <span>{loading ? 'جاري الفحص...' : 'بدء الفحص الآمن'}</span>
              </button>
            </div>
          </div>

          {/* Registered-account history only; guest scans are never listed here. */}
          {!isGuest && (
          <section className="recent-section" aria-label="سجل المستخدم المسجل">
            <div className="recent-header">
              <h2 className="recent-title">آخر الفحوصات المحفوظة</h2>
              <span className="recent-count">{recentScans.length} فحوصات</span>
            </div>

            <div className="recent-list">
              {recentScans.length === 0 ? <p role="status">لا توجد فحوصات محفوظة بعد.</p> : recentScans.map((scan, idx) => {
                const statusKey = scan.classification || 'SAFE';
                const cfg = STATUS_CFG[statusKey] || STATUS_CFG.UNKNOWN;
                const StatusSvg = cfg.icon;
                const displayUrl = scan.input_value_masked || scan.url || 'رابط مفحوص';

                return (
                  <div
                    className="recent-item"
                    key={scan.id || idx}
                  >
                    <span className={`recent-icon ${cfg.className}`}>
                      <StatusSvg size={18} color="currentColor" />
                    </span>
                    <div className="recent-info">
                      <span className="recent-url" dir="ltr">
                        {displayUrl}
                      </span>
                      <span className="recent-meta">
                        {cfg.label} • فحص محفوظ
                      </span>
                    </div>
                    <span className="recent-arrow">←</span>
                  </div>
                );
              })}
            </div>
          </section>
          )}
        </div>
      </main>

      <style>{`
        .scanner-desktop-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: var(--space-6);
        }

        @media (min-width: 900px) {
          .scanner-desktop-grid {
            grid-template-columns: 65% 35%;
          }
        }
      `}</style>
    </div>
  );
}
