import { useState } from 'react';
import Header from './Header';
import { useLanguage } from '../context/LanguageContext';
import {
  CheckCircleIcon,
  AlertTriangleIcon,
  XCircleIcon,
  HelpCircleIcon,
  ShieldCheckIcon,
  CpuIcon,
  SparklesIcon,
  PinIcon,
  TargetIcon,
  RefreshIcon,
  ClipboardIcon
} from './Icons';
import '../styles/result.css';

export default function ResultScreen({ result, onReset, activeTab, setActiveTab, isGuest = true, onNavigateAuth }) {
  const { t } = useLanguage();
  const [copied, setCopied] = useState(false);
  const classification = result?.classification || 'UNKNOWN';

  const CONFIG = {
    SAFE: {
      icon: CheckCircleIcon,
      labelAr: t('result.safeLabelAr'),
      labelEn: t('result.safeLabelEn'),
      title: t('result.safeTitle'),
      description: t('result.safeDesc'),
      className: 'safe',
    },
    SUSPICIOUS: {
      icon: AlertTriangleIcon,
      labelAr: t('result.suspiciousLabelAr'),
      labelEn: t('result.suspiciousLabelEn'),
      title: t('result.suspiciousTitle'),
      description: t('result.suspiciousDesc'),
      className: 'suspicious',
    },
    DANGEROUS: {
      icon: XCircleIcon,
      labelAr: t('result.dangerousLabelAr'),
      labelEn: t('result.dangerousLabelEn'),
      title: t('result.dangerousTitle'),
      description: t('result.dangerousDesc'),
      className: 'dangerous',
    },
    UNKNOWN: {
      icon: HelpCircleIcon,
      labelAr: t('result.unknownLabelAr'),
      labelEn: t('result.unknownLabelEn'),
      title: t('result.unknownTitle'),
      description: t('result.unknownDesc'),
      className: 'unknown',
    },
  };

  const config = CONFIG[classification] || CONFIG.UNKNOWN;
  const StatusIcon = config.icon;
  const confidence = Number.isFinite(result?.confidence) ? (result.confidence * 100).toFixed(1) : null;
  const vt = result?.virustotal || {};
  const ml = result?.ml_model || {};
  const exp = result?.explanation || {};
  const url = result?.input_value || '';

  const handleCopyReport = () => {
    if (isGuest || !navigator.clipboard?.writeText) return;
    const reportText = `Nabeh SafeLink Report:\nURL: ${url}\nClassification: ${config.title}\nConfidence: ${confidence}%\nRecommendation: ${exp.recommendation || t('result.defaultRec')}`;
    navigator.clipboard.writeText(reportText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const sourceLabel = result?.source ? t('result.sourceLabel', { source: result.source }) : t('result.hybridSource');

  return (
    <div className="result-page">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} onNavigateAuth={onNavigateAuth} />

      <main className="page-container">
        {/* Desktop 2-Column Responsive Grid Layout */}
        <div className="result-desktop-grid">
          {/* Main Analysis Card (65% Width) */}
          <section className="card result-main-card" aria-label="نتائج الفحص الرئيسية">
            {/* Status Badge */}
            <div className={`result-badge result-badge-${config.className}`} role="status">
              <StatusIcon size={32} color="currentColor" />
              <div className="result-badge-labels">
                <span className="result-badge-ar">{config.labelAr}</span>
                <span className="result-badge-en">{config.labelEn} • {sourceLabel}</span>
              </div>
            </div>

            {/* Inspected URL Box */}
            <div className="inspected-url-box">
              <span className="url-label">{t('result.inspectedUrlLabel')}</span>
              <span className="url-text" dir="ltr">{url}</span>
            </div>

            <h2 className="result-title">{config.title}</h2>
            <p className="result-desc">{config.description}</p>

            {/* Never manufacture a confidence percentage when the scanner returned UNKNOWN. */}
            {confidence !== null && (
              <div className="confidence-block" aria-label={`${t('result.confidenceLabel')}: ${confidence}%`}>
                <div className="confidence-header">
                  <span>{t('result.confidenceLabel')}</span>
                  <span className={`confidence-value confidence-value-${config.className}`}>{confidence}%</span>
                </div>
                <div className="confidence-bar">
                  <div className={`confidence-fill confidence-fill-${config.className}`} style={{ width: `${confidence}%` }}></div>
                </div>
              </div>
            )}

            {/* Gemini AI Explanation Block */}
            {exp.summary && (
              <div className="explanation-block">
                <div className="explanation-header">
                  <h3 className="details-title">
                    <SparklesIcon size={18} color="var(--color-secondary)" />
                    <span>{t('result.aiAnalysisTitle')}</span>
                  </h3>
                  <span className="gemini-tag">{t('result.aiModelTag')}</span>
                </div>

                <p className="explanation-text">{exp.summary}</p>

                {Array.isArray(exp.reasons) && exp.reasons.length > 0 && (
                  <ul className="reasons-list">
                    {exp.reasons.map((reason, i) => (
                      <li key={i}>
                        <PinIcon size={14} color="var(--color-secondary)" />
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                )}

                {exp.recommendation && (
                  <div className="recommendation-block">
                    <TargetIcon size={18} color="var(--color-secondary)" />
                    <div className="rec-content">
                      <span className="rec-title">{t('result.recommendationTitle')}</span>
                      <span className="rec-text">{exp.recommendation}</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>

          {/* Engine Metrics & Actions Side Panel (35% Width) */}
          <aside className="result-side-panel">
            {/* VirusTotal Engines Details */}
            {vt.total_engines > 0 && (
              <div className="card details-block">
                <h3 className="details-title">
                  <ShieldCheckIcon size={18} color="var(--color-secondary)" />
                  <span>{t('result.vtEnginesTitle')}</span>
                </h3>
                <div className="details-grid">
                  <div className="detail-item">
                    <span className="detail-label">{t('result.vtDangerous')}</span>
                    <span className="detail-value" style={{ color: 'var(--color-danger)' }}>{vt.malicious || 0}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">{t('result.vtSuspicious')}</span>
                    <span className="detail-value" style={{ color: 'var(--color-warning)' }}>{vt.suspicious || 0}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">{t('result.vtSafe')}</span>
                    <span className="detail-value" style={{ color: 'var(--color-success)' }}>{vt.harmless || 0}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">{t('result.vtTotal')}</span>
                    <span className="detail-value">{vt.total_engines || 0}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Machine Learning Model Prediction Details */}
            {ml.classification && (
              <div className="card ml-details-block">
                <div className="ml-header">
                  <CpuIcon size={18} color="var(--color-secondary)" />
                  <h3 className="details-title" style={{ margin: 0 }}>{t('result.mlModelTitle')}</h3>
                </div>
                <div className="ml-body">
                  <div className="ml-stat">
                    <span className="ml-stat-label">{t('result.mlLocalPrediction')}</span>
                    <span className={`ml-stat-badge ml-${(ml.classification || '').toLowerCase()}`}>
                      {ml.classification === 'SAFE' ? t('result.mlSafeBadge') : ml.classification === 'DANGEROUS' ? t('result.mlDangerousBadge') : t('result.mlSuspiciousBadge')}
                    </span>
                  </div>
                  <div className="ml-stat">
                    <span className="ml-stat-val" dir="ltr">
                      {t('result.mlRiskProb', { prob: ((ml.phishing_prob || 0) * 100).toFixed(1) })}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="card result-actions">
              <button className="btn btn-primary" onClick={onReset} type="button">
                <RefreshIcon size={18} color="#FFFFFF" />
                <span>{t('result.scanNewBtn')}</span>
              </button>
              {!isGuest && <button
                className={`btn ${copied ? 'btn-navy' : 'btn-outline'}`}
                onClick={handleCopyReport}
                type="button"
              >
                <ClipboardIcon size={18} color="currentColor" />
                <span>{copied ? t('result.copiedReportBtn') : t('result.copyReportBtn')}</span>
              </button>}
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
