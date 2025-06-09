# Telegram Video Code Bot

Bu bot foydalanuvchilarga maxsus kodlar orqali videolarni yetkazib berish uchun yaratilgan.

## O'rnatish

1. Kerakli paketlarni o'rnatish:
```bash
pip install -r requirements.txt
```

2. `.env` faylini yarating va quyidagi o'zgaruvchilarni kiriting:
```
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_id_here
```

3. Botni ishga tushirish:
```bash
python bot.py
```

## Foydalanish

### Foydalanuvchilar uchun
- `/start` - Botni ishga tushirish
- Kodni matn ko'rinishida yuborish orqali videoni olish

### Admin uchun
- `/admin` - Admin panelni ochish
- Yangi kod-video bog'lash
- Mavjud kodlarni o'chirish
- Kodlar ro'yxatini ko'rish

## Fayl tuzilishi
- `bot.py` - Bot asosiy logikasi
- `videos.json` - Kodlar va videolar mapping
- `videos/` - Video fayllar papkasi
- `.env` - Muhim ma'lumotlar (bot token va admin ID)
- `requirements.txt` - Kerakli paketlar ro'yxati 