import { useEffect, useState, useMemo } from 'react';
import { ShieldCheckIcon } from './Icons';
import { useLanguage } from '../context/LanguageContext';
import '../styles/loading.css';

export default function LoadingScreen({ url, scanType = 'URL', onCancel }) {
  const { t, dir, lang } = useLanguage();
  const [messageIndex, setMessageIndex] = useState(0);

  const isText = scanType === 'TEXT';

  const messages = useMemo(() => {
    if (isText) {
      return lang === 'ar'
        ? [
            'جاري فحص الرسالة النصية والتحقق من خلوها من الاحتيال...',
            'وكيل الذكاء الاصطناعي يبحث في الإنترنت ويقارن بالمصادر الرسمية...',
            'فحص الرابط المدمج ورصد أساليب الاستدراج البنكي...',
            'تقسيم الرسالة وتحديد مدى المصداقية والأمان...',
            'إعداد التقرير التفسيري للرسالة النصية...',
          ]
        : [
            'Analyzing text message for smishing & fraud...',
            'AI Agent searching online & comparing with official sources...',
            'Auditing embedded link & detecting banking lure tactics...',
            'Segmenting message & verifying authenticity...',
            'Generating comprehensive SMS security report...',
          ];
    }

    const defaultMessages = [
      'جاري تحليل الرابط والتحقق الهيكلي...',
      'فحص قواعد البيانات العالمية للتهديدات...',
      'التحقق عبر نموذج التعلم الآلي والذكاء الاصطناعي...',
      'تحليل مؤشرات الاحتيال والانتحال...',
      'إعداد التقرير التفسيري الشامل...',
    ];

    return t('loading.messages') || defaultMessages;
  }, [isText, lang, t]);

  useEffect(() => {
    if (messages.length <= 1) return undefined;

    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 2200);

    return () => clearInterval(interval);
  }, [messages.length]);

  return (
    <div className="loading-page" role="status" aria-busy="true" dir={dir}>
      <div className="loading-bg" aria-hidden="true">
        <div className="loading-bg-shape loading-bg-shape-1" />
        <div className="loading-bg-shape loading-bg-shape-2" />
      </div>

      <div className="loading-content fade-in">
        <div className="loading-spinner-wrapper" aria-hidden="true">
          <div className="loading-ring-dots" />
          <div className="loading-ring-static" />
          <div className="loading-ring-main" />
          <div className="loading-icon">
            <ShieldCheckIcon size={44} color="var(--color-secondary, #1E90FF)" />
          </div>
        </div>

        <h2 className="loading-title">
          {isText
            ? lang === 'ar'
              ? 'جاري فحص الرسالة النصية واصطياد الاحتيال'
              : 'Performing SMS Smishing & Fraud Analysis'
            : t('loading.title') || (lang === 'ar' ? 'جاري الفحص' : 'Scanning')}
        </h2>

        <p className="loading-message" key={messageIndex} aria-live="polite">
          {messages[messageIndex]}
        </p>

        {url && (
          <div className="loading-url-box">
            <span className="loading-url-label">
              {isText
                ? lang === 'ar'
                  ? 'نص الرسالة:'
                  : 'Message Content:'
                : t('loading.urlLabel') || (lang === 'ar' ? 'الرابط:' : 'URL:')}
            </span>
            <span className="loading-url-value" dir="auto">
              {url}
            </span>
          </div>
        )}

        <div className="loading-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>

        {onCancel && (
          <button
            type="button"
            className="loading-cancel-btn"
            onClick={onCancel}
          >
            {t('loading.cancelBtn') || (lang === 'ar' ? 'إلغاء' : 'Cancel')}
          </button>
        )}

        <p className="loading-hint">
          {t('loading.hint') || (lang === 'ar' ? 'يتم الفحص عبر الذكاء الاصطناعي' : 'Scanned via AI and security engines')}
        </p>
      </div>
    </div>
  );
}