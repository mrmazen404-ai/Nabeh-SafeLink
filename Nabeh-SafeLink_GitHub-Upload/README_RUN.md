# Nabeh SafeLink — التشغيل والخصوصية

## المتطلبات

- Python 3.11 أو أحدث
- Node.js 20 أو أحدث
- npm
- Supabase وGemini وVirusTotal وEmailJS وUpstash Redis عند تفعيل التكاملات

## 1. إعداد قاعدة البيانات

1. طبّق المخطط الأساسي مرة واحدة من:
   `backend/sql/nabeh_complete_database_study_schema.sql`
2. طبّق Migration بيانات المستخدم والسياسات من:
   `backend/sql/user_privacy_data_schema.sql`
3. لا تشغّل Migration الخصوصية قبل المخطط الأساسي؛ فهي تضيف أعمدة وجداول تعتمد عليه.
4. راجع النصوص القانونية seeded داخل Migration مع الجهة الأكاديمية/القانونية قبل الإنتاج.

## 2. تشغيل Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# ضع القيم المطلوبة داخل .env دون مشاركة الأسرار
uvicorn main:app --host 0.0.0.0 --port 8000
```

فحوص الصحة:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/api/v1/health`
- OpenAPI: `http://localhost:8000/docs`

## 3. تشغيل Frontend

```bash
cd frontend
npm ci
npm run dev
```

إنتاج:

```bash
npm run build
npm run preview
```

## 4. الوظائف الجديدة

- الوثائق العامة: `/terms` و`/privacy` و`/disclaimer`.
- إدارة بيانات الحساب: `/settings/privacy`.
- تصدير البيانات: `GET /api/v1/dashboard/privacy/export`.
- إخفاء الفحص: `POST /api/v1/scans/{scan_id}/hide`.
- حذف بيانات الفحص: `DELETE /api/v1/scans/{scan_id}`؛ وهو حذف منطقي يمسح المدخل المقنّع ويزيله من سجل المستخدم.
- حذف الحساب: إنشاء طلب ثم تأكيده بكلمة المرور والعبارة `DELETE MY ACCOUNT` عبر `DELETE /api/v1/dashboard/account`.

## 5. الاختبارات

```bash
python -m compileall -q backend main.py
pytest -q
cd frontend && npm run build
```

تحتاج اختبارات الخدمات الحية وقاعدة Supabase الفعلية إلى بيئة staging ومفاتيحها. لا يحتوي الأرشيف على ملف `.env` أو أسرار حقيقية.
