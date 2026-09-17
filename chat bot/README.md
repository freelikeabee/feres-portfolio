# Photo-Unlock Telegram Bot (paid with Telegram Stars ⭐)

Sells individual photos. Users see a blurred preview with an "Unlock for X⭐"
button; tapping it opens a native Telegram Stars payment; on success the bot
instantly delivers the full photo.

---

## 1. Create the bot account (you have to do this part — it needs your phone number)

1. Open Telegram and search for **@BotFather**.
2. Send `/newbot`.
3. Give it a display name (e.g. "My Photo Shop"), then a username ending in
   `bot` (e.g. `myphotoshop_bot`).
4. BotFather replies with a **token** that looks like `123456789:AAExample...`.
   Copy it — this goes in `.env` as `BOT_TOKEN`.
5. **Enable Stars payments (usually already on by default):**
   Message BotFather `/mybots` → select your bot → **Payments** → you should
   see Telegram Stars listed as available. No separate payment provider or
   bank account is needed — Stars are handled entirely by Telegram.
6. Get your own numeric Telegram ID by messaging **@userinfobot** — it replies
   with your ID instantly. This goes in `.env` as `ADMIN_IDS` so the bot knows
   who's allowed to add/remove photos.

---

## 2. Configure

```bash
cd telegram-stars-bot
cp .env.example .env
# then edit .env and paste in your real BOT_TOKEN and ADMIN_IDS
```

## 3. Run it locally (good for testing first)

```bash
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

Leave that terminal running, then in Telegram:
- Message your bot `/start`
- Send it a photo, then **reply** to that photo with:
  `/addphoto 50 A cool sunset I took last week`
  (50 = price in Stars)
- Run `/gallery` to see the blurred preview + unlock button
- Tap it, pay with Stars (in a test environment or with real Stars), and the
  full photo gets delivered automatically.

## 4. Admin commands

| Command | What it does |
|---|---|
| `/addphoto <price> <description>` | Reply to a photo with this to add it to the catalog |
| `/removephoto <id>` | Removes a photo from the catalog |
| `/listphotos` | Lists every photo in the catalog with its id/price |

## 5. User commands

| Command | What it does |
|---|---|
| `/start` | Welcome message |
| `/gallery` | Browse locked photos, unlock with Stars |
| `/myphotos` | Re-view anything you've already bought, for free |

---

## 6. Deploying so it runs 24/7 (recommended: Railway)

Running `python bot.py` on your own laptop only works while your laptop is on
and connected. For a bot that's always online, deploy it:

**Railway.app (easiest, has a free tier):**
1. Push this folder to a GitHub repo.
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo.
3. In the project's **Variables** tab, add `BOT_TOKEN` and `ADMIN_IDS` (same
   values as your `.env`).
4. Under **Settings → Deploy**, set the start command to:
   `python bot.py`
5. Deploy. Railway keeps it running continuously.

**Alternative: your own VPS (e.g. a $5/mo droplet):**
```bash
git clone <your repo>
cd telegram-stars-bot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real values
nohup python bot.py &  # or better: run it under systemd / pm2 / screen
```

---

## Notes

- Photos are stored in Telegram itself — the bot only stores each photo's
  `file_id` in a local SQLite file (`bot.db`), not the image bytes. If you
  redeploy to a *different* host, copy `bot.db` along with it or you'll lose
  the catalog/purchase history.
- Telegram Stars payments don't need a payment provider token, bank account,
  or business verification — this is the simplest paid-content path Telegram
  offers.
- Want subscriptions instead of one-off unlocks, or a "tip jar" mode? The
  same `send_invoice` pattern extends easily — just ask.
