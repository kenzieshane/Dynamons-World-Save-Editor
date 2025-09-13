
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
from PIL import Image, ImageTk
import requests
from io import BytesIO

class DynamonPartyEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dynamon Party Editor")
        self.geometry("800x600")

        self.current_file_path = None
        self.tree = None
        self.dynamons_data_string = None
        self.dynamons = []

        # --- UI Elements ---
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Menu Bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open XML", command=self.load_xml)
        file_menu.add_command(label="Save XML", command=self.save_xml)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        self.dynamons_frame = ttk.LabelFrame(self.main_frame, text="Dynamons")
        self.dynamons_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_xml(self):
        path = filedialog.askopenfilename(filetypes=[("XML Files", "*.xml")])
        if not path:
            return

        try:
            self.tree = ET.parse(path)
            self.current_file_path = path
            self.status_bar.config(text=f"Opened: {self.current_file_path}")
            self.find_and_parse_dynamons_data()
            self.display_dynamons()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load or parse XML file: {e}")

    def find_and_parse_dynamons_data(self):
        root = self.tree.getroot()
        for string_tag in root.findall(".//string"):
            if string_tag.get("name") == "dynamons_worldMONS_DATA":
                self.dynamons_data_string = string_tag.text
                break
        
        if self.dynamons_data_string:
            self.dynamons = self.parse_dynamons_string(self.dynamons_data_string)

    def parse_dynamons_string(self, data_string):
        dynamons = []
        parts = data_string.strip().split(';')
        for part in parts:
            if not part:
                continue
            attributes = part.split(',')
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
        # Clear existing widgets
        for widget in self.dynamons_frame.winfo_children():
            widget.destroy()
        
        self.dynamon_widgets = []

        for i, dynamon in enumerate(self.dynamons):
            dynamon_frame = ttk.Frame(self.dynamons_frame, relief=tk.RIDGE, padding=5)
            dynamon_frame.pack(pady=5, fill=tk.X)

            widgets = {}

            # Image placeholder
            img_label = self.get_image_label(dynamon["name"], dynamon_frame)
            img_label.grid(row=0, column=0, rowspan=4, padx=5)

            # Attributes
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
        # Placeholder image
        img = Image.new('RGB', (100, 100), color = 'gray')
        img_tk = ImageTk.PhotoImage(img)
        label = ttk.Label(parent, image=img_tk)
        label.image = img_tk # Keep a reference
        return label

    def update_dynamons_from_ui(self):
        for i, widgets in enumerate(self.dynamon_widgets):
            self.dynamons[i]['name'] = widgets['name'].get()
            self.dynamons[i]['level'] = widgets['level'].get()
            self.dynamons[i]['health'] = widgets['health'].get()

    def serialize_dynamons_to_string(self):
        new_data_parts = []
        for dynamon in self.dynamons:
            part = f"{dynamon['name']},{dynamon['level']},{dynamon['health']},{dynamon['unknown1']},{dynamon['unknown2']},{dynamon['value1']},{dynamon['unknown3']},{dynamon['value2']}"
            new_data_parts.append(part)
        return ';'.join(new_data_parts) + ';'

    def save_xml(self):
        if not self.current_file_path or not self.tree:
            messagebox.showerror("Error", "No XML file loaded.")
            return

        try:
            self.update_dynamons_from_ui()
            new_dynamons_string = self.serialize_dynamons_to_string()

            root = self.tree.getroot()
            updated = False
            for string_tag in root.findall(".//string"):
                if string_tag.get("name") == "dynamons_worldMONS_DATA":
                    string_tag.text = new_dynamons_string
                    updated = True
                    break
            
            if not updated:
                messagebox.showerror("Error", "Could not find the dynamons_worldMONS_DATA string in the XML.")
                return

            self.tree.write(self.current_file_path, encoding='utf-8', xml_declaration=True)
            self.status_bar.config(text=f"Saved to: {self.current_file_path}")
            messagebox.showinfo("Success", "File saved successfully!")

        except Exception as e:
            messagebox.showerror("Error Saving File", f"Could not save the file:\n{e}")
            self.status_bar.config(text="Error saving file")


if __name__ == "__main__":
    app = DynamonPartyEditor()
    app.mainloop()
