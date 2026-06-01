import schedule
import time
from datetime import datetime
from sync import sync_invoices
from scheduler import process_reminders


def run_sync():
    print(f"\n{'='*50}")
    print(f"🔄 Syncing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    try:
        sync_invoices()
    except Exception as e:
        print(f"❌ Sync failed: {str(e)}")


def run_reminder_check():
    print(f"\n{'='*50}")
    print(f"📬 Checking reminders at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    try:
        process_reminders()
    except Exception as e:
        print(f"❌ Reminder engine failed: {str(e)}")


if __name__ == "__main__":
    print("🚀 Zoho Finance Reminder System started...")
    print("🔄 Sync scheduled: 9 AM, 2 PM, 6 PM daily")
    print("📬 Reminders checked: every hour\n")

    # run once immediately on startup
    run_sync()
    run_reminder_check()

    # sync 3 times a day
    schedule.every().day.at("09:00").do(run_sync)
    schedule.every().day.at("14:00").do(run_sync)
    schedule.every().day.at("18:00").do(run_sync)

    # check reminders every hour
    schedule.every().hour.do(run_reminder_check)

    while True:
        schedule.run_pending()
        time.sleep(60)