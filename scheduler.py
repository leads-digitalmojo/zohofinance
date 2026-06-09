from datetime import datetime, timedelta
import db
from whatsapp import send_whatsapp

# Configuration
MAX_REMINDERS = 5
REMINDER_GAP_DAYS = 7
MAX_FIRST_REMINDER_AGE = 30


def process_reminders():
    print("Running reminder engine...")

    invoices = db.get_active_invoices()
    sent_count = 0

    today = datetime.now().date()
    today_str = today.strftime("%Y-%m-%d")

    for inv in invoices:

        customer_name = inv.get("customer_name", "Unknown")

        # No phone number
        if not inv.get("whatsapp_number"):
            print(f"⚠️ No number for {customer_name}, skipping")
            continue

        # Parse invoice date
        try:
            created = datetime.strptime(
                inv["invoice_date"],
                "%Y-%m-%d"
            ).date()
        except Exception:
            print(f"⚠️ Bad date for {customer_name}, skipping")
            continue

        reminder_count = inv.get("reminder_count", 0)

        # Stop after 5 reminders
        if reminder_count >= MAX_REMINDERS:
            print(f"⏰ {customer_name} — all reminders completed")
            continue

        # Skip stale records that never received reminder #1
        days_old = (today - created).days

        if (
            reminder_count == 0 and
            days_old > MAX_FIRST_REMINDER_AGE
        ):
            print(
                f"⏭️ Skipping stale: "
                f"{customer_name} ({days_old} days old)"
            )
            continue

        last_reminded = inv.get("last_reminder_date")

        # Prevent duplicate send on same day
        if last_reminded == today_str:
            print(
                f"⏭️ Already reminded "
                f"{customer_name} today, skipping"
            )
            continue

        # Reminder #1
        if reminder_count == 0:

            next_reminder_date = created

        # Reminder #2 onward
        else:

            if not last_reminded:
                print(
                    f"⚠️ Missing last_reminder_date "
                    f"for {customer_name}, skipping"
                )
                continue

            try:
                last_reminder_date = datetime.strptime(
                    last_reminded,
                    "%Y-%m-%d"
                ).date()

            except Exception:
                print(
                    f"⚠️ Invalid last_reminder_date "
                    f"for {customer_name}, skipping"
                )
                continue

            next_reminder_date = (
                last_reminder_date +
                timedelta(days=REMINDER_GAP_DAYS)
            )

        # Not due yet
        if today < next_reminder_date:
            print(
                f"⏭️ Not due yet: "
                f"{customer_name} "
                f"(next: {next_reminder_date})"
            )
            continue

        invoice_type = inv.get(
            "invoice_type",
            "tax_invoice"
        )

        numbers = []

        primary = inv.get("whatsapp_number")
        secondary = inv.get("whatsapp_number_2")

        if primary:
            numbers.append(primary.strip())

        if secondary and secondary.strip():
            numbers.append(secondary.strip())

        all_sent = True

        for number in numbers:

            try:

                send_whatsapp(
                    number,
                    customer_name,
                    inv["amount"],
                    inv["invoice_date"],
                    inv.get("invoice_url", ""),
                    invoice_type
                )

                print(
                    f"✅ [{invoice_type}] "
                    f"Reminder #{reminder_count + 1} "
                    f"→ {customer_name} ({number})"
                )

            except Exception as e:

                print(
                    f"❌ Failed → "
                    f"{customer_name} ({number}): {e}"
                )

                all_sent = False

        # Update reminder only if all messages sent successfully
        if all_sent:

            db.update_reminder(
                inv["invoice_id"],
                reminder_count + 1
            )

            sent_count += 1

    print(f"\n✅ Done. {sent_count} reminders sent.")


if __name__ == "__main__":
    db.init_db()
    process_reminders()