from datetime import datetime, timedelta
import db
from whatsapp import send_whatsapp

# reminder intervals in days from creation date
REMINDER_INTERVALS = [0, 7, 14, 21, 28]

# max age in days for first reminder — skip stale records
MAX_FIRST_REMINDER_AGE = 30


def process_reminders():
    print("Running reminder engine...")

    invoices = db.get_active_invoices()
    sent_count = 0
    today = datetime.now().date()
    today_str = today.strftime("%Y-%m-%d")

    for inv in invoices:

        if not inv["whatsapp_number"]:
            print(f"⚠️ No number for {inv['customer_name']}, skipping")
            continue

        try:
            created = datetime.strptime(inv["invoice_date"], "%Y-%m-%d").date()
        except:
            print(f"⚠️ Bad date for {inv['customer_name']}, skipping")
            continue

        reminder_count = inv["reminder_count"]

        # skip stale invoices older than 30 days that never got a reminder
        days_old = (today - created).days
        if days_old > MAX_FIRST_REMINDER_AGE and reminder_count == 0:
            print(f"⏭️ Skipping stale: {inv['customer_name']} ({days_old} days old)")
            continue

        # all reminders done
        if reminder_count >= len(REMINDER_INTERVALS):
            print(f"⏰ {inv['customer_name']} — all reminders done")
            continue

        # calculate next reminder date
        next_reminder_date = created + timedelta(days=REMINDER_INTERVALS[reminder_count])

        # prevent double firing same day
        last_reminded = inv.get("last_reminder_date", "")
        if last_reminded == today_str:
            print(f"⏭️ Already reminded {inv['customer_name']} today, skipping")
            continue

        if today >= next_reminder_date:
            invoice_type = inv.get("invoice_type", "tax_invoice")

            numbers = [inv["whatsapp_number"]]
            num2 = inv.get("whatsapp_number_2", "")
            if num2 and num2.strip():
                numbers.append(num2.strip())

            all_sent = True
            for number in numbers:
                try:
                    send_whatsapp(
                        number,
                        inv["customer_name"],
                        inv["amount"],
                        inv["invoice_date"],
                        inv.get("invoice_url", ""),
                        invoice_type
                    )
                    print(f"✅ [{invoice_type}] Reminder #{reminder_count + 1} → {inv['customer_name']} ({number})")
                except Exception as e:
                    print(f"❌ Failed → {inv['customer_name']} ({number}): {str(e)}")
                    all_sent = False

            if all_sent:
                db.update_reminder(inv["invoice_id"], reminder_count + 1)
                sent_count += 1

    print(f"\n✅ Done. {sent_count} reminders sent.")


if __name__ == "__main__":
    db.init_db()
    process_reminders()