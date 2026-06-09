import tkinter as tk
from tkinter import ttk, messagebox
from db import execute_query, insert_order_with_items
from excel_export import export_table_to_excel
from order_calc import calculate_order_cost

class ClientWindow:
    def __init__(self, user):
        self.user = user
        self.customer_id = user['customer_id']
        self.window = tk.Tk()
        self.window.title("Панель клиента")
        self.window.geometry("900x600")
        self.create_widgets()

    def create_widgets(self):
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True)

        # Каталог товаров
        self.catalog_frame = ttk.Frame(notebook)
        notebook.add(self.catalog_frame, text="Каталог товаров")
        self.create_catalog_tab()

        # Мои заказы
        self.orders_frame = ttk.Frame(notebook)
        notebook.add(self.orders_frame, text="Мои заказы")
        self.create_orders_tab()

        # Новый заказ
        self.new_order_frame = ttk.Frame(notebook)
        notebook.add(self.new_order_frame, text="Новый заказ")
        self.create_new_order_tab()

    def create_catalog_tab(self):
        tree = ttk.Treeview(self.catalog_frame, columns=('id','name','unit','price'), show='headings')
        tree.heading('id', text='ID')
        tree.heading('name', text='Товар')
        tree.heading('unit', text='Ед.')
        tree.heading('price', text='Цена, руб')
        tree.pack(fill='both', expand=True)

        products = execute_query("SELECT id,name,unit,price FROM Products ORDER BY name", fetch_all=True)
        for p in products:
            tree.insert('', 'end', values=(p['id'], p['name'], p['unit'], p['price']))

        btn_frame = tk.Frame(self.catalog_frame)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="Экспорт каталога в Excel",
                  command=lambda: self.export_catalog()).pack(side='left', padx=5)

    def export_catalog(self):
        try:
            export_table_to_excel('Products', 'catalog.xlsx')
            messagebox.showinfo("Экспорт", "Каталог сохранён в catalog.xlsx")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {e}")

    def create_orders_tab(self):
        self.orders_tree = ttk.Treeview(self.orders_frame, columns=('id','date','total'), show='headings')
        self.orders_tree.heading('id', text='№ заказа')
        self.orders_tree.heading('date', text='Дата')
        self.orders_tree.heading('total', text='Сумма, руб')
        self.orders_tree.pack(fill='both', expand=True)
        self.refresh_orders()

        btn_frame = tk.Frame(self.orders_frame)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="Рассчитать стоимость выбранного заказа",
                  command=self.show_order_cost).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Экспорт моих заказов в Excel",
                  command=self.export_orders).pack(side='left', padx=5)

        self.items_tree = ttk.Treeview(self.orders_frame, columns=('product','qty','price','total'), show='headings')
        self.items_tree.heading('product', text='Товар')
        self.items_tree.heading('qty', text='Кол-во')
        self.items_tree.heading('price', text='Цена за ед.')
        self.items_tree.heading('total', text='Сумма')
        self.items_tree.pack(fill='both', expand=True, pady=5)
        tk.Label(self.orders_frame, text="Позиции выбранного заказа:").pack()

    def refresh_orders(self):
        for i in self.orders_tree.get_children():
            self.orders_tree.delete(i)
        orders = execute_query("SELECT id, order_date, total_amount FROM Orders WHERE customer_id=%s ORDER BY id DESC",
                               (self.customer_id,), fetch_all=True)
        for o in orders:
            self.orders_tree.insert('', 'end', values=(o['id'], o['order_date'], o['total_amount']))

    def show_order_cost(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите заказ")
            return
        order_id = self.orders_tree.item(selected[0])['values'][0]
        cost = calculate_order_cost(order_id)
        messagebox.showinfo("Стоимость заказа", f"Полная стоимость заказа №{order_id}: {cost:.2f} руб.")
        items = execute_query("""
            SELECT p.name, oi.quantity, oi.unit_price, oi.total
            FROM OrderItems oi
            JOIN Products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (order_id,), fetch_all=True)
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        for item in items:
            self.items_tree.insert('', 'end', values=(item['name'], item['quantity'], item['unit_price'], item['total']))

    def export_orders(self):
        orders = execute_query("SELECT * FROM Orders WHERE customer_id=%s", (self.customer_id,), fetch_all=True)
        if orders:
            import pandas as pd
            df = pd.DataFrame(orders)
            df.to_excel('my_orders.xlsx', index=False)
            messagebox.showinfo("Экспорт", "Сохранено в my_orders.xlsx")
        else:
            messagebox.showinfo("Нет данных", "У вас нет заказов")

    def create_new_order_tab(self):
        self.cart = []

        left_frame = tk.Frame(self.new_order_frame)
        left_frame.pack(side='left', fill='both', expand=True)

        tk.Label(left_frame, text="Доступные товары:").pack()
        self.products_tree = ttk.Treeview(left_frame, columns=('id','name','price'), show='headings')
        self.products_tree.heading('id', text='ID')
        self.products_tree.heading('name', text='Товар')
        self.products_tree.heading('price', text='Цена')
        self.products_tree.pack(fill='both', expand=True)
        products = execute_query("SELECT id,name,price FROM Products ORDER BY name", fetch_all=True)
        for p in products:
            self.products_tree.insert('', 'end', values=(p['id'], p['name'], p['price']))

        right_frame = tk.Frame(self.new_order_frame)
        right_frame.pack(side='right', fill='both', expand=True)

        tk.Label(right_frame, text="Корзина:").pack()
        self.cart_listbox = tk.Listbox(right_frame, width=50)
        self.cart_listbox.pack(fill='both', expand=True)

        tk.Label(right_frame, text="Количество:").pack(pady=5)
        self.qty_entry = tk.Entry(right_frame)
        self.qty_entry.pack(pady=5)

        btn_frame = tk.Frame(right_frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Добавить в корзину", command=self.add_to_cart).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Удалить выбранное из корзины", command=self.remove_from_cart).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Оформить заказ", command=self.checkout).pack(side='left', padx=5)

    def add_to_cart(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите товар")
            return
        prod_id, name, price = self.products_tree.item(selected[0])['values']
        qty_str = self.qty_entry.get().strip()
        if not qty_str:
            messagebox.showerror("Ошибка", "Введите количество")
            return
        try:
            qty = float(qty_str)
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Количество должно быть положительным числом")
            return
        total = qty * float(price)
        self.cart.append((prod_id, name, qty, price, total))
        self.cart_listbox.insert('end', f"{name} x {qty} = {total:.2f} руб.")
        self.qty_entry.delete(0, tk.END)

    def remove_from_cart(self):
        selected = self.cart_listbox.curselection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите позицию в корзине")
            return
        index = selected[0]
        del self.cart[index]
        self.cart_listbox.delete(index)

    def checkout(self):
        if not self.cart:
            messagebox.showerror("Ошибка", "Корзина пуста")
            return
        if not self.customer_id:
            messagebox.showerror("Ошибка", "Ваш аккаунт не привязан к заказчику.")
            return

        try:
            order_id, total_sum = insert_order_with_items(self.customer_id, self.cart)
            messagebox.showinfo("Успех", f"Заказ №{order_id} оформлен на сумму {total_sum:.2f} руб.")
            self.cart.clear()
            self.cart_listbox.delete(0, tk.END)
            self.refresh_orders()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось оформить заказ: {e}")