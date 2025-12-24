# باقي الـ functions للبرنامج
# سيتم دمجها في الملف الرئيسي

def calc_walls_with_deduction(self):
    """حساب الجدران بعد طرح الفراغات"""
    if not self.walls:
        messagebox.showwarning("Warning", "No walls! Pick walls first.")
        return
    
    # Calculate total openings area
    total_openings = 0
    for d in self.doors:
        total_openings += d['area']
    for w in self.windows:
        total_openings += w['area']
    
    # Distribute openings across walls proportionally
    total_wall_area = sum(w['area'] for w in self.walls)
    if total_wall_area <= 0:
        return
    
    for wall in self.walls:
        ratio = wall['area'] / total_wall_area
        deducted = total_openings * ratio
        wall['deducted'] = deducted
        wall['net'] = wall['area'] - deducted
    
    self.refresh_walls_table()
    messagebox.showinfo("Success", f"✅ Deducted {total_openings:.2f} m² from walls")

def add_finish_from_rooms(self, finish_type):
    """إضافة مساحة من الغرف للتشطيب"""
    if not self.rooms:
        messagebox.showwarning("Warning", "No rooms! Pick rooms first.")
        return
    
    total = sum(r['area'] for r in self.rooms)
    self.finishes[finish_type].append(('Rooms', total))
    self.update_finish_labels()
    messagebox.showinfo("Success", f"✅ Added {total:.2f} m² to {finish_type}")

def add_finish_from_walls(self, finish_type):
    """إضافة مساحة من الجدران للتشطيب"""
    if not self.walls:
        messagebox.showwarning("Warning", "No walls! Pick walls first.")
        return
    
    total = sum(w['net'] for w in self.walls)
    self.finishes[finish_type].append(('Walls', total))
    self.update_finish_labels()
    messagebox.showinfo("Success", f"✅ Added {total:.2f} m² to {finish_type}")

def deduct_openings_from_finish(self, finish_type):
    """طرح مساحات الفراغات من التشطيب"""
    total_openings = 0
    for d in self.doors:
        total_openings += d['area']
    for w in self.windows:
        total_openings += w['area']
    
    if total_openings > 0:
        self.finishes[finish_type].append(('Deduct Openings', -total_openings))
        self.update_finish_labels()
        messagebox.showinfo("Success", f"✅ Deducted {total_openings:.2f} m² from {finish_type}")
    else:
        messagebox.showwarning("Warning", "No openings to deduct!")

def update_finish_labels(self):
    """تحديث مساحات التشطيبات"""
    plaster_total = sum(item[1] for item in self.finishes['plaster'])
    paint_total = sum(item[1] for item in self.finishes['paint'])
    tiles_total = sum(item[1] for item in self.finishes['tiles'])
    
    self.plaster_label.config(text=f"Area = {plaster_total:.3f} m²")
    self.paint_label.config(text=f"Area = {paint_total:.3f} m²")
    self.tiles_label.config(text=f"Area = {tiles_total:.3f} m²")

def update_summary(self):
    """تحديث الملخص الشامل"""
    self.summary_text.delete('1.0', tk.END)
    
    summary = "="*60 + "\n"
    summary += "           BILIND - COMPLETE PROJECT SUMMARY\n"
    summary += "="*60 + "\n\n"
    
    # Rooms
    summary += "📋 ROOMS:\n"
    summary += "-"*60 + "\n"
    for i, r in enumerate(self.rooms, 1):
        summary += f"{i}. Layer: {r['layer']:<15} | W×L: {r['width']} × {r['length']:<8} | "
        summary += f"Perim: {r['perim']:.3f} m | Area: {r['area']:.3f} m²\n"
    total_rooms = sum(r['area'] for r in self.rooms)
    summary += f"\nTotal Rooms Area: {total_rooms:.3f} m²\n\n"
    
    # Doors
    summary += "🚪 DOORS:\n"
    summary += "-"*60 + "\n"
    for i, d in enumerate(self.doors, 1):
        summary += f"{i}. Layer: {d['layer']:<15} | W×H: {d['width']:.3f} × {d['height']:.3f} m | "
        summary += f"Area: {d['area']:.3f} m²\n"
    total_doors = sum(d['area'] for d in self.doors)
    summary += f"\nTotal Doors Area: {total_doors:.3f} m²\n\n"
    
    # Windows
    summary += "🪟 WINDOWS:\n"
    summary += "-"*60 + "\n"
    for i, w in enumerate(self.windows, 1):
        summary += f"{i}. Layer: {w['layer']:<15} | W×H: {w['width']:.3f} × {w['height']:.3f} m | "
        summary += f"Area: {w['area']:.3f} m²\n"
    total_windows = sum(w['area'] for w in self.windows)
    summary += f"\nTotal Windows Area: {total_windows:.3f} m²\n\n"
    
    # Walls
    if self.walls:
        summary += "🧱 WALLS:\n"
        summary += "-"*60 + "\n"
        for i, w in enumerate(self.walls, 1):
            summary += f"{i}. Layer: {w['layer']:<15} | L×H: {w['length']:.3f} × {w['height']:.3f} m | "
            summary += f"Gross: {w['area']:.3f} m² | Deduct: {w['deducted']:.3f} m² | Net: {w['net']:.3f} m²\n"
        total_walls_net = sum(w['net'] for w in self.walls)
        summary += f"\nTotal Walls Net Area: {total_walls_net:.3f} m²\n\n"
    
    # Finishes
    summary += "🎨 FINISHES:\n"
    summary += "-"*60 + "\n"
    
    plaster_total = sum(item[1] for item in self.finishes['plaster'])
    paint_total = sum(item[1] for item in self.finishes['paint'])
    tiles_total = sum(item[1] for item in self.finishes['tiles'])
    
    summary += f"🏗️  PLASTER (زريقة):  {plaster_total:.3f} m²\n"
    summary += f"🎨 PAINT (دهان):     {paint_total:.3f} m²\n"
    summary += f"🟦 TILES (سيراميك):  {tiles_total:.3f} m²\n\n"
    
    summary += "="*60 + "\n"
    summary += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    summary += "="*60 + "\n"
    
    self.summary_text.insert('1.0', summary)

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

def refresh_doors_table(self):
    for item in self.doors_tree.get_children():
        self.doors_tree.delete(item)
    
    for door in self.doors:
        self.doors_tree.insert('', tk.END, values=(
            door['layer'],
            f"{door['width']:.3f}",
            f"{door['height']:.3f}",
            f"{door['perim']:.3f}",
            f"{door['area']:.3f}"
        ))

def refresh_windows_table(self):
    for item in self.windows_tree.get_children():
        self.windows_tree.delete(item)
    
    for window in self.windows:
        self.windows_tree.insert('', tk.END, values=(
            window['layer'],
            f"{window['width']:.3f}",
            f"{window['height']:.3f}",
            f"{window['perim']:.3f}",
            f"{window['area']:.3f}"
        ))

def refresh_walls_table(self):
    for item in self.walls_tree.get_children():
        self.walls_tree.delete(item)
    
    for wall in self.walls:
        self.walls_tree.insert('', tk.END, values=(
            wall['layer'],
            f"{wall['length']:.3f}",
            f"{wall['height']:.3f}",
            f"{wall['area']:.3f}",
            f"{wall['deducted']:.3f}",
            f"{wall['net']:.3f}"
        ))
    
    total_net = sum(w['net'] for w in self.walls)
    self.walls_total_label.config(text=f"Total Net Wall Area = {total_net:.3f} m²")

def update_totals(self):
    num_rooms = len(self.rooms)
    num_doors = len(self.doors)
    num_windows = len(self.windows)
    
    self.totals_label.config(text=f"Totals: {num_rooms} Rooms | {num_doors} Doors | {num_windows} Windows")

def reset_data(self):
    if messagebox.askyesno("Reset", "Clear ALL data?"):
        self.rooms.clear()
        self.doors.clear()
        self.windows.clear()
        self.walls.clear()
        self.finishes = {'plaster': [], 'paint': [], 'tiles': []}
        
        self.refresh_rooms_table()
        self.refresh_doors_table()
        self.refresh_windows_table()
        self.refresh_walls_table()
        self.update_totals()
        self.update_finish_labels()
        self.update_summary()

def update_scale(self):
    try:
        self.scale = float(self.scale_entry.get())
        if self.scale <= 0:
            raise ValueError
    except:
        messagebox.showerror("Error", "Invalid scale!")
        self.scale = 1.0
        self.scale_entry.delete(0, tk.END)
        self.scale_entry.insert(0, "1.0")

def copy_to_clipboard(self):
    """نسخ كل البيانات"""
    self.update_summary()
    text = self.summary_text.get('1.0', tk.END)
    self.root.clipboard_clear()
    self.root.clipboard_append(text)
    messagebox.showinfo("Success", "✅ Copied to clipboard!")

def export_csv(self):
    """تصدير CSV"""
    filename = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile=f"bilind_full_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    
    if not filename:
        return
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # Rooms
        writer.writerow([])
        writer.writerow(["ROOMS"])
        writer.writerow(["Layer", "Width(m)", "Length(m)", "Perimeter(m)", "Area(m²)"])
        for r in self.rooms:
            writer.writerow([r['layer'], r['width'], r['length'], f"{r['perim']:.3f}", f"{r['area']:.3f}"])
        
        # Doors
        writer.writerow([])
        writer.writerow(["DOORS"])
        writer.writerow(["Layer", "Width(m)", "Height(m)", "Perimeter(m)", "Area(m²)"])
        for d in self.doors:
            writer.writerow([d['layer'], f"{d['width']:.3f}", f"{d['height']:.3f}", f"{d['perim']:.3f}", f"{d['area']:.3f}"])
        
        # Windows
        writer.writerow([])
        writer.writerow(["WINDOWS"])
        writer.writerow(["Layer", "Width(m)", "Height(m)", "Perimeter(m)", "Area(m²)"])
        for w in self.windows:
            writer.writerow([w['layer'], f"{w['width']:.3f}", f"{w['height']:.3f}", f"{w['perim']:.3f}", f"{w['area']:.3f}"])
        
        # Walls
        if self.walls:
            writer.writerow([])
            writer.writerow(["WALLS"])
            writer.writerow(["Layer", "Length(m)", "Height(m)", "Gross(m²)", "Deducted(m²)", "Net(m²)"])
            for w in self.walls:
                writer.writerow([w['layer'], f"{w['length']:.3f}", f"{w['height']:.3f}", 
                               f"{w['area']:.3f}", f"{w['deducted']:.3f}", f"{w['net']:.3f}"])
        
        # Finishes
        writer.writerow([])
        writer.writerow(["FINISHES"])
        plaster_total = sum(item[1] for item in self.finishes['plaster'])
        paint_total = sum(item[1] for item in self.finishes['paint'])
        tiles_total = sum(item[1] for item in self.finishes['tiles'])
        writer.writerow(["Plaster (m²)", f"{plaster_total:.3f}"])
        writer.writerow(["Paint (m²)", f"{paint_total:.3f}"])
        writer.writerow(["Tiles (m²)", f"{tiles_total:.3f}"])
    
    messagebox.showinfo("Success", f"✅ CSV saved:\n{filename}")

def insert_table(self):
    """إدراج جدول في AutoCAD"""
    messagebox.showinfo("Info", "Feature coming soon!\nUse Copy or CSV export for now.")
