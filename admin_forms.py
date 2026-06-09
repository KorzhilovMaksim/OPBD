import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from db import execute_query, insert_production_with_materials
from excel_export import export_table_to_excel
from order_calc import calculate_order_cost, calculate_material_cost_for_product

class AdminWindow:
    def __init__(self, user):
        self.user = user
        self.window = tk.Tk()
        self.window.title("Панель администратора")
        self.window.geometry("1100x700")
        self.product_map = {}
        self.material_map = {}
        self.create_widgets()

    def create_widgets(self):
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True)

        self.products_frame = ttk.Frame(notebook)
        notebook.add(self.products_frame, text="Товары")
        self.create_products_tab()

        self.materials_frame = ttk.Frame(notebook)
        notebook.add(self.materials_frame, text="Материалы")
        self.create_materials_tab()

        self.spec_frame = ttk.Frame(notebook)
        notebook.add(self.spec_frame, text="Спецификации")
        self.create_spec_tab()

        self.orders_frame = ttk.Frame(notebook)
        notebook.add(self.orders_frame, text="Заказы")
        self.create_orders_tab()

        self.productions_frame = ttk.Frame(notebook)
        notebook.add(self.productions_frame, text="Производства")
        self.create_productions_tab()

        self.customers_frame = ttk.Frame(notebook)
        notebook.add(self.customers_frame, text="Контрагенты")
        self.create_customers_tab()

        self.users_frame = ttk.Frame(notebook)
        notebook.add(self.users_frame, text="Пользователи")
        self.create_users_tab()

    # -------------------- Продукты --------------------
    def create_products_tab(self):
        self.products_tree = ttk.Treeview(self.products_frame, columns=('id','name','unit','price'), show='headings')
        self.products_tree.heading('id', text='ID')
        self.products_tree.heading('name', text='Название')
        self.products_tree.heading('unit', text='Ед. изм.')
        self.products_tree.heading('price', text='Цена')
        self.products_tree.pack(fill='both', expand=True)
        self.refresh_products()

        btn_frame = tk.Frame(self.products_frame)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="Добавить", command=self.add_product).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Редактировать", command=self.edit_product).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Удалить", command=self.delete_product).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Экспорт в Excel", command=lambda: self.export_table('Products', 'products.xlsx')).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Себестоимость продукта", command=self.show_material_cost).pack(side='left', padx=5)

    def refresh_products(self):
        for i in self.products_tree.get_children():
            self.products_tree.delete(i)
        products = execute_query("SELECT * FROM Products ORDER BY id", fetch_all=True)
        for p in products:
            self.products_tree.insert('', 'end', values=(p['id'], p['name'], p['unit'], p['price']))

    def add_product(self):
        win = tk.Toplevel(self.window)
        win.title("Новый товар")
        win.geometry("300x300")
        tk.Label(win, text="Название:").pack(pady=5)
        name_entry = tk.Entry(win)
        name_entry.pack(pady=5)
        tk.Label(win, text="Единица измерения:").pack(pady=5)
        unit_entry = tk.Entry(win)
        unit_entry.pack(pady=5)
        tk.Label(win, text="Цена:").pack(pady=5)
        price_entry = tk.Entry(win)
        price_entry.pack(pady=5)

        def save():
            name = name_entry.get().strip()
            unit = unit_entry.get().strip()
            price_str = price_entry.get().strip()
            if not name or not unit or not price_str:
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
            try:
                price = float(price_str)
                if price < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Цена должна быть неотрицательным числом")
                return
            execute_query("INSERT INTO Products (name, unit, price) VALUES (%s, %s, %s)",
                          (name, unit, price))
            win.destroy()
            self.refresh_products()

        tk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def edit_product(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите товар")
            return
        values = self.products_tree.item(selected[0])['values']
        pid = values[0]
        current_name, current_unit, current_price = values[1], values[2], values[3]

        win = tk.Toplevel(self.window)
        win.title("Редактировать товар")
        win.geometry("300x300")
        tk.Label(win, text="Название:").pack(pady=5)
        name_entry = tk.Entry(win)
        name_entry.insert(0, current_name)
        name_entry.pack(pady=5)
        tk.Label(win, text="Единица измерения:").pack(pady=5)
        unit_entry = tk.Entry(win)
        unit_entry.insert(0, current_unit)
        unit_entry.pack(pady=5)
        tk.Label(win, text="Цена:").pack(pady=5)
        price_entry = tk.Entry(win)
        price_entry.insert(0, current_price)
        price_entry.pack(pady=5)

        def save():
            name = name_entry.get().strip()
            unit = unit_entry.get().strip()
            price_str = price_entry.get().strip()
            if not name or not unit or not price_str:
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
            try:
                price = float(price_str)
                if price < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Цена должна быть неотрицательным числом")
                return
            execute_query("UPDATE Products SET name=%s, unit=%s, price=%s WHERE id=%s",
                          (name, unit, price, pid))
            win.destroy()
            self.refresh_products()

        tk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def delete_product(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите товар")
            return
        if messagebox.askyesno("Подтверждение", "Удалить товар? Все связанные данные будут удалены."):
            pid = self.products_tree.item(selected[0])['values'][0]
            execute_query("DELETE FROM Products WHERE id=%s", (pid,))
            self.refresh_products()

    def show_material_cost(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите товар")
            return
        pid = self.products_tree.item(selected[0])['values'][0]
        cost = calculate_material_cost_for_product(pid)
        messagebox.showinfo("Себестоимость", f"Себестоимость продукта из материалов: {cost:.2f} руб.")

    # -------------------- Материалы --------------------
    def create_materials_tab(self):
        self.materials_tree = ttk.Treeview(self.materials_frame, columns=('id','name','unit','price'), show='headings')
        self.materials_tree.heading('id', text='ID')
        self.materials_tree.heading('name', text='Название')
        self.materials_tree.heading('unit', text='Ед. изм.')
        self.materials_tree.heading('price', text='Цена')
        self.materials_tree.pack(fill='both', expand=True)
        self.refresh_materials()

        btn_frame = tk.Frame(self.materials_frame)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="Добавить", command=self.add_material).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Редактировать", command=self.edit_material).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Удалить", command=self.delete_material).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Экспорт в Excel", command=lambda: self.export_table('Materials', 'materials.xlsx')).pack(side='left', padx=5)

    def refresh_materials(self):
        for i in self.materials_tree.get_children():
            self.materials_tree.delete(i)
        materials = execute_query("SELECT * FROM Materials ORDER BY id", fetch_all=True)
        for m in materials:
            self.materials_tree.insert('', 'end', values=(m['id'], m['name'], m['unit'], m['price']))

    def add_material(self):
        win = tk.Toplevel(self.window)
        win.title("Новый материал")
        win.geometry("300x300")
        tk.Label(win, text="Название:").pack(pady=5)
        name_entry = tk.Entry(win)
        name_entry.pack(pady=5)
        tk.Label(win, text="Единица измерения:").pack(pady=5)
        unit_entry = tk.Entry(win)
        unit_entry.pack(pady=5)
        tk.Label(win, text="Цена:").pack(pady=5)
        price_entry = tk.Entry(win)
        price_entry.pack(pady=5)

        def save():
            name = name_entry.get().strip()
            unit = unit_entry.get().strip()
            price_str = price_entry.get().strip()
            if not name or not unit or not price_str:
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
            try:
                price = float(price_str)
                if price < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Цена должна быть неотрицательным числом")
                return
            execute_query("INSERT INTO Materials (name, unit, price) VALUES (%s, %s, %s)",
                          (name, unit, price))
            win.destroy()
            self.refresh_materials()

        tk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def edit_material(self):
        selected = self.materials_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите материал")
            return
        values = self.materials_tree.item(selected[0])['values']
        mid = values[0]
        current_name, current_unit, current_price = values[1], values[2], values[3]

        win = tk.Toplevel(self.window)
        win.title("Редактировать материал")
        win.geometry("300x300")
        tk.Label(win, text="Название:").pack(pady=5)
        name_entry = tk.Entry(win)
        name_entry.insert(0, current_name)
        name_entry.pack(pady=5)
        tk.Label(win, text="Единица измерения:").pack(pady=5)
        unit_entry = tk.Entry(win)
        unit_entry.insert(0, current_unit)
        unit_entry.pack(pady=5)
        tk.Label(win, text="Цена:").pack(pady=5)
        price_entry = tk.Entry(win)
        price_entry.insert(0, current_price)
        price_entry.pack(pady=5)

        def save():
            name = name_entry.get().strip()
            unit = unit_entry.get().strip()
            price_str = price_entry.get().strip()
            if not name or not unit or not price_str:
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
            try:
                price = float(price_str)
                if price < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Цена должна быть неотрицательным числом")
                return
            execute_query("UPDATE Materials SET name=%s, unit=%s, price=%s WHERE id=%s",
                          (name, unit, price, mid))
            win.destroy()
            self.refresh_materials()

        tk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def delete_material(self):
        selected = self.materials_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите материал")
            return
        if messagebox.askyesno("Подтверждение", "Удалить материал? Все связанные спецификации будут удалены."):
            mid = self.materials_tree.item(selected[0])['values'][0]
            execute_query("DELETE FROM Materials WHERE id=%s", (mid,))
            self.refresh_materials()

    # -------------------- Спецификации --------------------
    def create_spec_tab(self):
        self.refresh_product_map()
        self.refresh_material_map()

        top_frame = tk.Frame(self.spec_frame)
        top_frame.pack(fill='x', pady=5)
        tk.Label(top_frame, text="Продукт:").pack(side='left', padx=5)
        self.product_combo = ttk.Combobox(top_frame, state='readonly', width=40)
        self.product_combo['values'] = list(self.product_map.keys())
        self.product_combo.pack(side='left', padx=5)
        tk.Button(top_frame, text="Загрузить спецификацию", command=self.load_spec_for_product).pack(side='left', padx=5)
        tk.Button(top_frame, text="Добавить материал в спецификацию", command=self.add_spec_item).pack(side='left', padx=5)

        self.spec_tree = ttk.Treeview(self.spec_frame, columns=('material_id', 'material_name', 'quantity', 'unit'), show='headings')
        self.spec_tree.heading('material_id', text='ID материала')
        self.spec_tree.heading('material_name', text='Материал')
        self.spec_tree.heading('quantity', text='Кол-во на ед. продукта')
        self.spec_tree.heading('unit', text='Ед. изм.')
        self.spec_tree.pack(fill='both', expand=True)

        btn_frame = tk.Frame(self.spec_frame)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="Удалить выбранную строку", command=self.delete_spec_item).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Редактировать количество", command=self.edit_spec_quantity).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Экспорт спецификации в Excel", command=self.export_current_spec).pack(side='left', padx=5)

        self.current_product_id = None

    def refresh_product_map(self):
        products = execute_query("SELECT id, name FROM Products ORDER BY name", fetch_all=True)
        self.product_map = {p['name']: p['id'] for p in products}

    def refresh_material_map(self):
        materials = execute_query("SELECT id, name FROM Materials ORDER BY name", fetch_all=True)
        self.material_map = {m['name']: m['id'] for m in materials}

    def load_spec_for_product(self):
        product_name = self.product_combo.get()
        if not product_name or product_name not in self.product_map:
            messagebox.showerror("Ошибка", "Выберите продукт")
            return
        self.current_product_id = self.product_map[product_name]
        self.refresh_spec_tree()

    def refresh_spec_tree(self):
        for i in self.spec_tree.get_children():
            self.spec_tree.delete(i)
        if not self.current_product_id:
            return
        spec = execute_query("""
            SELECT pm.material_id, m.name, pm.quantity, m.unit
            FROM ProductMaterial pm
            JOIN Materials m ON pm.material_id = m.id
            WHERE pm.product_id = %s
        """, (self.current_product_id,), fetch_all=True)
        for row in spec:
            self.spec_tree.insert('', 'end', values=(row['material_id'], row['name'], row['quantity'], row['unit']))

    def add_spec_item(self):
        if not self.current_product_id:
            messagebox.showerror("Ошибка", "Сначала выберите продукт")
            return
        if not self.material_map:
            messagebox.showerror("Ошибка", "Нет материалов в базе")
            return
        win = tk.Toplevel(self.window)
        win.title("Добавить материал в спецификацию")
        tk.Label(win, text="Материал:").pack(pady=5)
        combo = ttk.Combobox(win, values=list(self.material_map.keys()), state='readonly', width=40)
        combo.pack(pady=5)
        tk.Label(win, text="Количество на единицу продукта:").pack(pady=5)
        qty_entry = tk.Entry(win)
        qty_entry.pack(pady=5)

        def save():
            material_name = combo.get()
            if not material_name or material_name not in self.material_map:
                messagebox.showerror("Ошибка", "Выберите материал")
                return
            qty_str = qty_entry.get().strip()
            if not qty_str:
                messagebox.showerror("Ошибка", "Введите количество")
                return
            try:
                qty = float(qty_str)
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Количество должно быть положительным")
                return
            material_id = self.material_map[material_name]
            exists = execute_query("SELECT * FROM ProductMaterial WHERE product_id=%s AND material_id=%s",
                                    (self.current_product_id, material_id), fetch_one=True)
            if exists:
                messagebox.showerror("Ошибка", "Материал уже добавлен")
                return
            execute_query("INSERT INTO ProductMaterial (product_id, material_id, quantity) VALUES (%s, %s, %s)",
                          (self.current_product_id, material_id, qty))
            win.destroy()
            self.refresh_spec_tree()
        tk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def delete_spec_item(self):
        selected = self.spec_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите строку")
            return
        if not self.current_product_id:
            return
        values = self.spec_tree.item(selected[0])['values']
        material_id = values[0]
        if messagebox.askyesno("Подтверждение", "Удалить материал из спецификации?"):
            execute_query("DELETE FROM ProductMaterial WHERE product_id=%s AND material_id=%s",
                          (self.current_product_id, material_id))
            self.refresh_spec_tree()

    def edit_spec_quantity(self):
        selected = self.spec_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите строку")
            return
        values = self.spec_tree.item(selected[0])['values']
        material_id = values[0]
        current_qty = values[2]
        new_qty = simpledialog.askfloat("Редактирование", "Новое количество:", initialvalue=current_qty)
        if new_qty is None:
            return
        if new_qty <= 0:
            messagebox.showerror("Ошибка", "Количество должно быть положительным")
            return
        execute_query("UPDATE ProductMaterial SET quantity=%s WHERE product_id=%s AND material_id=%s",
                      (new_qty, self.current_product_id, material_id))
        self.refresh_spec_tree()

    def export_current_spec(self):
        if not self.current_product_id:
            messagebox.showerror("Ошибка", "Нет выбранного продукта")
            return
        spec = execute_query("""
            SELECT m.name as material, pm.quantity, m.unit
            FROM ProductMaterial pm
            JOIN Materials m ON pm.material_id = m.id
            WHERE pm.product_id = %s
        """, (self.current_product_id,), fetch_all=True)
        import pandas as pd
        if spec:
            df = pd.DataFrame(spec)
            filename = f"spec_product_{self.current_product_id}.xlsx"
            df.to_excel(filename, index=False)
            messagebox.showinfo("Экспорт", f"Сохранено в {filename}")
        else:
            messagebox.showinfo("Нет данных", "Спецификация пуста")

    # -------------------- Заказы --------------------
    def create_orders_tab(self):
        self.orders_tree = ttk.Treeview(self.orders_frame, columns=('id', 'customer', 'date', 'total'), show='headings')
        self.orders_tree.heading('id', text='№ заказа')
        self.orders_tree.heading('customer', text='Заказчик')
        self.orders_tree.heading('date', text='Дата')
        self.orders_tree.heading('total', text='Сумма')
        self.orders_tree.pack(fill='both', expand=True)
        self.refresh_orders()

        btn_frame = tk.Frame(self.orders_frame)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="Рассчитать стоимость заказа", command=self.calc_order_cost).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Просмотреть позиции заказа", command=self.view_order_items).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Экспорт заказов в Excel", command=lambda: self.export_table('Orders', 'orders.xlsx')).pack(side='left', padx=5)

        self.items_tree = ttk.Treeview(self.orders_frame, columns=('product', 'quantity', 'price', 'total'), show='headings')
        self.items_tree.heading('product', text='Товар')
        self.items_tree.heading('quantity', text='Кол-во')
        self.items_tree.heading('price', text='Цена за ед.')
        self.items_tree.heading('total', text='Сумма')
        self.items_tree.pack(fill='both', expand=True, pady=5)

    def refresh_orders(self):
        for i in self.orders_tree.get_children():
            self.orders_tree.delete(i)
        orders = execute_query("""
            SELECT o.id, c.name as customer, o.order_date, o.total_amount
            FROM Orders o
            LEFT JOIN Customers c ON o.customer_id = c.id
            ORDER BY o.id DESC
        """, fetch_all=True)
        for o in orders:
            self.orders_tree.insert('', 'end', values=(o['id'], o['customer'], o['order_date'], o['total_amount']))

    def calc_order_cost(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите заказ")
            return
        order_id = self.orders_tree.item(selected[0])['values'][0]
        cost = calculate_order_cost(order_id)
        messagebox.showinfo("Стоимость заказа", f"Полная стоимость заказа №{order_id}: {cost:.2f} руб.")

    def view_order_items(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите заказ")
            return
        order_id = self.orders_tree.item(selected[0])['values'][0]
        items = execute_query("""
            SELECT p.name as product, oi.quantity, oi.unit_price, oi.total
            FROM OrderItems oi
            JOIN Products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (order_id,), fetch_all=True)
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        for item in items:
            self.items_tree.insert('', 'end', values=(item['product'], item['quantity'], item['unit_price'], item['total']))

    # -------------------- Производства (админ) --------------------
    def create_productions_tab(self):
        top_frame = tk.Frame(self.productions_frame)
        top_frame.pack(fill='x', pady=5)
        tk.Button(top_frame, text="Создать производство", command=self.create_production).pack(side='left', padx=5)
        tk.Button(top_frame, text="Изменить статус", command=self.change_production_status).pack(side='left', padx=5)
        tk.Button(top_frame, text="Обновить", command=self.refresh_productions).pack(side='left', padx=5)

        self.productions_tree = ttk.Treeview(self.productions_frame, columns=('id','product','quantity','date','status'), show='headings')
        self.productions_tree.heading('id', text='№')
        self.productions_tree.heading('product', text='Продукт')
        self.productions_tree.heading('quantity', text='Кол-во')
        self.productions_tree.heading('date', text='Дата')
        self.productions_tree.heading('status', text='Статус')
        self.productions_tree.pack(fill='both', expand=True)
        self.refresh_productions()

        self.prod_materials_tree = ttk.Treeview(self.productions_frame, columns=('material','quantity','unit'), show='headings')
        self.prod_materials_tree.heading('material', text='Материал')
        self.prod_materials_tree.heading('quantity', text='Кол-во')
        self.prod_materials_tree.heading('unit', text='Ед. изм.')
        self.prod_materials_tree.pack(fill='both', expand=True, pady=5)
        self.productions_tree.bind('<<TreeviewSelect>>', self.on_production_select)

    def refresh_productions(self):
        for i in self.productions_tree.get_children():
            self.productions_tree.delete(i)
        prods = execute_query("""
            SELECT p.id, pr.name as product, p.quantity, p.production_date, p.status
            FROM Productions p
            JOIN Products pr ON p.product_id = pr.id
            ORDER BY p.id DESC
        """, fetch_all=True)
        for prod in prods:
            self.productions_tree.insert('', 'end', values=(prod['id'], prod['product'], prod['quantity'], prod['production_date'], prod['status']))

    def on_production_select(self, event):
        selected = self.productions_tree.selection()
        if not selected:
            return
        prod_id = self.productions_tree.item(selected[0])['values'][0]
        materials = execute_query("""
            SELECT m.name, pm.quantity, m.unit
            FROM ProductionMaterials pm
            JOIN Materials m ON pm.material_id = m.id
            WHERE pm.production_id = %s
        """, (prod_id,), fetch_all=True)
        for i in self.prod_materials_tree.get_children():
            self.prod_materials_tree.delete(i)
        for mat in materials:
            self.prod_materials_tree.insert('', 'end', values=(mat['name'], mat['quantity'], mat['unit']))

    def change_production_status(self):
        selected = self.productions_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите производство")
            return
        prod_id = self.productions_tree.item(selected[0])['values'][0]
        current_status = self.productions_tree.item(selected[0])['values'][4]
        new_status = simpledialog.askstring("Статус", "Введите новый статус (planned, in_progress, completed):", initialvalue=current_status)
        if new_status not in ['planned', 'in_progress', 'completed']:
            messagebox.showerror("Ошибка", "Неверный статус")
            return
        execute_query("UPDATE Productions SET status=%s WHERE id=%s", (new_status, prod_id))
        self.refresh_productions()

    def create_production(self):
        win = tk.Toplevel(self.window)
        win.title("Новое производство")
        win.geometry("600x500")

        tk.Label(win, text="Выберите продукт:").pack(pady=5)
        product_combo = ttk.Combobox(win, state='readonly', width=40)
        products = execute_query("SELECT id, name FROM Products ORDER BY name", fetch_all=True)
        product_map = {p['name']: p['id'] for p in products}
        product_combo['values'] = list(product_map.keys())
        product_combo.pack(pady=5)

        tk.Label(win, text="Количество:").pack(pady=5)
        qty_entry = tk.Entry(win)
        qty_entry.pack(pady=5)

        tree = ttk.Treeview(win, columns=('material', 'quantity', 'unit'), show='headings')
        tree.heading('material', text='Материал')
        tree.heading('quantity', text='Необходимое кол-во')
        tree.heading('unit', text='Ед. изм.')
        tree.pack(fill='both', expand=True, pady=10)

        def calc_materials(*args):
            for i in tree.get_children():
                tree.delete(i)
            product_name = product_combo.get()
            if not product_name or product_name not in product_map:
                return
            product_id = product_map[product_name]
            qty_str = qty_entry.get().strip()
            if not qty_str:
                return
            try:
                qty = float(qty_str)
                if qty <= 0:
                    return
            except:
                return
            spec = execute_query("""
                SELECT m.name, pm.quantity * %s as needed, m.unit
                FROM ProductMaterial pm
                JOIN Materials m ON pm.material_id = m.id
                WHERE pm.product_id = %s
            """, (qty, product_id), fetch_all=True)
            for row in spec:
                tree.insert('', 'end', values=(row['name'], row['needed'], row['unit']))

        product_combo.bind('<<ComboboxSelected>>', calc_materials)
        qty_entry.bind('<KeyRelease>', calc_materials)

        def save():
            product_name = product_combo.get()
            qty_str = qty_entry.get().strip()
            if not product_name or product_name not in product_map:
                messagebox.showerror("Ошибка", "Выберите продукт")
                return
            if not qty_str:
                messagebox.showerror("Ошибка", "Введите количество")
                return
            try:
                qty = float(qty_str)
                if qty <= 0:
                    raise ValueError
            except:
                messagebox.showerror("Ошибка", "Количество должно быть положительным числом")
                return
            product_id = product_map[product_name]
            spec = execute_query("""
                SELECT material_id, quantity
                FROM ProductMaterial
                WHERE product_id = %s
            """, (product_id,), fetch_all=True)
            if not spec:
                messagebox.showerror("Ошибка", "Для выбранного продукта не задана спецификация")
                return
            materials = [{'material_id': row['material_id'], 'quantity': row['quantity'] * qty} for row in spec]
            try:
                prod_id = insert_production_with_materials(product_id, qty, materials)
                messagebox.showinfo("Успех", f"Производство №{prod_id} создано")
                win.destroy()
                self.refresh_productions()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать производство: {e}")

        tk.Button(win, text="Создать", command=save).pack(pady=10)

    # -------------------- Контрагенты (Customers) --------------------
    def create_customers_tab(self):
        self.customers_tree = ttk.Treeview(self.customers_frame,
                                           columns=('id', 'name', 'inn', 'address', 'phone', 'is_salesman', 'is_buyer'),
                                           show='headings')
        self.customers_tree.heading('id', text='ID')
        self.customers_tree.heading('name', text='Название')
        self.customers_tree.heading('inn', text='ИНН')
        self.customers_tree.heading('address', text='Адрес')
        self.customers_tree.heading('phone', text='Телефон')
        self.customers_tree.heading('is_salesman', text='Продавец?')
        self.customers_tree.heading('is_buyer', text='Покупатель?')
        self.customers_tree.pack(fill='both', expand=True)
        self.refresh_customers()

        btn_frame = tk.Frame(self.customers_frame)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="Добавить", command=self.add_customer).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Редактировать", command=self.edit_customer).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Удалить", command=self.delete_customer).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Экспорт в Excel", command=lambda: self.export_table('Customers', 'customers.xlsx')).pack(side='left', padx=5)

    def refresh_customers(self):
        for i in self.customers_tree.get_children():
            self.customers_tree.delete(i)
        customers = execute_query("SELECT * FROM Customers ORDER BY id", fetch_all=True)
        for c in customers:
            self.customers_tree.insert('', 'end', values=(
                c['id'],
                c['name'],
                c['inn'] or '',
                c['address'] or '',
                c['phone'] or '',
                'Да' if c['is_salesman'] else 'Нет',
                'Да' if c['is_buyer'] else 'Нет'
            ))

    def add_customer(self):
        win = tk.Toplevel(self.window)
        win.title("Новый контрагент")
        win.geometry("400x350")

        fields = {}
        labels = [
            ('name', 'Название:', tk.Entry),
            ('inn', 'ИНН:', tk.Entry),
            ('address', 'Адрес:', tk.Entry),
            ('phone', 'Телефон:', tk.Entry)
        ]
        for i, (key, label, widget_class) in enumerate(labels):
            tk.Label(win, text=label).pack(pady=2)
            fields[key] = widget_class(win, width=40)
            fields[key].pack(pady=2)

        tk.Label(win, text="Продавец?").pack(pady=2)
        salesman_var = tk.BooleanVar()
        tk.Checkbutton(win, variable=salesman_var).pack(pady=2)

        tk.Label(win, text="Покупатель?").pack(pady=2)
        buyer_var = tk.BooleanVar()
        tk.Checkbutton(win, variable=buyer_var).pack(pady=2)

        def save():
            name = fields['name'].get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Название обязательно")
                return
            inn = fields['inn'].get().strip() or None
            address = fields['address'].get().strip() or None
            phone = fields['phone'].get().strip() or None
            is_salesman = salesman_var.get()
            is_buyer = buyer_var.get()
            try:
                execute_query("""
                    INSERT INTO Customers (name, inn, address, phone, is_salesman, is_buyer)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, inn, address, phone, is_salesman, is_buyer))
                win.destroy()
                self.refresh_customers()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить: {e}")

        tk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def edit_customer(self):
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите контрагента")
            return
        values = self.customers_tree.item(selected[0])['values']
        cid = values[0]
        current_name, current_inn, current_address, current_phone, current_salesman, current_buyer = values[1:]

        win = tk.Toplevel(self.window)
        win.title("Редактировать контрагента")
        win.geometry("400x350")

        fields = {}
        labels = [
            ('name', 'Название:', current_name),
            ('inn', 'ИНН:', current_inn if current_inn != '' else None),
            ('address', 'Адрес:', current_address if current_address != '' else None),
            ('phone', 'Телефон:', current_phone if current_phone != '' else None)
        ]
        for key, label, default in labels:
            tk.Label(win, text=label).pack(pady=2)
            fields[key] = tk.Entry(win, width=40)
            fields[key].insert(0, default if default else '')
            fields[key].pack(pady=2)

        tk.Label(win, text="Продавец?").pack(pady=2)
        salesman_var = tk.BooleanVar(value=(current_salesman == 'Да'))
        tk.Checkbutton(win, variable=salesman_var).pack(pady=2)

        tk.Label(win, text="Покупатель?").pack(pady=2)
        buyer_var = tk.BooleanVar(value=(current_buyer == 'Да'))
        tk.Checkbutton(win, variable=buyer_var).pack(pady=2)

        def save():
            name = fields['name'].get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Название обязательно")
                return
            inn = fields['inn'].get().strip() or None
            address = fields['address'].get().strip() or None
            phone = fields['phone'].get().strip() or None
            is_salesman = salesman_var.get()
            is_buyer = buyer_var.get()
            try:
                execute_query("""
                    UPDATE Customers 
                    SET name=%s, inn=%s, address=%s, phone=%s, is_salesman=%s, is_buyer=%s
                    WHERE id=%s
                """, (name, inn, address, phone, is_salesman, is_buyer, cid))
                win.destroy()
                self.refresh_customers()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить: {e}")

        tk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def delete_customer(self):
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите контрагента")
            return
        if messagebox.askyesno("Подтверждение", "Удалить контрагента? Это может повлиять на связанные заказы и пользователей."):
            cid = self.customers_tree.item(selected[0])['values'][0]
            try:
                execute_query("DELETE FROM Customers WHERE id=%s", (cid,))
                self.refresh_customers()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")

    # -------------------- Пользователи (админ) --------------------
    def create_users_tab(self):
        self.users_tree = ttk.Treeview(self.users_frame, columns=('id', 'username', 'role', 'customer_id', 'failed_attempts', 'is_locked'), show='headings')
        self.users_tree.heading('id', text='ID')
        self.users_tree.heading('username', text='Логин')
        self.users_tree.heading('role', text='Роль')
        self.users_tree.heading('customer_id', text='ID заказчика')
        self.users_tree.heading('failed_attempts', text='Попытки')
        self.users_tree.heading('is_locked', text='Заблокирован')
        self.users_tree.pack(fill='both', expand=True)
        self.refresh_users()

        btn_frame = tk.Frame(self.users_frame)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="Добавить", command=self.add_user).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Редактировать", command=self.edit_user).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Удалить", command=self.delete_user).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Заблокировать", command=self.lock_user).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Разблокировать", command=self.unlock_user).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Сбросить попытки", command=self.reset_failed_attempts).pack(side='left', padx=5)

    def refresh_users(self):
        for i in self.users_tree.get_children():
            self.users_tree.delete(i)
        users = execute_query("SELECT id, username, role, customer_id, failed_attempts, is_locked FROM Users ORDER BY id", fetch_all=True)
        for u in users:
            self.users_tree.insert('', 'end', values=(u['id'], u['username'], u['role'], u['customer_id'], u['failed_attempts'], 'Да' if u['is_locked'] else 'Нет'))

    def add_user(self):
        win = tk.Toplevel(self.window)
        win.title("Добавить пользователя")
        win.geometry("300x350")

        tk.Label(win, text="Логин:").pack(pady=5)
        username_entry = tk.Entry(win)
        username_entry.pack(pady=5)

        tk.Label(win, text="Пароль:").pack(pady=5)
        pass_entry = tk.Entry(win, show="*")
        pass_entry.pack(pady=5)

        tk.Label(win, text="Роль:").pack(pady=5)
        role_combo = ttk.Combobox(win, values=['admin', 'client', 'producer'], state='readonly')
        role_combo.pack(pady=5)

        tk.Label(win, text="ID заказчика (если клиент или продюсер):").pack(pady=5)
        customer_entry = tk.Entry(win)
        customer_entry.pack(pady=5)

        def save():
            username = username_entry.get().strip()
            password = pass_entry.get()
            role = role_combo.get()
            customer_id = customer_entry.get().strip() if customer_entry.get().strip() else None
            if not username or not password or not role:
                messagebox.showerror("Ошибка", "Заполните логин, пароль и роль")
                return
            if role in ('client', 'producer') and not customer_id:
                messagebox.showerror("Ошибка", "Для клиента и продюсера необходим ID заказчика")
                return
            existing = execute_query("SELECT id FROM Users WHERE username=%s", (username,), fetch_one=True)
            if existing:
                messagebox.showerror("Ошибка", "Пользователь с таким логином уже существует")
                return
            import hashlib
            pwd_hash = hashlib.sha256(password.encode()).hexdigest()
            try:
                execute_query("INSERT INTO Users (username, password_hash, role, customer_id, failed_attempts, is_locked) VALUES (%s,%s,%s,%s,0,FALSE)",
                              (username, pwd_hash, role, customer_id))
                win.destroy()
                self.refresh_users()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить: {e}")

        tk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def edit_user(self):
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите пользователя")
            return
        values = self.users_tree.item(selected[0])['values']
        uid = values[0]
        current_username, current_role, current_customer_id = values[1], values[2], values[3]

        win = tk.Toplevel(self.window)
        win.title("Редактировать пользователя")
        win.geometry("300x300")

        tk.Label(win, text="Логин:").pack(pady=5)
        username_entry = tk.Entry(win)
        username_entry.insert(0, current_username)
        username_entry.pack(pady=5)

        tk.Label(win, text="Роль:").pack(pady=5)
        role_combo = ttk.Combobox(win, values=['admin', 'client', 'producer'], state='readonly')
        role_combo.set(current_role)
        role_combo.pack(pady=5)

        tk.Label(win, text="ID заказчика:").pack(pady=5)
        customer_entry = tk.Entry(win)
        customer_entry.insert(0, str(current_customer_id) if current_customer_id else '')
        customer_entry.pack(pady=5)

        def save():
            username = username_entry.get().strip()
            role = role_combo.get()
            customer_id = customer_entry.get().strip() if customer_entry.get().strip() else None
            if not username or not role:
                messagebox.showerror("Ошибка", "Заполните логин и роль")
                return
            if role in ('client', 'producer') and not customer_id:
                messagebox.showerror("Ошибка", "Для клиента и продюсера необходим ID заказчика")
                return
            try:
                execute_query("UPDATE Users SET username=%s, role=%s, customer_id=%s WHERE id=%s",
                              (username, role, customer_id, uid))
                win.destroy()
                self.refresh_users()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить: {e}")

        tk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def delete_user(self):
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите пользователя")
            return
        if messagebox.askyesno("Подтверждение", "Удалить пользователя?"):
            uid = self.users_tree.item(selected[0])['values'][0]
            execute_query("DELETE FROM Users WHERE id=%s", (uid,))
            self.refresh_users()

    def lock_user(self):
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите пользователя")
            return
        uid = self.users_tree.item(selected[0])['values'][0]
        execute_query("UPDATE Users SET is_locked=TRUE WHERE id=%s", (uid,))
        self.refresh_users()

    def unlock_user(self):
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите пользователя")
            return
        uid = self.users_tree.item(selected[0])['values'][0]
        execute_query("UPDATE Users SET is_locked=FALSE, failed_attempts=0 WHERE id=%s", (uid,))
        self.refresh_users()

    def reset_failed_attempts(self):
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите пользователя")
            return
        uid = self.users_tree.item(selected[0])['values'][0]
        execute_query("UPDATE Users SET failed_attempts=0 WHERE id=%s", (uid,))
        self.refresh_users()

    # -------------------- Общие утилиты --------------------
    def export_table(self, table_name, filename):
        try:
            export_table_to_excel(table_name, filename)
            messagebox.showinfo("Экспорт", f"Таблица {table_name} сохранена в {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {e}")