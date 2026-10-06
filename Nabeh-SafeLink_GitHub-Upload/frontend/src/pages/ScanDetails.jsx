import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { getScanDetails } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import { AlertTriangleIcon, CheckCircleIcon, ShieldCheckIcon } from '../components/Icons';
import './advanced-pages.css';

export default function ScanDetails({ activeTab, setActiveTab, onNavigateAuth }) {
  const { dir, t, lang } = useLanguage();
  const { scanId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getScanDetails(scanId)
      .then((res) => setData(res.data))
      .catch((err) => setError(err?.response?.data?.detail || t('scanDetails.loadError')));
  }, [scanId, t]);

  const scan = data?.scan;
  const explanation = data?.explanation;
  const stages = scan?.analysis_snapshot && Object.keys(scan.analysis_snapshot).length ? scan.analysis_snapshot : {};
  const stageList = Object.entries(stages);

  const getLabel = (cls) => t(`scanDetails.labels.${cls}`) || cls || t('scanDetails.labels.UNKNOWN');
  const getStageName = (key) => t(`scanDetails.stages.${key}`) || key;

  return (
    <div className="advanced-page" dir={dir}>
      <Header activeTab={activeTab} setActiveTab={setActiveTab} onNavigateAuth={onNavigateAuth} />
      <main className="advanced-container">
        <button className="back-link" onClick={() => navigate('/history')}>
          {t('scanDetails.backToHistory')}
        </button>

        {error && <div className="advanced-alert error">{error}</div>}
        {!scan && !error && <div className="advanced-card">{t('scanDetails.loading')}</div>}

        {scan && (
          <>
            <section className={`details-hero ${String(scan.classification || 'UNKNOWN').toLowerCase()}`}>
              <div>
                <span className="advanced-kicker">{t('scanDetails.kicker')}</span>
                <h1>{t('scanDetails.title')}</h1>
                <p dir="ltr">{scan.input_value_masked || '••••'}</p>
              </div>
              <div className="verdict-pill">
                {scan.classification === 'DANGEROUS' ? <AlertTriangleIcon size={20} /> : <CheckCircleIcon size={20} />}
                {getLabel(scan.classification)}
              </div>
            </section>

            <section className="details-meta">
              <Meta label={t('scanDetails.inputType')} value={scan.input_type === 'TEXT' ? t('scanDetails.textType') : t('scanDetails.urlType')} />
              <Meta label={t('scanDetails.confidence')} value={scan.confidence_score == null ? t('scanDetails.notAvailable') : `${(scan.confidence_score * 100).toFixed(1)}%`} />
              <Meta label={t('scanDetails.completedAt')} value={formatDate(scan.completed_at || scan.created_at, lang)} />
              <Meta label={t('scanDetails.status')} value={scan.status === 'COMPLETED' ? t('scanDetails.statusCompleted') : scan.status} />
            </section>

            <section className="advanced-card">
              <div className="section-heading">
                <div>
                  <span className="advanced-kicker">{t('scanDetails.analysisChain')}</span>
                  <h2>{t('scanDetails.fullStages')}</h2>
                </div>
                <ShieldCheckIcon size={28} />
              </div>

              {stageList.length ? (
                <div className="stage-list">
                  {stageList.map(([key, stage]) => (
                    <Stage key={key} title={getStageName(key)} stage={stage} t={t} />
                  ))}
                </div>
              ) : (
                <div className="stage-list">
                  <Stage
                    title={t('scanDetails.localAnalysis')}
                    stage={{
                      status: 'COMPLETED',
                      classification: scan.classification,
                      confidence: scan.confidence_score,
                      note: t('scanDetails.legacyNote'),
                    }}
                    t={t}
                  />
                  <Stage
                    title={t('scanDetails.finalVerdict')}
                    stage={{
                      status: 'COMPLETED',
                      classification: scan.classification,
                      confidence: scan.confidence_score,
                    }}
                    t={t}
                  />
                </div>
              )}
            </section>

            <section className="advanced-grid">
              <article className="advanced-card">
                <div className="section-heading">
                  <div>
                    <span className="advanced-kicker">{t('scanDetails.aiSection')}</span>
                    <h2>{t('scanDetails.explanationRecommendation')}</h2>
                  </div>
                </div>
                <p className="explanation-copy">{explanation?.summary || t('scanDetails.noExplanation')}</p>
                <div className="recommendation-box">
                  <strong>{t('scanDetails.securityRecommendation')}</strong>
                  <p>{explanation?.recommendation || scan.recommendation || t('scanDetails.defaultRec')}</p>
                </div>
                {Array.isArray(explanation?.reasons) && explanation.reasons.length > 0 && (
                  <ul className="reason-list">
                    {explanation.reasons.map((reason, index) => (
                      <li key={index}>{typeof reason === 'string' ? reason : JSON.stringify(reason)}</li>
                    ))}
                  </ul>
                )}
              </article>

              <article className="advanced-card action-card">
                <h2>{t('scanDetails.actionsTitle')}</h2>
                <button className="primary-button" onClick={() => navigate(`/export-report?scanId=${encodeURIComponent(scan.id)}`)}>
                  {t('scanDetails.exportBtn')}
                </button>
                <button className="secondary-button" onClick={() => navigate(`/compare?ids=${encodeURIComponent(scan.id)}`)}>
                  {t('scanDetails.compareBtn')}
                </button>
              </article>
            </section>
          </>
        )}
      </main>
      <Footer activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  );
}

function Stage({ title, stage, t }) {
  const values = Object.entries(stage || {}).filter(([key]) => !['evidence'].includes(key));
  return (
    <article className="stage-card">
      <div className="stage-status">
        <CheckCircleIcon size={19} /> {t('scanDetails.stageCompleted')}
      </div>
      <h3>{title}</h3>
      <div className="stage-values">
        {values.map(([key, value]) => (
          <div key={key}>
            <span>{humanize(key)}</span>
            <strong>{typeof value === 'object' ? JSON.stringify(value) : String(value ?? '—')}</strong>
          </div>
        ))}
      </div>
    </article>
  );
}

function Meta({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function humanize(value) {
  return String(value).replaceAll('_', ' ');
}

function formatDate(value, lang = 'ar') {
  return value
    ? new Intl.DateTimeFormat(lang === 'ar' ? 'ar' : 'en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
    : '—';
}
