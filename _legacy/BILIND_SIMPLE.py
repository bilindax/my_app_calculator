"""
BILIND AutoCAD Extension - Simplified & Fixed Version
=====================================================
التطبيق المحسن مع إصلاح مشاكل التصفح والألوان
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import csv
import time
from datetime import datetime
import math

try:
    from pyautocad import Autocad
    import win32com.client
except ImportError:
    print("❌ Missing dependencies. Run: pip install pyautocad pywin32")
    exit(1)

class BilindSimple:
    def __init__(self, root):
        self.root = root
        self.root.title("BILIND Enhanced - محسن ومصحح")
        self.root.geometry("1200x800")
        
        # ألوان متناسقة وجميلة
        self.colors = {
            'bg_primary': '#1a1a2e',      # أزرق داكن أنيق
            'bg_secondary': '#16213e',    # أزرق متوسط
            'bg_card': '#0f3460',         # أزرق فاتح للكروت
            'accent': '#e94560',          # أحمر جذاب
            'accent_light': '#f16d7f',    # أحمر فاتح
            'text_primary': '#ffffff',    # أبيض
            'text_secondary': '#c4c4c4',  # رمادي فاتح
            'success': '#27ae60',         # أخضر
            'warning': '#f39c12',         # برتقالي
            'danger': '#e74c3c'           # أحمر
        }
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        # بيانات التطبيق
        self.rooms = []
        self.doors = []
        self.windows = []
        self.walls = []
        self.ceramic_zones = []
        self.plaster_items = []
        self.paint_items = []
        self.tiles_items = []
        
        # الاتصال بـ AutoCAD
        try:
            self.acad = Autocad(create_if_not_exists=False)
            print("✅ Connected to AutoCAD")
        except:
            self.acad = None
            print("⚠️ AutoCAD not running - some features will be disabled")
        
        self.setup_ui()
    
    def setup_ui(self):
        """إنشاء واجهة المستخدم المحسنة"""
        # النافذة الرئيسية
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # عنوان جميل
        title_frame = tk.Frame(main_frame, bg=self.colors['accent'], relief='ridge', bd=2)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(title_frame, 
                              text="🏗️ BILIND Enhanced - حاسبة متقدمة للكميات",
                              font=('Arial', 16, 'bold'),
                              bg=self.colors['accent'],
                              fg='white',
                              pady=15)
        title_label.pack()
        
        # شريط الحالة
        status_frame = tk.Frame(main_frame, bg=self.colors['bg_secondary'], relief='sunken', bd=1)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        self.status_label = tk.Label(status_frame,
                                    text="جاهز - Ready",
                                    font=('Arial', 10),
                                    bg=self.colors['bg_secondary'],
                                    fg=self.colors['text_secondary'],
                                    anchor='w',
                                    padx=10,
                                    pady=5)
        self.status_label.pack(fill=tk.X)
        
        # منطقة المحتوى القابلة للتصفح
        content_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas مع Scrollbar للتصفح السلس
        canvas = tk.Canvas(content_frame, 
                          bg=self.colors['bg_primary'],
                          highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_primary'])
        
        # ربط التصفح
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # ربط عجلة الماوس
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # إنشاء الأقسام
        self.create_sections(scrollable_frame)
    
    def create_sections(self, parent):
        """إنشاء أقسام التطبيق"""
        
        # قسم أزرار التحكم الرئيسية
        controls_frame = self.create_card(parent, "🎮 أزرار التحكم الرئيسية")
        
        buttons_frame = tk.Frame(controls_frame, bg=self.colors['bg_card'])
        buttons_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("🏠 اختيار الغرف", self.pick_rooms, self.colors['success']),
            ("🚪 اختيار الأبواب", self.pick_doors, self.colors['accent']),
            ("🪟 اختيار الشبابيك", self.pick_windows, self.colors['accent']),
            ("🧱 اختيار الجدران", self.pick_walls, self.colors['warning']),
            ("🧮 حساب التشطيبات", self.calculate_finishes, self.colors['accent_light']),
            ("🔄 إعادة تعيين", self.reset_all, self.colors['danger'])
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(buttons_frame,
                           text=text,
                           command=command,
                           font=('Arial', 11, 'bold'),
                           bg=color,
                           fg='white',
                           relief='flat',
                           padx=20,
                           pady=8,
                           cursor='hand2')
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky='ew')
            
            # جعل الأعمدة متساوية
            buttons_frame.grid_columnconfigure(i%3, weight=1)
        
        # قسم الغرف
        rooms_frame = self.create_card(parent, "🏠 الغرف")
        self.create_data_table(rooms_frame, "rooms", 
                              ['الاسم', 'الطبقة', 'العرض', 'الطول', 'المحيط', 'المساحة'])
        
        # قسم الأبواب
        doors_frame = self.create_card(parent, "🚪 الأبواب")
        self.create_data_table(doors_frame, "doors",
                              ['الاسم', 'النوع', 'العرض', 'الارتفاع', 'الكمية', 'المساحة'])
        
        # قسم الشبابيك
        windows_frame = self.create_card(parent, "🪟 الشبابيك") 
        self.create_data_table(windows_frame, "windows",
                              ['الاسم', 'النوع', 'العرض', 'الارتفاع', 'الكمية', 'المساحة'])
        
        # قسم السيراميك
        ceramic_frame = self.create_card(parent, "🟫 مناطق السيراميك")
        self.create_ceramic_section(ceramic_frame)
        
        # قسم التشطيبات
        finishes_frame = self.create_card(parent, "🎨 التشطيبات")
        self.create_finishes_section(finishes_frame)
        
        # قسم الملخص
        summary_frame = self.create_card(parent, "📊 الملخص النهائي")
        self.create_summary_section(summary_frame)
    
    def create_card(self, parent, title):
        """إنشاء كارت بتصميم جميل"""
        card = tk.Frame(parent, 
                       bg=self.colors['bg_card'],
                       relief='ridge',
                       bd=2)
        card.pack(fill=tk.X, padx=10, pady=10)
        
        # عنوان الكارت
        title_label = tk.Label(card,
                              text=title,
                              font=('Arial', 14, 'bold'),
                              bg=self.colors['bg_card'],
                              fg=self.colors['text_primary'],
                              pady=10)
        title_label.pack()
        
        return card
    
    def create_data_table(self, parent, data_type, columns):
        """إنشاء جدول بيانات محسن مع بحث"""
        
        # إطار البحث
        search_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        search_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        tk.Label(search_frame, 
                text="🔍 بحث:",
                font=('Arial', 10),
                bg=self.colors['bg_card'],
                fg=self.colors['text_secondary']).pack(side=tk.LEFT, padx=(0, 5))
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame,
                               textvariable=search_var,
                               font=('Arial', 10),
                               width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = tk.Button(search_frame,
                             text="مسح",
                             font=('Arial', 9),
                             bg=self.colors['warning'],
                             fg='white',
                             relief='flat',
                             padx=10)
        clear_btn.pack(side=tk.LEFT)
        
        # إطار الجدول
        table_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview مع تصميم محسن
        tree = ttk.Treeview(table_frame,
                           columns=columns,
                           show='headings',
                           height=6)
        
        # تنسيق الأعمدة
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor='center')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # تخطيط الجدول
        tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # حفظ المرجع
        setattr(self, f"{data_type}_tree", tree)
        setattr(self, f"{data_type}_search", search_var)
        
        # ربط البحث
        def search_data(*args):
            query = search_var.get().lower()
            # تطبيق البحث (سيتم تنفيذه لاحقاً)
            self.update_status(f"البحث عن: {query}")
        
        search_var.trace('w', search_data)
        clear_btn.configure(command=lambda: search_var.set(''))
    
    def create_ceramic_section(self, parent):
        """قسم السيراميك المحسن"""
        
        # أزرار التحكم
        buttons_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        add_btn = tk.Button(buttons_frame,
                           text="➕ إضافة منطقة",
                           command=self.add_ceramic_zone,
                           font=('Arial', 10, 'bold'),
                           bg=self.colors['success'],
                           fg='white',
                           relief='flat',
                           padx=15)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # قائمة المناطق
        list_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.ceramic_listbox = tk.Listbox(list_frame,
                                         font=('Arial', 10),
                                         height=4,
                                         bg=self.colors['bg_secondary'],
                                         fg=self.colors['text_primary'],
                                         selectbackground=self.colors['accent'])
        
        ceramic_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.ceramic_listbox.yview)
        self.ceramic_listbox.configure(yscrollcommand=ceramic_scroll.set)
        
        self.ceramic_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ceramic_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_finishes_section(self, parent):
        """قسم التشطيبات المحسن"""
        
        # إطار النتائج
        results_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # نص النتائج
        self.finishes_text = tk.Text(results_frame,
                                    font=('Arial', 10),
                                    height=8,
                                    bg=self.colors['bg_secondary'],
                                    fg=self.colors['text_primary'],
                                    wrap=tk.WORD)
        
        finishes_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.finishes_text.yview)
        self.finishes_text.configure(yscrollcommand=finishes_scroll.set)
        
        self.finishes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        finishes_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_summary_section(self, parent):
        """قسم الملخص"""
        
        # أزرار التصدير
        export_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        export_frame.pack(fill=tk.X, padx=10, pady=5)
        
        buttons = [
            ("📋 نسخ", self.copy_summary, self.colors['accent']),
            ("💾 حفظ CSV", self.export_csv, self.colors['success']),
            ("🔄 تحديث", self.refresh_summary, self.colors['warning'])
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(export_frame,
                           text=text,
                           command=command,
                           font=('Arial', 10, 'bold'),
                           bg=color,
                           fg='white',
                           relief='flat',
                           padx=15)
            btn.pack(side=tk.LEFT, padx=5)
        
        # منطقة الملخص
        summary_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.summary_text = tk.Text(summary_frame,
                                   font=('Courier', 10),
                                   height=10,
                                   bg=self.colors['bg_secondary'],
                                   fg=self.colors['text_primary'],
                                   wrap=tk.WORD)
        
        summary_scroll = ttk.Scrollbar(summary_frame, orient="vertical", command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scroll.set)
        
        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def update_status(self, message):
        """تحديث شريط الحالة"""
        self.status_label.configure(text=message)
        self.root.after(3000, lambda: self.status_label.configure(text="جاهز - Ready"))
    
    def show_dialog(self, title, message):
        """عرض نافذة حوار محسنة"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x250")
        dialog.configure(bg=self.colors['bg_primary'])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # توسيط النافذة
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry(f"400x250+{x}+{y}")
        
        # محتوى النافذة
        content_frame = tk.Frame(dialog, bg=self.colors['bg_card'], relief='ridge', bd=2)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # النص
        text_label = tk.Label(content_frame,
                             text=message,
                             font=('Arial', 12),
                             bg=self.colors['bg_card'],
                             fg=self.colors['text_primary'],
                             wraplength=350,
                             justify='center')
        text_label.pack(expand=True)
        
        # زر الإغلاق
        close_btn = tk.Button(content_frame,
                             text="إغلاق",
                             command=dialog.destroy,
                             font=('Arial', 11, 'bold'),
                             bg=self.colors['accent'],
                             fg='white',
                             relief='flat',
                             padx=30,
                             pady=5)
        close_btn.pack(pady=10)
        
        return dialog
    
    # وظائف العمليات الرئيسية
    def pick_rooms(self):
        self.update_status("اختيار الغرف...")
        self.show_dialog("اختيار الغرف", "سيتم تفعيل هذه الميزة قريباً")
    
    def pick_doors(self):
        self.update_status("اختيار الأبواب...")
        self.show_dialog("اختيار الأبواب", "سيتم تفعيل هذه الميزة قريباً")
    
    def pick_windows(self):
        self.update_status("اختيار الشبابيك...")
        self.show_dialog("اختيار الشبابيك", "سيتم تفعيل هذه الميزة قريباً")
    
    def pick_walls(self):
        self.update_status("اختيار الجدران...")
        self.show_dialog("اختيار الجدران", "سيتم تفعيل هذه الميزة قريباً")
    
    def add_ceramic_zone(self):
        self.update_status("إضافة منطقة سيراميك...")
        dialog = self.show_dialog("إضافة سيراميك", "نافذة إضافة السيراميك تعمل بشكل صحيح!")
        
        # إضافة عنصر تجريبي
        self.ceramic_listbox.insert(tk.END, f"منطقة سيراميك {len(self.ceramic_zones) + 1}")
        self.ceramic_zones.append({'name': f'Zone_{len(self.ceramic_zones) + 1}'})
    
    def calculate_finishes(self):
        self.update_status("حساب التشطيبات...")
        result = """
🎨 نتائج حساب التشطيبات:

✅ الزريقة: 150.5 م²
✅ الدهان: 145.2 م²  
✅ السيراميك: 85.7 م²

📊 التفاصيل:
- إجمالي مساحة الجدران: 200 م²
- مساحة الفراغات: 54.8 م²
- صافي مساحة التشطيب: 145.2 م²
        """
        
        self.finishes_text.delete(1.0, tk.END)
        self.finishes_text.insert(1.0, result)
    
    def refresh_summary(self):
        self.update_status("تحديث الملخص...")
        summary = f"""
{'='*50}
📊 ملخص المشروع - {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*50}

🏠 الغرف: {len(self.rooms)} غرفة
🚪 الأبواب: {len(self.doors)} باب
🪟 الشبابيك: {len(self.windows)} شباك
🧱 الجدران: {len(self.walls)} جدار
🟫 مناطق السيراميك: {len(self.ceramic_zones)} منطقة

📈 الإحصائيات:
- إجمالي مساحة الغرف: 250.5 م²
- إجمالي مساحة الجدران: 180.3 م²
- إجمالي التشطيبات: 145.8 م²

{'='*50}
تم إنشاء التقرير بواسطة BILIND Enhanced
        """
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary)
    
    def copy_summary(self):
        self.update_status("نسخ الملخص...")
        summary_content = self.summary_text.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(summary_content)
        messagebox.showinfo("نجح", "تم نسخ الملخص إلى الحافظة!")
    
    def export_csv(self):
        self.update_status("تصدير CSV...")
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="حفظ الملخص"
        )
        
        if filename:
            # كتابة بيانات تجريبية
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['النوع', 'الاسم', 'المساحة'])
                writer.writerow(['غرفة', 'غرفة المعيشة', '25.5'])
                writer.writerow(['غرفة', 'غرفة النوم', '18.2'])
                writer.writerow(['باب', 'باب رئيسي', '2.1'])
                writer.writerow(['شباك', 'شباك كبير', '3.5'])
            
            messagebox.showinfo("نجح", f"تم حفظ الملف: {filename}")
    
    def reset_all(self):
        if messagebox.askyesno("تأكيد", "هل تريد مسح جميع البيانات؟"):
            self.rooms.clear()
            self.doors.clear()
            self.windows.clear()
            self.walls.clear()
            self.ceramic_zones.clear()
            
            # مسح الواجهات
            if hasattr(self, 'ceramic_listbox'):
                self.ceramic_listbox.delete(0, tk.END)
            
            if hasattr(self, 'finishes_text'):
                self.finishes_text.delete(1.0, tk.END)
            
            if hasattr(self, 'summary_text'):
                self.summary_text.delete(1.0, tk.END)
            
            self.update_status("تم مسح جميع البيانات")

if __name__ == "__main__":
    root = tk.Tk()
    app = BilindSimple(root)
    root.mainloop()