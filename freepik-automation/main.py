import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.ui.main_window import MainWindow
import customtkinter as ctk

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
