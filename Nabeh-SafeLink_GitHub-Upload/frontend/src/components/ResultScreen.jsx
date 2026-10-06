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
  ClipboardIcon,
  LinkIcon
} from './Icons';
import '../styles/result.css';

export default function ResultScreen({ result, onReset, activeTab, setActiveTab, isGuest = true, onNavigateAuth }) {
  const { t, dir, lang } = useLanguage();
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

  const isTextScan = result?.input_type === 'TEXT' || (url && !url.startsWith('http') && url.includes(' '));
  const extractedUrl = result?.extracted_url || null;

  const handleCopyReport = () => {
    if (isGuest || !navigator.clipboard?.writeText) return;
    const reportText = `Nabeh SafeLink Report (${isTextScan ? 'SMS' : 'URL'}):\nContent: ${url}\nClassification: ${config.title}\nConfidence: ${confidence}%\nRecommendation: ${exp.recommendation || t('result.defaultRec')}`;
    navigator.clipboard.writeText(reportText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const sourceLabel = result?.source ? t('result.sourceLabel', { source: result.source }) : t('result.hybridSource');

  return (
    <div className="result-page" dir={dir}>
      <Header activeTab={activeTab} setActiveTab={setActiveTab} onNavigateAuth={onNavigateAuth} />

      <main className="page-container">
        {/* Desktop 2-Column Responsive Grid Layout */}
        <div className="result-desktop-grid">
          {/* Main Analysis Card (65% Width) */}
          <section className="card result-main-card" aria-label={t('result.pageLabel')}>
            {/* Status Badge */}
            <div className={`result-badge result-badge-${config.className}`} role="status">
              <StatusIcon size={32} color="currentColor" />
              <div className="result-badge-labels">
                <span className="result-badge-ar">
                  {isTextScan
                    ? (classification === 'DANGEROUS' ? (lang === 'ar' ? 'رسالة احتيالية خطيرة (Smishing)' : 'High Risk Smishing SMS') : classification === 'SUSPICIOUS' ? (lang === 'ar' ? 'رسالة مشبوهة بحاجة للحذر' : 'Suspicious Message') : (lang === 'ar' ? 'رسالة نصية آمنة' : 'Safe Message'))
                    : config.labelAr}
                </span>
                <span className="result-badge-en">{config.labelEn} • {sourceLabel}</span>
              </div>
            </div>

            <div className="result-trust-strip">
              <span className="result-trust-title">
                {isTextScan
                  ? (lang === 'ar' ? 'تحليل أمان الرسائل النصية' : 'SMS / TEXT SECURITY ANALYSIS')
                  : (lang === 'ar' ? 'ملخص الفحص الأمني' : 'SECURITY ANALYSIS SUMMARY')}
              </span>
              <span><ShieldCheckIcon size={14} />{isTextScan ? (lang === 'ar' ? 'كشف الاستدراج والروابط' : 'Smishing & Link Audit') : (lang === 'ar' ? 'تحليل متعدد الطبقات' : 'Multi-layer analysis')}</span>
              <span><SparklesIcon size={14} />{lang === 'ar' ? 'مدعوم بـ Google Gemini AI' : 'Google Gemini AI'}</span>
            </div>

            {/* Inspected Content Box */}
            <div className="inspected-url-box">
              <span className="url-label">
                {isTextScan
                  ? (lang === 'ar' ? 'نص الرسالة المفحوصة (SMS Message):' : 'Inspected Text Content:')
                  : t('result.inspectedUrlLabel')}
              </span>
              <div className="url-text" dir="auto" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginTop: '6px' }}>
                {url}
              </div>
              {extractedUrl && (
                <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px dashed var(--color-border-subtle)', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: 'var(--color-warning)' }}>
                  <LinkIcon size={16} color="currentColor" />
                  <span><strong>{lang === 'ar' ? 'رابط مدمج مكتشف:' : 'Extracted Link:'}</strong></span>
                  <span dir="ltr" style={{ textDecoration: 'underline' }}>{extractedUrl}</span>
                </div>
              )}
            </div>

            <h2 className="result-title">
              {isTextScan
                ? (classification === 'DANGEROUS'
                  ? (lang === 'ar' ? 'خطر! رسالة نصية احتيالية (Smishing)' : 'Danger! Fraudulent Smishing SMS')
                  : classification === 'SUSPICIOUS'
                  ? (lang === 'ar' ? 'تنبيه: رسالة نصية مشبوهة' : 'Warning: Suspicious Text Message')
                  : (lang === 'ar' ? 'رسالة نصية آمنة وموثوقة' : 'Safe & Verified Text Message'))
                : config.title}
            </h2>
            <p className="result-desc">
              {isTextScan
                ? (classification === 'DANGEROUS'
                  ? (lang === 'ar' ? 'تم رصد مؤشرات احتيال واستدراج بنكي أو انتحال لجهة رسمية. لا تنقر على أي رابط ولا تشارك بياناتك أو رموز OTP!' : 'High-risk phishing tactics, bank spoofing, or credential lures detected in this message.')
                  : classification === 'SUSPICIOUS'
                  ? (lang === 'ar' ? 'يحتوي النص على مصطلحات مريبة أو ادعاءات غير مؤكدة. توخَّ الحذر وتأكد عبر القنوات الرسمية.' : 'Suspicious wording or unverified claims detected. Proceed with caution.')
                  : (lang === 'ar' ? 'لم يتم العثور على أنماط احتيال أو روابط ضارة في هذه الرسالة.' : 'No phishing indicators or malicious links detected in this message.'))
                : config.description}
            </p>

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
                    <span>{isTextScan ? (lang === 'ar' ? 'نتائج بحث ومقارنة وكيل الذكاء الاصطناعي (Gemini AI Research)' : 'AI Research Agent Findings') : t('result.aiAnalysisTitle')}</span>
                  </h3>
                  <span className="gemini-tag">{t('result.aiModelTag')}</span>
                </div>

                <p className="explanation-text">{exp.summary}</p>

                {/* AI Agent Message Breakdown & Segmentation Card */}
                {isTextScan && (
                  <div style={{ marginTop: '16px', padding: '14px', borderRadius: '8px', background: 'var(--color-bg-subtle)', border: '1px solid var(--color-border-subtle)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontWeight: 'bold', fontSize: '0.95rem', color: 'var(--color-secondary)' }}>
                      <SparklesIcon size={16} color="var(--color-secondary)" />
                      <span>{lang === 'ar' ? 'تقسيم وتحليل وكيل الذكاء الاصطناعي للرسالة (AI Agent Breakdown):' : 'AI Agent Message Segmentation & Research:'}</span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-subtle)' }}>{lang === 'ar' ? 'الجهة المدعاة / المنتحلة:' : 'Claimed Entity:'}</span>
                        <strong style={{ fontSize: '0.95rem', color: 'var(--color-text-primary)' }}>{exp.claimed_sender || (lang === 'ar' ? 'جهة غير محددة' : 'Unverified Sender')}</strong>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-subtle)' }}>{lang === 'ar' ? 'الموقع والنطاق الرسمي المعتمد:' : 'Verified Official Domain:'}</span>
                        <strong dir="ltr" style={{ fontSize: '0.95rem', color: 'var(--color-success)' }}>{exp.official_domain || (lang === 'ar' ? 'غير متاح' : 'N/A')}</strong>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-subtle)' }}>{lang === 'ar' ? 'طبيعة الاستدراج والادعاء:' : 'Lure / Claim Type:'}</span>
                        <strong style={{ fontSize: '0.95rem', color: 'var(--color-warning)' }}>{exp.lure_type || (lang === 'ar' ? 'ادعاء تحديث بيانات/طلب حثيث' : 'Urgent Credential Lure')}</strong>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-subtle)' }}>{lang === 'ar' ? 'حالة الأصالة والمصداقية:' : 'Authenticity Status:'}</span>
                        <strong style={{ fontSize: '0.95rem', color: classification === 'DANGEROUS' ? 'var(--color-danger)' : classification === 'SUSPICIOUS' ? 'var(--color-warning)' : 'var(--color-success)' }}>
                          {exp.authenticity_status || (classification === 'DANGEROUS' ? (lang === 'ar' ? 'احتيالية مزيفة (Fake SMS)' : 'Fake Phishing SMS') : classification === 'SUSPICIOUS' ? (lang === 'ar' ? 'مشبوهة (Unverified)' : 'Unverified SMS') : (lang === 'ar' ? 'رسالة رسمية وحقيقية' : 'Official SMS'))}
                        </strong>
                      </div>
                    </div>
                  </div>
                )}

                {Array.isArray(exp.reasons) && exp.reasons.length > 0 && (
                  <ul className="reasons-list" style={{ marginTop: '16px' }}>
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
                      <span className="rec-title">{isTextScan ? (lang === 'ar' ? 'توصية نابه لحماية الرسائل النصية:' : 'Nabeh SMS Protection Advice:') : t('result.recommendationTitle')}</span>
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
                      {Number.isFinite(ml.phishing_prob)
                        ? t('result.mlRiskProb', { prob: (ml.phishing_prob * 100).toFixed(1) })
                        : (lang === 'ar' ? 'النموذج غير متاح' : 'Model Unavailable')}
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
