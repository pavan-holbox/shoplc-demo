import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import date, datetime
from decimal import Decimal
import requests
from load_dotenv import load_dotenv
import os
load_dotenv()
from nano_banana import virtual_tryon
# from email_trial import send_product_email




def get_access_token():

    url ="https://atsapiuat.tjc.tv/api/Account/GetToken"

    headers = {
        "accept": "*/*",
        "Content-Type": "application/json"
    }
    payload = {
        "username": os.getenv("username"),
        "password": os.getenv("password")
    }   

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(response.json())  
        data = response.json()
        token = data.get("Data") 
        os.environ["bearer_token"] = token  
        return token
    else:
        print(f"Error {response.status_code}: {response.text}")

        
def fetch_orders(phone_number):

    url = f"https://atsapiuat.tjc.tv/api/ShoppingBuddy/GetCustomerOrder?phoneno={phone_number.replace("+1", "", 1).strip()}"

    api_key = os.getenv("bearer_token")  
    if not api_key:
        raise Exception("Bearer token is missing! Set environment variable 'bearer_token'.")
    headers = {
        "accept": "*/*",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json-patch+json"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 401 or "Unauthorized" in resp.text or resp.status_code == 400:
        token = get_access_token()
        print("------------------------------",token)
        headers["Authorization"] = f"Bearer {token}"
        resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(f"Request failed with {resp.status_code}: {resp.text}")


def get_order_information(orderno):

    url = f"https://atsapiuat.tjc.tv/api/ShoppingBuddy/GetOrderDetails?orderno={orderno}"
    print(url)
    api_key = os.getenv("bearer_token")
    headers = {
        "accept": "*/*",
        "Authorization": f"Bearer {api_key}",
         "Content-Type": "application/json-patch+json"
    }

    resp = requests.get(url, headers=headers)
    if resp.status_code == 401 or "Unauthorized" in resp.text :
        token = get_access_token()
        print("------------------------------",token)
        headers["Authorization"] = f"Bearer {token}"
        resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        return resp.json() 
    else:
        raise Exception(f"Request failed with {resp.status_code}: {resp.text}")
        

def make_json_safe(rows):
    def convert_value(val):
        if isinstance(val, (datetime, date)):
            return val.isoformat()
        if isinstance(val, Decimal):
            return float(val)
        return val

    return [
        {k: convert_value(v) for k, v in row.items()}
        for row in rows
    ]

def get_db_connection():
    return psycopg2.connect(
        dbname="shoplc_voice",
        user="ShopLC_Voice",
        password="voice_agent_shoplc1",
        host="localhost",
        port="5432",
        cursor_factory=RealDictCursor
    )

def get_products_list():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """ 
                select * from upsell_products
                """
            )
            rows = cur.fetchall()
            return make_json_safe(rows)
    finally:
        conn.close()


def get_user_details(phone_number):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """ 
                select * from customers where phone_number = %s 
                """,(phone_number.replace("+1", "", 1).strip(),)
            )
            rows = cur.fetchall()
            return make_json_safe(rows)
    finally:
        conn.close()



def get_customer_id_by_mobile(mobile_number):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT customer_id 
                FROM customers 
                WHERE phone_number = %s
            """, (mobile_number,))
            row = cur.fetchone()
            return row['customer_id'] if row else None
    finally:
        conn.close()


def get_recent_orders_by_customer_id(customer_id, limit=3):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * 
                FROM orders 
                WHERE customer_id = %s 
                ORDER BY order_date DESC 
                LIMIT %s
            """, (customer_id, limit))
            rows = cur.fetchall()
            return make_json_safe(rows) 
    finally:
        conn.close()


FUNCTION_MAP = {
    "fetch_orders":fetch_orders,
    "get_order_information":get_order_information,
    "get_products_list":get_products_list,
    "get_user_details":get_user_details,
    "virtual_tryon":virtual_tryon
}


def get_order_by_order_id(order_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * 
                FROM orders 
                WHERE order_id = %s
            """, (order_id,))
            row = cur.fetchone()
            return row['order_id'] if row else None
    finally:
        conn.close()


def get_orders_by_customer_id_and_date(customer_id, order_date):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * 
                FROM orders 
                WHERE customer_id = %s 
                  AND order_date = %s 
            """, (customer_id, order_date))
            rows = cur.fetchall()
            return make_json_safe(rows) 
    finally:
        conn.close()


def get_order_by_product_name(customer_id, product_name):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT order_id, product, no_of_items, order_date, order_status 
                FROM orders 
                WHERE customer_id = %s 
                  AND LOWER(product) LIKE LOWER(%s)
                ORDER BY order_date DESC
                LIMIT 1
            """, (customer_id, f"%{product_name}%"))
            rows = cur.fetchall()
            return make_json_safe(rows) 
    finally:
        conn.close()


def get_recent_refunds_by_customer_id(customer_id, limit=5):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * 
                FROM refunds 
                WHERE customer_id = %s 
                ORDER BY refund_initiated_date DESC 
                LIMIT %s
            """, (customer_id, limit))
            rows = cur.fetchall()
            return make_json_safe(rows) 
    finally:
        conn.close()


def get_recent_refunds_by_product_name(customer_id, product_name):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.refund_id, r.order_id, r.refund_status,r.refund_method, r.refund_initiated_date, r.refund_processed_date
                FROM refunds r
                JOIN orders o ON r.order_id = o.order_id
                WHERE r.customer_id = %s 
                  AND LOWER(o.product_name) LIKE LOWER(%s)
                ORDER BY r.refund_initiated_date DESC
                LIMIT 1
            """, (customer_id, f"%{product_name}%"))
            rows = cur.fetchall()
            return make_json_safe(rows) 
    finally:
        conn.close()



def get_refund_by_order_id(order_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * 
                FROM refunds 
                WHERE order_id = %s
            """, (order_id,))
            row = cur.fetchone()
            return row['order_id'] if row else None
    finally:
        conn.close()


def get_customer_email_by_phone(phone_number: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT email
                FROM customers
                WHERE phone_number = %s
                """,
                (phone_number,)
            )
            row = cur.fetchone()
            return row["email"] if row else None
    finally:
        conn.close()




# FUNCTION_MAP = {
#     'get_customer_id_by_mobile':get_customer_id_by_mobile,
#     'get_recent_orders_by_customer_id':get_recent_orders_by_customer_id,
#     'get_orders_by_customer_id_and_date':get_orders_by_customer_id_and_date,
#     'get_order_by_product_name':get_order_by_product_name,
#     'get_recent_refunds_by_customer_id':get_recent_refunds_by_customer_id,
#     'get_recent_refunds_by_product_name':get_recent_refunds_by_product_name,
#     'get_refund_by_order_id':get_refund_by_order_id,
#     'get_order_by_order_id' : get_order_by_order_id
# }


# Once you understand the item (Order / refund) that user is lookingfor , you can utilise the order id as well to know product info