import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import shutil
from datetime import datetime
from PIL import Image, ImageTk
import urllib.request
import io
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class SaveEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("KenzieShane's Dynamons Save Editor")
        self.root.geometry("800x600")

        self.current_file = None
        self.backup_dir = Path("save_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # URL for the default save file
        self.default_save_url = "https://kenzieshane.my.id/MainActivity.xml"  # Replace with your actual URL

        self.create_widgets()
        self.set_default_values()

    def create_widgets(self):
        # File Controls
        file_frame = ttk.Frame(self.root)
        file_frame.pack(pady=10, fill=tk.X)

        ttk.Button(file_frame, text="Load Save", command=self.load_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Save Changes", command=self.save_file).pack(side=tk.LEFT, padx=5)
        # New button for loading default save from URL
        ttk.Button(file_frame, text="Load Default Save from URL", command=self.load_default_from_url).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="About", command=self.show_about).pack(side=tk.RIGHT, padx=5)
        
        # Status label to show download progress
        self.status_var = tk.StringVar()
        status_label = ttk.Label(self.root, textvariable=self.status_var)
        status_label.pack(pady=5)
        
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

        # Party Tab
        party_frame = ttk.Frame(notebook)
        self.create_party_tab(party_frame)
        notebook.add(party_frame, text="Party")

        # Debug Tab
        debug_frame = ttk.Frame(notebook)
        self.create_debug_tab(debug_frame)
        notebook.add(debug_frame, text="Advanced")

    def show_about(self):
        about_win = tk.Toplevel(self.root)  # create new window
        about_win.title("About")
        about_win.geometry("500x275")  # size of the window
        about_win.resizable(False, False)  # make it fixed size
    
        try:
            logo = Image.open(resource_path("logo.png"))  # replace with your logo filename
            logo = logo.resize((50, 50))  # optional: resize
            self.logo_img = ImageTk.PhotoImage(logo)  # keep a reference
            ttk.Label(about_win, image=self.logo_img).pack(pady=10)
        except:
            pass  # Skip logo if not available

        ttk.Label(about_win, text="Dynamons Save Editor", font=("Arial", 14, "bold"), justify='center').pack(pady=10)
        ttk.Label(about_win, text="Version 1.0\nCreated by KenzieShane.\nKenzieShane is not affiliated to Azerion Casual or any of the Dynamons World Developer.\nPlease use this software responsibly.\nPurchase the IAP in the game to support the developers!", justify='center').pack(pady=5)
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

    def create_party_tab(self, frame):
        container = ttk.Frame(frame)
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.dynamons_frame = ttk.Frame(canvas)

        self.dynamons_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.dynamons_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        container.pack(fill=tk.BOTH, expand=True)
        canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")

        self.dynamons = []
        self.dynamon_widgets = []

    def find_and_parse_dynamons_data(self, root):
        dynamons_data_string = None
        for string_tag in root.findall(".//string"):
            if string_tag.get("name") == "dynamons_worldMONS_DATA":
                dynamons_data_string = string_tag.text
                break
        
        if dynamons_data_string:
            self.dynamons = self.parse_dynamons_string(dynamons_data_string)

    def parse_dynamons_string(self, data_string):
        dynamons = []
        parts = data_string.strip().split(';')
        for part in parts:
            if not part:
                continue
            attributes = part.split(',')
            if len(attributes) < 8: continue
            dynamon = {
                "name": attributes[0],
                "level": attributes[1],
                "health": attributes[2],
                "unknown1": attributes[3],
                "unknown2": attributes[4],
                "value1": attributes[5],
                "unknown3": attributes[6],
                "value2": attributes[7],
            }
            dynamons.append(dynamon)
        return dynamons

    def display_dynamons(self):
        for widget in self.dynamons_frame.winfo_children():
            widget.destroy()
        
        self.dynamon_widgets = []

        for i, dynamon in enumerate(self.dynamons):
            dynamon_frame = ttk.Frame(self.dynamons_frame, relief=tk.RIDGE, padding=5)
            dynamon_frame.pack(pady=5, fill=tk.X)

            widgets = {}

            img_label = self.get_image_label(dynamon["name"], dynamon_frame)
            img_label.grid(row=0, column=0, rowspan=4, padx=5)

            ttk.Label(dynamon_frame, text="Name:").grid(row=0, column=1, sticky=tk.W)
            name_entry = ttk.Entry(dynamon_frame)
            name_entry.insert(0, dynamon["name"])
            name_entry.grid(row=0, column=2, sticky=tk.W)
            widgets['name'] = name_entry

            ttk.Label(dynamon_frame, text="Level:").grid(row=1, column=1, sticky=tk.W)
            level_entry = ttk.Entry(dynamon_frame)
            level_entry.insert(0, dynamon["level"])
            level_entry.grid(row=1, column=2, sticky=tk.W)
            widgets['level'] = level_entry
            
            ttk.Label(dynamon_frame, text="Health:").grid(row=2, column=1, sticky=tk.W)
            health_entry = ttk.Entry(dynamon_frame)
            health_entry.insert(0, dynamon["health"])
            health_entry.grid(row=2, column=2, sticky=tk.W)
            widgets['health'] = health_entry
            
            self.dynamon_widgets.append(widgets)

    def get_image_label(self, dynamon_name, parent):
        try:
            # Construct the path to the image file
            image_path = resource_path(f"images/{dynamon_name.lower()}.png")

            # Open and display the image
            img = Image.open(image_path)
            img = img.resize((100, 100)) # Resize if necessary
            img_tk = ImageTk.PhotoImage(img)

            label = ttk.Label(parent, image=img_tk)
            label.image = img_tk # Keep a reference

        except FileNotFoundError:
            # If image is not found, show a placeholder
            img = Image.new('RGB', (100, 100), color = 'gray')
            img_tk = ImageTk.PhotoImage(img)
            label = ttk.Label(parent, image=img_tk)
            label.image = img_tk
        except Exception as e:
            label = ttk.Label(parent, text="Image Error")

        return label

    def update_dynamons_from_ui(self):
        if not hasattr(self, 'dynamon_widgets'): return
        for i, widgets in enumerate(self.dynamon_widgets):
            self.dynamons[i]['name'] = widgets['name'].get()
            self.dynamons[i]['level'] = widgets['level'].get()
            self.dynamons[i]['health'] = widgets['health'].get()

    def serialize_dynamons_to_string(self):
        if not hasattr(self, 'dynamons'): return ""
        new_data_parts = []
        for dynamon in self.dynamons:
            part = f"{dynamon['name']},{dynamon['level']},{dynamon['health']},{dynamon['unknown1']},{dynamon['unknown2']},{dynamon['value1']},{dynamon['unknown3']},{dynamon['value2']}"
            new_data_parts.append(part)
        return ';'.join(new_data_parts) + ';'

    def load_default_from_url(self):
        """Load the default save file from a URL"""
        try:
            self.status_var.set("Downloading save file...")
            self.root.update()  # Update the UI to show the status
            
            # Download the file from URL
            with urllib.request.urlopen(self.default_save_url) as response:
                xml_content = response.read()
                
            # Parse the XML content
            tree = ET.parse(io.BytesIO(xml_content))
            root = tree.getroot()
            
            # Create a temporary file to work with
            temp_file = Path("temp_save.xml")
            tree.write(temp_file, encoding='utf-8', xml_declaration=True)
            
            self.current_file = temp_file
            self.create_backup()
            
            # Load values into GUI
            for key, var in self.vars.items():
                element = root.find(f'.//string[@name="{key}"]')
                var.set(element.text if element is not None else "")

            self.find_and_parse_dynamons_data(root)
            self.display_dynamons()
                
            self.status_var.set("Default save file loaded successfully!")
            messagebox.showinfo("Success", "Default save file loaded from URL!")
            
        except Exception as e:
            self.status_var.set("Error loading from URL")
            messagebox.showerror("Error", f"Failed to load file from URL:\n{str(e)}")
            self.current_file = None

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

            self.find_and_parse_dynamons_data(root)
            self.display_dynamons()

            self.status_var.set("Save file loaded successfully!")
            messagebox.showinfo("Success", "Save file loaded successfully!")
        except Exception as e:
            self.status_var.set("Error loading file")
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
                # This logic for item_vars seems incorrect based on the create_items_tab method
                # Assuming item_vars keys are "Heal Spray", "Discatch Special", "Unlimited Snacks"
                if self.item_vars["Heal Spray"].get():
                    existing["heal_spray"] = "heal_spray,9999"
                if self.item_vars["Discatch Special"].get():
                    existing["discatch_special"] = "discatch_special,1"
                if self.item_vars["Unlimited Snacks"].get():
                    existing["unlimited_snacks"] = "unlimited_snacks,1"
                items.text = ';'.join(existing.values())

            # Save party data
            self.update_dynamons_from_ui()
            new_dynamons_string = self.serialize_dynamons_to_string()
            for string_tag in root.findall(".//string"):
                if string_tag.get("name") == "dynamons_worldMONS_DATA":
                    string_tag.text = new_dynamons_string
                    break

            tree.write(self.current_file, encoding='utf-8', xml_declaration=True)
            self.status_var.set("Save file updated!")
            messagebox.showinfo("Success", "Save file updated!")
        except Exception as e:
            self.status_var.set("Error saving file")
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
            self.status_var.set(f"Restored backup from {backups[-1].name}")
            messagebox.showinfo("Restored", f"Restored backup from {backups[-1].name}")
        except Exception as e:
            self.status_var.set("Error restoring backup")
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
    try:
        root.iconbitmap(resource_path("profile.ico"))
    except:
        pass  # Skip if icon not available
    app = SaveEditor(root)
    root.mainloop()
