import os
import aiohttp
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import date, datetime
from decimal import Decimal
import requests
from load_dotenv import load_dotenv
import os
load_dotenv()

# user_info = {}


async def get_access_token():
    url = "https://atsapiuat.tjc.tv/api/Account/GetToken"

    headers = {
        "accept": "*/*",
        "Content-Type": "application/json"
    }
    payload = {
        "username": os.getenv("username"),
        "password": os.getenv("password")
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                print(data)
                token = data.get("Data")
                if token:
                    os.environ["bearer_token"] = token
                    return token
                else:
                    raise Exception("No token found in response.")
            else:
                text = await response.text()
                raise Exception(f"Error {response.status}: {text}")


async def fetch_orders(phone_number: str):
    url = f"https://atsapiuat.tjc.tv/api/ShoppingBuddy/GetCustomerOrder?phoneno={phone_number.replace('+1', '', 1).strip()}"

    api_key = os.getenv("bearer_token")
    if not api_key:
        raise Exception("Bearer token is missing! Set environment variable 'bearer_token'.")

    headers = {
        "accept": "*/*",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json-patch+json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            text = await resp.text()
            if resp.status == 401 or "Unauthorized" in text or resp.status == 400:
                token = await get_access_token()
                print("------------------------------", token)
                headers["Authorization"] = f"Bearer {token}"
                async with session.get(url, headers=headers) as retry_resp:
                    if retry_resp.status == 200:
                        return await retry_resp.json()
                    else:
                        raise Exception(f"Request failed with {retry_resp.status}: {await retry_resp.text()}")
            
            if resp.status == 200:
                return await resp.json()
            else:
                raise Exception(f"Request failed with {resp.status}: {text}")



async def get_order_information(orderno: str):
    url = f"https://atsapiuat.tjc.tv/api/ShoppingBuddy/GetOrderDetails?orderno={orderno}"
    print(url)

    api_key = os.getenv("bearer_token")
    headers = {
        "accept": "*/*",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json-patch+json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            text = await resp.text()

            if resp.status == 401 or "Unauthorized" in text:
                from your_module import get_access_token  
                token = await get_access_token()
                print("------------------------------", token)
                headers["Authorization"] = f"Bearer {token}"

                async with session.get(url, headers=headers) as retry_resp:
                    if retry_resp.status == 200:
                        return await retry_resp.json()
                    else:
                        raise Exception(f"Request failed with {retry_resp.status}: {await retry_resp.text()}")

            if resp.status == 200:
                return await resp.json()
            else:
                raise Exception(f"Request failed with {resp.status}: {text}")





import asyncpg
import os

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
}

async def get_db_connection():
    return await asyncpg.connect(**DB_CONFIG)

def make_json_safe(rows):
    # Convert asyncpg Records to dicts
    return [dict(row) for row in rows]

async def get_products_list():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""SELECT * FROM upsell_products""")
        return make_json_safe(rows)
    finally:
        await conn.close()


async def get_user_details(phone_number: str):
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            """SELECT * FROM customers WHERE phone_number = $1""",
            phone_number.replace("+1", "", 1).strip()
        )
        return make_json_safe(rows)
    finally:
        await conn.close()
