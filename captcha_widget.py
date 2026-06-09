import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random

class CaptchaWidget(tk.Frame):
    def __init__(self, parent, images_paths, correct_order=None, on_success=None):
        super().__init__(parent)
        self.images_paths = images_paths  # список из 4 путей
        if correct_order is None:
            self.correct_order = list(range(4))
        else:
            self.correct_order = correct_order
        self.current_order = self.correct_order.copy()
        random.shuffle(self.current_order)
        self.buttons = []
        self.selected = None
        self.on_success = on_success

        self.load_images()
        self.create_grid()

    def load_images(self):
        self.photo_images = []
        for path in self.images_paths:
            img = Image.open(path)
            img = img.resize((120, 120), Image.Resampling.LANCZOS)
            self.photo_images.append(ImageTk.PhotoImage(img))

    def create_grid(self):
        for i in range(2):
            for j in range(2):
                idx = i*2 + j
                img_idx = self.current_order[idx]
                btn = tk.Button(self, image=self.photo_images[img_idx],
                                command=lambda i=i, j=j: self.on_click(i, j))
                btn.grid(row=i, column=j, padx=5, pady=5)
                self.buttons.append((btn, img_idx, i, j))

        # self.check_btn = tk.Button(self, text="Проверить порядок", command=self.check)
        # self.check_btn.grid(row=2, column=0, columnspan=2, pady=10)

    def on_click(self, row, col):
        idx = row*2 + col
        if self.selected is None:
            self.selected = (row, col)
            self.buttons[idx][0].config(relief="sunken")
        else:
            sel_row, sel_col = self.selected
            sel_idx = sel_row*2 + sel_col
            cur_idx = idx
            # Меняем местами
            self.current_order[sel_idx], self.current_order[cur_idx] = self.current_order[cur_idx], self.current_order[sel_idx]
            # Перестроить сетку
            for btn, _, r, c in self.buttons:
                btn.destroy()
            self.buttons.clear()
            self.create_grid()
            self.selected = None

    def check(self):
        if self.current_order == self.correct_order:
            messagebox.showinfo("Капча", "Порядок верный!")
            if self.on_success:
                self.on_success()
        else:
            messagebox.showerror("Капча", "Неверный порядок. Попробуйте ещё раз.")