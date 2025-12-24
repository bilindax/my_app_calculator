"""
Quick Demo: Phase 10 Modern UI Enhancements
============================================
Run this script to see the visual improvements in action.
"""

import tkinter as tk
from tkinter import ttk, messagebox

try:
    from bilind.ui.modern_styles import ModernStyleManager
    print("✅ ttkbootstrap installed and imported successfully")
    HAS_TTKBOOTSTRAP = True
except ImportError:
    print("⚠️ ttkbootstrap not installed - using fallback")
    HAS_TTKBOOTSTRAP = False


def demo_modern_ui():
    """Show a comparison of before/after styling."""
    
    root = tk.Tk()
    root.title("BILIND Phase 10 - Modern UI Demo")
    root.geometry("900x600")
    
    # Apply modern styling
    if HAS_TTKBOOTSTRAP:
        modern_style = ModernStyleManager(root, theme_name='cyborg')
        print(f"✅ Applied theme: cyborg")
    else:
        style = ttk.Style()
        style.theme_use('clam')
        print("✅ Using fallback clam theme")
    
    # Header
    header = tk.Frame(root, bg='#00d4ff', height=80)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    
    tk.Label(
        header,
        text="🎨 BILIND Modern UI Demo - Phase 10",
        font=('Segoe UI Semibold', 18),
        bg='#00d4ff',
        fg='#000000'
    ).pack(pady=25)
    
    # Main content
    content = ttk.Frame(root, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    # Info label
    info = ttk.Label(
        content,
        text="✨ New Features: Alternating rows, smooth hover, modern dark themes, enhanced buttons",
        font=('Segoe UI', 10)
    )
    info.pack(pady=(0, 10))
    
    # Demo treeview with alternating rows
    tree_frame = ttk.LabelFrame(content, text="Sample Data Table (Alternating Rows)", padding=10)
    tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    tree = ttk.Treeview(
        tree_frame,
        columns=('Name', 'Type', 'Value', 'Status'),
        show='headings',
        height=10
    )
    
    # Configure columns
    tree.heading('Name', text='Item Name')
    tree.heading('Type', text='Type')
    tree.heading('Value', text='Value (m²)')
    tree.heading('Status', text='Status')
    
    tree.column('Name', width=200)
    tree.column('Type', width=150)
    tree.column('Value', width=120)
    tree.column('Status', width=120)
    
    # Sample data
    sample_data = [
        ('Room 1', 'Bedroom', '12.50', '✅ Complete'),
        ('Room 2', 'Living Room', '25.30', '✅ Complete'),
        ('Room 3', 'Kitchen', '15.80', '⏳ Pending'),
        ('Door D1', 'Wood', '1.89', '✅ Complete'),
        ('Door D2', 'Steel', '2.10', '✅ Complete'),
        ('Window W1', 'Aluminum', '1.80', '⏳ Pending'),
        ('Wall 1', 'External', '45.60', '✅ Complete'),
        ('Wall 2', 'Internal', '32.40', '✅ Complete'),
    ]
    
    for idx, item in enumerate(sample_data):
        tree.insert('', 'end', values=item)
    
    # Add scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Apply modern enhancements
    if HAS_TTKBOOTSTRAP and hasattr(modern_style, 'enhance_treeview'):
        modern_style.enhance_treeview(tree)
        print("✅ Applied alternating rows and hover effects")
    
    # Buttons demo
    button_frame = ttk.Frame(content)
    button_frame.pack(pady=10)
    
    ttk.Button(button_frame, text="✅ Primary Action", style='Accent.TButton').pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="🗑️ Delete", style='Danger.TButton').pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Cancel", style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
    
    # Status bar
    status = tk.Frame(root, bg='#1a1d23', height=30)
    status.pack(fill=tk.X, side=tk.BOTTOM)
    status.pack_propagate(False)
    
    tk.Label(
        status,
        text="🎉 Phase 10 Complete: Modern UI with ttkbootstrap themes applied",
        bg='#1a1d23',
        fg='#00d4ff',
        font=('Segoe UI', 9)
    ).pack(pady=5, padx=10, anchor=tk.W)
    
    # Theme info
    if HAS_TTKBOOTSTRAP:
        theme_info = f"Current Theme: {modern_style.theme_name.upper()}"
        available_themes = ", ".join(ModernStyleManager.get_available_themes())
        messagebox.showinfo(
            "Phase 10 Complete ✅",
            f"{theme_info}\n\n"
            f"Available themes:\n{available_themes}\n\n"
            "Go to Settings → Appearance to change themes in the main app."
        )
    else:
        messagebox.showinfo(
            "Demo Running in Fallback Mode",
            "ttkbootstrap not installed.\n\n"
            "Install it to see modern themes:\n"
            "pip install ttkbootstrap"
        )
    
    root.mainloop()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("BILIND Phase 10: Modern UI Enhancements - Demo")
    print("="*60)
    print("\nStarting demo window...")
    demo_modern_ui()
