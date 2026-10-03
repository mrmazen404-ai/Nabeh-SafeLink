import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  CpuIcon,
  GlobeIcon,
  LinkIcon,
  MoonIcon,
  SearchIcon,
  ShieldCheckIcon,
  SunIcon,
} from '../components/Icons';
import './welcome-page.css';

const team = [
  ['Aryam Odeh Al-Huwaiti', '451004106'],
  ['Nouf Odeh Al-Huwaiti', '451006979'],
  ['Jawharah Odeh Al-Huwaiti', '451000039'],
  ['Wasaif Mahmoud Al-Balawi', '451003974'],
];

const content = {
  ar: {
    eyebrow: 'مشروع تخرج • أمن سيبراني ذكي',
    heroTitle: 'احمِ عالمك الرقمي بذكاء',
    heroCopy: 'Nabeh SafeLink منصة ويب ذكية تساعدك على تحليل الروابط والرسائل واكتشاف مؤشرات التصيد والتهديدات الإلكترونية قبل التفاعل معها.',
    scan: 'ابدأ الفحص الآن',
    login: 'تسجيل الدخول',
    register: 'إنشاء حساب',
    openHome: 'فتح لوحة التحكم',
    welcome: 'مرحبًا بك مجددًا في Nabeh SafeLink',
    newScan: 'بدء فحص جديد',
    theme: 'تبديل الثيم',
    language: 'English',
    features: [
      ['فحص ذكي', 'تحليل الروابط والرسائل للكشف عن مؤشرات التصيد والاحتيال.', SearchIcon],
      ['حماية استباقية', 'اكتشاف التهديد قبل فتح الرابط أو مشاركة بياناتك.', ShieldCheckIcon],
      ['خصوصية موثوقة', 'فحص الضيف يعرض النتيجة الحالية دون حفظها في سجل المستخدم.', ShieldCheckIcon],
    ],
    missionLabel: 'فكرة المشروع',
    missionTitle: 'Scan • Detect • Stay Safe',
    missionCopy: 'نحو تجربة رقمية أكثر وعيًا وأمانًا، بقرارات واضحة قبل الضغط على أي رابط.',
    graduation: 'مشروع تخرج',
    teamTitle: 'فريق Nabeh SafeLink',
    idLabel: 'الرقم الجامعي',
    supervisor: 'المشرفة الأكاديمية',
    year: '1448 هـ – 2026 م',
    priority: '“Your online safety” is our priority',
    footer: 'منصة ويب ذكية للكشف والوقاية من التهديدات الإلكترونية',
  },
  en: {
    eyebrow: 'Graduation Project • Intelligent Cybersecurity',
    heroTitle: 'Protect Your Digital World with Intelligence',
    heroCopy: 'Nabeh SafeLink is an intelligent web platform that analyzes URLs and messages to detect phishing indicators and online threats before you interact with them.',
    scan: 'Start a Safe Scan',
    login: 'Sign in',
    register: 'Create account',
    openHome: 'Open dashboard',
    welcome: 'Welcome back to Nabeh SafeLink',
    newScan: 'Start a new scan',
    theme: 'Toggle theme',
    language: 'العربية',
    features: [
      ['Smart scanning', 'Analyze links and messages for phishing and fraud indicators.', SearchIcon],
      ['Proactive protection', 'Identify threats before opening a link or sharing your data.', ShieldCheckIcon],
      ['Trusted privacy', 'Guest scans show the current result without saving it to your history.', ShieldCheckIcon],
    ],
    missionLabel: 'Project vision',
    missionTitle: 'Scan • Detect • Stay Safe',
    missionCopy: 'Building a more aware and secure digital experience, one decision before every click.',
    graduation: 'Graduation Project',
    teamTitle: 'The Nabeh SafeLink Team',
    idLabel: 'Academic ID',
    supervisor: 'Academic supervisor',
    year: '1448 H – 2026 G',
    priority: '“Your online safety” is our priority',
    footer: 'An intelligent web platform for cyber threat detection and prevention',
  },
};

export default function WelcomePage() {
  const navigate = useNavigate();
  const { isGuest } = useAuth();
  const { lang, toggleLanguage, dir } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  const text = content[lang] || content.ar;
  const ForwardIcon = dir === 'rtl' ? ArrowLeftIcon : ArrowRightIcon;

  return (
    <main className="welcome-page" dir={dir}>
      <div className="welcome-glow welcome-glow-one" aria-hidden="true" />
      <div className="welcome-glow welcome-glow-two" aria-hidden="true" />

      <header className="welcome-header">
        <button type="button" className="welcome-brand" onClick={() => navigate('/welcome')} aria-label="Nabeh SafeLink">
          <span className="welcome-brand-icon"><ShieldCheckIcon size={24} color="#FFFFFF" /></span>
          <span className="welcome-brand-copy"><strong>Nabeh</strong><b>SafeLink</b></span>
        </button>
        <div className="welcome-controls">
          <button type="button" className="welcome-control" onClick={toggleLanguage} aria-label="Change language" title={text.language}>
            <GlobeIcon size={17} color="currentColor" /><span>{text.language}</span>
          </button>
          <button type="button" className="welcome-control welcome-theme-control" onClick={toggleTheme} aria-label={text.theme} title={text.theme}>
            {theme === 'dark' ? <SunIcon size={17} color="currentColor" /> : <MoonIcon size={17} color="currentColor" />}
          </button>
          {!isGuest && <span className="welcome-session-badge"><CheckCircleIcon size={15} color="currentColor" /> {text.welcome}</span>}
        </div>
      </header>

      <section className="welcome-hero">
        <div className="welcome-hero-copy">
          <span className="welcome-eyebrow"><span className="welcome-eyebrow-dot" />{text.eyebrow}</span>
          <h1>{text.heroTitle}</h1>
          <p className="welcome-hero-description">{text.heroCopy}</p>
          <div className="welcome-actions">
            <button type="button" className="welcome-primary-button" onClick={() => navigate('/scan')}>
              <SearchIcon size={19} color="#FFFFFF" /><span>{isGuest ? text.scan : text.newScan}</span><ForwardIcon size={17} color="#FFFFFF" />
            </button>
            {isGuest ? (
              <>
                <button type="button" className="welcome-secondary-button" onClick={() => navigate('/register')}>{text.register}</button>
                <button type="button" className="welcome-text-button" onClick={() => navigate('/login')}>{text.login}</button>
              </>
            ) : (
              <button type="button" className="welcome-secondary-button" onClick={() => navigate('/home')}>{text.openHome}</button>
            )}
          </div>
          <div className="welcome-trust-line"><CheckCircleIcon size={16} color="#16A34A" /> {text.missionCopy}</div>
        </div>

        <div className="welcome-visual" aria-label="Nabeh SafeLink security illustration">
          <div className="welcome-visual-orbit welcome-orbit-one" />
          <div className="welcome-visual-orbit welcome-orbit-two" />
          <div className="welcome-visual-card welcome-card-top"><CpuIcon size={17} color="#1E5EFF" /><span>AI threat analysis</span></div>
          <div className="welcome-shield-wrap">
            <div className="welcome-shield-halo" />
            <div className="welcome-shield"><ShieldCheckIcon size={92} color="#FFFFFF" /><span className="welcome-shield-link"><LinkIcon size={38} color="#FFFFFF" /></span></div>
          </div>
          <div className="welcome-visual-card welcome-card-bottom"><span className="welcome-status-dot" /> <span>Protection active</span></div>
        </div>
      </section>

      <section className="welcome-mission">
        <div><span className="welcome-section-label">{text.missionLabel}</span><h2>{text.missionTitle}</h2></div>
        <p>{text.missionCopy}</p>
      </section>

      <section className="welcome-features" aria-label={text.missionLabel}>
        {text.features.map(([title, description, Icon]) => (
          <article className="welcome-feature-card" key={title}><span className="welcome-feature-icon"><Icon size={21} color="#1E5EFF" /></span><div><h3>{title}</h3><p>{description}</p></div></article>
        ))}
      </section>

      <section className="welcome-graduation" aria-label={text.graduation}>
        <div className="welcome-graduation-heading"><span className="welcome-section-label">{text.graduation}</span><h2>{text.teamTitle}</h2><p>{text.footer}</p></div>
        <div className="welcome-team-grid">
          {team.map(([name, id], index) => <article className="welcome-member" key={id}><span className="welcome-member-number">0{index + 1}</span><div><strong>{name}</strong><small>{text.idLabel}: <bdi>{id}</bdi></small></div></article>)}
        </div>
        <div className="welcome-supervisor"><div><span>{text.supervisor}</span><strong>Dr. Arij Al-Faidi</strong></div><b>{text.year}</b></div>
      </section>

      <footer className="welcome-footer"><span>{text.priority}</span><span>Nabeh SafeLink • {text.graduation} • 2026</span></footer>
    </main>
  );
}
