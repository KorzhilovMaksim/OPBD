from db import execute_query

def calculate_order_cost(order_id):
    items = execute_query("SELECT SUM(total) as total FROM OrderItems WHERE order_id=%s", (order_id,), fetch_one=True)
    return items['total'] if items and items['total'] else 0

def calculate_material_cost_for_product(product_id):
    mats = execute_query("""
        SELECT pm.quantity, m.price 
        FROM ProductMaterial pm
        JOIN Materials m ON pm.material_id = m.id
        WHERE pm.product_id = %s
    """, (product_id,), fetch_all=True)
    total = sum(m['quantity'] * m['price'] for m in mats)
    return total