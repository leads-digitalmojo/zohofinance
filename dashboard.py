import streamlit as st
import sqlite3
import pandas as pd
import db

st.set_page_config(page_title="Invoice Dashboard", layout="wide")
st.title("📊 Invoice Reminder Dashboard")

db.init_db()

conn = sqlite3.connect("reminders.db")

df = pd.read_sql_query("""
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
""", conn)

conn.close()

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