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
import { useLanguage } from '../context/LanguageContext';

const STATUS_CFG = {
  SAFE: { icon: CheckCircleIcon, className: 'recent-safe' },
  SUSPICIOUS: { icon: AlertTriangleIcon, className: 'recent-suspicious' },
  DANGEROUS: { icon: XCircleIcon, className: 'recent-dangerous' },
  UNKNOWN: { icon: HelpCircleIcon, className: 'recent-unknown' },
};

export default function Scanner({ initialUrl = '', onClearInitial, activeTab, setActiveTab, isGuest = true, onNavigateAuth }) {
  const { t, lang, dir } = useLanguage();
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
      setError(t('scanner.errEmptyInput'));
      return;
    }

    if (loading) return;

    setError('');
    setLoading(true);
    setResult(null);

    try {
      const response = await scanURL(textToScan.trim(), lang, isGuest, scanType);
      if (response && response.success) {
        setResult(response.data);
        if (!isGuest) fetchScans();
      } else {
        setError(t('scanner.errScanFailed'));
      }
    } catch (err) {
      setError(t('scanner.errServerConnection'));
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
      setError(t('scanner.errPaste'));
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
    return <LoadingScreen url={url} scanType={scanType} />;
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
    <div className="scanner-page" dir={dir}>
      <Header activeTab={activeTab} setActiveTab={setActiveTab} onNavigateAuth={onNavigateAuth} />

      <main className="page-container">
        {/* Guest Mode Privacy Notice (Strict PRD Compliance) */}
        {isGuest && (
          <div className="scanner-guest-notice">
            <InfoIcon size={18} color="#16A34A" />
            <span>
              <strong>{t('scanner.guestTitle')}</strong> {t('scanner.guestDesc')}
              <br />
              <small>{t('scanner.guestPrivacy')}</small>
            </span>
          </div>
        )}

        {/* Desktop 2-Column Grid */}
        <div className="scanner-desktop-grid">
          {/* Main Input Panel */}
          <div>
            {/* Toggle Mode URL vs TEXT */}
            <div className="scanner-toggle-bar">
              <button
                type="button"
                className={`scanner-toggle-btn ${scanType === 'URL' ? 'active' : ''}`}
                onClick={() => setScanType('URL')}
              >
                <LinkIcon size={16} color="currentColor" />
                <span>{t('scanner.tabUrl')}</span>
              </button>
              <button
                type="button"
                className={`scanner-toggle-btn ${scanType === 'TEXT' ? 'active' : ''}`}
                onClick={() => setScanType('TEXT')}
              >
                <span>{t('scanner.tabText')}</span>
              </button>
            </div>
            <div className="scanner-input-card">
              <div className="scanner-hero-row">
                <div className="scanner-hero-mark" aria-hidden="true">
                  <span className="scanner-hero-shield"><CheckCircleIcon size={22} color="#FFFFFF" /></span>
                </div>
                <div className="scanner-hero-copy">
                  <span className="scanner-kicker">{dir === 'rtl' ? 'مركز نابح للحماية الذكية' : 'NABEH SECURE WORKSPACE'}</span>
                  <span className="scanner-live-status"><i />{dir === 'rtl' ? 'حماية نشطة ومراقبة فورية' : 'Live protection enabled'}</span>
                </div>
              </div>
              <h1 className="scanner-title">{t('scanner.pageTitle')}</h1>
              <p className="scanner-subtitle">
                {scanType === 'URL'
                  ? t('scanner.subUrl')
                  : t('scanner.subText')}
              </p>
              <div className="scanner-trust-row" aria-label={dir === 'rtl' ? 'مزايا الفحص' : 'Scan capabilities'}>
                <span><CheckCircleIcon size={14} />{dir === 'rtl' ? 'تحليل بالذكاء الاصطناعي' : 'AI analysis'}</span>
                <span><CheckCircleIcon size={14} />{dir === 'rtl' ? 'فحص متعدد المصادر' : 'Multi-source scan'}</span>
                <span><CheckCircleIcon size={14} />{dir === 'rtl' ? 'خصوصية أولاً' : 'Privacy first'}</span>
              </div>

              <div className="scanner-input-wrapper">
                <span className="scanner-input-icon">
                  <LinkIcon size={18} color="var(--color-primary)" />
                </span>
                <input
                  ref={inputRef}
                  type="text"
                  className="scanner-input"
                  placeholder={scanType === 'URL' ? t('scanner.placeholderUrl') : t('scanner.placeholderText')}
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
                    title={t('scanner.clear')}
                    type="button"
                  >
                    <span>{t('scanner.clear')}</span>
                  </button>
                ) : (
                  <button
                    className="input-action-btn paste-btn"
                    onClick={handlePaste}
                    title={t('scanner.paste')}
                    type="button"
                  >
                    <ClipboardIcon size={14} color="currentColor" />
                    <span>{t('scanner.paste')}</span>
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
                <span>{loading ? t('scanner.scanningBtn') : t('scanner.startBtn')}</span>
              </button>
            </div>
          </div>

          {/* Registered-account history only; guest scans are never listed here. */}
          {!isGuest && (
          <section className="recent-section" aria-label={t('scanner.recentScansTitle')}>
            <div className="recent-header">
              <h2 className="recent-title">{t('scanner.recentScansTitle')}</h2>
              <span className="recent-count">{t('scanner.recentCount', { count: recentScans.length })}</span>
            </div>

            <div className="recent-list">
              {recentScans.length === 0 ? <p role="status">{t('scanner.noRecentScans')}</p> : recentScans.map((scan, idx) => {
                const statusKey = scan.classification || 'SAFE';
                const cfg = STATUS_CFG[statusKey] || STATUS_CFG.UNKNOWN;
                const statusLabel = statusKey === 'SAFE' ? t('result.safeLabelAr') : statusKey === 'SUSPICIOUS' ? t('result.suspiciousLabelAr') : statusKey === 'DANGEROUS' ? t('result.dangerousLabelAr') : t('result.unknownLabelAr');
                const StatusSvg = cfg.icon;
                const displayUrl = scan.input_value_masked || scan.url || t('home.scannedUrl');

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
                        {statusLabel} • {t('scanner.savedScan')}
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
