# my_script.py

import tkinter as tk

def on_button_click():
    label.config(text="Hello, " + entry.get())

app = tk.Tk()
app.title("My App")

entry = tk.Entry(app)
entry.pack()

button = tk.Button(app, text="Click me!", command=on_button_click)
button.pack()

label = tk.Label(app, text="Welcome!")
label.pack()

app.mainloop()
