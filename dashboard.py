import streamlit as st
import pandas as pd
import db
import os

# Inject Streamlit secret into env so db.py picks it up
if "DATABASE_URL" in st.secrets:
    os.environ["DATABASE_URL"] = st.secrets["DATABASE_URL"]

st.set_page_config(page_title="Invoice Dashboard", layout="wide")
st.title("📊 Invoice Reminder Dashboard")

db.init_db()

conn, DictCursor, _ = db._connect()
if DictCursor:
    cur = conn.cursor(DictCursor)
else:
    import sqlite3
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

cur.execute("""
    SELECT
        customer_name,
        amount,
        status,
        whatsapp_number,
        reminder_count,
        invoice_date,
        sent_at
    FROM reminders
    ORDER BY invoice_date DESC
""")

rows = cur.fetchall()
conn.close()

df = pd.DataFrame([dict(r) for r in rows])

st.subheader("📋 All Invoices")

if df.empty:
    st.warning("No data found. Run sync.py first.")
else:
    st.success(f"Total invoices: {len(df)}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Overdue", len(df[df["status"] == "overdue"]))
    col2.metric("Paid", len(df[df["status"] == "paid"]))
    col3.metric("With Phone Number", len(df[df["whatsapp_number"] != ""]))

    status_filter = st.selectbox(
        "Filter by status",
        options=["all"] + list(df["status"].dropna().unique())
    )

    if status_filter != "all":
        df = df[df["status"] == status_filter]

    st.dataframe(df, use_container_width=True)
