import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import base64
import json

class WholeThingEditor(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("The Whole Thing Editor(TM) - v2.0")
        self.geometry("800x600")

        self.current_file_path = None
        self.data = {}

        # --- UI Elements ---
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview for key-value editing
        self.tree = ttk.Treeview(self.main_frame, columns=("Value",), selectmode="browse")
        self.tree.heading("#0", text="Key")
        self.tree.heading("Value", text="Value")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Status Bar
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Menu Bar ---
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # --- Bindings ---
        self.tree.bind("<Double-1>", self.on_double_click)

    def _populate_tree(self, parent, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                node = self.tree.insert(parent, 'end', text=key, open=True)
                self._populate_tree(node, value)
            else:
                self.tree.insert(parent, 'end', text=key, values=(value,))

    def open_file(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        
        try:
            with open(path, 'rb') as f:
                encoded_content = f.read()
            
            decoded_content = base64.b64decode(encoded_content).decode('utf-8')
            self.data = json.loads(decoded_content)

            # Clear existing tree
            for i in self.tree.get_children():
                self.tree.delete(i)

            self._populate_tree('' , self.data)
            
            self.current_file_path = path
            self.status_bar.config(text=f"Opened: {self.current_file_path}")
        except Exception as e:
            messagebox.showerror("Error Opening File", f"Could not read or decode the file as Base64/JSON:\n{e}")
            self.status_bar.config(text="Error opening file")

    def _tree_to_dict(self, parent):
        dictionary = {}
        for node_id in self.tree.get_children(parent):
            key = self.tree.item(node_id, 'text')
            children = self.tree.get_children(node_id)
            if children: # It's a category (dict)
                dictionary[key] = self._tree_to_dict(node_id)
            else: # It's a key-value pair
                value = self.tree.item(node_id, 'values')[0]
                # Try to convert back to original type (int, float, bool)
                if value.isdigit():
                    dictionary[key] = int(value)
                elif value.replace('.','',1).isdigit():
                    dictionary[key] = float(value)
                elif value.lower() in ['true', 'false']:
                    dictionary[key] = value.lower() == 'true'
                else:
                    dictionary[key] = value
        return dictionary

    def save_file(self):
        if not self.current_file_path:
            self.save_file_as()
            return
        self._write_to_path(self.current_file_path)

    def save_file_as(self):
        path = filedialog.asksaveasfilename()
        if not path:
            return
        self._write_to_path(path)
        self.current_file_path = path
        self.status_bar.config(text=f"Saved to: {self.current_file_path}")

    def _write_to_path(self, path):
        try:
            self.data = self._tree_to_dict('')
            json_content = json.dumps(self.data, indent=4)
            encoded_content = base64.b64encode(json_content.encode('utf-8'))
            
            with open(path, 'wb') as f:
                f.write(encoded_content)
            
            self.status_bar.config(text=f"Saved: {path}")
        except Exception as e:
            messagebox.showerror("Error Saving File", f"Could not construct or save the file:\n{e}")
            self.status_bar.config(text="Error saving file")

    def on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        if column != "#1": # Only allow editing in the "Value" column
            return

        item_id = self.tree.focus()
        if not self.tree.get_children(item_id): # Ensure it's a leaf node
            x, y, width, height = self.tree.bbox(item_id, "Value")

            entry_var = tk.StringVar()
            entry = ttk.Entry(self.tree, textvariable=entry_var)
            entry.place(x=x, y=y, width=width, height=height)
            
            original_value = self.tree.item(item_id, 'values')[0]
            entry_var.set(original_value)
            entry.focus_force()

            def save_edit(event=None):
                new_value = entry_var.get()
                self.tree.set(item_id, "Value", new_value)
                entry.destroy()

            entry.bind("<Return>", save_edit)
            entry.bind("<FocusOut>", lambda e: entry.destroy())
            entry.bind("<Escape>", lambda e: entry.destroy())

if __name__ == "__main__":
    app = WholeThingEditor()
    app.mainloop()
