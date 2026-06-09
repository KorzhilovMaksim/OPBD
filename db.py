import pymysql
from config import DB_CONFIG

def get_connection():
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            if fetch_one:
                return cursor.fetchone()
            if fetch_all:
                return cursor.fetchall()
            conn.commit()
            return cursor.lastrowid if not (fetch_one or fetch_all) else None
    finally:
        conn.close()

def insert_order_with_items(customer_id, cart):
    """Вставляет заказ и его позиции в одной транзакции, возвращает order_id и сумму."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            conn.begin()
            cursor.execute("INSERT INTO Orders (customer_id, order_date, total_amount) VALUES (%s, CURDATE(), 0)",
                           (customer_id,))
            order_id = cursor.lastrowid
            total_sum = 0
            for prod_id, name, qty, price, total in cart:
                cursor.execute("INSERT INTO OrderItems (order_id, product_id, quantity, unit_price, total) VALUES (%s,%s,%s,%s,%s)",
                               (order_id, prod_id, qty, price, total))
                total_sum += total
            cursor.execute("UPDATE Orders SET total_amount=%s WHERE id=%s", (total_sum, order_id))
            conn.commit()
            return order_id, total_sum
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def insert_production_with_materials(product_id, quantity, materials):
    """
    Вставляет производственный заказ и автоматически списывает материалы.
    materials: список словарей {'material_id': int, 'quantity': float}
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            conn.begin()
            cursor.execute("INSERT INTO Productions (product_id, quantity, production_date, status) VALUES (%s, %s, CURDATE(), 'planned')",
                           (product_id, quantity))
            prod_order_id = cursor.lastrowid
            for mat in materials:
                cursor.execute("INSERT INTO ProductionMaterials (production_id, material_id, quantity) VALUES (%s, %s, %s)",
                               (prod_order_id, mat['material_id'], mat['quantity']))
            conn.commit()
            return prod_order_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_failed_attempts(username, increment=True):
    """Увеличивает или сбрасывает счетчик неудачных попыток."""
    if increment:
        execute_query("UPDATE Users SET failed_attempts = failed_attempts + 1 WHERE username = %s", (username,))
        # Блокируем если попыток >= 3
        execute_query("UPDATE Users SET is_locked = TRUE WHERE username = %s AND failed_attempts >= 3", (username,))
    else:
        execute_query("UPDATE Users SET failed_attempts = 0, is_locked = FALSE WHERE username = %s", (username,))

def is_user_locked(username):
    """Проверяет, заблокирован ли пользователь."""
    user = execute_query("SELECT is_locked FROM Users WHERE username = %s", (username,), fetch_one=True)
    return user and user['is_locked']