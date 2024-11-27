from tkinter import Tk
from gui import TelegramAdder
import os

def on_closing():
    # Perform any cleanup here if necessary
    print("Cleaning up resources...")
    # If you have threads, you might want to join them here
    # Example: thread.join()

    # Explicitly quit and destroy the root window
    root.quit()
    root.destroy()

def main():
    global root  # Make root global if you need to access it from another function
    root = Tk()
    app = TelegramAdder(root)
    root.title("Telegram Manager")
    
    # Get the current directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the window icon with full path
    icon_path = os.path.join(current_dir, "icon.ico")
    # root.iconbitmap(icon_path)
    
    # Bind the on_closing function to the window close event
    root.protocol("WM_DELETE_WINDOW", on_closing)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted by user. Exiting...")
        on_closing()
    finally:
        # Perform any additional cleanup here if necessary
        pass

if __name__ == "__main__":
    main()