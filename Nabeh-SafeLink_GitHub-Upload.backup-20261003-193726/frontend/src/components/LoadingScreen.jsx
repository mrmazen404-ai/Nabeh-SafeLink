import { useEffect, useState } from 'react';
import { ShieldCheckIcon } from './Icons';
import { useLanguage } from '../context/LanguageContext';
import '../styles/loading.css';

export default function LoadingScreen({ url, onCancel }) {
  const { t } = useLanguage();
  const [messageIndex, setMessageIndex] = useState(0);

  const messages = t('loading.messages') || [
    'جاري تحليل الرابط والتحقق الهيكلي...',
    'فحص قواعد البيانات العالمية للتهديدات...',
    'التحقق عبر نموذجات التعلم الآلي والذكاء الاصطناعي...',
    'تحليل مؤشرات الاحتيال والانتحال...',
    'إعداد التقرير التفسيري الشامل...',
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 2200);

    return () => clearInterval(interval);
  }, [messages.length]);

  return (
    <div className="loading-page" role="status" aria-busy="true">
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
          <div className="loading-icon">
            <ShieldCheckIcon size={44} color="#1E90FF" />
          </div>
        </div>

        {/* Title */}
        <h2 className="loading-title">{t('loading.title')}</h2>

        {/* Message with ARIA live feedback */}
        <p className="loading-message" key={messageIndex} aria-live="polite">
          {messages[messageIndex]}
        </p>

        {/* URL Display */}
        {url && (
          <div className="loading-url-box">
            <span className="loading-url-label">{t('loading.urlLabel')}</span>
            <span className="loading-url-value" dir="ltr">
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
