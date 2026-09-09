import os
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL")


def _connect():
    if DATABASE_URL:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        return conn, psycopg2.extras.RealDictCursor, "%s"
    path = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "reminders.db"))
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn, None, "?"


def init_db():
    conn, DictCursor, ph = _connect()
    cur = conn.cursor()

    pk = "SERIAL PRIMARY KEY" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS reminders (
            id {pk},
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

    extra_cols = [
        ("whatsapp_number_2", "TEXT"),
        ("last_reminder_date", "TEXT"),
        ("invoice_type", "TEXT DEFAULT 'tax_invoice'"),
    ]
    for col, typedef in extra_cols:
        try:
            if DATABASE_URL:
                cur.execute(f"ALTER TABLE reminders ADD COLUMN IF NOT EXISTS {col} {typedef}")
            else:
                cur.execute(f"ALTER TABLE reminders ADD COLUMN {col} {typedef}")
        except Exception:
            if DATABASE_URL:
                conn.rollback()

    conn.commit()
    conn.close()


def upsert_invoice(inv):
    conn, DictCursor, ph = _connect()
    cur = conn.cursor()

    cur.execute(f"""
        INSERT INTO reminders (
            invoice_id, customer_name, whatsapp_number, whatsapp_number_2,
            amount, status, invoice_type, invoice_date, invoice_url
        )
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
        ON CONFLICT(invoice_id) DO UPDATE SET
            customer_name=EXCLUDED.customer_name,
            whatsapp_number=EXCLUDED.whatsapp_number,
            whatsapp_number_2=EXCLUDED.whatsapp_number_2,
            amount=EXCLUDED.amount,
            status=EXCLUDED.status,
            invoice_type=EXCLUDED.invoice_type,
            invoice_date=EXCLUDED.invoice_date,
            invoice_url=EXCLUDED.invoice_url
    """, (
        inv["invoice_id"], inv["customer_name"],
        inv["whatsapp_number"], inv["whatsapp_number_2"],
        inv["amount"], inv["status"], inv["invoice_type"],
        inv["invoice_date"], inv.get("invoice_url", "")
    ))

    conn.commit()
    conn.close()


def get_active_invoices():
    conn, DictCursor, ph = _connect()
    cur = conn.cursor(DictCursor) if DictCursor else conn.cursor()

    cur.execute("""
        SELECT * FROM reminders
        WHERE status IN ('sent', 'open', 'overdue', 'partially_paid', 'pending')
        AND reminder_count < 5
    """)

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_reminder(invoice_id, count):
    from datetime import datetime
    conn, DictCursor, ph = _connect()
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE reminders
        SET reminder_count = {ph},
            last_reminder_date = {ph},
            sent_at = CURRENT_TIMESTAMP
        WHERE invoice_id = {ph}
    """, (count, datetime.now().strftime("%Y-%m-%d"), invoice_id))

    conn.commit()
    conn.close()


def mark_paid(invoice_id):
    conn, DictCursor, ph = _connect()
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE reminders
        SET status = 'paid',
            reminder_count = 5
        WHERE invoice_id = {ph}
    """, (invoice_id,))

    conn.commit()
    conn.close()
