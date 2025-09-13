import os
import json
import asyncio
import aiohttp
import asyncpg
from load_dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal
from nano_banana import virtual_tryon




load_dotenv()
# ========== CONFIG ==========
USER_INFO_JSON = "user_info.json"

DB_CONFIG = {
    "user": os.getenv("user"),
    "password": os.getenv("pass"),
    "database": os.getenv("dbname"),
    "host": os.getenv("host"),
    "port": int(os.getenv("port", 5432)),
}


# ========== CACHE ==========
_user_cache = {}          # in-memory results
_inflight_tasks = {}      # track ongoing fetches (avoid duplicate calls)





def make_json_safe(rows):
    safe_rows = []
    for row in rows:
        record = {}
        for key, value in dict(row).items():
            if isinstance(value, datetime):
                record[key] = value.isoformat()  # e.g. "2025-08-29T12:41:08"
            else:
                record[key] = value
        safe_rows.append(record)
    return safe_rows

async def _load_from_disk():
    if os.path.exists(USER_INFO_JSON):
        with open(USER_INFO_JSON, "r", encoding="UTF-8") as f:
            return json.load(f)
    return {}


async def init_cache():
    global _user_cache
    _user_cache = await _load_from_disk()


async def _save_to_disk():
    await asyncio.to_thread(
        lambda: open(USER_INFO_JSON, "w", encoding="UTF-8").write(
            json.dumps(_user_cache, ensure_ascii=False, indent=4)
        )
    )


# ========== DB HELPERS ==========
async def get_db_connection():
    return await asyncpg.connect(**DB_CONFIG)


# ========== TOKEN ==========
async def get_access_token():
    url = "https://atsapiuat.tjc.tv/api/Account/GetToken"
    headers = {"accept": "*/*", "Content-Type": "application/json"}
    payload = {"username": os.getenv("username"), "password": os.getenv("password")}
    print(payload)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                print(data)
                token = data.get("Data")
                if not token:
                    raise Exception("No token in response")
                os.environ["bearer_token"] = token
                return token
            else:
                raise Exception(f"Token request failed {response.status}: {await response.text()}")


# ========== TOOL: GET USER DETAILS ==========
async def get_user_details(phone_number: str, call_sid : str):
    phone = phone_number.replace("+1", "", 1).strip()

    # 1. Check in-memory cache
    if call_sid in _user_cache and "user_details" in _user_cache[call_sid]:
        return _user_cache[call_sid]["user_details"]

    # 2. If another task is fetching → wait
    if call_sid in _inflight_tasks:
        await _inflight_tasks[call_sid]
        return _user_cache.get(call_sid, {}).get("user_details")

    async def fetch_and_cache():
        conn = await get_db_connection()
        try:
            rows = await conn.fetch("SELECT * FROM customers WHERE phone_number = $1", phone)
            print(rows)
            user_details = make_json_safe(rows)
        finally:
            await conn.close()

        # Save to cache
        if call_sid not in _user_cache:
            _user_cache[call_sid] = {}
        _user_cache[call_sid]["user_details"] = user_details
        await _save_to_disk()
        return user_details

    task = asyncio.create_task(fetch_and_cache())
    _inflight_tasks[call_sid] = task
    try:
        return await task
    finally:
        _inflight_tasks.pop(call_sid, None)

async def get_products_list():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
                """ 
                select * from upsell_products
                """
            )
        # rows = cur.fetchall()
        return make_json_safe(rows)
    finally:
        conn.close()


# ========== TOOL: FETCH ORDERS ==========
async def fetch_orders(phone_number: str,call_sid:str):
    phone = phone_number.replace("+1", "", 1).strip()

    # 1. Check in-memory cache
    if call_sid in _user_cache and "orders" in _user_cache[call_sid]:
        return _user_cache[call_sid]["orders"]

    # 2. If another task is fetching → wait
    if call_sid in _inflight_tasks:
        await _inflight_tasks[call_sid]
        return _user_cache.get(call_sid, {}).get("orders")

    async def fetch_and_cache():
        url = f"https://atsapiuat.tjc.tv/api/ShoppingBuddy/GetCustomerOrder?phoneno={phone}"
        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {os.getenv('bearer_token')}",
            "Content-Type": "application/json-patch+json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                text = await resp.text()
                if resp.status in (400, 401) or "Unauthorized" in text:
                    token = await get_access_token()
                    headers["Authorization"] = f"Bearer {token}"
                    async with session.get(url, headers=headers) as retry_resp:
                        if retry_resp.status == 200:
                            orders = await retry_resp.json()
                        else:
                            raise Exception(f"Retry failed {retry_resp.status}: {await retry_resp.text()}")
                elif resp.status == 200:
                    orders = await resp.json()
                else:
                    raise Exception(f"Fetch orders failed {resp.status}: {text}")

        # Save to cache
        if call_sid not in _user_cache:
            _user_cache[call_sid] = {}
        _user_cache[call_sid]["orders"] = orders
        await _save_to_disk()
        return orders

    task = asyncio.create_task(fetch_and_cache())
    _inflight_tasks[call_sid] = task
    try:
        return await task
    finally:
        _inflight_tasks.pop(call_sid, None)




async def get_order_information( orderno: str, call_sid: str):
    cache_key = f"{call_sid}:{orderno}"  # unique cache key per call + order

    # 1. Check in-memory cache
    if cache_key in _user_cache and "order_info" in _user_cache[cache_key]:
        return _user_cache[cache_key]["order_info"]

    # 2. If another task is fetching → wait for it
    if cache_key in _inflight_tasks:
        await _inflight_tasks[cache_key]
        return _user_cache.get(cache_key, {}).get("order_info")

    async def fetch_and_cache():
        url = f"https://atsapiuat.tjc.tv/api/ShoppingBuddy/GetOrderDetails?orderno={orderno}"
        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {os.getenv('bearer_token')}",
            "Content-Type": "application/json-patch+json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                text = await resp.text()

                if resp.status == 401 or "Unauthorized" in text:
                    # refresh token
                    token = await get_access_token()
                    headers["Authorization"] = f"Bearer {token}"

                    async with session.get(url, headers=headers) as retry_resp:
                        if retry_resp.status == 200:
                            order_info = await retry_resp.json()
                        else:
                            raise Exception(
                                f"Retry failed {retry_resp.status}: {await retry_resp.text()}"
                            )
                elif resp.status == 200:
                    order_info = await resp.json()
                else:
                    raise Exception(f"Fetch order info failed {resp.status}: {text}")

        # Save to cache + disk
        if cache_key not in _user_cache:
            _user_cache[cache_key] = {}
        _user_cache[cache_key]["order_info"] = order_info
        await _save_to_disk()
        return order_info

    task = asyncio.create_task(fetch_and_cache())
    _inflight_tasks[cache_key] = task
    try:
        return await task
    finally:
        _inflight_tasks.pop(cache_key, None)


FUNCTION_MAP = {
    "fetch_orders":fetch_orders,
    "get_order_information":get_order_information,
    "get_products_list":get_products_list,
    "get_user_details":get_user_details,
    "virtual_tryon":virtual_tryon
}