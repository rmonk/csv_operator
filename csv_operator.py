#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import json
import subprocess

class CSVEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Column Editor")
        self.root.geometry("1000x700")

        # Data and Config State
        self.df = pd.DataFrame()
        self.column_configs = {} # Stores the logic: { "Name": { "type": "...", "value": "..." } }
        self.current_file_path = None

        # GUI Layout
        self.create_widgets()

    def create_widgets(self):
        # Top Toolbar
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text="Open CSV", command=self.open_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Add Column", command=self.open_add_column_dialog).pack(side=tk.LEFT, padx=2)
        
        # Edit Button
        self.edit_btn = ttk.Button(toolbar, text="Edit Selected", command=self.open_edit_dialog_from_selection, state=tk.DISABLED)
        self.edit_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Load Config", command=self.load_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save CSV", command=self.save_csv).pack(side=tk.LEFT, padx=2)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Main Content Area (Treeview)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        self.tree = ttk.Treeview(main_frame, show="headings")
        
        # Scrollbars
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(main_frame, orient="horizontal", command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Bind Right-Click for Editing
        self.tree.bind("<Button-3>", self.on_column_right_click)

    def on_column_right_click(self, event):
        """Identify which column was right-clicked."""
        # Get column index (#1, #2, etc.) from the x-coordinate
        col_index = self.tree.identify_column(event.x)
        
        if not col_index:
            return

        # Get the column name (removing the * if it exists)
        heading_text = self.tree.heading(col_index)['text']
        col_name = heading_text.lstrip('*')

        # Check if this column is a computed one (in our config)
        if col_name in self.column_configs:
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Edit Operation", command=lambda: self.open_edit_column_dialog(col_name))
            menu.add_command(label="Delete Column", command=lambda: self.delete_column(col_name))
            menu.post(event.x_root, event.y_root)

    def delete_column(self, col_name):
        if messagebox.askyesno("Confirm", f"Delete column '{col_name}' and its logic?"):
            # Remove from DataFrame
            if col_name in self.df.columns:
                del self.df[col_name]
            # Remove from Config
            if col_name in self.column_configs:
                del self.column_configs[col_name]
            self.update_display()

    # --- File Operations ---

    def open_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        
        try:
            self.current_file_path = file_path
            self.df = pd.read_csv(file_path, encoding='utf-8-sig', engine='python')
            self.update_display()
            self.status_var.set(f"Loaded: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")

    def save_csv(self):
        if self.current_file_path is None:
            messagebox.showwarning("Warning", "No file loaded to save.")
            return
        
        try:
            save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if save_path:
                self.df.to_csv(save_path, index=False)
                self.status_var.set(f"Saved to: {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV: {e}")

    # --- Column Logic ---

    def open_add_column_dialog(self):
        self._open_column_dialog(new_mode=True)

    def open_edit_dialog_from_selection(self):
        # Find currently selected column
        selection = self.tree.selection()
        if not selection:
            return
        
        # Get the ID of the selected item
        item_id = selection[0]
        
        # Get the columns for that item to find the column name
        columns = self.tree["columns"]
        
        # Determine which column we are editing based on what is in the selected row?
        # Actually, easier: Check the column headers. 
        # But simpler: We need to know the column name.
        # Let's iterate columns to find which one corresponds to the selection? 
        # No, Treeview selection is per row.
        # We need to know the column name. 
        # Since we can't easily get the column name from the selection ID alone without checking headers,
        # let's iterate all computed columns in the UI to see if we can guess?
        # Better: Check the column IDs.
        
        # Get the column index of the selected item
        item_index = self.tree.index(item_id)
        if item_index == 0: return # Top row is usually empty or index 0
        
        # We need the col name. Let's just iterate the computed columns list.
        # If we are here, user clicked "Edit Selected", so there must be a column clicked.
        # This button is currently hard to trigger without right-clicking due to logic complexity.
        # Let's rely on the Right-Click menu for precision.
        messagebox.showinfo("Info", "Right-click on the column header to edit it.")

    def open_edit_column_dialog(self, col_name):
        config = self.column_configs[col_name]
        self._open_column_dialog(new_mode=False, col_name=col_name, config=config)

    def _open_column_dialog(self, new_mode, col_name=None, config=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Column" if not new_mode else "Add Column")
        dialog.geometry("500x400")

        # 1. Column Name
        ttk.Label(dialog, text="Column Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)
        
        if not new_mode:
            name_entry.insert(0, col_name)
            name_entry.config(state='readonly') # Can't rename for simplicity, or enable if needed

        # 2. Type Selection
        ttk.Label(dialog, text="Type:").pack(pady=5)
        type_var = tk.StringVar(value=config.get("type", "python"))
        type_combo = ttk.Combobox(dialog, textvariable=type_var, values=["python", "command", "value"], state="readonly")
        type_combo.pack(pady=5)
        
        # 3. Content Input
        ttk.Label(dialog, text="Content / Logic:").pack(pady=5)
        content_text = tk.Text(dialog, width=50, height=10)
        content_text.pack(pady=5)
        
        if type_var.get() == "python":
            content_text.insert(tk.END, config.get("value", "col1 + col2 * 2"))
            content_text.insert(tk.END, "\n\nVariables available: All current column names")
        elif type_var.get() == "command":
            content_text.insert(tk.END, config.get("value", 'echo "Value: {col1}"'))
            content_text.insert(tk.END, "\n\nPlaceholders: Use {column_name} for variables")
        else:
            content_text.insert(tk.END, config.get("value", "Static text value"))

        def apply_logic():
            name = name_entry.get().strip()
            logic_type = type_var.get()
            logic_str = content_text.get("1.0", tk.END).strip()

            if not name:
                messagebox.showerror("Error", "Column name is required.")
                return

            if not logic_str:
                messagebox.showerror("Error", "Logic is required.")
                return

            try:
                if logic_type == "value":
                    self.df[name] = logic_str
                
                elif logic_type == "python":
                    self.df[name] = self.df.apply(
                        lambda row: eval(logic_str, {}, row.to_dict()), axis=1
                    )
                
                elif logic_type == "command":
                    self.status_var.set("Applying command logic...")
                    self.root.update_idletasks()
                    
                    for idx, row in self.df.iterrows():
                        cmd_str = logic_str
                        for col in self.df.columns:
                            if col in row:
                                cmd_str = cmd_str.replace(f"{{{col}}}").replace(str(row[col]))
                        
                        try:
                            result = subprocess.run(
                                cmd_str, 
                                shell=True, 
                                capture_output=True, 
                                text=True, 
                                timeout=10
                            )
                            output = result.stdout.strip() if result.stdout else result.stderr.strip()
                            self.df.at[idx, name] = output
                        except Exception as e:
                            self.df.at[idx, name] = f"Error: {e}"
                    
                    self.status_var.set("Command logic applied.")
                
                # Update Config
                if new_mode:
                    self.column_configs[name] = {"type": logic_type, "value": logic_str}
                else:
                    # Update existing
                    self.column_configs[col_name] = {"type": logic_type, "value": logic_str}
                    # If name changed, rename in DF
                    if name != col_name:
                        self.df.rename(columns={col_name: name}, inplace=True)

                self.update_display()
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply logic: {e}")

        ttk.Button(dialog, text="Apply / Update", command=apply_logic).pack(pady=10)

    def update_display(self):
        # Reset Column Configuration
        self.tree["columns"] = ()

        # Clear all existing rows
        self.tree.delete(*self.tree.get_children())

        if self.df.empty:
            self.status_var.set("No data loaded.")
            return

        # Add columns
        self.tree["columns"] = tuple(self.df.columns)

        for col in self.df.columns:
            self.tree.column(col, width=100, anchor=tk.CENTER)
            self.tree.heading(col, text=col)
            
            if col in self.column_configs:
                self.tree.heading(col, text=f"*{col}")

        # Insert Data
        limit = 100
        try:
            for i, row in self.df.head(limit).iterrows():
                values = []
                for col in self.df.columns:
                    val = row[col] if col in row else ""
                    values.append(str(val))
                self.tree.insert("", tk.END, values=values)
            
            self.status_var.set(f"Loaded {len(self.df.columns)} columns, {min(len(self.df), limit)} rows.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- Save/Load Config ---

    def save_config(self):
        if not self.column_configs:
            messagebox.showinfo("Info", "No custom columns to save.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path:
            return

        try:
            with open(file_path, "w") as f:
                json.dump(self.column_configs, f, indent=4)
            messagebox.showinfo("Success", "Configuration saved.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def load_config(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                new_configs = json.load(f)
            
            for col_name, config in new_configs.items():
                logic_type = config.get("type")
                logic_str = config.get("value")

                try:
                    if logic_type == "value":
                        self.df[col_name] = logic_str
                    
                    elif logic_type == "python":
                        self.df[col_name] = self.df.apply(
                            lambda row: eval(logic_str, {}, row.to_dict()), axis=1
                        )
                    
                    elif logic_type == "command":
                         for idx, row in self.df.iterrows():
                            cmd_str = logic_str
                            for col in self.df.columns:
                                if col in row:
                                    cmd_str = cmd_str.replace(f"{{{col}}}", str(row[col]))
                            
                            try:
                                result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True, timeout=10)
                                output = result.stdout.strip() if result.stdout else result.stderr.strip()
                                self.df.at[idx, col_name] = output
                            except Exception:
                                pass
                    
                    self.column_configs[col_name] = config

                except Exception as e:
                    print(f"Failed to load column '{col_name}': {e}")

            self.update_display()
            messagebox.showinfo("Success", "Configuration loaded.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVEditorApp(root)
    root.mainloop()

