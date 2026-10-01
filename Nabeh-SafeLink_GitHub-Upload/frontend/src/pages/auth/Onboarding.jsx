import { useState } from 'react';
import Logo from '../../components/Logo';
import { ShieldCheckIcon, SearchIcon, SparklesIcon } from '../../components/Icons';

const STEPS = [
  {
    title: 'مرحباً بك في نابه SafeLink',
    subtitle: 'نظامك المؤسسي الفعال لكشف محاولات الاحتيال والتصيد الإلكتروني عبر الروابط والرسائل.',
    icon: ShieldCheckIcon
  },
  {
    title: 'فحص فوري وتحليل متقدم',
    subtitle: 'دمج بين أكثر من 90 محرك فحص عالمي ونموذج تعلم آلي محلي مدرب بـ 42 ميزة لهياكل الروابط.',
    icon: SearchIcon
  },
  {
    title: 'تفسيرات وتوصيات ذكية باللغة العربية',
    subtitle: 'تحليل دقيق مدعوم بالذكاء الاصطناعي مع إعطاء توصيات أمنية عملية لحماية بياناتك وحساباتك.',
    icon: SparklesIcon
  }
];

export default function Onboarding({ onComplete }) {
  const [currentStep, setCurrentStep] = useState(0);

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
    }
  };

  const StepIcon = STEPS[currentStep].icon;

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg-subtle)', padding: '20px' }}>
      <div className="card" style={{ maxWidth: '480px', width: '100%', textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 'var(--space-6)' }}>
          <Logo size="lg" showTagline={true} />
        </div>

        <div style={{ margin: 'var(--space-6) 0', display: 'flex', justifyContent: 'center' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'var(--color-success-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <StepIcon size={32} color="var(--color-secondary)" />
          </div>
        </div>

        <h1 style={{ fontSize: 'var(--text-xl)', fontWeight: 700, color: 'var(--color-primary)', marginBottom: 'var(--space-2)' }}>
          {STEPS[currentStep].title}
        </h1>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6, marginBottom: 'var(--space-6)' }}>
          {STEPS[currentStep].subtitle}
        </p>

        {/* Step Indicators */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: 'var(--space-6)' }}>
          {STEPS.map((_, i) => (
            <div
              key={i}
              style={{
                width: i === currentStep ? '24px' : '8px',
                height: '8px',
                borderRadius: '4px',
                background: i === currentStep ? 'var(--color-secondary)' : 'var(--color-border)',
                transition: 'all 0.2s ease'
              }}
            />
          ))}
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={onComplete}
            style={{ flex: 1 }}
          >
            تخطي إلى الفحص
          </button>

          <button
            type="button"
            className="btn btn-primary"
            onClick={handleNext}
            style={{ flex: 1 }}
          >
            {currentStep === STEPS.length - 1 ? 'بدء الاستخدام' : 'التالي'}
          </button>
        </div>
      </div>
    </div>
  );
}
