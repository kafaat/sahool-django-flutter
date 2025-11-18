# Sahool Smart Agriculture Platform - Django + Flutter

منصة سهول الزراعية الذكية - نسخة Django + Flutter

## البنية

```
sahool-django-flutter/
├── backend/          # Django REST API
│   ├── sahool/      # المشروع الرئيسي
│   ├── farms/       # تطبيق المزارع
│   ├── fields/      # تطبيق الحقول
│   ├── iot/         # تطبيق IoT
│   ├── users/       # تطبيق المستخدمين
│   └── api/         # API endpoints
├── frontend/         # Flutter Mobile App
│   ├── lib/
│   │   ├── models/
│   │   ├── services/
│   │   ├── screens/
│   │   └── widgets/
│   └── assets/
└── docs/            # التوثيق
```

## الميزات

### Backend (Django)
- ✅ Django REST Framework
- ✅ JWT Authentication
- ✅ PostgreSQL Database
- ✅ Celery للمهام الخلفية
- ✅ Redis للتخزين المؤقت
- ✅ Docker support

### Frontend (Flutter)
- ✅ Material Design 3
- ✅ Offline-First مع SQLite
- ✅ Google Maps Integration
- ✅ دعم كامل للغة العربية
- ✅ مزامنة تلقائية

## التكامل مع المشروع الحالي

المشروع الحالي (React + Node.js) والمشروع الجديد (Django + Flutter) يعملان معاً:

- **Django API** يخدم كلاً من React Web و Flutter Mobile
- **قاعدة بيانات موحدة** مشتركة
- **JWT Authentication** موحد بين النظامين
- **Redis Cache** مشترك

## التثبيت

### Backend (Django)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend (Flutter)

```bash
cd frontend
flutter pub get
flutter run
```

### Docker

```bash
docker-compose up -d
```

## المتغيرات البيئية

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:pass@localhost:5432/sahool
REDIS_URL=redis://localhost:6379

# Flutter
API_BASE_URL=https://api.sahool.com
```

## API Documentation

الوثائق التفاعلية متاحة على:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## الترخيص

MIT License
