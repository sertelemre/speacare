# Multi-AI Panel

Çoklu yapay zekâ paneli - Sol'da kanallar, üstte kişiler/botlar, orta mesaj akışı, sağda Notlar/Dokümanlar/Kaynaklar/Görevler. Her kanalda farklı LLM sağlayıcılarından beslenen personaya sahip botlar konuşur; muhalif bot(lar) zorunlu.

## 🏗️ Proje Yapısı

```
speacare/
├── apps/
│   ├── api/          # Django 5 + DRF + Channels + Celery
│   ├── web/          # Next.js 14 + Tailwind + shadcn/ui
│   └── orchestrator/ # LLM çoklayıcı + tartışma motoru
├── docker-compose.yml
├── Makefile
└── README.md
```

## 🚀 Hızlı Başlangıç

### 1. Gereksinimler
- Docker & Docker Compose
- Node.js 18+ (pnpm)
- Python 3.11+

### 2. Kurulum

```bash
# Repository'yi klonla
git clone <repo-url>
cd speacare

# Environment variables'ları ayarla
cp .env.example .env
# .env dosyasını düzenle ve API key'lerini ekle

# Development environment'ı başlat
make dev

# Database migration'ları çalıştır
make migrate

# Seed data'yı yükle
make seed
```

### 3. Servisleri Başlat

```bash
# API server (Django)
cd apps/api
python manage.py runserver

# Web server (Next.js)
cd apps/web
pnpm dev

# Celery worker (background tasks)
cd apps/api
celery -A core worker --loglevel=info

# Celery beat (scheduled tasks)
cd apps/api
celery -A core beat --loglevel=info
```

## 🔧 Konfigürasyon

### Environment Variables

```bash
# Database
DATABASE_URL=postgres://user:password@localhost:5432/multi_ai_panel_db

# Redis
REDIS_URL=redis://localhost:6379/0
CHANNELS_REDIS_URL=redis://localhost:6379/1

# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

# S3 Storage (MinIO)
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=multi-ai-panel

# LLM API Keys
OPENAI_API_KEY=your-openai-key
GEMINI_API_KEY=your-gemini-key
DEEPSEEK_API_KEY=your-deepseek-key
GROK_API_KEY=your-grok-key

# NextAuth
NEXTAUTH_SECRET=your-nextauth-secret
NEXTAUTH_URL=http://localhost:3000
```

## 🎯 Özellikler

### ✅ Tamamlanan
- [x] Django 5 + DRF API
- [x] Next.js 14 Web UI
- [x] WebSocket real-time communication
- [x] JWT Authentication
- [x] Multi-LLM provider support (OpenAI, Gemini, Groq, DeepSeek)
- [x] Bot management system
- [x] Channel-based discussions
- [x] Thread management
- [x] Message voting system
- [x] Document generation (consensus, summaries)
- [x] Celery background tasks
- [x] Docker Compose setup
- [x] Seed data with default bots

### 🔄 Geliştirme Aşamasında
- [ ] File upload system
- [ ] Advanced bot personas
- [ ] Task management
- [ ] Source management
- [ ] Advanced analytics

## 🤖 Bot Tipleri

### Varsayılan Botlar
- **CMO**: Marketing strategist (OpenAI GPT-4)
- **Satış Direktörü**: Sales strategist (OpenAI GPT-4)
- **Finans Analisti**: Financial analyst (Gemini)
- **PM**: Product manager (OpenAI GPT-4)
- **Devil's Advocate**: Critical challenger (Groq)
- **Risk Analisti**: Risk assessment (DeepSeek)
- **Scribe**: Meeting facilitator (Gemini)
- **Doc-Maker**: Document creator (OpenAI GPT-4)

## 📡 API Endpoints

### Authentication
- `POST /api/auth/jwt/obtain/` - Login
- `POST /api/auth/jwt/refresh/` - Refresh token
- `POST /api/auth/register/` - Register
- `GET /api/auth/me/` - User profile

### Channels
- `GET /api/channels/` - List channels
- `POST /api/channels/` - Create channel
- `GET /api/channels/{id}/` - Channel details
- `POST /api/channels/{id}/invite-bot/` - Invite bot

### Threads
- `GET /api/channels/{id}/threads/` - List threads
- `POST /api/channels/{id}/threads/` - Create thread
- `POST /api/channels/{id}/threads/{id}/debate-round/` - Start debate
- `POST /api/channels/{id}/threads/{id}/consensus/` - Generate consensus

### Messages
- `GET /api/channels/{id}/messages/` - List messages
- `POST /api/channels/{id}/messages/` - Send message

### Bots
- `GET /api/bots/` - List bots
- `POST /api/bots/` - Create bot
- `GET /api/bots/llm-providers/` - Available providers

## 🧪 Test

```bash
# API tests
make test

# Web tests
cd apps/web
pnpm test
```

## 📚 Dokümantasyon

- API Documentation: `http://localhost:8002/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8002/api/schema/redoc/`

## 🐳 Docker

```bash
# Development
make dev

# Stop services
make down
```

## 🔄 Workflow

1. **Kanal Oluştur**: Yeni bir tartışma kanalı oluştur
2. **Bot Davet Et**: Kanala uygun botları davet et
3. **Thread Başlat**: Konuya özel thread oluştur
4. **Tartışma Başlat**: Botlar otomatik olarak tartışmaya katılır
5. **Oylama**: Botlar birbirlerinin mesajlarını oylar
6. **Özet**: Scribe bot otomatik özet çıkarır
7. **Uzlaşı**: Consensus dokümanı oluşturulur

## 🤝 Katkıda Bulunma

1. Fork yap
2. Feature branch oluştur (`git checkout -b feature/amazing-feature`)
3. Commit yap (`git commit -m 'Add amazing feature'`)
4. Push yap (`git push origin feature/amazing-feature`)
5. Pull Request oluştur

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.
