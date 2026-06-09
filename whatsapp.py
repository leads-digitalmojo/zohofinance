import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("INTERAKT_API_KEY")


def clean_number(to):
    to = to.replace("+", "").replace("-", "").replace(" ", "").strip()
    if len(to) == 10:
        to = "91" + to
    return to


def send_whatsapp(to, customer_name, amount, invoice_date, invoice_url="", invoice_type="tax_invoice"):

    to = clean_number(to)
    print(f"📱 Sending to: {to} | type: {invoice_type}")


    # format date nicely
    try:
        from datetime import datetime
        formatted_date = datetime.strptime(invoice_date, "%Y-%m-%d").strftime("%d-%b-%Y")
    except:
        formatted_date = invoice_date

    # pick template based on invoice type
    if invoice_type == "quote":
        template_name = "quote_reminder_v2"
    else:
        template_name = "tax_invoice_reminder_v2"

    payload = {
        "countryCode": "+91",
        "phoneNumber": to[2:],
        "callbackData": f"{invoice_type}_reminder",
        "type": "Template",
        "template": {
            "name": template_name,
            "languageCode": "en",
            "bodyValues": [
                customer_name,
                str(amount),
                formatted_date,
                invoice_url
            ]
        }
    }

    # only add button if we have a valid URL
    

    headers = {
        "Authorization": f"Basic {API_KEY}",
        "Content-Type": "application/json"
    }

    res = requests.post(
        "https://api.interakt.ai/v1/public/message/",
        json=payload,
        headers=headers
    )

    print("Interakt:", res.text)

    data = res.json()

    if not data.get("result", False):
        raise Exception(res.text)

    return data