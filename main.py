from auth import AuthWindow
from admin_forms import AdminWindow
from client_forms import ClientWindow

def on_login_success(user):
    role = user['role']
    if role == 'admin':
        AdminWindow(user).window.mainloop()
    else:  # client
        ClientWindow(user).window.mainloop()

if __name__ == "__main__":
    auth = AuthWindow(on_login_success)
    auth.run()