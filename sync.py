import db
from zoho import get_invoices, get_estimates, get_contact


def get_phone_numbers(contact_id):
    phone_1 = ""
    phone_2 = ""

    if not contact_id:
        return phone_1, phone_2

    contact_data = get_contact(contact_id)
    if not contact_data:
        return phone_1, phone_2

    contact = contact_data.get("contact", {})
    mobile = contact.get("mobile", "").strip()
    work_phone = contact.get("work_phone", "").strip()
    phone_field = contact.get("phone", "").strip()

    # primary — prefer mobile
    phone_1 = mobile or work_phone or phone_field or ""

    # secondary — if two different numbers exist
    if mobile and work_phone and mobile != work_phone:
        phone_2 = work_phone
    elif mobile and phone_field and mobile != phone_field:
        phone_2 = phone_field

    return phone_1, phone_2


def sync_invoices():
    print("🚀 Starting Zoho sync...")
    db.init_db()

    total = 0

    # ── Pull Tax Invoices ─────────────────────────────────────
    try:
        data = get_invoices()
        invoices = data.get("invoices", [])
        print(f"📊 Tax invoices fetched: {len(invoices)}")

        for inv in invoices:
            invoice_id = inv.get("invoice_id")
            customer_name = inv.get("customer_name")
            amount = inv.get("total")
            status = inv.get("status")
            invoice_date = inv.get("date")
            invoice_url = inv.get("invoice_url", "")
            contact_id = inv.get("customer_id")

            phone_1, phone_2 = get_phone_numbers(contact_id)

            phones_display = phone_1 or "NO NUMBER"
            if phone_2:
                phones_display += f" + {phone_2}"

            print(f"💾 [TAX] {customer_name} | {status} | 📱 {phones_display}")

            record = {
                "invoice_id": invoice_id,
                "customer_name": customer_name,
                "whatsapp_number": phone_1,
                "whatsapp_number_2": phone_2,
                "amount": amount,
                "status": status,
                "invoice_type": "tax_invoice",
                "invoice_date": invoice_date,
                "invoice_url": invoice_url
            }

            db.upsert_invoice(record)

            if status in ("paid", "void"):
                db.mark_paid(invoice_id)

            total += 1

    except Exception as e:
        print("❌ Invoice sync failed:", str(e))

    # ── Pull Quotes/Estimates ─────────────────────────────────
    try:
        data = get_estimates()
        estimates = data.get("estimates", [])
        print(f"📋 Quotes fetched: {len(estimates)}")

        for est in estimates:
            estimate_id = est.get("estimate_id")
            customer_name = est.get("customer_name")
            amount = est.get("total")
            status = est.get("status")
            estimate_date = est.get("date")
            estimate_url = est.get("estimate_url", "")
            contact_id = est.get("customer_id")

            phone_1, phone_2 = get_phone_numbers(contact_id)

            phones_display = phone_1 or "NO NUMBER"
            if phone_2:
                phones_display += f" + {phone_2}"

            print(f"💾 [QUOTE] {customer_name} | {status} | 📱 {phones_display}")

            record = {
                "invoice_id": f"EST-{estimate_id}",
                "customer_name": customer_name,
                "whatsapp_number": phone_1,
                "whatsapp_number_2": phone_2,
                "amount": amount,
                "status": status,
                "invoice_type": "quote",
                "invoice_date": estimate_date,
                "invoice_url": estimate_url
            }

            db.upsert_invoice(record)

            # stop reminders if quote is accepted/invoiced/void
            if status in ("invoiced", "void"):
                db.mark_paid(f"EST-{estimate_id}")

            total += 1

    except Exception as e:
        print("❌ Quote sync failed:", str(e))

    print(f"\n✅ Sync completed: {total} records processed")


if __name__ == "__main__":
    sync_invoices()