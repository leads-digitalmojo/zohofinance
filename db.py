import sqlite3

DB = "reminders.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id TEXT UNIQUE,
        customer_name TEXT,
        whatsapp_number TEXT,
        whatsapp_number_2 TEXT,
        amount REAL,
        status TEXT,
        invoice_type TEXT DEFAULT 'tax_invoice',
        invoice_date TEXT,
        invoice_url TEXT,
        reminder_count INTEGER DEFAULT 0,
        last_reminder_date TEXT,
        sent_at TIMESTAMP
    )
    """)

    # add columns if they don't exist (for existing databases)
    for col in [
        "ALTER TABLE reminders ADD COLUMN whatsapp_number_2 TEXT",
        "ALTER TABLE reminders ADD COLUMN last_reminder_date TEXT",
        "ALTER TABLE reminders ADD COLUMN invoice_type TEXT DEFAULT 'tax_invoice'"
    ]:
        try:
            cur.execute(col)
        except:
            pass

    conn.commit()
    conn.close()


def upsert_invoice(inv):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO reminders (
        invoice_id,
        customer_name,
        whatsapp_number,
        whatsapp_number_2,
        amount,
        status,
        invoice_type,
        invoice_date,
        invoice_url
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(invoice_id) DO UPDATE SET
        customer_name=excluded.customer_name,
        whatsapp_number=excluded.whatsapp_number,
        whatsapp_number_2=excluded.whatsapp_number_2,
        amount=excluded.amount,
        status=excluded.status,
        invoice_type=excluded.invoice_type,
        invoice_date=excluded.invoice_date,
        invoice_url=excluded.invoice_url
    """, (
        inv["invoice_id"],
        inv["customer_name"],
        inv["whatsapp_number"],
        inv["whatsapp_number_2"],
        inv["amount"],
        inv["status"],
        inv["invoice_type"],
        inv["invoice_date"],
        inv.get("invoice_url", "")
    ))

    conn.commit()
    conn.close()


def get_active_invoices():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM reminders
        WHERE status IN ('sent', 'open', 'overdue', 'partially_paid', 'accepted', 'pending')
        AND reminder_count < 5
    """)

    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]


def update_reminder(invoice_id, count):
    from datetime import datetime
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        UPDATE reminders
        SET reminder_count = ?,
            last_reminder_date = ?,
            sent_at = CURRENT_TIMESTAMP
        WHERE invoice_id = ?
    """, (count, datetime.now().strftime("%Y-%m-%d"), invoice_id))

    conn.commit()
    conn.close()


def mark_paid(invoice_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        UPDATE reminders
        SET status = 'paid',
            reminder_count = 5
        WHERE invoice_id = ?
    """, (invoice_id,))

    conn.commit()
    conn.close()