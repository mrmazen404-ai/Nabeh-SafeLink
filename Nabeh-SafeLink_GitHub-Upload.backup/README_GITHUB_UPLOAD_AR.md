# ملفات رفع Nabeh SafeLink إلى GitHub

هذه حزمة مصدر جاهزة لرفعها إلى **جذر** مستودع `Nabeh-SafeLink` وربطه بـVercel. ليست ملف ZIP يُرفع منفرداً إلى GitHub؛ نزّل الأرشيف وفكّه أولاً، ثم ارفع محتوياته إلى المستودع.

## محتويات الحزمة

- `main.py` و`backend_bundle.zip` وملفات إعداد Python/FastAPI اللازمة لتشغيل API على Vercel.
- `frontend/src` وملفات Vite و`frontend/dist` المبنية، التي يحتاجها مدخل FastAPI لتقديم الواجهة.
- `backend/tests` وملف `backend/.env.example` الذي يحتوي أسماء المتغيرات فقط دون قيم أسرار.
- `vercel.json` بإعدادات المنطقة `syd1` ورؤوس الحماية، و`.gitignore` لمنع رفع الملفات الحساسة والمؤقتة.

## طريقة الرفع

1. نزّل الملف `Nabeh-SafeLink_GitHub-Upload.zip` وفك ضغطه على جهازك.
2. افتح المجلد المستخرج؛ تأكد أن `vercel.json` و`main.py` و`frontend/` و`backend_bundle.zip` ظاهرة مباشرة في مستوى المجلد.
3. ارفع **محتويات هذا المجلد** إلى جذر مستودع GitHub الخاص، وليس مجلداً متداخلاً داخل المستودع. استخدم GitHub Desktop أو Git محلياً، ثم نفّذ commit وpush للفرع الإنتاجي.
4. استورد المستودع نفسه في Vercel. اترك Root Directory على الجذر المحتوي على `vercel.json` و`main.py`، ولا تنشئ مشروعاً فارغاً أو مشروعاً ثانياً.

## إعداد الأسرار في Vercel

لا تضع الأسرار داخل GitHub أو في ملف `.env` مرفوع. أضف القيم الجديدة والمدوّرة في **Project Settings → Environment Variables** فقط:

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SECRET_KEY` — خادمي فقط، لا يوضع في الواجهة.
- `NABEH_CORS_ALLOWED_ORIGINS` — الأصول الدقيقة المسموحة، مثل `https://intellidefenda.com,https://www.intellidefenda.com`.
- عند تفعيل الخدمات: `GEMINI_API_KEY`, `VIRUSTOTAL_API_KEY`, `EMAILJS_SERVICE_ID`, `EMAILJS_TEMPLATE_ID`, `EMAILJS_PUBLIC_KEY`, `EMAILJS_PRIVATE_KEY`, `EMAILJS_HOOK_SECRET`.

دوّر أي مفاتيح قديمة ظهرت في ملفات سابقة قبل إعادة استخدامها. اربط Supabase Send Email Hook بالمسار `/api/v1/auth/send-email-hook` واضبط سر Bearer نفسه في Supabase وفي متغير `EMAILJS_HOOK_SECRET` في Vercel. اختبر الإرسال قبل فتح التسجيل العام.

## ملفات مستبعدة عمداً

- ملفات `.env` أو أي مفاتيح/شهادات فعلية.
- `node_modules` وملفات `__pycache__` وبيئات Python المؤقتة.
- `frontend/build` لأنه ناتج قديم من CRA؛ النسخة الحالية هي `frontend/dist` المبنية بـVite.
- ملفات SQL؛ migrations قاعدة البيانات نُفذت بالفعل على Supabase الحي، وإعادة تشغيل ملف الحذف قد تكون مدمرة.
- ملفات نماذج `joblib` أو `pickle` غير موثقة المصدر والتحقق.

لا تغيّر سجلات DNS حتى ينجح نشر Vercel وتُتحقق من النطاق والشهادة.