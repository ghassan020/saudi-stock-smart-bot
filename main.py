import csv
import requests
import time
import os
from flask import Flask
from waitress import serve
import threading

# إعدادات Telegram من متغير بيئة
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "756852322"

def send_telegram(message_text):
    if not TOKEN:
        print("Telegram token not set.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message_text}
    try:
        requests.get(url, params=params)
    except Exception as e:
        print("فشل في إرسال الرسالة:", e)

# Flask app للبقاء نشط في Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running."

# ملف CSV
csv_filename = "saudi-stock-alerts-with-adjustment.csv"

def start_bot():
    while True:
        try:
            with open(csv_filename, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                rows = list(reader)

            updated = False

            for row in rows:
                try:
                    symbol = row["السهم"]
                    current = float(row["السعر الحالي"])
                    entry = float(row["نقطة الدخول"])
                    target = float(row["الهدف"])
                    stop = float(row["وقف الخسارة"])
                    support = float(row["دعم التعديل الذكي"])
                    status = row["حالة التنبيه"]

                    if status == "" and (entry * 0.99 <= current < entry):
                        msg = f"🚨 *تنبيه اقتراب دخول*\n\n📈 السهم: {symbol}\n💵 السعر الحالي: {current} ريال\n🎯 نقطة الدخول: {entry} ريال"
                        send_telegram(msg)
                        row["حالة التنبيه"] = "تنبيه اقتراب"
                        updated = True

                    elif status in ["", "تنبيه اقتراب"] and current >= entry:
                        msg = f"🚨 *فرصة دخول مؤكدة*\n\n📈 السهم: {symbol}\n💵 السعر الحالي: {current} ريال\n🎯 نقطة الدخول: {entry} ريال\n✅ الهدف: {target} ريال\n🛑 وقف الخسارة: {stop} ريال\n🧠 استراتيجية: دخول فني بعد اختراق\n📊 التقييم الفني: مرتفع جداً"
                        send_telegram(msg)
                        row["حالة التنبيه"] = "تم الدخول"
                        updated = True

                    elif status == "تم الدخول" and current >= target:
                        msg = f"✅ *تحقق الهدف*\n\n📈 السهم: {symbol}\n💵 السعر الحالي: {current} ريال\n🎯 الهدف: {target} ريال"
                        send_telegram(msg)
                        row["حالة التنبيه"] = "تحقق الهدف"
                        updated = True

                    elif status == "تم الدخول" and current <= stop:
                        msg = f"❌ *تفعيل وقف الخسارة*\n\n📉 السهم: {symbol}\n💵 السعر الحالي: {current} ريال\n🛑 وقف الخسارة: {stop} ريال"
                        send_telegram(msg)
                        row["حالة التنبيه"] = "وقف الخسارة"
                        updated = True

                    elif status == "تم الدخول" and current <= support:
                        msg = f"🧠 *تنبيه تعديل ذكي - دخول ثاني*\n\n📈 السهم: {symbol}\n💵 السعر الحالي: {current} ريال\n📉 دعم التعديل: {support} ريال\n🎯 الهدف: {target} ريال\n🛑 وقف الخسارة: {stop} ريال"
                        send_telegram(msg)
                        row["حالة التنبيه"] = "تم التعديل - دخول ثاني"
                        updated = True

                except Exception:
                    continue

            if updated:
                with open(csv_filename, mode='w', encoding='utf-8-sig', newline='') as fw:
                    writer = csv.DictWriter(fw, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)

        except Exception as e:
            print("خطأ في قراءة الملف:", e)

        time.sleep(60)

# تشغيل تحليل الأسهم في الخلفية
threading.Thread(target=start_bot).start()

# تشغيل خادم الإنتاج باستخدام waitress
if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)