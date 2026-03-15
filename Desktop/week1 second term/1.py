import tkinter as tk

def btnUP():
    global counting
    counting+=1
    tmp = f'btn UP: {counting}'
    print(tmp)
    label.config(text=tmp)

def btnDOWN():
    global counting
    counting-=1
    tmp = f'btn DOWN: {counting}'
    print(tmp)
    label.config(text=tmp)

counting = 0

root = tk.Tk()
root.geometry("400x300")

btn1 = tk.Button(root, text="Up1",command=btnUP)
btn1.pack(pady=5)
btn2 = tk.Button(root, text="Down1",command=btnDOWN)
btn2.pack(pady=5)

label = tk.Label(root,text='Inital')
label.pack(pady=5)

root.mainloop()