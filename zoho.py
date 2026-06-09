import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
ORG_ID = os.getenv("ZOHO_ORG_ID")

TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
API_URL = "https://www.zohoapis.com/books/v3"

_cached_token = None
_token_expiry = 0


def get_access_token():
    global _cached_token, _token_expiry

    if _cached_token and time.time() < _token_expiry:
        return _cached_token

    payload = {
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
    }

    try:
        res = requests.post(TOKEN_URL, data=payload, timeout=10)
        data = res.json()
    except Exception as e:
        print("❌ Token request failed:", str(e))
        raise

    if "access_token" not in data:
        print("❌ Zoho token generation failed:", data)
        raise Exception("Failed to generate access token from Zoho")

    _cached_token = data["access_token"]
    _token_expiry = time.time() + 3300

    return _cached_token


def get_invoices():
    token = get_access_token()

    url = f"{API_URL}/invoices"
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    params = {
        "organization_id": ORG_ID,
        "per_page": 200,
        "sort_column": "date",
        "sort_order": "D"
    }

    res = requests.get(url, headers=headers, params=params)
    print("📊 INVOICE STATUS:", res.status_code)

    if res.status_code != 200:
        raise Exception(res.text)

    return res.json()


def get_estimates():
    token = get_access_token()

    url = f"{API_URL}/estimates"
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    params = {
        "organization_id": ORG_ID,
        "per_page": 200,
        "sort_column": "date",
        "sort_order": "D"
    }

    res = requests.get(url, headers=headers, params=params)
    print("📋 ESTIMATE STATUS:", res.status_code)

    if res.status_code != 200:
        raise Exception(res.text)

    return res.json()


def get_contact(contact_id):
    if not contact_id:
        return None

    token = get_access_token()

    url = f"{API_URL}/contacts/{contact_id}"
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    params = {"organization_id": ORG_ID}

    res = requests.get(url, headers=headers, params=params)

    if res.status_code != 200:
        print("⚠️ Contact fetch failed:", res.text)
        return None

    return res.json()

def get_estimate_details(estimate_id):
    token = get_access_token()

    url = f"{API_URL}/estimates/{estimate_id}"

    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }

    params = {
        "organization_id": ORG_ID
    }

    res = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    print("ESTIMATE DETAILS:", res.status_code)

    if res.status_code != 200:
        print(res.text)
        return None

    return res.json()