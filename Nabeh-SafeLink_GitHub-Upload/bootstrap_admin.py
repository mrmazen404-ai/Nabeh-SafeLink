import requests
import json

# ===== الإعدادات =====
URL = "http://localhost:8000/api/v1/admin/auth/bootstrap"
BOOTSTRAP_TOKEN = "E4_d2Qu1WLALLTmq-YiP233leU3teXh47OTGtvuurJgIsZwe-V6o0Iyz3EXaDL44"

EMAIL = "mr.mazenn404@gmail.com"
DISPLAY_NAME = "System Administrator"
PASSWORD = "Mr!Mazen@2026#Secure"

# ===== الطلب =====
headers = {
    "Content-Type": "application/json",
    "X-Admin-Bootstrap-Token": BOOTSTRAP_TOKEN,
}

payload = {
    "email": EMAIL,
    "display_name": DISPLAY_NAME,
    "password": PASSWORD,
}

print("=" * 60)
print(f"📤 {URL}")
print("=" * 60)

try:
    r = requests.post(URL, headers=headers, json=payload, timeout=30)

    print(f"\n📥 Status: {r.status_code}\n")

    try:
        print(json.dumps(r.json(), indent=4, ensure_ascii=False))
    except ValueError:
        print(r.text)

    if r.status_code in (200, 201):
        print("\n✅ تم إنشاء المشرف بنجاح!")
    elif r.status_code == 409:
        print("\n⚠️ المشرف موجود مسبقاً")
    elif r.status_code == 401:
        print("\n❌ التوكن غير صحيح")
    elif r.status_code == 403:
        print("\n❌ Bootstrap معطّل")
    else:
        print(f"\n❌ فشل: {r.status_code}")

except requests.exceptions.ConnectionError:
    print("❌ Backend مو شغال")
except Exception as e:
    print(f"❌ خطأ: {e}")