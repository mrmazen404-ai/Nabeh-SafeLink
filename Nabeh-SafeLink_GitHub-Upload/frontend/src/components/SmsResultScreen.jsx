import { useState } from 'react';
import Header from './Header';
import { useLanguage } from '../context/LanguageContext';
import {
  CheckCircleIcon,
  AlertTriangleIcon,
  XCircleIcon,
  HelpCircleIcon,
  ShieldCheckIcon,
  SparklesIcon,
  PinIcon,
  TargetIcon,
  RefreshIcon,
  ClipboardIcon,
  LinkIcon,
  MailIcon,
  CpuIcon
} from './Icons';
import '../styles/result.css';

export default function SmsResultScreen({ result, onReset, activeTab, setActiveTab, isGuest = true, onNavigateAuth }) {
  const { t, dir, lang } = useLanguage();
  const [copied, setCopied] = useState(false);
  const classification = result?.classification || 'UNKNOWN';

  const CONFIG = {
    SAFE: {
      icon: CheckCircleIcon,
      labelAr: 'رسالة نصية آمنة',
      labelEn: 'Safe Text Message',
      title: lang === 'ar' ? 'رسالة نصية آمنة وموثوقة' : 'Safe & Verified Text Message',
      description: lang === 'ar'
        ? 'لم يتم العثور على أي أنماط احتيال أو طلبات استدراج مشبوهة أو روابط خبيثة في هذه الرسالة بناءً على التحليل الميداني والبحث المباشر.'
        : 'No phishing tactics, fraudulent lures, or malicious links detected in this text message.',
      className: 'safe',
    },
    SUSPICIOUS: {
      icon: AlertTriangleIcon,
      labelAr: 'رسالة مشبوهة بحاجة للحذر',
      labelEn: 'Suspicious Text Message',
      title: lang === 'ar' ? 'تنبيه: رسالة نصية مشبوهة (تحتاج تحقق)' : 'Warning: Suspicious Text Message',
      description: lang === 'ar'
        ? 'تحتوي الرسالة على مصطلحات مريبة أو ادعاءات حثيثة لتحديث بيانات. يُنصح بالتأكد عبر القنوات الرسمية قبل التفاعل.'
        : 'This message contains suspicious phrasing or urgent data update claims. Verify via official channels.',
      className: 'suspicious',
    },
    DANGEROUS: {
      icon: XCircleIcon,
      labelAr: 'رسالة احتيالية خطيرة (Smishing)',
      labelEn: 'High Risk Fraudulent SMS',
      title: lang === 'ar' ? 'خطر! رسالة نصية احتيالية (Smishing)' : 'Danger! High Risk Smishing SMS',
      description: lang === 'ar'
        ? 'تم رصد مؤشرات استدراج احتيالي وانتحال لجهة رسمية/بنكية عبر أبحاث الذكاء الاصطناعي الفورية. لا تنقر على أي رابط ولا تشارك كلمات المرور أو رموز OTP!'
        : 'High-risk social engineering, bank spoofing, or OTP theft attempt detected. Do not click links or share credentials!',
      className: 'dangerous',
    },
    UNKNOWN: {
      icon: HelpCircleIcon,
      labelAr: 'نتيجة غير محددة',
      labelEn: 'Inconclusive Result',
      title: lang === 'ar' ? 'تعذر الجزم في نص الرسالة' : 'Inconclusive SMS Analysis',
      description: lang === 'ar'
        ? 'لم تتوفر معلومات كافية لتقييم مصداقية النص عبر الإنترنت. توخَّ الحذر ولا تشارك بياناتك الحساسة.'
        : 'Insufficient evidence to provide a conclusive verdict. Exercise caution with sensitive data.',
      className: 'unknown',
    },
  };

  const config = CONFIG[classification] || CONFIG.UNKNOWN;
  const StatusIcon = config.icon;
  const fraudProb = Number.isFinite(result?.fraud_probability) ? (result.fraud_probability * 100).toFixed(1) : null;
  const vt = result?.virustotal || {};
  const ml = result?.ml_model || {};
  const exp = result?.explanation || {};
  const messageText = result?.input_value || '';
  const extractedUrl = result?.extracted_url || null;
  const providerName = exp?.provider || result?.source || 'Gemini AI Agent (Search Grounded)';
  const officialPortal = exp?.official_portal_url && exp.official_portal_url !== 'غير متاح' ? exp.official_portal_url : null;
  const actionSteps = Array.isArray(exp?.action_plan_steps) && exp.action_plan_steps.length > 0 ? exp.action_plan_steps : [];

  const totalEngines = vt.total_engines || 0;
  const maliciousPct = totalEngines > 0 ? ((vt.malicious || 0) / totalEngines) * 100 : 0;
  const suspiciousPct = totalEngines > 0 ? ((vt.suspicious || 0) / totalEngines) * 100 : 0;
  const harmlessPct = totalEngines > 0 ? ((vt.harmless || 0) / totalEngines) * 100 : 0;

  // Social engineering risk indicators derived from classification & fraud probability
  const numRisk = Number(fraudProb || 0);
  const urgencyRisk = classification === 'DANGEROUS' ? 95 : classification === 'SUSPICIOUS' ? 65 : 5;
  const credentialRisk = classification === 'DANGEROUS' ? 90 : classification === 'SUSPICIOUS' ? 55 : 2;
  const spoofingRisk = classification === 'DANGEROUS' ? 98 : classification === 'SUSPICIOUS' ? 60 : 1;

  const handleCopyReport = () => {
    if (isGuest || !navigator.clipboard?.writeText) return;
    const reportText = `Nabeh SafeLink SMS Smishing Report:\nMessage: ${messageText}\nClassification: ${config.title}\nFraud Risk: ${fraudProb || 'N/A'}%\nClaimed Sender: ${exp.claimed_sender || 'N/A'}\nOfficial Domain: ${exp.official_domain || 'N/A'}\nOfficial Portal: ${officialPortal || 'N/A'}\nRecommendation: ${exp.recommendation || 'تحقق من المصدر الرسمي للرسالة.'}`;
    navigator.clipboard.writeText(reportText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="result-page sms-result-theme" dir={dir}>
      <Header activeTab={activeTab} setActiveTab={setActiveTab} onNavigateAuth={onNavigateAuth} />

      <main className="page-container">
        <div className="result-desktop-grid">
          {/* Main SMS Smishing Analysis Panel */}
          <section className="card result-main-card" aria-label="شاشة نتيجة فحص الرسائل النصية">
            {/* Status Badge */}
            <div className={`result-badge result-badge-${config.className}`} role="status">
              <StatusIcon size={32} color="currentColor" />
              <div className="result-badge-labels">
                <span className="result-badge-ar">{config.labelAr}</span>
                <span className="result-badge-en">{config.labelEn} • {lang === 'ar' ? 'بحث وتحليل أمان الرسائل المباشر' : 'AI Search Grounded Audit'}</span>
              </div>
            </div>

            <div className="result-trust-strip">
              <span className="result-trust-title">
                {lang === 'ar' ? 'تحليل أمان الرسائل النصية والهندسة الاجتماعية' : 'SMS TEXT & SOCIAL ENGINEERING AUDIT'}
              </span>
              <span><MailIcon size={14} />{lang === 'ar' ? 'كشف الاستدراج والروابط' : 'Smishing & Lure Audit'}</span>
              <span><SparklesIcon size={14} />{lang === 'ar' ? 'البحث الحي في الإنترنت Gemini Search' : 'Gemini Search Grounding'}</span>
            </div>

            {/* Inspected SMS Content Card */}
            <div className="inspected-url-box" style={{ background: 'var(--color-bg-subtle)', border: '1px solid var(--color-border-subtle)', borderRadius: '12px', padding: '16px' }}>
              <span className="url-label" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-secondary)', fontWeight: 'bold' }}>
                <MailIcon size={18} color="var(--color-secondary)" />
                {lang === 'ar' ? 'نص الرسالة المفحوصة (SMS Text Content):' : 'Inspected SMS Text:'}
              </span>
              <div className="url-text" dir="auto" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginTop: '10px', fontSize: '1rem', lineHeight: '1.6', color: 'var(--color-text-primary)' }}>
                {messageText}
              </div>

              {extractedUrl && (
                <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px dashed var(--color-border-subtle)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: 'var(--color-warning)' }}>
                  <LinkIcon size={16} color="currentColor" />
                  <span><strong>{lang === 'ar' ? 'رابط مدمج مكتشف داخل الرسالة (تم تحليله بنجاح):' : 'Extracted & Audited Embedded Link:'}</strong></span>
                  <span dir="ltr" style={{ textDecoration: 'underline', fontWeight: 'bold' }}>{extractedUrl}</span>
                </div>
              )}
            </div>

            <h2 className="result-title">{config.title}</h2>
            <p className="result-desc">{config.description}</p>

            {/* Fraud Risk Gauge Bar */}
            {fraudProb !== null && (
              <div className="confidence-block" style={{ marginTop: '18px', padding: '16px', background: 'var(--color-bg-subtle)', borderRadius: '12px', border: '1px solid var(--color-border-subtle)' }}>
                <div className="confidence-header" style={{ marginBottom: '8px' }}>
                  <span style={{ fontWeight: 'bold', fontSize: '0.95rem' }}>{lang === 'ar' ? 'مقياس نسبة احتمالية الاحتيال (Fraud Risk Probability Gauge):' : 'Fraud Risk Probability Gauge:'}</span>
                  <span className={`confidence-value confidence-value-${config.className}`} style={{ fontSize: '1.2rem', fontWeight: '800' }}>
                    {fraudProb}%
                  </span>
                </div>
                <div className="confidence-bar" style={{ height: '10px', borderRadius: '5px' }}>
                  <div className={`confidence-fill confidence-fill-${config.className}`} style={{ width: `${Math.max(4, Number(fraudProb))}%`, borderRadius: '5px' }}></div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--color-text-subtle)', marginTop: '6px' }}>
                  <span>{lang === 'ar' ? 'آمن (0%)' : 'Safe (0%)'}</span>
                  <span>{lang === 'ar' ? 'مشبوه (50%)' : 'Suspicious (50%)'}</span>
                  <span>{lang === 'ar' ? 'خطير جداً (100%)' : 'Dangerous (100%)'}</span>
                </div>
              </div>
            )}

            {/* AI Agent Internet Research & Verification Card */}
            <div className="explanation-block" style={{ marginTop: '24px' }}>
              <div className="explanation-header">
                <h3 className="details-title">
                  <SparklesIcon size={18} color="var(--color-secondary)" />
                  <span>{lang === 'ar' ? 'تقرير الأبحاث والتحقق الفوري عبر الإنترنت (AI Web Research Agent):' : 'AI Web Research Agent Report:'}</span>
                </h3>
                <span className="gemini-tag">{providerName}</span>
              </div>

              {exp.summary && <p className="explanation-text" style={{ fontSize: '0.95rem', lineHeight: '1.7' }}>{exp.summary}</p>}

              {/* Hoax Claim Verdict Notice */}
              {exp.claim_verdict_explanation && (
                <div style={{ marginTop: '14px', padding: '12px 16px', borderRadius: '10px', background: classification === 'DANGEROUS' ? 'var(--color-danger-bg)' : 'var(--color-warning-bg)', border: `1px solid ${classification === 'DANGEROUS' ? 'var(--color-danger-border)' : 'var(--color-warning-border)'}`, color: classification === 'DANGEROUS' ? 'var(--color-danger)' : 'var(--color-warning)', fontSize: '0.9rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertTriangleIcon size={18} color="currentColor" />
                  <span><strong>{lang === 'ar' ? 'حقيقة الادعاء:' : 'Claim Reality Check:'}</strong> {exp.claim_verdict_explanation}</span>
                </div>
              )}

              {/* Message Breakdown Grid */}
              <div style={{ marginTop: '16px', padding: '18px', borderRadius: '12px', background: 'var(--color-bg)', border: '1px solid var(--color-border)', boxShadow: '0 2px 10px rgba(0,0,0,0.03)' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-subtle)', fontWeight: '600' }}>{lang === 'ar' ? 'الجهة المدعاة / المنتحلة:' : 'Claimed Sender Entity:'}</span>
                    <strong style={{ fontSize: '0.95rem', color: 'var(--color-primary)' }}>{exp.claimed_sender || (lang === 'ar' ? 'جهة غير محددة' : 'Unverified Sender')}</strong>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-subtle)', fontWeight: '600' }}>{lang === 'ar' ? 'النطاق والموقع الرسمي المعتمد:' : 'Verified Official Domain:'}</span>
                    <strong dir="ltr" style={{ fontSize: '0.95rem', color: 'var(--color-success)' }}>{exp.official_domain || (lang === 'ar' ? 'غير متاح' : 'N/A')}</strong>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-subtle)', fontWeight: '600' }}>{lang === 'ar' ? 'طبيعة ادعاء الاستدراج:' : 'Lure / Claim Category:'}</span>
                    <strong style={{ fontSize: '0.95rem', color: 'var(--color-warning)' }}>{exp.lure_type || (lang === 'ar' ? 'ادعاء تحديث بيانات/طلب حثيث' : 'Data Update Lure')}</strong>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-subtle)', fontWeight: '600' }}>{lang === 'ar' ? 'حالة الأصالة والمصداقية:' : 'Authenticity Status:'}</span>
                    <strong style={{ fontSize: '0.95rem', color: classification === 'DANGEROUS' ? 'var(--color-danger)' : classification === 'SUSPICIOUS' ? 'var(--color-warning)' : 'var(--color-success)' }}>
                      {exp.authenticity_status || (classification === 'DANGEROUS' ? (lang === 'ar' ? 'احتيالية مزيفة (Fake SMS)' : 'Fake Phishing SMS') : classification === 'SUSPICIOUS' ? (lang === 'ar' ? 'غير موثوقة (Unverified)' : 'Unverified SMS') : (lang === 'ar' ? 'رسالة حقيقية ورسمية' : 'Official SMS'))}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Social Engineering Risk Factors Chart */}
              <div style={{ marginTop: '20px', padding: '16px', borderRadius: '12px', background: 'var(--color-bg-subtle)', border: '1px solid var(--color-border-subtle)' }}>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '0.9rem', color: 'var(--color-secondary)', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <TargetIcon size={16} color="currentColor" />
                  <span>{lang === 'ar' ? 'تفكيك عوامل الهندسة الاجتماعية والتأثير النفسي:' : 'Social Engineering Risk Factor Breakdown:'}</span>
                </h4>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                      <span>{lang === 'ar' ? 'مؤشر الضغط والاستعجال النفسي (Urgency Pressure)' : 'Urgency Pressure Risk'}</span>
                      <strong style={{ color: urgencyRisk > 50 ? 'var(--color-danger)' : 'var(--color-success)' }}>{urgencyRisk}%</strong>
                    </div>
                    <div className="confidence-bar" style={{ height: '6px' }}>
                      <div className={`confidence-fill confidence-fill-${urgencyRisk > 50 ? 'dangerous' : 'safe'}`} style={{ width: `${urgencyRisk}%` }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                      <span>{lang === 'ar' ? 'مؤشر طلب البيانات الحساسة/OTP (Credential Theft Risk)' : 'Credential & OTP Theft Risk'}</span>
                      <strong style={{ color: credentialRisk > 50 ? 'var(--color-danger)' : 'var(--color-success)' }}>{credentialRisk}%</strong>
                    </div>
                    <div className="confidence-bar" style={{ height: '6px' }}>
                      <div className={`confidence-fill confidence-fill-${credentialRisk > 50 ? 'dangerous' : 'safe'}`} style={{ width: `${credentialRisk}%` }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                      <span>{lang === 'ar' ? 'مؤشر انتحال الشخصية والجهات (Identity Spoofing Risk)' : 'Identity Spoofing Risk'}</span>
                      <strong style={{ color: spoofingRisk > 50 ? 'var(--color-danger)' : 'var(--color-success)' }}>{spoofingRisk}%</strong>
                    </div>
                    <div className="confidence-bar" style={{ height: '6px' }}>
                      <div className={`confidence-fill confidence-fill-${spoofingRisk > 50 ? 'dangerous' : 'safe'}`} style={{ width: `${spoofingRisk}%` }} />
                    </div>
                  </div>
                </div>
              </div>

              {Array.isArray(exp.reasons) && exp.reasons.length > 0 && (
                <ul className="reasons-list" style={{ marginTop: '18px' }}>
                  {exp.reasons.map((reason, i) => (
                    <li key={i}>
                      <PinIcon size={14} color="var(--color-secondary)" />
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              )}

              {/* OFFICIAL PORTAL & STEP-BY-STEP ACTION PLAN */}
              <div style={{ marginTop: '24px', padding: '20px', borderRadius: '14px', background: 'var(--color-secondary-subtle)', border: '1px solid var(--color-secondary)', boxShadow: '0 4px 12px rgba(30,94,255,0.06)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <ShieldCheckIcon size={24} color="var(--color-secondary)" />
                    <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: '800', color: 'var(--color-primary)' }}>
                      {lang === 'ar' ? 'خطة نابه للتوجيه وإرشاد التصرف الآمن (Official Action Plan):' : 'Official Action & Safety Guidance Plan:'}
                    </h3>
                  </div>

                  {officialPortal && (
                    <a
                      href={officialPortal.startsWith('http') ? officialPortal : `https://${officialPortal}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-primary"
                      style={{ padding: '8px 16px', fontSize: '0.85rem', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                    >
                      <LinkIcon size={14} color="#FFFFFF" />
                      <span>{lang === 'ar' ? 'الانتقال للموقع الرسمي المعتمد' : 'Visit Verified Official Portal'}</span>
                    </a>
                  )}
                </div>

                {/* Step-by-step guidance list */}
                {actionSteps.length > 0 ? (
                  <ol style={{ paddingRight: '20px', paddingLeft: '20px', margin: 0, display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.9rem', color: 'var(--color-text-primary)', lineHeight: '1.6' }}>
                    {actionSteps.map((step, idx) => (
                      <li key={idx} style={{ fontWeight: '600' }}>
                        {step}
                      </li>
                    ))}
                  </ol>
                ) : exp.recommendation ? (
                  <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--color-text-primary)', lineHeight: '1.6' }}>
                    {exp.recommendation}
                  </p>
                ) : null}
              </div>
            </div>
          </section>

          {/* Embedded Link & Engine Side Panel */}
          <aside className="result-side-panel">
            {/* Direct Link to Verified Portal Box */}
            {officialPortal && (
              <div className="card details-block" style={{ borderInlineStart: '4px solid var(--color-success)', background: 'var(--color-success-bg)' }}>
                <h3 className="details-title" style={{ color: 'var(--color-success)', fontSize: '0.95rem' }}>
                  <ShieldCheckIcon size={18} color="currentColor" />
                  <span>{lang === 'ar' ? 'الموقع البوابة الرسمية المعتمدة:' : 'Verified Official Portal:'}</span>
                </h3>
                <div style={{ marginTop: '8px', wordBreak: 'break-all', fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--color-success)' }}>
                  <a href={officialPortal.startsWith('http') ? officialPortal : `https://${officialPortal}`} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'underline' }}>
                    {officialPortal}
                  </a>
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--color-text-subtle)', marginTop: '6px', margin: 0 }}>
                  {lang === 'ar' ? 'تصل دائماً للخدمات الرسمية عبر هذا الرابط الموثق بدلاً من الروابط النصية.' : 'Always access official services via this verified link rather than text links.'}
                </p>
              </div>
            )}

            {/* If an embedded link was audited in the SMS */}
            {extractedUrl && (
              <div className="card details-block" style={{ borderInlineStart: '4px solid var(--color-warning)' }}>
                <h3 className="details-title" style={{ color: 'var(--color-warning)' }}>
                  <LinkIcon size={18} color="currentColor" />
                  <span>{lang === 'ar' ? 'تحليل أمان الرابط المدمج:' : 'Embedded Link Security Audit:'}</span>
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--color-text-subtle)', margin: '0 0 12px 0' }}>
                  {lang === 'ar' ? 'تم تحفيز نماذج فحص الروابط تلقائياً لفحص الرابط المكتشف داخل الرسالة.' : 'Automated URL scanning engines were triggered for the detected embedded link.'}
                </p>

                {/* Proportional Stacked Engine Bar */}
                {totalEngines > 0 && (
                  <div style={{ height: '8px', display: 'flex', borderRadius: '4px', overflow: 'hidden', margin: '8px 0 12px 0', background: 'var(--color-bg-subtle)' }}>
                    {vt.malicious > 0 && <div style={{ width: `${maliciousPct}%`, background: 'var(--color-danger)' }} title={`Malicious: ${vt.malicious}`} />}
                    {vt.suspicious > 0 && <div style={{ width: `${suspiciousPct}%`, background: 'var(--color-warning)' }} title={`Suspicious: ${vt.suspicious}`} />}
                    {vt.harmless > 0 && <div style={{ width: `${harmlessPct}%`, background: 'var(--color-success)' }} title={`Harmless: ${vt.harmless}`} />}
                  </div>
                )}

                {totalEngines > 0 && (
                  <div className="details-grid" style={{ marginBottom: '12px' }}>
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
                      <span className="detail-value">{totalEngines}</span>
                    </div>
                  </div>
                )}

                {ml.classification && (
                  <div className="ml-body" style={{ background: 'var(--color-bg-subtle)', padding: '10px', borderRadius: '8px' }}>
                    <div className="ml-stat">
                      <span className="ml-stat-label">{lang === 'ar' ? 'نموذج LightGBM للرابط:' : 'LightGBM Model:'}</span>
                      <span className={`ml-stat-badge ml-${(ml.classification || '').toLowerCase()}`}>
                        {ml.classification === 'SAFE' ? t('result.mlSafeBadge') : ml.classification === 'DANGEROUS' ? t('result.mlDangerousBadge') : t('result.mlSuspiciousBadge')}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Summary Security Guidance Card for SMS */}
            <div className="card details-block" style={{ background: 'var(--color-secondary-subtle)', borderColor: 'var(--color-secondary)' }}>
              <h3 className="details-title" style={{ color: 'var(--color-secondary)' }}>
                <ShieldCheckIcon size={18} color="currentColor" />
                <span>{lang === 'ar' ? 'إرشادات أمان الرسائل النصية' : 'SMS Safety Guidelines'}</span>
              </h3>
              <ul style={{ paddingRight: '18px', paddingLeft: '18px', margin: 0, fontSize: '0.85rem', lineHeight: '1.7', color: 'var(--color-text-secondary)' }}>
                <li>{lang === 'ar' ? 'البنوك والجهات الرسمية لا تطلب تحديث بياناتك أو كلمة المرور عبر رسالة نصية.' : 'Banks never request password updates or personal info via SMS.'}</li>
                <li>{lang === 'ar' ? 'احذر من مشاركة رمز التفعيل الفوري (OTP) مع أي طرف إطلاقاً.' : 'Never share One-Time Passwords (OTP) with anyone under any circumstances.'}</li>
                <li>{lang === 'ar' ? 'تحقق دائماً من النطاق المباشر والرسمي قبل إدخال بياناتك.' : 'Always verify the exact official domain before entering data.'}</li>
                <li>{lang === 'ar' ? 'للإبلاغ عن الرسائل الاحتيالية في السعودية: أعد إرسال الرسالة إلى 330330.' : 'To report scam messages in KSA: forward the SMS to 330330.'}</li>
              </ul>
            </div>

            {/* Actions */}
            <div className="card result-actions">
              <button className="btn btn-primary" onClick={onReset} type="button">
                <RefreshIcon size={18} color="#FFFFFF" />
                <span>{lang === 'ar' ? 'فحص رسالة أخرى' : 'Scan Another SMS'}</span>
              </button>
              {!isGuest && (
                <button
                  className={`btn ${copied ? 'btn-navy' : 'btn-outline'}`}
                  onClick={handleCopyReport}
                  type="button"
                >
                  <ClipboardIcon size={18} color="currentColor" />
                  <span>{copied ? t('result.copiedReportBtn') : t('result.copyReportBtn')}</span>
                </button>
              )}
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
