"""
BILIND AutoCAD Extension - Python Version (Enhanced)
=====================================================
نافذة Tkinter متقدمة لحساب:
- مساحات الغرف (W×L)
- الفتحات (أبواب/شبابيك) منفصلة
- الجدران مع طرح الفراغات
- الزريقة والدهان والسيراميك
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import math
import csv
import os
from datetime import datetime

try:
    import pyautocad
    from pyautocad import Autocad, APoint
except ImportError:
    print("⚠️ pyautocad not installed. Run: pip install pyautocad")
    exit(1)

class BilindApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BILIND - AutoCAD Room & Opening Calculator")
        self.root.geometry("900x700")
        self.root.configure(bg='#2b2b2b')
        
        # Keep window on top
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        
        # Connect to AutoCAD
        try:
            self.acad = Autocad(create_if_not_exists=False)
            self.doc = self.acad.doc
            self.root.title(f"BILIND - Connected to AutoCAD {self.acad.doc.Name}")
        except:
            messagebox.showerror("Error", "AutoCAD not running! Please open AutoCAD first.")
            self.root.destroy()
            return
        
        self.scale = 1.0  # 1 للمتر، 0.001 للـmm
        self.rooms = []
        self.doors = []
        self.windows = []
        self.walls = []
        self.finishes = {
            'plaster': [],  # زريقة
            'paint': [],    # دهان
            'tiles': []     # سيراميك
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        # Create Notebook (Tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Rooms & Openings
        tab1 = tk.Frame(notebook, bg='#2b2b2b')
        notebook.add(tab1, text="📐 Rooms & Openings")
        self.setup_tab1(tab1)
        
        # Tab 2: Walls
        tab2 = tk.Frame(notebook, bg='#2b2b2b')
        notebook.add(tab2, text="🧱 Walls")
        self.setup_tab2(tab2)
        
        # Tab 3: Finishes
        tab3 = tk.Frame(notebook, bg='#2b2b2b')
        notebook.add(tab3, text="🎨 Finishes")
        self.setup_tab3(tab3)
        
        # Tab 4: Summary
        tab4 = tk.Frame(notebook, bg='#2b2b2b')
        notebook.add(tab4, text="📊 Summary")
        self.setup_tab4(tab4)
    
    def setup_tab1(self, parent):
        # Top Frame - Controls
        top_frame = tk.Frame(parent, bg='#2b2b2b', pady=10)
        top_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(top_frame, text="Scale:", fg='white', bg='#2b2b2b', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.scale_entry = tk.Entry(top_frame, width=10, font=('Arial', 10))
        self.scale_entry.insert(0, "1.0")
        self.scale_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="🏠 Pick Rooms", command=self.pick_rooms, 
                 bg='#4CAF50', fg='white', font=('Arial', 9, 'bold'), 
                 padx=10, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=3)
        
        tk.Button(top_frame, text="🚪 Pick Doors", command=self.pick_doors,
                 bg='#8B4513', fg='white', font=('Arial', 9, 'bold'),
                 padx=10, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=3)
        
        tk.Button(top_frame, text="🪟 Pick Windows", command=self.pick_windows,
                 bg='#2196F3', fg='white', font=('Arial', 9, 'bold'),
                 padx=10, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=3)
        
        tk.Button(top_frame, text="🔄 Reset", command=self.reset_data,
                 bg='#FF9800', fg='white', font=('Arial', 9, 'bold'),
                 padx=10, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=3)
        
        # Rooms Table
        rooms_frame = tk.LabelFrame(parent, text="📋 ROOMS", fg='white', bg='#2b2b2b', 
                                   font=('Arial', 10, 'bold'), pady=5)
        rooms_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.rooms_tree = ttk.Treeview(rooms_frame, columns=('Layer', 'W(m)', 'L(m)', 'Perim(m)', 'Area(m²)'),
                                       show='headings', height=6)
        for col in self.rooms_tree['columns']:
            self.rooms_tree.heading(col, text=col)
            self.rooms_tree.column(col, width=130, anchor='center')
        
        scrollbar1 = ttk.Scrollbar(rooms_frame, orient=tk.VERTICAL, command=self.rooms_tree.yview)
        self.rooms_tree.configure(yscroll=scrollbar1.set)
        scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)
        self.rooms_tree.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Doors Table
        doors_frame = tk.LabelFrame(parent, text="🚪 DOORS", 
                                    fg='white', bg='#2b2b2b', font=('Arial', 10, 'bold'), pady=5)
        doors_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.doors_tree = ttk.Treeview(doors_frame, 
                                       columns=('Layer', 'W(m)', 'H(m)', 'Perim(m)', 'Area(m²)'),
                                       show='headings', height=4)
        for col in self.doors_tree['columns']:
            self.doors_tree.heading(col, text=col)
            self.doors_tree.column(col, width=120, anchor='center')
        
        scrollbar2 = ttk.Scrollbar(doors_frame, orient=tk.VERTICAL, command=self.doors_tree.yview)
        self.doors_tree.configure(yscroll=scrollbar2.set)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        self.doors_tree.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Windows Table
        windows_frame = tk.LabelFrame(parent, text="🪟 WINDOWS", 
                                      fg='white', bg='#2b2b2b', font=('Arial', 10, 'bold'), pady=5)
        windows_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.windows_tree = ttk.Treeview(windows_frame, 
                                         columns=('Layer', 'W(m)', 'H(m)', 'Perim(m)', 'Area(m²)'),
                                         show='headings', height=4)
        for col in self.windows_tree['columns']:
            self.windows_tree.heading(col, text=col)
            self.windows_tree.column(col, width=120, anchor='center')
        
        scrollbar3 = ttk.Scrollbar(windows_frame, orient=tk.VERTICAL, command=self.windows_tree.yview)
        self.windows_tree.configure(yscroll=scrollbar3.set)
        scrollbar3.pack(side=tk.RIGHT, fill=tk.Y)
        self.windows_tree.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Bottom Frame - Totals
        bottom_frame = tk.Frame(parent, bg='#2b2b2b', pady=5)
        bottom_frame.pack(fill=tk.X, padx=10)
        
        self.totals_label = tk.Label(bottom_frame, text="Totals: 0 Rooms | 0 Doors | 0 Windows",
                                    fg='#4CAF50', bg='#2b2b2b', font=('Arial', 10, 'bold'))
        self.totals_label.pack(side=tk.LEFT, padx=10)
    
    def setup_tab2(self, parent):
        """تبويب الجدران"""
        # Top Frame
        top_frame = tk.Frame(parent, bg='#2b2b2b', pady=10)
        top_frame.pack(fill=tk.X, padx=10)
        
        tk.Button(top_frame, text="🧱 Pick Walls", command=self.pick_walls,
                 bg='#795548', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="➖ Deduct Openings", command=self.calc_walls_with_deduction,
                 bg='#FF5722', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Walls Table
        walls_frame = tk.LabelFrame(parent, text="🧱 WALLS", fg='white', bg='#2b2b2b', 
                                   font=('Arial', 11, 'bold'), pady=10)
        walls_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.walls_tree = ttk.Treeview(walls_frame, 
                                       columns=('Layer', 'Length(m)', 'Height(m)', 'Area(m²)', 'Deducted(m²)', 'Net(m²)'),
                                       show='headings', height=10)
        for col in self.walls_tree['columns']:
            self.walls_tree.heading(col, text=col)
            self.walls_tree.column(col, width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(walls_frame, orient=tk.VERTICAL, command=self.walls_tree.yview)
        self.walls_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.walls_tree.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Totals
        self.walls_total_label = tk.Label(parent, text="Total Net Wall Area = 0.00 m²",
                                          fg='#4CAF50', bg='#2b2b2b', font=('Arial', 12, 'bold'))
        self.walls_total_label.pack(pady=10)
    
    def setup_tab3(self, parent):
        """تبويب التشطيبات (زريقة/دهان/سيراميك)"""
        # Instructions
        info_frame = tk.Frame(parent, bg='#2b2b2b', pady=10)
        info_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(info_frame, text="🎨 Finishes Calculator - حساب التشطيبات",
                fg='yellow', bg='#2b2b2b', font=('Arial', 12, 'bold')).pack()
        
        # Plaster (زريقة)
        plaster_frame = tk.LabelFrame(parent, text="🏗️ PLASTER (زريقة)", fg='white', bg='#2b2b2b', 
                                     font=('Arial', 10, 'bold'), pady=5)
        plaster_frame.pack(fill=tk.X, padx=10, pady=5)
        
        plaster_btn_frame = tk.Frame(plaster_frame, bg='#2b2b2b')
        plaster_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(plaster_btn_frame, text="➕ Add from Rooms", command=lambda: self.add_finish_from_rooms('plaster'),
                 bg='#4CAF50', fg='white', font=('Arial', 9), padx=10, pady=3).pack(side=tk.LEFT, padx=3)
        tk.Button(plaster_btn_frame, text="➕ Add from Walls", command=lambda: self.add_finish_from_walls('plaster'),
                 bg='#795548', fg='white', font=('Arial', 9), padx=10, pady=3).pack(side=tk.LEFT, padx=3)
        tk.Button(plaster_btn_frame, text="➖ Deduct Openings", command=lambda: self.deduct_openings_from_finish('plaster'),
                 bg='#FF5722', fg='white', font=('Arial', 9), padx=10, pady=3).pack(side=tk.LEFT, padx=3)
        
        self.plaster_label = tk.Label(plaster_frame, text="Area = 0.00 m²", fg='#4CAF50', bg='#2b2b2b', font=('Arial', 10, 'bold'))
        self.plaster_label.pack(pady=5)
        
        # Paint (دهان)
        paint_frame = tk.LabelFrame(parent, text="🎨 PAINT (دهان)", fg='white', bg='#2b2b2b', 
                                   font=('Arial', 10, 'bold'), pady=5)
        paint_frame.pack(fill=tk.X, padx=10, pady=5)
        
        paint_btn_frame = tk.Frame(paint_frame, bg='#2b2b2b')
        paint_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(paint_btn_frame, text="➕ Add from Rooms", command=lambda: self.add_finish_from_rooms('paint'),
                 bg='#4CAF50', fg='white', font=('Arial', 9), padx=10, pady=3).pack(side=tk.LEFT, padx=3)
        tk.Button(paint_btn_frame, text="➕ Add from Walls", command=lambda: self.add_finish_from_walls('paint'),
                 bg='#795548', fg='white', font=('Arial', 9), padx=10, pady=3).pack(side=tk.LEFT, padx=3)
        tk.Button(paint_btn_frame, text="➖ Deduct Openings", command=lambda: self.deduct_openings_from_finish('paint'),
                 bg='#FF5722', fg='white', font=('Arial', 9), padx=10, pady=3).pack(side=tk.LEFT, padx=3)
        
        self.paint_label = tk.Label(paint_frame, text="Area = 0.00 m²", fg='#4CAF50', bg='#2b2b2b', font=('Arial', 10, 'bold'))
        self.paint_label.pack(pady=5)
        
        # Tiles (سيراميك)
        tiles_frame = tk.LabelFrame(parent, text="🟦 TILES (سيراميك)", fg='white', bg='#2b2b2b', 
                                   font=('Arial', 10, 'bold'), pady=5)
        tiles_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tiles_btn_frame = tk.Frame(tiles_frame, bg='#2b2b2b')
        tiles_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(tiles_btn_frame, text="➕ Add from Rooms", command=lambda: self.add_finish_from_rooms('tiles'),
                 bg='#4CAF50', fg='white', font=('Arial', 9), padx=10, pady=3).pack(side=tk.LEFT, padx=3)
        tk.Button(tiles_btn_frame, text="➕ Add from Walls", command=lambda: self.add_finish_from_walls('tiles'),
                 bg='#795548', fg='white', font=('Arial', 9), padx=10, pady=3).pack(side=tk.LEFT, padx=3)
        tk.Button(tiles_btn_frame, text="➖ Deduct Openings", command=lambda: self.deduct_openings_from_finish('tiles'),
                 bg='#FF5722', fg='white', font=('Arial', 9), padx=10, pady=3).pack(side=tk.LEFT, padx=3)
        
        self.tiles_label = tk.Label(tiles_frame, text="Area = 0.00 m²", fg='#4CAF50', bg='#2b2b2b', font=('Arial', 10, 'bold'))
        self.tiles_label.pack(pady=5)
    
    def setup_tab4(self, parent):
        """تبويب الملخص النهائي"""
        # Export buttons
        export_frame = tk.Frame(parent, bg='#2b2b2b', pady=10)
        export_frame.pack(fill=tk.X, padx=10)
        
        tk.Button(export_frame, text="📋 Copy All", command=self.copy_to_clipboard,
                 bg='#9C27B0', fg='white', font=('Arial', 10, 'bold'), 
                 padx=15, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(export_frame, text="💾 Export CSV", command=self.export_csv,
                 bg='#795548', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(export_frame, text="📊 Insert Table", command=self.insert_table,
                 bg='#607D8B', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Summary text
        summary_frame = tk.LabelFrame(parent, text="📊 COMPLETE SUMMARY", fg='white', bg='#2b2b2b', 
                                     font=('Arial', 11, 'bold'), pady=10)
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, width=80, height=25, 
                                                      font=('Consolas', 10), bg='#1e1e1e', fg='#00ff00')
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Update button
        tk.Button(parent, text="🔄 Refresh Summary", command=self.update_summary,
                 bg='#FF9800', fg='white', font=('Arial', 11, 'bold'),
                 padx=20, pady=8, cursor='hand2').pack(pady=10)
    
    def update_scale(self):
        try:
            self.scale = float(self.scale_entry.get())
            if self.scale <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Invalid scale value!")
            self.scale = 1.0
            self.scale_entry.delete(0, tk.END)
            self.scale_entry.insert(0, "1.0")
    
    def pick_rooms(self):
        """اختيار الغرف (Polylines/Hatches/Regions)"""
        self.update_scale()
        self.root.withdraw()
        
        try:
            try:
                self.doc.SelectionSets.Item("ROOMS_TEMP").Delete()
            except:
                pass
            
            self.acad.prompt("\n=== Select ROOMS (closed polylines/hatches) ===")
            selection = self.doc.SelectionSets.Add("ROOMS_TEMP")
            selection.SelectOnScreen()
            
            count = 0
            for obj in selection:
                try:
                    area_du = 0
                    try:
                        area_du = obj.Area
                    except:
                        continue
                    
                    if area_du <= 0:
                        continue
                    
                    perim_du = 0
                    try:
                        perim_du = obj.Length
                    except:
                        pass
                    
                    try:
                        layer = obj.Layer
                    except:
                        layer = "Unknown"
                    
                    # حساب W×L بدقة من BoundingBox
                    w_str, l_str = "-", "-"
                    try:
                        bbox = obj.GetBoundingBox()
                        min_pt = bbox[0]
                        max_pt = bbox[1]
                        
                        w_du = abs(max_pt[0] - min_pt[0])
                        l_du = abs(max_pt[1] - min_pt[1])
                        
                        w_m = w_du * self.scale
                        l_m = l_du * self.scale
                        
                        # فحص إذا الشكل منتظم (tolerance 15%)
                        rect_area = w_du * l_du
                        if rect_area > 0:
                            diff_ratio = abs(area_du - rect_area) / rect_area
                            if diff_ratio <= 0.15:
                                w_str = f"{w_m:.3f}"
                                l_str = f"{l_m:.3f}"
                    except Exception as e:
                        print(f"BBox error: {e}")
                    
                    self.rooms.append({
                        'layer': layer,
                        'width': w_str,
                        'length': l_str,
                        'perim': perim_du * self.scale,
                        'area': area_du * self.scale * self.scale
                    })
                    count += 1
                    
                except Exception as e:
                    print(f"Skipping object: {str(e)}")
                    continue
            
            selection.Delete()
            
            if count > 0:
                self.refresh_rooms_table()
                self.update_totals()
                messagebox.showinfo("Success", f"✅ Added {count} room(s)")
            else:
                messagebox.showwarning("Warning", "No valid rooms!\nSelect closed polylines or hatches.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error:\n{str(e)}")
        finally:
            self.root.deiconify()
    
    def pick_doors(self):
        """اختيار الأبواب"""
        self.update_scale()
        self.root.withdraw()
        
        try:
            try:
                self.doc.SelectionSets.Item("DOORS_TEMP").Delete()
            except:
                pass
            
            self.acad.prompt("\n=== Select DOORS (blocks) ===")
            selection = self.doc.SelectionSets.Add("DOORS_TEMP")
            selection.SelectOnScreen()
            
            count = 0
            for block in selection:
                try:
                    try:
                        block_name = block.Name
                        layer = block.Layer
                    except:
                        continue
                    
                    w, h = self.get_block_dimensions(block)
                    if w is None or h is None:
                        continue
                    
                    w_m = w * self.scale
                    h_m = h * self.scale
                    
                    self.doors.append({
                        'layer': layer,
                        'width': w_m,
                        'height': h_m,
                        'perim': 2 * (w_m + h_m),
                        'area': w_m * h_m
                    })
                    count += 1
                    
                except Exception as e:
                    print(f"Skipping door: {str(e)}")
                    continue
            
            selection.Delete()
            
            if count > 0:
                self.refresh_doors_table()
                self.update_totals()
                messagebox.showinfo("Success", f"✅ Added {count} door(s)")
            else:
                messagebox.showwarning("Warning", "No valid doors selected!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error:\n{str(e)}")
        finally:
            self.root.deiconify()
    
    def pick_windows(self):
        """اختيار الشبابيك"""
        self.update_scale()
        self.root.withdraw()
        
        try:
            try:
                self.doc.SelectionSets.Item("WINDOWS_TEMP").Delete()
            except:
                pass
            
            self.acad.prompt("\n=== Select WINDOWS (blocks) ===")
            selection = self.doc.SelectionSets.Add("WINDOWS_TEMP")
            selection.SelectOnScreen()
            
            count = 0
            for block in selection:
                try:
                    try:
                        block_name = block.Name
                        layer = block.Layer
                    except:
                        continue
                    
                    w, h = self.get_block_dimensions(block)
                    if w is None or h is None:
                        continue
                    
                    w_m = w * self.scale
                    h_m = h * self.scale
                    
                    self.windows.append({
                        'layer': layer,
                        'width': w_m,
                        'height': h_m,
                        'perim': 2 * (w_m + h_m),
                        'area': w_m * h_m
                    })
                    count += 1
                    
                except Exception as e:
                    print(f"Skipping window: {str(e)}")
                    continue
            
            selection.Delete()
            
            if count > 0:
                self.refresh_windows_table()
                self.update_totals()
                messagebox.showinfo("Success", f"✅ Added {count} window(s)")
            else:
                messagebox.showwarning("Warning", "No valid windows selected!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error:\n{str(e)}")
        finally:
            self.root.deiconify()
    
    def pick_walls(self):
        """اختيار الجدران (خطوط)"""
        self.update_scale()
        self.root.withdraw()
        
        try:
            try:
                self.doc.SelectionSets.Item("WALLS_TEMP").Delete()
            except:
                pass
            
            # Get wall height from user
            height_str = tk.simpledialog.askstring("Wall Height", "Enter wall height (m):", initialvalue="3.0")
            if not height_str:
                self.root.deiconify()
                return
            
            try:
                wall_height = float(height_str)
            except:
                messagebox.showerror("Error", "Invalid height!")
                self.root.deiconify()
                return
            
            self.acad.prompt("\n=== Select WALLS (lines/polylines) ===")
            selection = self.doc.SelectionSets.Add("WALLS_TEMP")
            selection.SelectOnScreen()
            
            count = 0
            for obj in selection:
                try:
                    length_du = 0
                    try:
                        length_du = obj.Length
                    except:
                        continue
                    
                    if length_du <= 0:
                        continue
                    
                    try:
                        layer = obj.Layer
                    except:
                        layer = "Unknown"
                    
                    length_m = length_du * self.scale
                    area_m2 = length_m * wall_height
                    
                    self.walls.append({
                        'layer': layer,
                        'length': length_m,
                        'height': wall_height,
                        'area': area_m2,
                        'deducted': 0,
                        'net': area_m2
                    })
                    count += 1
                    
                except Exception as e:
                    print(f"Skipping wall: {str(e)}")
                    continue
            
            selection.Delete()
            
            if count > 0:
                self.refresh_walls_table()
                messagebox.showinfo("Success", f"✅ Added {count} wall(s)")
            else:
                messagebox.showwarning("Warning", "No valid walls selected!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error:\n{str(e)}")
        finally:
            self.root.deiconify()
    
    def get_block_dimensions(self, block):
        """قراءة أبعاد البلوك من Attributes أو BoundingBox"""
        w, h = None, None
        
        # Try attributes first
        try:
            if block.HasAttributes:
                for att in block.GetAttributes():
                    try:
                        tag = att.TagString.upper()
                        if tag in ["WIDTH", "W"]:
                            try:
                                w = float(att.TextString)
                            except:
                                pass
                        elif tag in ["HEIGHT", "H"]:
                            try:
                                h = float(att.TextString)
                            except:
                                pass
                    except:
                        continue
        except:
            pass
        
        # Fallback to BoundingBox
        if w is None or h is None:
            try:
                bbox = block.GetBoundingBox()
                min_pt = bbox[0]
                max_pt = bbox[1]
                if w is None:
                    w = abs(max_pt[0] - min_pt[0])
                if h is None:
                    h = abs(max_pt[1] - min_pt[1])
            except:
                return None, None
        
        return w, h
    
    def pick_blocks(self):
        """اختيار البلوكات (أبواب/شبابيك)"""
        self.update_scale()
        self.root.withdraw()
        
        try:
            # Delete selection set if exists
            try:
                self.doc.SelectionSets.Item("BLOCKS_TEMP").Delete()
            except:
                pass
            
            self.acad.prompt("\nSelect BLOCKS (doors/windows): ")
            selection = self.doc.SelectionSets.Add("BLOCKS_TEMP")
            
            # Select without filter - user picks manually
            selection.SelectOnScreen()
            
            count = 0
            for block in selection:
                try:
                    # Check if it's a block reference
                    try:
                        block_name = block.Name
                    except:
                        continue  # Skip if not a block
                    
                    name = block_name.upper()
                    
                    try:
                        layer = block.Layer.upper()
                    except:
                        layer = "Unknown"
                    
                    # تحديد النوع
                    if "DOOR" in name or "DOOR" in layer:
                        block_type = "DOOR"
                    elif "WIN" in name or "WINDOW" in name or "WIN" in layer:
                        block_type = "WINDOW"
                    else:
                        block_type = "BLOCK"
                    
                    # قراءة Width/Height من Attributes
                    w, h = None, None
                    try:
                        if block.HasAttributes:
                            for att in block.GetAttributes():
                                try:
                                    tag = att.TagString.upper()
                                    if tag in ["WIDTH", "W"]:
                                        try:
                                            w = float(att.TextString)
                                        except:
                                            pass
                                    elif tag in ["HEIGHT", "H"]:
                                        try:
                                            h = float(att.TextString)
                                        except:
                                            pass
                                except:
                                    continue
                    except:
                        pass
                    
                    # Fallback لـ BoundingBox
                    if w is None or h is None:
                        try:
                            bbox = block.GetBoundingBox()
                            min_pt = bbox[0]
                            max_pt = bbox[1]
                            if w is None:
                                w = abs(max_pt[0] - min_pt[0])
                            if h is None:
                                h = abs(max_pt[1] - min_pt[1])
                        except:
                            w = w or 1.0
                            h = h or 1.0
                    
                    w_m = w * self.scale
                    h_m = h * self.scale
                    
                    self.openings.append({
                        'type': block_type,
                        'layer': block.Layer if hasattr(block, 'Layer') else "Unknown",
                        'width': w_m,
                        'height': h_m,
                        'perim': 2 * (w_m + h_m),
                        'area': w_m * h_m
                    })
                    count += 1
                    
                except Exception as e:
                    print(f"Skipping block: {str(e)}")
                    continue
            
            selection.Delete()
            
            if count > 0:
                self.refresh_openings_table()
                self.update_totals()
                messagebox.showinfo("Success", f"✅ Added {count} block(s)")
            else:
                messagebox.showwarning("Warning", "No valid blocks selected!\nPlease select block references (doors/windows).")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error picking blocks:\n{str(e)}")
        finally:
            self.root.deiconify()
    
    def refresh_rooms_table(self):
        for item in self.rooms_tree.get_children():
            self.rooms_tree.delete(item)
        
        for room in self.rooms:
            self.rooms_tree.insert('', tk.END, values=(
                room['layer'],
                room['width'],
                room['length'],
                f"{room['perim']:.3f}",
                f"{room['area']:.3f}"
            ))
    
    def refresh_openings_table(self):
        for item in self.openings_tree.get_children():
            self.openings_tree.delete(item)
        
        for opening in self.openings:
            self.openings_tree.insert('', tk.END, values=(
                opening['type'],
                opening['layer'],
                f"{opening['width']:.3f}",
                f"{opening['height']:.3f}",
                f"{opening['perim']:.3f}",
                f"{opening['area']:.3f}"
            ))
    
    def update_totals(self):
        total_area = sum(r['area'] for r in self.rooms) + sum(o['area'] for o in self.openings)
        total_perim = sum(r['perim'] for r in self.rooms) + sum(o['perim'] for o in self.openings)
        
        self.totals_label.config(text=f"Σ Perim = {total_perim:.3f} m  |  Σ Area = {total_area:.3f} m²")
    
    def reset_data(self):
        if messagebox.askyesno("Reset", "Clear all data?"):
            self.rooms.clear()
            self.openings.clear()
            self.refresh_rooms_table()
            self.refresh_openings_table()
            self.update_totals()
    
    def copy_to_clipboard(self):
        """نسخ البيانات كـ TSV للصق في Excel"""
        lines = ["Section\tLayer\tWidth(m)\tLength/Height(m)\tPerimeter(m)\tArea(m²)"]
        
        for r in self.rooms:
            lines.append(f"Room\t{r['layer']}\t{r['width']}\t{r['length']}\t{r['perim']:.3f}\t{r['area']:.3f}")
        
        for o in self.openings:
            lines.append(f"{o['type']}\t{o['layer']}\t{o['width']:.3f}\t{o['height']:.3f}\t{o['perim']:.3f}\t{o['area']:.3f}")
        
        total_area = sum(r['area'] for r in self.rooms) + sum(o['area'] for o in self.openings)
        total_perim = sum(r['perim'] for r in self.rooms) + sum(o['perim'] for o in self.openings)
        lines.append(f"TOTALS\t-\t-\t-\t{total_perim:.3f}\t{total_area:.3f}")
        
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(lines))
        messagebox.showinfo("Success", "✅ Copied to clipboard! Paste in Excel.")
    
    def export_csv(self):
        """تصدير CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"bilind_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not filename:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["Section", "Layer", "Width(m)", "Length/Height(m)", "Perimeter(m)", "Area(m²)"])
            
            for r in self.rooms:
                writer.writerow(["Room", r['layer'], r['width'], r['length'], f"{r['perim']:.3f}", f"{r['area']:.3f}"])
            
            for o in self.openings:
                writer.writerow([o['type'], o['layer'], f"{o['width']:.3f}", f"{o['height']:.3f}", 
                               f"{o['perim']:.3f}", f"{o['area']:.3f}"])
            
            total_area = sum(r['area'] for r in self.rooms) + sum(o['area'] for o in self.openings)
            total_perim = sum(r['perim'] for r in self.rooms) + sum(o['perim'] for o in self.openings)
            writer.writerow(["TOTALS", "-", "-", "-", f"{total_perim:.3f}", f"{total_area:.3f}"])
        
        messagebox.showinfo("Success", f"✅ CSV saved:\n{filename}")
    
    def insert_table(self):
        """إدراج جدول في AutoCAD"""
        try:
            self.root.iconify()
            self.acad.prompt("\nPick point for table: ")
            
            # إنشاء Table في AutoCAD
            point = self.acad.doc.Utility.GetPoint(Type="AcPromptStatus.OK")
            
            rows = 3 + len(self.rooms) + len(self.openings)  # Header + Rooms + Openings + Totals
            cols = 6
            
            table = self.acad.doc.ModelSpace.AddTable(point, rows, cols, 8, 30)
            
            # Headers
            headers = ["Section", "Layer", "Width(m)", "Length/Height(m)", "Perimeter(m)", "Area(m²)"]
            for i, header in enumerate(headers):
                table.SetText(0, i, header)
            
            row = 1
            table.SetText(row, 0, "ROOMS")
            row += 1
            
            for r in self.rooms:
                table.SetText(row, 0, "Room")
                table.SetText(row, 1, r['layer'])
                table.SetText(row, 2, str(r['width']))
                table.SetText(row, 3, str(r['length']))
                table.SetText(row, 4, f"{r['perim']:.3f}")
                table.SetText(row, 5, f"{r['area']:.3f}")
                row += 1
            
            table.SetText(row, 0, "OPENINGS")
            row += 1
            
            for o in self.openings:
                table.SetText(row, 0, o['type'])
                table.SetText(row, 1, o['layer'])
                table.SetText(row, 2, f"{o['width']:.3f}")
                table.SetText(row, 3, f"{o['height']:.3f}")
                table.SetText(row, 4, f"{o['perim']:.3f}")
                table.SetText(row, 5, f"{o['area']:.3f}")
                row += 1
            
            total_area = sum(r['area'] for r in self.rooms) + sum(o['area'] for o in self.openings)
            total_perim = sum(r['perim'] for r in self.rooms) + sum(o['perim'] for o in self.openings)
            table.SetText(row, 0, "TOTALS")
            table.SetText(row, 4, f"{total_perim:.3f}")
            table.SetText(row, 5, f"{total_area:.3f}")
            
            messagebox.showinfo("Success", "✅ Table inserted!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error inserting table: {e}")
        finally:
            self.root.deiconify()

if __name__ == "__main__":
    root = tk.Tk()
    app = BilindApp(root)
    root.mainloop()
