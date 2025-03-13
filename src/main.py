from src.gui import QuoteApp
import tkinter as tk

def main():
    root = tk.Tk()
    app = QuoteApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()