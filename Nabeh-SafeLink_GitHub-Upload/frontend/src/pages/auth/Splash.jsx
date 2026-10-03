import { useEffect, useState } from 'react';
import { LinkIcon } from '../../components/Icons';
import { useLanguage } from '../../context/LanguageContext';
import AuthPageControls from '../../components/AuthPageControls';
import '../../styles/splash.css';
import './login.css';

export default function Splash({ onComplete }) {
  const [isExiting, setIsExiting] = useState(false);
  const { t, dir } = useLanguage();

  useEffect(() => {
    // Reserve the final 460ms for a deliberate fade-out before the route changes.
    const exitTimer = setTimeout(() => setIsExiting(true), 9740);
    const completeTimer = setTimeout(() => {
      if (onComplete) onComplete();
    }, 10200);
    return () => {
      clearTimeout(exitTimer);
      clearTimeout(completeTimer);
    };
  }, [onComplete]);

  return (
    <main className={`splash-page${isExiting ? ' is-exiting' : ''}`} aria-label="Nabeh SafeLink" dir={dir}>
      <AuthPageControls />
      <div className="splash-background" aria-hidden="true" />

      <section className="splash-content" aria-live="polite">
        <div className="splash-brand-mark" aria-hidden="true">
          <svg className="splash-shield" viewBox="0 0 180 204" role="img">
            <defs>
              <linearGradient id="splashShieldGradient" x1="0" y1="0" x2="0.8" y2="1">
                <stop offset="0%" stopColor="#8CB9FF" />
                <stop offset="42%" stopColor="#3D82FF" />
                <stop offset="100%" stopColor="#1A2B5E" />
              </linearGradient>
              <linearGradient id="splashShieldEdge" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#B7D4FF" stopOpacity="0.15" />
              </linearGradient>
              <filter id="splashShieldShadow" x="-35%" y="-25%" width="170%" height="170%">
                <feDropShadow dx="0" dy="12" stdDeviation="10" floodColor="#1A2B5E" floodOpacity="0.2" />
              </filter>
            </defs>
            <path
              d="M90 7 165 34v55c0 49-29 86-75 108C44 175 15 138 15 89V34L90 7Z"
              fill="url(#splashShieldGradient)"
              stroke="url(#splashShieldEdge)"
              strokeWidth="4"
              strokeLinejoin="round"
              filter="url(#splashShieldShadow)"
            />
            <path
              d="M90 27 144 47v42c0 35-18 63-54 82-36-19-54-47-54-82V47l54-20Z"
              fill="none"
              stroke="#FFFFFF"
              strokeOpacity="0.22"
              strokeWidth="3"
            />
            <foreignObject x="48" y="62" width="84" height="84">
              <div className="splash-link-icon"><LinkIcon size={56} color="#FFFFFF" /></div>
            </foreignObject>
          </svg>
        </div>

        <div className="splash-wordmark">
          <h1>
            <span className="splash-wordmark-main">Nabeh</span>
            <span className="splash-wordmark-sub">SafeLink</span>
          </h1>
          <p className="splash-tagline">{t('splash.tagline')}</p>
        </div>

        <div className="splash-status-block">
          <span className="splash-status-title">{t('splash.status')}</span>
          <span className="splash-status-dots" aria-hidden="true"><i /><i /><i /></span>
        </div>
      </section>

      <p className="splash-footer">{t('splash.footer')}</p>

      <svg className="splash-waves" viewBox="0 0 1440 360" preserveAspectRatio="none" aria-hidden="true">
        <path className="splash-wave-back" d="M0 180c190-98 360-80 535-16 195 71 322 72 494-10 161-76 276-72 411-10v216H0Z" />
        <path className="splash-wave-mid" d="M0 232c168-80 322-75 487-9 190 76 345 79 520-14 158-83 281-65 433 9v142H0Z" />
        <path className="splash-wave-front" d="M0 294c180-67 327-58 498 3 193 69 359 61 525-22 147-73 278-66 417-5v87H0Z" />
      </svg>
    </main>
  );
}
