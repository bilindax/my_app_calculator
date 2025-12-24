import tkinter as tk
from tkinter import ttk
import winsound

class MiniPicker(tk.Toplevel):
    def __init__(self, parent, callback_pick, callback_finish, room_types, initial_type="Other", colors=None):
        super().__init__(parent)
        self.callback_pick = callback_pick
        self.callback_finish = callback_finish
        self.room_types = room_types
        self.colors = colors or {
            'bg_primary': '#2d2d2d',
            'bg_secondary': '#2d2d2d',
            'text_primary': '#ffffff',
            'text_secondary': '#aaaaaa',
            'accent': '#007acc',
            'danger': '#d9534f'
        }
        
        # Window setup
        self.title("Mini Picker")
        self.overrideredirect(True)  # Frameless
        self.attributes('-topmost', True)
        self.geometry("+100+100")  # Initial position
        
        # Styling
        bg_color = self.colors.get('bg_secondary', '#2d2d2d')
        fg_color = self.colors.get('text_primary', '#ffffff')
        self.configure(bg=bg_color)
        
        # Main Frame with border
        main_frame = tk.Frame(self, bg='#404040', bd=1) # Border color
        main_frame.pack(fill='both', expand=True)
        
        inner_frame = tk.Frame(main_frame, bg=bg_color)
        inner_frame.pack(fill='both', expand=True, padx=1, pady=1)
        
        # Drag handle
        title_bar = tk.Label(inner_frame, text=" :: Room Picker :: ", 
                            bg=self.colors.get('bg_primary', '#1a1d23'), 
                            fg=fg_color, cursor="fleur", font=('Segoe UI', 9))
        title_bar.pack(fill='x', side='top')
        title_bar.bind("<Button-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.do_move)
        
        # Content
        content_frame = tk.Frame(inner_frame, bg=bg_color, padx=12, pady=12)
        content_frame.pack(fill='both', expand=True)
        
        # Type Selector
        row1 = tk.Frame(content_frame, bg=bg_color)
        row1.pack(fill='x', pady=(0, 8))
        
        tk.Label(row1, text="Type:", bg=bg_color, fg=fg_color, font=('Segoe UI', 10)).pack(side='left', padx=(0, 8))
        
        self.type_var = tk.StringVar(value=initial_type)
        self.type_combo = ttk.Combobox(row1, textvariable=self.type_var, values=self.room_types, width=18, state='readonly')
        self.type_combo.pack(side='left')
        
        # Pick Button
        self.pick_btn = tk.Button(row1, text="PICK", command=self.on_pick, 
                                 bg=self.colors.get('accent', '#007acc'), 
                                 fg='white', relief='flat', 
                                 font=('Segoe UI Semibold', 9), padx=12)
        self.pick_btn.pack(side='left', padx=(8, 0))
        
        # Status Label
        self.status_label = tk.Label(content_frame, text="Ready to pick", 
                                    bg=bg_color, fg=self.colors.get('text_secondary', '#aaaaaa'), 
                                    font=('Segoe UI', 9))
        self.status_label.pack(fill='x', pady=(0, 8))
        
        # Finish Button
        finish_btn = tk.Button(content_frame, text="Finish / Close", command=self.on_finish, 
                              bg=self.colors.get('danger', '#d9534f'), 
                              fg='white', relief='flat',
                              font=('Segoe UI', 9))
        finish_btn.pack(fill='x')
        
        # Bind keys
        self.bind('<Return>', lambda e: self.on_pick())
        self.bind('<Escape>', lambda e: self.on_finish())
        
        # Center on screen roughly or remember position
        self.update_idletasks()
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def on_pick(self):
        rtype = self.type_var.get()
        self.status_label.config(text="Picking...", fg='#ffff00')
        self.update()
        
        # Hide mini picker temporarily to allow selection
        self.withdraw()
        count = self.callback_pick(rtype)
        self.deiconify()
        
        if count > 0:
            self.status_label.config(text=f"Added {count} {rtype}(s)", fg='#00ff00')
            try:
                winsound.Beep(1000, 200)
            except:
                pass
        else:
            self.status_label.config(text="No selection", fg='#ffaa00')

    def on_finish(self):
        self.callback_finish()
        self.destroy()
