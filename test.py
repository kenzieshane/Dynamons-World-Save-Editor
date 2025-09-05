import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import shutil
from datetime import datetime
from PIL import Image, ImageTk


class SaveEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("KenzieShane's Dynamons Save Editor")
        self.root.geometry("800x600")

        self.current_file = None
        self.backup_dir = Path("save_backups")
        self.backup_dir.mkdir(exist_ok=True)

        self.create_widgets()
        self.set_default_values()

    def create_widgets(self):

        # File Controls
        file_frame = ttk.Frame(self.root)
        file_frame.pack(pady=10, fill=tk.X)

        ttk.Button(file_frame, text="Load Save", command=self.load_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Save Changes", command=self.save_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="About", command=self.show_about).pack(side=tk.RIGHT, padx=5)
        
        # Main Content
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Player Tab
        player_frame = ttk.Frame(notebook)
        self.create_player_tab(player_frame)
        notebook.add(player_frame, text="Player")

        # Items Tab
        items_frame = ttk.Frame(notebook)
        self.create_items_tab(items_frame)
        notebook.add(items_frame, text="Items")

        # Debug Tab
        debug_frame = ttk.Frame(notebook)
        self.create_debug_tab(debug_frame)
        notebook.add(debug_frame, text="Advanced")

    def show_about(self):
        about_win = tk.Toplevel(self.root)  # create new window
        about_win.title("About")
        about_win.geometry("300x250")  # size of the window
        about_win.resizable(False, False)  # make it fixed size
    
        logo = Image.open("logo.png")  # replace with your logo filename
        logo = logo.resize((50, 50))  # optional: resize
        self.logo_img = ImageTk.PhotoImage(logo)  # keep a reference
        ttk.Label(about_win, image=self.logo_img).pack(pady=10)

        ttk.Label(about_win, text="Dynamons Save Editor", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(about_win, text="Version 1.0\nCreated by KenzieShane.\nKenzieShane is not affiliated to Azerion Casual or any of the Dynamons World Developer.\nPlease use this software responsibly.\nPurchase the IAP in the game to support the developers!").pack(pady=5)
        ttk.Button(about_win, text="Close", command=about_win.destroy).pack(pady=10)

        about_win.grab_set()
        self.root.wait_window(about_win)

    def create_player_tab(self, frame):
        entries = [
            ("Coins", "dynamons_worldPLAYER_COINS"),
            ("Dust", "dynamons_worldPLAYER_DUST"),
            ("PVP XP", "dynamons_worldPVP_LEAGUE_XP"),
            ("Trophies", "dynamons_worldPROF_TROPHIES"),
            ("Battle Speed", "dynamons_worldPREFER_TIME_SCALE"),
        ]
        self.vars = {}
        for i, (label, key) in enumerate(entries):
            ttk.Label(frame, text=label).grid(row=i, column=0, padx=5, pady=2, sticky=tk.W)
            self.vars[key] = tk.StringVar()
            ttk.Entry(frame, textvariable=self.vars[key]).grid(row=i, column=1, padx=5, pady=2)
        ttk.Button(frame, text="Max All", command=self.set_max_values).grid(row=len(entries), columnspan=2, pady=5)

    def create_items_tab(self, frame):
        self.item_vars = {
            "Heal Spray": tk.IntVar(value=0),
            "Discatch Special": tk.IntVar(value=0),
            "Unlimited Snacks": tk.IntVar(value=0),
        }
        for i, (item, var) in enumerate(self.item_vars.items()):
            ttk.Checkbutton(frame, text=item, variable=var).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Button(frame, text="Unlock All Maps", command=self.unlock_all_maps).grid(row=4, pady=10)
        ttk.Button(frame, text="Complete All Events", command=self.complete_events).grid(row=5, pady=5)

    def create_debug_tab(self, frame):
        ttk.Button(frame, text="Force Max Level", command=self.max_level).grid(row=0, pady=5)
        ttk.Button(frame, text="Unlock All Avatars", command=self.unlock_avatars).grid(row=1, pady=5)
        ttk.Button(frame, text="Restore Backup", command=self.restore_backup).grid(row=2, pady=5)

    # Core functionality
    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
        if not file_path:
            return
        try:
            self.current_file = Path(file_path)
            self.create_backup()
            tree = ET.parse(self.current_file)
            root = tree.getroot()
            # Load values into GUI
            for key, var in self.vars.items():
                element = root.find(f'.//string[@name="{key}"]')
                var.set(element.text if element is not None else "")
            messagebox.showinfo("Success", "Save file loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
            self.current_file = None

    def save_file(self):
        if not self.current_file:
            messagebox.showerror("Error", "No file loaded!")
            return
        try:
            tree = ET.parse(self.current_file)
            root = tree.getroot()
            # Save basic values
            for key, var in self.vars.items():
                element = root.find(f'.//string[@name="{key}"]')
                if element is not None:
                    element.text = var.get()
            # Save items
            items = root.find('.//string[@name="dynamons_worldITEMS_DATA"]')
            if items is not None:
                existing = {k.split(',')[0]: k for k in (items.text or "").split(';') if k}
                if self.item_vars["Heal Spray"].get():
                    existing["heal_spray"] = "heal_spray,999"
                if self.item_vars["Discatch Special"].get():
                    existing["discatch_special"] = "discatch_special,99"
                if self.item_vars["Unlimited Snacks"].get():
                    existing["unlimited_snacks"] = "unlimited_snacks,1"
                items.text = ';'.join(existing.values())
            tree.write(self.current_file, encoding='utf-8', xml_declaration=True)
            messagebox.showinfo("Success", "Save file updated!")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed:\n{str(e)}")
            self.restore_backup()

    def create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{self.current_file.stem}_{timestamp}.bak"
        shutil.copy(self.current_file, backup_file)
        # Keep only last 5 backups
        backups = sorted(self.backup_dir.glob("*.bak"), key=lambda x: x.stat().st_mtime)
        for old_backup in backups[:-5]:
            old_backup.unlink()

    def restore_backup(self):
        backups = sorted(self.backup_dir.glob("*.bak"), key=lambda x: x.stat().st_mtime)
        if not backups:
            messagebox.showinfo("Info", "No backups available")
            return
        try:
            shutil.copy(backups[-1], self.current_file)
            messagebox.showinfo("Restored", f"Restored backup from {backups[-1].name}")
        except Exception as e:
            messagebox.showerror("Error", f"Restore failed:\n{str(e)}")

    # Feature implementations (placeholders)
    def set_max_values(self):
        for key, var in self.vars.items():
            var.set("999999" if "COINS" in key else "9999")

    def unlock_all_maps(self):
        pass

    def complete_events(self):
        pass

    def max_level(self):
        pass

    def unlock_avatars(self):
        pass

    def set_default_values(self):
        defaults = {
            "dynamons_worldPLAYER_COINS": "9185",
            "dynamons_worldPLAYER_DUST": "74910",
            "dynamons_worldPVP_LEAGUE_XP": "50",
            "dynamons_worldPROF_TROPHIES": "10",
            "dynamons_worldPREFER_TIME_SCALE": "8",
        }
        for key, value in defaults.items():
            if hasattr(self, "vars") and key in self.vars:
                self.vars[key].set(value)

if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap("profile.ico")
    app = SaveEditor(root)
    root.mainloop()
