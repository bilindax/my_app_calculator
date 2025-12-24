"""
Room Type Picker Dialog
Allows user to select room type before picking rooms from AutoCAD.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class RoomTypePickerDialog:
    """Dialog to select room type and pick rooms from AutoCAD."""
    
    ROOM_TYPES = [
        "Living Room",
        "Bedroom",
        "Kitchen",
        "Bathroom",
        "Toilet",
        "Balcony",
        "Corridor",
        "Storage",
        "Dining Room",
        "Office",
        "Laundry",
        "Entrance",
        "Other"
    ]
    
    def __init__(self, parent, picker_callback):
        """
        Args:
            parent: Parent Tkinter widget
            picker_callback: Function(room_type: str) -> list[Room] to call when Pick is clicked
        """
        self.parent = parent
        self.picker_callback = picker_callback
        self.result = None  # Will store list of picked rooms
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Pick Rooms by Type")
        self.dialog.geometry("550x350")
        self.dialog.resizable(True, True)
        self.dialog.minsize(500, 300)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._center_dialog()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Header
        header_frame = ttk.Frame(self.dialog, padding=15)
        header_frame.pack(fill='x')
        
        ttk.Label(
            header_frame,
            text="🏠 Pick Rooms from AutoCAD",
            font=('Segoe UI', 12, 'bold')
        ).pack(anchor='w')
        
        ttk.Label(
            header_frame,
            text="Select room type, then pick rooms from drawing.",
            font=('Segoe UI', 9)
        ).pack(anchor='w', pady=(5, 0))
        
        # Room Type Selection
        type_frame = ttk.LabelFrame(self.dialog, text="Room Type", padding=15)
        type_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        ttk.Label(type_frame, text="Choose room type:").pack(anchor='w')
        
        self.room_type_var = tk.StringVar(value=self.ROOM_TYPES[0])
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.room_type_var,
            values=self.ROOM_TYPES,
            state='readonly',
            width=30
        )
        type_combo.pack(fill='x', pady=(5, 0))
        
        # Quantity hint
        ttk.Label(
            type_frame,
            text="Tip: You can pick multiple rooms of the same type at once.",
            font=('Segoe UI', 8, 'italic'),
            foreground='gray'
        ).pack(anchor='w', pady=(10, 0))
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog, padding=(15, 0, 15, 15))
        btn_frame.pack(fill='x')
        
        ttk.Button(
            btn_frame,
            text="📍 Pick from AutoCAD",
            command=self._on_pick,
            style='Accent.TButton',
            width=20
        ).pack(side='left', padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_cancel,
            width=15
        ).pack(side='left')
    
    def _center_dialog(self):
        """Center dialog on parent window."""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
    
    def _on_pick(self):
        """Call picker callback and close dialog."""
        room_type = self.room_type_var.get()
        
        try:
            # Call the picker function (should hide dialog, pick from AutoCAD, return rooms)
            picked_rooms = self.picker_callback(room_type)
            
            if picked_rooms:
                self.result = picked_rooms
                self.dialog.destroy()
            else:
                messagebox.showwarning("No Rooms Picked", "No rooms were selected from AutoCAD.")
        except Exception as e:
            messagebox.showerror("Picker Error", f"Failed to pick rooms:\n{e}")
    
    def _on_cancel(self):
        """Cancel and close dialog."""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and wait for result."""
        self.dialog.wait_window()
        return self.result
