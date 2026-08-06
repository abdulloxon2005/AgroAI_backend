# 🚀 AgroAI Serverni Production (VPS / Cloud Server) ga Joylashtirish Bo'yicha Qo'llanma

Ushbu qo'llanma **AgroAI** backend serverini Linux (Ubuntu / Debian) serveriga Docker, Docker Compose, Nginx va Let's Encrypt (SSL HTTPS) yordamida to'liq xavfsiz va yuqori unumdorlikda joylashtirishni bosqichma-bosqich tushuntiradi.

---

## 📋 Talablar
- Linux Ubuntu 22.04 / 24.04 LTS yoki Debian server (RAM: kamida 1GB/2GB, Storage: 20GB+)
- Domennomi (masalan: `api.agroai.uz` yoki Server IP manzili)
- Gemini API Key hamda OpenWeatherMap API Key

---

## 1-Bosqich: Serverni Tayyorlash va Docker O'rnatish

Serverga SSH orqali ulaning:
```bash
ssh root@server_ip_manzili
```

Tizimni yangilang va zaruriy dasturlarni o'rnating:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl wget unzip nano
```

Docker va Docker Compose-ni o'rnating:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl enable --now docker
```

---

## 2-Bosqich: Loyiha Kodini Serverga Yuklash

Serverda loyiha uchun papka yarating va loyihani yuklang:
```bash
cd /opt
sudo git clone <YUR_GIT_REPOSITORY_URL> agroai
cd agroai/server
```

---

## 3-Bosqich: Production Muhit Faylini (`.env.production`) Sozlash

`.env.production` faylini nusxalang hamda real API kalitlaringizni kiriting:
```bash
cp .env.production .env
nano .env
```

Quyidagi kalitlarni haqiqiy qiymatlar bilan almashtiring:
- `JWT_SECRET_KEY`: Tasodifiy uzundan-uzun maxfiy kalit (masalan: `openssl rand -hex 32` orqali generatsiya qiling).
- `GEMINI_API_KEY`: Google Gemini API Kalitingiz.
- `OPENWEATHERMAP_API_KEY`: OpenWeatherMap API Kalitingiz.
- `ALLOWED_ORIGINS`: `["*"]` yoki ilovangiz/vebsaytingiz domeni.

Saqlash uchun: `Ctrl + O` va keyin `Enter`, chiqish uchun: `Ctrl + X`.

---

## 4-Bosqich: Docker Konteynerlarni Ishga Tushirish

Konteynerlarni orqa fonda (detached mode) ko'tarish:
```bash
docker compose up -d --build
```

Konteynerlar holatini tekshirish:
```bash
docker compose ps
```
`agroai_backend` hamda `agroai_nginx` konteynerlari `Up (healthy)` holatida bo'lishi kerak.

Server loglarini kuzatish:
```bash
docker compose logs -f backend
```

---

## 5-Bosqich: Nginx va HTTPS SSL (Certbot) O'rnatish (Ixtiyoriy lekin Tavsiya Etiladi)

Agar domeningiz bo'lsa (masalan `api.agroai.uz`), domen uchun bepul SSL sertifikatini o'rnatish:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.agroai.uz
```

Sertifikat o'rnatilgach, HTTPS avtomatik faollashadi.

---

## 6-Bosqich: Server Salomatligini Tekshirish

Brauzer yoki `curl` orqali tekshiring:
```bash
curl http://server_ip_manzili/health
# Natija: {"status":"ok"}

curl http://server_ip_manzili/api/v1/weather/current?location=Tashkent
```

---

## 📱 7-Bosqich: Flutter Mobil Ilovasini Serverga Ulashtirish

Flutter mobil ilovangiz loyihasida `mobile/agroai/lib/core/config/api_config.dart` faylini oching hamda `baseUrl` ni backend serveringiz IP yoki domeni bilan almashtiring:

```dart
class ApiConfig {
  static const String baseUrl = 'http://YOUR_SERVER_IP'; // yoki 'https://api.agroai.uz'
}
```

Keyin mobil ilovani versiyaga yig'ing (`flutter build apk --release`).

---

## 🔄 Serverni Yangilash (Update Workflow)

Kelgusida kodingizni yangilaganizda serverda quyidagi buyruqni bajarasiz:
```bash
cd /opt/agroai/server
git pull
docker compose up -d --build
```

**AgroAI Production Backend Server muvaffaqiyatli ishga tushirildi! 🌾**
