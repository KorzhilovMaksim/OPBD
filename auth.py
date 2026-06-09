import tkinter as tk
from tkinter import messagebox, ttk
import hashlib
from db import execute_query, update_failed_attempts, is_user_locked
from captcha_widget import CaptchaWidget

class AuthWindow:
    def __init__(self, on_login_success):
        self.on_login_success = on_login_success
        self.window = tk.Tk()
        self.window.title("Авторизация")
        self.window.geometry("500x650")
        self.customer_map = {}
        self.create_widgets()

    def create_widgets(self):
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True)

        # Вкладка входа
        login_frame = ttk.Frame(notebook)
        notebook.add(login_frame, text="Вход")

        tk.Label(login_frame, text="Логин").pack(pady=5)
        self.login_entry = tk.Entry(login_frame)
        self.login_entry.pack(pady=5)

        tk.Label(login_frame, text="Пароль").pack(pady=5)
        self.pass_entry = tk.Entry(login_frame, show="*")
        self.pass_entry.pack(pady=5)

        self.captcha_frame = tk.Frame(login_frame)
        self.captcha_frame.pack(pady=10)
        self.init_captcha()

        tk.Button(login_frame, text="Войти", command=self.login).pack(pady=20)

        # Вкладка регистрации
        reg_frame = ttk.Frame(notebook)
        notebook.add(reg_frame, text="Регистрация")

        tk.Label(reg_frame, text="Логин").pack(pady=5)
        self.reg_login = tk.Entry(reg_frame)
        self.reg_login.pack(pady=5)

        tk.Label(reg_frame, text="Пароль").pack(pady=5)
        self.reg_pass = tk.Entry(reg_frame, show="*")
        self.reg_pass.pack(pady=5)

        tk.Label(reg_frame, text="Подтверждение пароля").pack(pady=5)
        self.reg_pass2 = tk.Entry(reg_frame, show="*")
        self.reg_pass2.pack(pady=5)

        tk.Label(reg_frame, text="Выберите заказчика (обязательно)").pack(pady=5)
        self.customer_combo = ttk.Combobox(reg_frame, state="readonly", width=40)
        self.load_customers()
        self.customer_combo.pack(pady=5)

        tk.Button(reg_frame, text="Зарегистрироваться", command=self.register).pack(pady=20)

    def load_customers(self):
        customers = execute_query("SELECT id, name FROM Customers ORDER BY name", fetch_all=True)
        names = []
        for c in customers:
            names.append(c['name'])
            self.customer_map[c['name']] = c['id']
        self.customer_combo['values'] = names

    def init_captcha(self):
        paths = [f"images/{i}.png" for i in range(1, 5)]
        self.captcha = CaptchaWidget(self.captcha_frame, paths, correct_order=[0,1,2,3])
        self.captcha.pack()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self):
        if not self.captcha.current_order == self.captcha.correct_order:
            messagebox.showerror("Ошибка", "Решите капчу")
            return
        username = self.login_entry.get().strip()
        password = self.pass_entry.get()
        if not username or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль")
            return

        # Проверка блокировки
        if is_user_locked(username):
            messagebox.showerror("Ошибка", "Пользователь заблокирован. Обратитесь к администратору.")
            return

        user = execute_query("SELECT * FROM Users WHERE username=%s AND password_hash=%s",
                             (username, self.hash_password(password)), fetch_one=True)
        if user:
            update_failed_attempts(username, increment=False)
            self.window.destroy()
            self.on_login_success(user)
        else:
            update_failed_attempts(username, increment=True)
            remaining = 3 - (execute_query("SELECT failed_attempts FROM Users WHERE username=%s", (username,), fetch_one) or {}).get('failed_attempts', 0)
            messagebox.showerror("Ошибка", f"Неверный логин или пароль. Осталось попыток: {remaining}")

    def register(self):
        username = self.reg_login.get().strip()
        password = self.reg_pass.get()
        password2 = self.reg_pass2.get()
        customer_name = self.customer_combo.get().strip()

        if not username or not password:
            messagebox.showerror("Ошибка", "Заполните логин и пароль")
            return
        if password != password2:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return
        if len(password) < 3:
            messagebox.showerror("Ошибка", "Пароль должен содержать не менее 3 символов")
            return
        if not customer_name or customer_name not in self.customer_map:
            messagebox.showerror("Ошибка", "Выберите заказчика из списка")
            return

        existing = execute_query("SELECT id FROM Users WHERE username=%s", (username,), fetch_one=True)
        if existing:
            messagebox.showerror("Ошибка", "Пользователь с таким логином уже существует")
            return

        customer_id = self.customer_map[customer_name]
        role = 'client'

        try:
            execute_query("INSERT INTO Users (username, password_hash, role, customer_id, failed_attempts, is_locked) VALUES (%s,%s,%s,%s,0,FALSE)",
                          (username, self.hash_password(password), role, customer_id))
            messagebox.showinfo("Успех", "Регистрация пройдена! Теперь войдите.")
            self.reg_login.delete(0, tk.END)
            self.reg_pass.delete(0, tk.END)
            self.reg_pass2.delete(0, tk.END)
            self.customer_combo.set('')
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось зарегистрировать: {e}")

    def run(self):
        self.window.mainloop()