import tkinter as tk
import random


class Ball:
    def __init__(self, canvas, x, y, radius):
        self.canvas = canvas
        self.radius = radius
        
        
        self.color = random.choice(["orange", "pink", "blue", "purple", "yellow"])
        
        
        self.id = canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=self.color
        )
        
        
        self.dx = random.randint(-5, 5)
        self.dy = random.randint(-5, 5)

        
        if self.dx == 0:
            self.dx = 3
        if self.dy == 0:
            self.dy = 3

        self.animate()

    def animate(self):
        self.canvas.move(self.id, self.dx, self.dy)
        x1, y1, x2, y2 = self.canvas.coords(self.id)

        # Bounce off walls
        if x1 <= 0 or x2 >= self.canvas.winfo_width():
            self.dx *= -1
        if y1 <= 0 or y2 >= self.canvas.winfo_height():
            self.dy *= -1

        self.canvas.after(20, self.animate)


root = tk.Tk()
root.title("Bouncing Balls")

canvas = tk.Canvas(root, width=800, height=600, bg="white")
canvas.pack()

for _ in range(5):
    Ball(canvas, 400, 300, 20)

root.mainloop()