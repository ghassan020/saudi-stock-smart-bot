import csv
import requests
import time
from flask import Flask
import threading

# إعدادات Telegram
TOKEN = "7687004188:AAEptk2YeH1RruqV83YyOTMdndU7sdA7fmo"
CHAT_ID = "756852322"

def send_telegram(message_text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message_text}
    requests.get(url, params=params)

# خادم Flask لتشغيل UptimeRobot
app = Flask('')
@app.route('/')
def home():
    return "Bot is running."

def run_web():
    app.run(host='0.0.0.0', port=8080)

# تشغيل Flask في خلفية Replit
threading.Thread(target=run_web).start()

# اسم ملف CSV
csv_filename = "saudi-stock-alerts-with-adjustment.csv"

# حلقة الفحص التلقائي
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

                # تنبيه اقتراب من نقطة الدخول (أقل من 1%)
                if status == "" and (entry * 0.99 <= current < entry):
                    msg = f"{symbol}: اقترب من نقطة الدخول (السعر الحالي {current} ريال)"
                    send_telegram(msg)
                    row["حالة التنبيه"] = "تنبيه اقتراب"
                    updated = True

                # تنبيه دخول فعلي
                elif status in ["", "تنبيه اقتراب"] and current >= entry:
                    msg = f"{symbol}: تنبيه دخول أول عند {entry}"
                    send_telegram(msg)
                    row["حالة التنبيه"] = "تم الدخول"
                    updated = True

                # تحقق الهدف
                elif status == "تم الدخول" and current >= target:
                    msg = f"{symbol}: ✅ تحقق الهدف عند {target}"
                    send_telegram(msg)
                    row["حالة التنبيه"] = "تحقق الهدف"
                    updated = True

                # وقف الخسارة
                elif status == "تم الدخول" and current <= stop:
                    msg = f"{symbol}: ❌ تفعيل وقف الخسارة عند {stop}"
                    send_telegram(msg)
                    row["حالة التنبيه"] = "وقف الخسارة"
                    updated = True

                # دخول ذكي (تعديل)
                elif status == "تم الدخول" and current <= support:
                    msg = f"{symbol}: دخول ثاني ذكي عند الدعم {support}"
                    send_telegram(msg)
                    row["حالة التنبيه"] = "تم التعديل - دخول ثاني"
                    updated = True

            except Exception as e:
                continue

        if updated:
            with open(csv_filename, mode='w', encoding='utf-8-sig', newline='') as fw:
                writer = csv.DictWriter(fw, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

    except Exception as e:
        print("خطأ أثناء قراءة أو كتابة الملف:", e)

    time.sleep(60)