import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { compareScans, getScans } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import './advanced-pages.css';

export default function Comparison({ activeTab, setActiveTab, onNavigateAuth }) {
  const { dir, t, lang } = useLanguage();
  const [searchParams] = useSearchParams();
  const [scans, setScans] = useState([]);
  const [selected, setSelected] = useState(searchParams.get('ids')?.split(',').filter(Boolean) || []);
  const [comparison, setComparison] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getScans()
      .then((res) => setScans(res.data || []))
      .catch(() => setError(t('comparison.loadError')))
      .finally(() => setLoading(false));
  }, [t]);

  const toggle = (id) =>
    setSelected((items) =>
      items.includes(id) ? items.filter((item) => item !== id) : items.length < 4 ? [...items, id] : items
    );

  const runCompare = async () => {
    if (selected.length < 2) {
      setError(t('comparison.minError'));
      return;
    }
    setError('');
    try {
      const result = await compareScans(selected);
      setComparison(result.data || []);
    } catch (err) {
      setError(err?.response?.data?.detail || t('comparison.failError'));
    }
  };

  const rows = comparison.length
    ? comparison
    : scans.filter((scan) => selected.includes(scan.id)).sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

  const getClassLabel = (cls) => t(`scanDetails.labels.${cls}`) || cls || t('scanDetails.labels.UNKNOWN');

  return (
    <div className="advanced-page" dir={dir}>
      <Header activeTab={activeTab} setActiveTab={setActiveTab} onNavigateAuth={onNavigateAuth} />
      <main className="advanced-container">
        <div className="page-title-row">
          <div>
            <span className="advanced-kicker">{t('comparison.kicker')}</span>
            <h1>{t('comparison.title')}</h1>
            <p>{t('comparison.subtitle')}</p>
          </div>
        </div>

        <section className="advanced-card">
          <div className="section-heading">
            <div>
              <h2>{t('comparison.selectTitle')}</h2>
              <span className="muted">{t('comparison.selectMuted')}</span>
            </div>
            <button className="primary-button" disabled={selected.length < 2} onClick={runCompare}>
              {t('comparison.runBtn')}
            </button>
          </div>

          {error && <div className="advanced-alert error">{error}</div>}
          {loading ? (
            <p>{t('comparison.loading')}</p>
          ) : (
            <div className="select-scan-list">
              {scans.map((scan) => (
                <label className={selected.includes(scan.id) ? 'selected' : ''} key={scan.id}>
                  <input
                    type="checkbox"
                    checked={selected.includes(scan.id)}
                    onChange={() => toggle(scan.id)}
                  />
                  <span>
                    <strong>{scan.input_value_masked || '••••'}</strong>
                    <small>
                      {formatDate(scan.created_at, lang)} · {getClassLabel(scan.classification)}
                    </small>
                  </span>
                </label>
              ))}
            </div>
          )}
        </section>

        {rows.length >= 2 && (
          <>
            <section className="advanced-card">
              <div className="section-heading">
                <div>
                  <span className="advanced-kicker">{t('comparison.resultsKicker')}</span>
                  <h2>{t('comparison.trendTitle')}</h2>
                </div>
                <span className="comparison-trend">{getTrendLabel(rows, t)}</span>
              </div>

              <div className="comparison-table">
                <div className="comparison-row header">
                  <span>{t('comparison.rowHeaderScan')}</span>
                  <span>{t('comparison.rowHeaderClass')}</span>
                  <span>{t('comparison.rowHeaderConfidence')}</span>
                  <span>{t('comparison.rowHeaderDate')}</span>
                </div>
                {rows.map((scan, index) => (
                  <div className="comparison-row" key={scan.id}>
                    <span>
                      <b>#{index + 1}</b> {scan.input_value_masked || '••••'}
                    </span>
                    <span className={`result-tag ${String(scan.classification).toLowerCase()}`}>
                      {getClassLabel(scan.classification)}
                    </span>
                    <span>{scan.confidence_score == null ? '—' : `${(scan.confidence_score * 100).toFixed(1)}%`}</span>
                    <span>{formatDate(scan.created_at, lang)}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="advanced-grid">
              <article className="advanced-card">
                <h2>{t('comparison.insightTitle')}</h2>
                <p className="explanation-copy">{getComparisonInsight(rows, t)}</p>
              </article>
              <article className="advanced-card">
                <h2>{t('comparison.methodologyTitle')}</h2>
                <p className="explanation-copy">{t('comparison.methodologyDesc')}</p>
              </article>
            </section>
          </>
        )}
      </main>
      <Footer activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  );
}

function formatDate(value, lang = 'ar') {
  return value
    ? new Intl.DateTimeFormat(lang === 'ar' ? 'ar' : 'en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
    : '—';
}

function getTrendLabel(rows, t) {
  const first = Number(rows[0]?.confidence_score || 0);
  const last = Number(rows[rows.length - 1]?.confidence_score || 0);
  return last > first ? t('comparison.trendUp') : last < first ? t('comparison.trendDown') : t('comparison.trendStable');
}

function getComparisonInsight(rows, t) {
  const dangerous = rows.filter((row) => row.classification === 'DANGEROUS').length;
  if (dangerous) {
    return t('comparison.insightDangerous', { count: dangerous });
  }
  return t('comparison.insightSafe');
}
