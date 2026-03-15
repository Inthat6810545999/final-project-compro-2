import tkinter as tk
import random


# =========================
# Base Shape Class
# =========================
class Shape:
    def __init__(self, canvas, color):
        self.canvas = canvas
        self.size = random.randint(10, 30)

        self.x = random.randint(0, canvas.width - self.size)
        self.y = random.randint(0, canvas.height - self.size)

        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)

        while abs(self.vx) < 0.5:
            self.vx = random.uniform(-2, 2)
        while abs(self.vy) < 0.5:
            self.vy = random.uniform(-2, 2)

        self.color = color
        self.id = None

    def move(self, speed_multiplier):
        dx = self.vx * speed_multiplier
        dy = self.vy * speed_multiplier

        self.canvas.move(self.id, dx, dy)
        x1, y1, x2, y2 = self.canvas.coords(self.id)

        # Bounce logic
        if x1 <= 0 and self.vx < 0:
            self.vx = -self.vx
        if x2 >= self.canvas.width and self.vx > 0:
            self.vx = -self.vx
        if y1 <= 0 and self.vy < 0:
            self.vy = -self.vy
        if y2 >= self.canvas.height and self.vy > 0:
            self.vy = -self.vy

        # Snap inside bounds
        x1, y1, x2, y2 = self.canvas.coords(self.id)
        if x1 < 0:
            self.canvas.move(self.id, -x1, 0)
        if y1 < 0:
            self.canvas.move(self.id, 0, -y1)
        if x2 > self.canvas.width:
            self.canvas.move(self.id, self.canvas.width - x2, 0)
        if y2 > self.canvas.height:
            self.canvas.move(self.id, 0, self.canvas.height - y2)

    def update_color(self, new_color):
        self.canvas.itemconfig(self.id, fill=new_color)


class Ball(Shape):
    def __init__(self, canvas, color):
        super().__init__(canvas, color)
        self.id = canvas.create_oval(
            self.x, self.y,
            self.x + self.size,
            self.y + self.size,
            fill=color,
            outline="black"
        )


class Rectangle(Shape):
    def __init__(self, canvas, color):
        super().__init__(canvas, color)
        self.id = canvas.create_rectangle(
            self.x, self.y,
            self.x + self.size,
            self.y + self.size,
            fill=color,
            outline="black"
        )


# =========================
# Canvas Class
# =========================
class BouncingShapeCanvas(tk.Canvas):
    def __init__(self, master, color="orange", **kwargs):
        super().__init__(master,
                         bg="white",
                         highlightthickness=1,
                         highlightbackground="black",
                         **kwargs)

        self.width = 400
        self.height = 300

        self.speed_multiplier = tk.IntVar(value=5)
        self.color_var = tk.StringVar(value=color)

        self.shapes = []
        for i in range(50):
            if i % 2 == 0:
                self.shapes.append(Ball(self, color))
            else:
                self.shapes.append(Rectangle(self, color))

        self.bind("<Configure>", self.on_resize)

        self.animate()

    def on_resize(self, event):
        self.width = event.width
        self.height = event.height

    def animate(self):
        # 🔥 ทำให้ค่า speed ไม่ติดลบ
        speed = abs(self.speed_multiplier.get())

        for shape in self.shapes:
            shape.move(speed / 5)
            shape.update_color(self.color_var.get())

        self.after(16, self.animate)


# =========================
# Config Panel
# =========================
class ConfigPanel(tk.LabelFrame):
    def __init__(self, master, canvas, title):
        super().__init__(master,
                         text=title,
                         bg="white",
                         fg="black",
                         highlightthickness=0)

        self.canvas = canvas

        tk.Label(self, text="Speed Multiplier",
                 bg="white", fg="black").pack()

        tk.Scale(self,
                 from_=-10,
                 to=10,
                 orient=tk.HORIZONTAL,
                 variable=canvas.speed_multiplier,
                 bg="white",
                 fg="black",
                 highlightthickness=0).pack(fill="x")

        tk.Label(self, text="Select Color",
                 bg="white", fg="black").pack()

        for color in ["orange", "blue", "green", "purple"]:
            tk.Radiobutton(self,
                           text=color.capitalize(),
                           value=color,
                           variable=canvas.color_var,
                           bg="white",
                           fg="black",
                           highlightthickness=0).pack(anchor="w")


# =========================
# Main App
# =========================
def main():
    root = tk.Tk()
    root.title("Interactive Multi-Canvas Bouncing Shapes")
    root.configure(bg="white")

    left_frame = tk.Frame(root, bg="white")
    right_frame = tk.Frame(root, bg="white")

    left_frame.grid(row=0, column=0, sticky="ns")
    right_frame.grid(row=0, column=1, sticky="nsew")

    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=1)

    canvases = []

    for r in range(2):
        right_frame.grid_rowconfigure(r, weight=1)
        for c in range(2):
            right_frame.grid_columnconfigure(c, weight=1)

            canvas = BouncingShapeCanvas(right_frame)
            canvas.grid(row=r, column=c, sticky="nsew", padx=5, pady=5)
            canvases.append(canvas)

    for i, canvas in enumerate(canvases):
        panel = ConfigPanel(left_frame, canvas, f"Panel {i+1} Config")
        panel.pack(fill="x", padx=10, pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()