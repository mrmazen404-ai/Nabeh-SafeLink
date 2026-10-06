import { useEffect, useState } from 'react';
import { ShieldCheckIcon } from './Icons';
import { useLanguage } from '../context/LanguageContext';
import '../styles/loading.css';

export default function LoadingScreen({ url, scanType = 'URL', onCancel }) {
  const { t, dir, lang } = useLanguage();
  const [messageIndex, setMessageIndex] = useState(0);

  const isText = scanType === 'TEXT' || (url && !url.startsWith('http') && url.includes(' '));

  const messages = isText
    ? (lang === 'ar'
      ? [
          'جاري فحص الرسالة النصية والتحقق من خلوها من الاحتيال...',
          'وكيل الذكاء الاصطناعي يبحث في الإنترنت ويقارن بالمصادر الرسمية...',
          'فحص الرابط المدمج ورصد أساليب الاستدراج البنكي...',
          'تقسيم الرسالة وتحديد مدى المصداقية والأمان...',
          'إعداد التقرير التفسيري للرسالة النصية...'
        ]
      : [
          'Analyzing text message for smishing & fraud...',
          'AI Agent searching online & comparing with official sources...',
          'Auditing embedded link & detecting banking lure tactics...',
          'Segmenting message & verifying authenticity...',
          'Generating comprehensive SMS security report...'
        ])
    : (t('loading.messages') || [
        'جاري تحليل الرابط والتحقق الهيكلي...',
        'فحص قواعد البيانات العالمية للتهديدات...',
        'التحقق عبر نموذجات التعلم الآلي والذكاء الاصطناعي...',
        'تحليل مؤشرات الاحتيال والانتحال...',
        'إعداد التقرير التفسيري الشامل...',
      ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 2200);

    return () => clearInterval(interval);
  }, [messages.length]);

  return (
    <div className="loading-page" role="status" aria-busy="true" dir={dir}>
      <div className="loading-bg">
        <div className="loading-bg-shape loading-bg-shape-1"></div>
        <div className="loading-bg-shape loading-bg-shape-2"></div>
      </div>

      <div className="loading-content fade-in">
        {/* Spinner */}
        <div className="loading-spinner-wrapper">
          <div className="loading-ring loading-ring-1"></div>
          <div className="loading-ring loading-ring-2"></div>
          <div className="loading-ring loading-ring-3"></div>
          <div className="loading-scan-line" aria-hidden="true"></div>
          <div className="loading-icon">
            <ShieldCheckIcon size={44} color="#1E90FF" />
          </div>
        </div>

        {/* Title */}
        <h2 className="loading-title">
          {isText
            ? (lang === 'ar' ? 'جاري فحص الرسالة النصية واصطياد الاحتيال' : 'Performing SMS Smishing & Fraud Analysis')
            : t('loading.title')}
        </h2>

        {/* Message with ARIA live feedback */}
        <p className="loading-message" key={messageIndex} aria-live="polite">
          {messages[messageIndex]}
        </p>

        {/* URL / Message Display */}
        {url && (
          <div className="loading-url-box">
            <span className="loading-url-label">
              {isText
                ? (lang === 'ar' ? 'نص الرسالة:' : 'Message Content:')
                : t('loading.urlLabel')}
            </span>
            <span className="loading-url-value" dir="auto">
              {url}
            </span>
          </div>
        )}

        {/* Progress Dots */}
        <div className="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>

        {/* Cancel Button if supported */}
        {onCancel && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCancel}
            style={{
              marginTop: 'var(--space-3)',
              padding: '6px 16px',
              fontSize: '13px',
              backgroundColor: 'rgba(255,255,255,0.1)',
              color: '#ffffff',
              border: '1px solid rgba(255,255,255,0.2)'
            }}
          >
            {t('loading.cancelBtn')}
          </button>
        )}

        {/* Hint */}
        <p className="loading-hint">
          {t('loading.hint')}
        </p>
      </div>
    </div>
  );
}
