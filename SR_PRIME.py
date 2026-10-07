import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import shutil
import tempfile
import webbrowser
from datetime import datetime

# Pillow library import
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# --- UNIVERSAL SELECT, COPY, PASTE & RIGHT CLICK MENU ---
def setup_text_shortcuts_and_menu(root):
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Cut", command=lambda: root.focus_get().event_generate('<<Cut>>'))
    menu.add_command(label="Copy", command=lambda: root.focus_get().event_generate('<<Copy>>'))
    menu.add_command(label="Paste", command=lambda: root.focus_get().event_generate('<<Paste>>'))
    menu.add_separator()
    menu.add_command(label="Select All", command=lambda: root.focus_get().event_generate('<<SelectAll>>'))

    def show_popup(event):
        try:
            widget = event.widget
            widget.focus_set()
            menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass

    def select_all(event):
        widget = event.widget
        try:
            widget.select_range(0, 'end')
            widget.icursor('end')
            return 'break'
        except Exception:
            try:
                widget.tag_add("sel", "1.0", "end")
                return 'break'
            except Exception:
                pass

    for cls in ("Entry", "TEntry", "Text"):
        root.bind_class(cls, "<Button-3>", show_popup)
        root.bind_class(cls, "<Control-a>", select_all)
        root.bind_class(cls, "<Control-A>", select_all)
        root.bind_class(cls, "<Control-c>", lambda e: e.widget.event_generate("<<Copy>>"))
        root.bind_class(cls, "<Control-C>", lambda e: e.widget.event_generate("<<Copy>>"))
        root.bind_class(cls, "<Control-v>", lambda e: e.widget.event_generate("<<Paste>>"))
        root.bind_class(cls, "<Control-V>", lambda e: e.widget.event_generate("<<Paste>>"))
        root.bind_class(cls, "<Control-x>", lambda e: e.widget.event_generate("<<Cut>>"))
        root.bind_class(cls, "<Control-X>", lambda e: e.widget.event_generate("<<Cut>>"))

BASE_DIR = r"D:\Shree_Radha_ERP"
BACKUP_DIR = os.path.join(BASE_DIR, "Backups")
DB_NAME = os.path.join(BASE_DIR, "shree_radha_consultant.db")

def create_auto_backup():
    """Software close hone par database ka auto backup banata hai"""
    try:
        if os.path.exists(DB_NAME):
            os.makedirs(BACKUP_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_file = os.path.join(BACKUP_DIR, f"Backup_{timestamp}.db")
            shutil.copy2(DB_NAME, backup_file)
            
            # Disk space bachane ke liye sirf latest 20 backup copies rakhenge
            backups = [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.startswith("Backup_") and f.endswith(".db")]
            backups.sort(key=os.path.getmtime)
            while len(backups) > 20:
                oldest = backups.pop(0)
                try:
                    os.remove(oldest)
                except Exception:
                    pass
    except Exception:
        pass

def init_db():
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_code TEXT UNIQUE,
        name TEXT NOT NULL,
        contact TEXT,
        address TEXT,
        gstin TEXT,
        aadhaar_no TEXT,
        monthly_fee REAL DEFAULT 0,
        opening_bal REAL DEFAULT 0,
        fy_period TEXT DEFAULT '1-Apr-26 to 31-Mar-27',
        created_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT UNIQUE NOT NULL,
        default_rate REAL DEFAULT 0,
        unit TEXT DEFAULT 'NOS'
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE,
        invoice_date TEXT,
        client_id INTEGER,
        for_month TEXT,
        particulars TEXT,
        amount REAL,
        narration TEXT,
        FOREIGN KEY (client_id) REFERENCES clients (id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receipt_no TEXT UNIQUE,
        receipt_date TEXT,
        client_id INTEGER,
        amount REAL,
        payment_mode TEXT,
        ref_no TEXT,
        towards_month TEXT,
        remarks TEXT,
        FOREIGN KEY (client_id) REFERENCES clients (id)
    )
    """)
    cur.execute("SELECT COUNT(*) FROM items")
    if cur.fetchone()[0] == 0:
        seed_items = [
            ("GST RETURN FILING - MONTHLY", 1000.0, "MTH"),
            ("INCOME TAX RETURN (ITR)", 2000.0, "NOS"),
            ("DIGITAL SIGNATURE (DSC CLASS 3)", 2000.0, "NOS"),
            ("GST NEW REGISTRATION", 2500.0, "NOS"),
            ("ACCOUNTING & AUDITING CHARGES", 3000.0, "MTH"),
            ("PAN / TAN APPLICATION", 500.0, "NOS"),
            ("TDS RETURN FILING", 1500.0, "QTR")
        ]
        cur.executemany("INSERT INTO items (item_name, default_rate, unit) VALUES (?, ?, ?)", seed_items)
    conn.commit()
    conn.close()

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

def parse_smart_date(date_text):
    text = date_text.strip().replace("/", "-").replace(".", "-").replace(" ", "-")
    now = datetime.now()
    cur_year = now.year
    cur_month = now.month
    parts = [p for p in text.split("-") if p]
    try:
        if len(parts) == 1 and parts[0].isdigit():
            day = int(parts[0])
            dt = datetime(cur_year, cur_month, day)
            return dt.strftime("%Y-%m-%d")
        elif len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            day = int(parts[0])
            month = int(parts[1])
            dt = datetime(cur_year, month, day)
            return dt.strftime("%Y-%m-%d")
        elif len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            if len(parts[0]) == 4:
                dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
            else:
                yr = int(parts[2])
                if yr < 100: yr += 2000
                dt = datetime(yr, int(parts[1]), int(parts[0]))
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return date_text

def bind_auto_select(entry_widget):
    def select_all(event):
        entry_widget.after(10, lambda: entry_widget.select_range(0, tk.END))
    entry_widget.bind("<FocusIn>", select_all)

def bind_smart_date(entry_widget, str_var, next_widget=None):
    bind_auto_select(entry_widget)
    def on_enter(event):
        converted = parse_smart_date(str_var.get())
        str_var.set(converted)
        if next_widget: next_widget.focus_set()
        return "break"
    def on_blur(event):
        converted = parse_smart_date(str_var.get())
        str_var.set(converted)
    entry_widget.bind("<Return>", on_enter)
    entry_widget.bind("<KP_Enter>", on_enter)
    entry_widget.bind("<FocusOut>", on_blur)

def parse_smart_month(text):
    t = text.strip()
    if not t:
        return datetime.now().strftime("%B %Y")
    now = datetime.now()
    cur_year = now.year
    parts = t.split()
    first_part = parts[0].lower()
    custom_year = cur_year

    if len(parts) > 1 and parts[1].isdigit():
        y_val = int(parts[1])
        if y_val < 100: y_val += 2000
        custom_year = y_val

    if first_part.isdigit():
        m_idx = int(first_part)
        if 1 <= m_idx <= 12:
            return f"{MONTH_NAMES[m_idx - 1]} {custom_year}"

    for m in MONTH_NAMES:
        if m.lower().startswith(first_part):
            return f"{m} {custom_year}"
    return t

def bind_smart_month(entry_widget, str_var, next_widget=None):
    bind_auto_select(entry_widget)
    def on_enter(event):
        converted = parse_smart_month(str_var.get())
        str_var.set(converted)
        if next_widget: next_widget.focus_set()
        return "break"
    def on_blur(event):
        converted = parse_smart_month(str_var.get())
        str_var.set(converted)
    entry_widget.bind("<Return>", on_enter)
    entry_widget.bind("<KP_Enter>", on_enter)
    entry_widget.bind("<FocusOut>", on_blur)

class UpperStringVar(tk.StringVar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trace_add("write", self._to_upper)

    def _to_upper(self, *args):
        val = self.get()
        if val != val.upper():
            self.set(val.upper())

class ShreeRadhaERP(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title("SR PRIME - Accounting ERP")
        self.geometry("1366x768")
        self.minsize(1100, 660)
        self.configure(bg="#0F172A")
        
        # Window Close [X] par auto backup hook
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        setup_text_shortcuts_and_menu(self)

        self.current_screen = "SELECT_PARTY"
        self.current_active_party = None
        self.active_delete_handler = None
        self.active_print_handler = None
        
        self.setup_styles()
        self.build_top_ribbon()
        
        self.main_container = tk.Frame(self, bg="#0F172A")
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        self.bind_all("<Escape>", self.handle_universal_escape)
        self.bind("<Alt-d>", lambda e: self.trigger_alt_d())
        self.bind("<Alt-D>", lambda e: self.trigger_alt_d())
        self.bind("<Alt-p>", lambda e: self.trigger_alt_p())
        self.bind("<Alt-P>", lambda e: self.trigger_alt_p())
        self.bind("<F8>", lambda e: self.show_sale_invoice())
        self.bind("<F6>", lambda e: self.show_receipt_voucher())
        
        self.show_intro_splash_logo()

    def on_window_close(self):
        if messagebox.askyesno("Quit SR PRIME", "Quit ERP? (Auto-backup save karke band karein?)", default="yes"):
            create_auto_backup()
            self.destroy()

    def show_intro_splash_logo(self):
        splash = tk.Toplevel(self)
        splash.overrideredirect(True)
        splash.configure(bg="#0B132B")
        
        w, h = 580, 400
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        splash.geometry(f"{w}x{h}+{x}+{y}")

        outer_f = tk.Frame(splash, bg="#1E293B", bd=3, relief="solid")
        outer_f.pack(fill="both", expand=True, padx=4, pady=4)

        top_bar = tk.Frame(outer_f, bg="#0F172A", height=32)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="🌸 ॥ श्री राधा कृष्णाय नमः ॥ 🌸", font=("Segoe UI", 11, "bold"), fg="#FDE047", bg="#0F172A").pack(pady=4)

        img_loaded = False
        possible_names = ["radha_krishna.png", "radha_krishna.jpg", "radha_krishna.jpeg"]
        for fname in possible_names:
            p = os.path.join(BASE_DIR, fname)
            if os.path.exists(p) and PIL_AVAILABLE:
                try:
                    pil_img = Image.open(p).resize((145, 145), Image.Resampling.LANCZOS)
                    self.intro_tk = ImageTk.PhotoImage(pil_img)
                    tk.Label(outer_f, image=self.intro_tk, bg="#1E293B").pack(pady=(12, 4))
                    img_loaded = True
                    break
                except Exception:
                    pass

        if not img_loaded:
            tk.Label(outer_f, text="⚡", font=("Segoe UI", 52), fg="#FDE047", bg="#1E293B").pack(pady=(12, 2))

        tk.Label(outer_f, text="⚡ SR PRIME ERP", font=("Trebuchet MS", 25, "bold"), fg="#FDE047", bg="#1E293B").pack()
        tk.Label(outer_f, text="SHREE RADHA CONSULTANT", font=("Segoe UI", 13, "bold"), fg="#38BDF8", bg="#1E293B").pack(pady=(2, 0))
        tk.Label(outer_f, text="Professional Tax, GST & Financial Advisory Chamber", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#1E293B").pack()

        lbl_load = tk.Label(outer_f, text="⚡ Initializing Database, Masters & Auto Backup Engine...", font=("Segoe UI", 9, "bold italic"), fg="#34D399", bg="#1E293B")
        lbl_load.pack(side="bottom", pady=14)

        def finish_splash():
            splash.destroy()
            self.deiconify()
            try:
                self.state('zoomed')
            except Exception:
                pass
            self.show_select_party_screen()

        self.after(4500, finish_splash)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#1E40AF", foreground="#FFFFFF")
        style.configure("Treeview", font=("Segoe UI", 10, "bold"), rowheight=32, background="#0F172A", foreground="#FFFFFF", fieldbackground="#0F172A")
        style.map("Treeview", background=[('selected', '#F59E0B')], foreground=[('selected', '#000000')])
        style.configure("TCombobox", font=("Segoe UI", 10, "bold"))

    def build_top_ribbon(self):
        self.top_ribbon = tk.Frame(self, bg="#020617", height=46)
        self.top_ribbon.pack(side="top", fill="x")
        
        self.lbl_logo = tk.Label(self.top_ribbon, text="⚡ SR PRIME", font=("Segoe UI", 13, "bold"), fg="#FDE047", bg="#020617", padx=15)
        self.lbl_logo.pack(side="left")

        self.lbl_ribbon_title = tk.Label(self.top_ribbon, text="| Shree Radha Consultant ERP", font=("Segoe UI", 11, "bold"), fg="#38BDF8", bg="#020617")
        self.lbl_ribbon_title.pack(side="left")

        self.r_btns = tk.Frame(self.top_ribbon, bg="#020617")
        self.r_btns.pack(side="right", padx=10)

        self.btn_shut = tk.Button(self.r_btns, text="Back / Exit (Esc)", command=lambda: self.handle_universal_escape(None), font=("Segoe UI", 9, "bold"), bg="#BE123C", fg="#FFFFFF", bd=0, padx=14, pady=5, cursor="hand2")
        self.btn_shut.pack(side="left", padx=2)

    def trigger_alt_d(self):
        if self.active_delete_handler:
            self.active_delete_handler()
        else:
            messagebox.showinfo("Alt + D", "Pehle row select karein.")

    def trigger_alt_p(self):
        if self.active_print_handler:
            self.active_print_handler()
        elif self.current_active_party:
            self.print_party_ledger_pdf()

    def handle_universal_escape(self, event=None):
        if self.current_screen in ["VOUCHER", "STATEMENT_VIEW"]:
            if self.current_active_party:
                self.show_gateway_of_tally()
            else:
                self.show_select_party_screen()
            return "break"
        elif self.current_screen == "GATEWAY_TALLY":
            self.current_active_party = None
            self.show_select_party_screen()
            return "break"
        elif self.current_screen == "SELECT_PARTY":
            if messagebox.askyesno("Quit SR PRIME", "Quit ERP? (Auto-backup save karke band karein?)", default="yes"):
                create_auto_backup()
                self.destroy()
            return "break"

    def clear_main(self):
        self.active_delete_handler = None
        self.active_print_handler = None
        self.unbind("<Down>")
        self.unbind("<Up>")
        self.unbind("<Return>")
        self.unbind("<KP_Enter>")
        self.unbind("<Key>")
        for w in self.main_container.winfo_children():
            w.destroy()

    def get_or_create_client_id(self, party_name):
        party_name = party_name.strip().upper()
        if not party_name:
            return None
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id FROM clients WHERE UPPER(name) = ?", (party_name,))
        row = cur.fetchone()
        if row:
            cid = row[0]
        else:
            cur.execute("SELECT client_code FROM clients WHERE client_code LIKE '10%' OR client_code LIKE 'CL-%'")
            existing_codes = cur.fetchall()
            max_num = 100028
            for r in existing_codes:
                c_str = str(r[0]).replace("CL-", "")
                if c_str.isdigit():
                    max_num = max(max_num, int(c_str))
            code = str(max_num + 1)
            cur.execute("""
            INSERT INTO clients (client_code, name, contact, address, gstin, aadhaar_no, fy_period, created_at)
            VALUES (?, ?, '', '', '', '', '1-Apr-26 to 31-Mar-27', ?)
            """, (code, party_name, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            cid = cur.lastrowid
        conn.close()
        return cid

    # ================= 1. PARTY MASTER (SELECT COMPANY / PARTY) =================
    def show_select_party_screen(self):
        self.clear_main()
        self.current_screen = "SELECT_PARTY"
        self.current_active_party = None
        self.lbl_ribbon_title.config(text="| Select Company / Party (Master Hub)", fg="#38BDF8")

        main_box = tk.Frame(self.main_container, bg="#0A1128", bd=0)
        main_box.pack(fill="both", expand=True, padx=0, pady=0)

        top_crest = tk.Frame(main_box, bg="#1E293B", height=42)
        top_crest.pack(fill="x", side="top")
        top_crest.pack_propagate(False)

        tk.Label(top_crest, text="⚡ SR PRIME | COMPANY & PARTY MASTER HUB", font=("Segoe UI", 12, "bold"), fg="#FDE047", bg="#1E293B").pack(side="left", padx=15)
        tk.Label(top_crest, text="Select Company to Enter Gateway of Tally | Auto Backup Enabled", font=("Segoe UI", 10, "bold"), fg="#38BDF8", bg="#1E293B").pack(side="right", padx=15)

        body_f = tk.Frame(main_box, bg="#0A1128")
        body_f.pack(fill="both", expand=True, padx=6, pady=4)
        body_f.columnconfigure(0, weight=3)
        body_f.columnconfigure(1, weight=5)
        body_f.columnconfigure(2, weight=3)
        body_f.rowconfigure(0, weight=1)

        # LEFT PANEL
        left_card = tk.Frame(body_f, bg="#0F172A", bd=2, relief="solid", padx=16, pady=16)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)

        tk.Label(left_card, text="🏛 CHAMBER & FIRM", font=("Segoe UI", 14, "bold"), fg="#38BDF8", bg="#0F172A").pack(anchor="w")
        tk.Label(left_card, text="SHREE RADHA CONSULTANT", font=("Segoe UI", 12, "bold"), fg="#FDE047", bg="#0F172A").pack(anchor="w", pady=(4, 0))
        tk.Label(left_card, text="Prop. Vinay Yadav | Tax Advocate", font=("Segoe UI", 10, "bold"), fg="#F1F5F9", bg="#0F172A").pack(anchor="w")
        tk.Label(left_card, text="Income Tax, GST & Financial Advisory", font=("Segoe UI", 9, "normal"), fg="#94A3B8", bg="#0F172A").pack(anchor="w", pady=(0, 10))

        tk.Frame(left_card, bg="#334155", height=2).pack(fill="x", pady=8)

        tk.Label(left_card, text="📋 Master Repository Guidelines:", font=("Segoe UI", 11, "bold"), fg="#34D399", bg="#0F172A").pack(anchor="w", pady=(2, 6))
        
        guidelines = [
            "✔ Single Client Profile for GST & ITR",
            "✔ Instant Search by Party Name or Code",
            "✔ Date-wise Ledger Synchronization",
            "✔ Multi-Year Statement Continuity",
            "✔ Local Encrypted Offline Master Base"
        ]
        for g_item in guidelines:
            tk.Label(left_card, text=g_item, font=("Segoe UI", 9, "bold"), fg="#CBD5E1", bg="#0F172A").pack(anchor="w", pady=3)

        tk.Frame(left_card, bg="#334155", height=2).pack(fill="x", pady=10)

        tk.Label(left_card, text="📍 Chamber Address:", font=("Segoe UI", 10, "bold"), fg="#FDE047", bg="#0F172A").pack(anchor="w")
        tk.Label(left_card, text="Jamalpur Station Road, Muhammadabad Gohna,\nMau District, Uttar Pradesh - 276403", font=("Segoe UI", 9, "normal"), fg="#CBD5E1", bg="#0F172A", justify="left").pack(anchor="w", pady=(3, 6))
        tk.Label(left_card, text="📞 Support: +91 8009844246", font=("Segoe UI", 9, "bold"), fg="#38BDF8", bg="#0F172A").pack(anchor="w")

        l_foot = tk.Frame(left_card, bg="#090E17", bd=1, relief="solid", padx=10, pady=8)
        l_foot.pack(fill="x", side="bottom")
        tk.Label(l_foot, text="● CLIENT MASTER REPOSITORY LIVE", font=("Segoe UI", 8, "bold"), fg="#34D399", bg="#090E17").pack(anchor="center")

        # CENTER PANEL
        center_frame = tk.Frame(body_f, bg="#0A1128")
        center_frame.grid(row=0, column=1, sticky="nsew", pady=0)

        tally_box = tk.Frame(center_frame, bg="#0F172A", bd=3, relief="solid")
        tally_box.pack(fill="both", expand=True)

        t_header = tk.Frame(tally_box, bg="#1E40AF", height=42)
        t_header.pack(fill="x")
        t_header.pack_propagate(False)
        tk.Label(t_header, text="SELECT COMPANY / PARTY MASTER", font=("Trebuchet MS", 15, "bold"), fg="#FFFFFF", bg="#1E40AF").pack(pady=8)

        t_body = tk.Frame(tally_box, bg="#0F172A", padx=16, pady=6)
        t_body.pack(fill="both", expand=True)

        search_card = tk.Frame(t_body, bg="#172554", bd=2, relief="solid", highlightthickness=1, highlightbackground="#2563EB", padx=10, pady=6)
        search_card.pack(fill="x", pady=(2, 6))

        tk.Label(search_card, text="🔍 SEARCH PARTY / CODE:", font=("Segoe UI", 10, "bold"), fg="#60A5FA", bg="#172554").pack(side="left", padx=5)
        search_var = tk.StringVar()
        search_e = tk.Entry(search_card, textvariable=search_var, font=("Segoe UI", 11, "bold"), width=24, bg="#0F172A", fg="#FDE047", insertbackground="#FDE047", bd=1, relief="solid")
        search_e.pack(side="left", padx=8)
        bind_auto_select(search_e)

        table_f = tk.Frame(t_body, bg="#0F172A", bd=2, relief="solid", highlightthickness=1, highlightbackground="#0284C7")
        table_f.pack(fill="both", expand=True, pady=4)

        cols = ("Name", "Code", "Period")
        tree = ttk.Treeview(table_f, columns=cols, show="", selectmode="browse")
        tree.column("Name", width=340, anchor="w")
        tree.column("Code", width=120, anchor="w")
        tree.column("Period", width=160, anchor="e")

        sc = tk.Scrollbar(table_f, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        actions_f = tk.Frame(t_body, bg="#0F172A", pady=4)
        actions_f.pack(fill="x", side="bottom")

        btn_create = tk.Button(actions_f, text="+ CREATE NEW PARTY (ALT + C)", command=self.show_create_party_dialog, font=("Segoe UI", 10, "bold"), bg="#0284C7", fg="#FFFFFF", bd=0, padx=16, pady=8, cursor="hand2")
        btn_create.pack(side="left", fill="x", expand=True, padx=(0, 4))

        def delete_selected_party():
            sel = tree.selection()
            if not sel: return
            p_id = int(sel[0])
            match = next((p for p in party_cache if p["id"] == p_id), None)
            if not match: return
            if messagebox.askyesno("Confirm Delete (Alt+D)", f"Delete Party '{match['name']}'?"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("DELETE FROM sales_invoices WHERE client_id=?", (p_id,))
                conn.execute("DELETE FROM receipts WHERE client_id=?", (p_id,))
                conn.execute("DELETE FROM clients WHERE id=?", (p_id,))
                conn.commit()
                conn.close()
                load_parties()

        btn_delete = tk.Button(actions_f, text="DELETE PARTY (ALT + D)", command=delete_selected_party, font=("Segoe UI", 10, "bold"), bg="#BE123C", fg="#FFFFFF", bd=0, padx=16, pady=8, cursor="hand2")
        btn_delete.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # RIGHT PANEL
        right_card = tk.Frame(body_f, bg="#0F172A", bd=2, relief="solid", padx=16, pady=16)
        right_card.grid(row=0, column=2, sticky="nsew", padx=(6, 0), pady=0)

        tk.Label(right_card, text="⚡ MASTER ANALYTICS", font=("Segoe UI", 13, "bold"), fg="#38BDF8", bg="#0F172A").pack(anchor="w")
        lbl_status = tk.Label(right_card, text="● CLIENT REPOSITORY READY", font=("Segoe UI", 10, "bold"), fg="#34D399", bg="#0F172A")
        lbl_status.pack(anchor="w", pady=(3, 10))

        tk.Frame(right_card, bg="#334155", height=2).pack(fill="x", pady=6)

        lbl_total_parties = tk.Label(right_card, text="Total Registered: ...", font=("Segoe UI", 10, "bold"), fg="#FDE047", bg="#0F172A")
        lbl_total_parties.pack(anchor="w", pady=2)

        stats_f = tk.Frame(right_card, bg="#1E293B", padx=10, pady=8)
        stats_f.pack(fill="x", pady=6)
        tk.Label(stats_f, text="Default Financial Year:", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#1E293B").pack(anchor="w")
        tk.Label(stats_f, text="1-Apr-2026 to 31-Mar-2027", font=("Segoe UI", 10, "bold"), fg="#60A5FA", bg="#1E293B").pack(anchor="w")

        tk.Frame(right_card, bg="#334155", height=2).pack(fill="x", pady=8)

        tk.Label(right_card, text="⌨ Tally Function & Hotkey Guide:", font=("Segoe UI", 10, "bold"), fg="#38BDF8", bg="#0F172A").pack(anchor="w", pady=(2, 4))

        hotkey_list = [
            ("Alt + C", "Create New Party Master"),
            ("Enter", "Open Selected Company"),
            ("Alt + D", "Delete Highlighted Record"),
            ("↓ / ↑", "Move Selection Cursor"),
            ("Esc", "Exit Software System")
        ]
        for k_btn, k_act in hotkey_list:
            k_row = tk.Frame(right_card, bg="#0F172A")
            k_row.pack(fill="x", pady=2)
            tk.Label(k_row, text=k_btn, font=("Segoe UI", 8, "bold"), fg="#FDE047", bg="#1E293B", padx=6, pady=1, width=8).pack(side="left")
            tk.Label(k_row, text=f" {k_act}", font=("Segoe UI", 9, "normal"), fg="#E2E8F0", bg="#0F172A").pack(side="left", padx=4)

        r_foot = tk.Frame(right_card, bg="#090E17", bd=1, relief="solid", padx=10, pady=8)
        r_foot.pack(fill="x", side="bottom")
        tk.Label(r_foot, text="🔒 AUTO BACKUP PROTECTED DB", font=("Segoe UI", 8, "bold"), fg="#34D399", bg="#090E17").pack(anchor="center")

        party_cache = []

        def load_parties():
            party_cache.clear()
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT id, client_code, name, fy_period, contact, address, gstin, aadhaar_no FROM clients ORDER BY name COLLATE NOCASE ASC")
            rows = cur.fetchall()
            conn.close()
            for r in rows:
                party_cache.append({
                    "id": r[0], "code": r[1], "name": r[2], "period": r[3] or "1-Apr-26 to 31-Mar-27",
                    "contact": r[4], "address": r[5], "gstin": r[6], "aadhaar": r[7]
                })
            render()
            lbl_total_parties.config(text=f"Total Registered: {len(party_cache)} Companies / Clients")

        def render(q=""):
            for item in tree.get_children():
                tree.delete(item)
            term = q.strip().lower()
            for p in party_cache:
                if not term or term in p["name"].lower() or term in p["code"].lower():
                    tree.insert("", "end", iid=str(p["id"]), values=(
                        p["name"],
                        f"({p['code'].replace('CL-', '') if 'CL-' in p['code'] else p['code']})",
                        p["period"]
                    ))
            children = tree.get_children()
            if children:
                tree.selection_set(children[0])
                tree.focus(children[0])

        search_var.trace_add("write", lambda *args: render(search_var.get()))

        def open_selected_party(event=None):
            sel = tree.selection()
            if not sel: return
            p_id = int(sel[0])
            match = next((p for p in party_cache if p["id"] == p_id), None)
            if match:
                self.current_active_party = match
                self.lbl_ribbon_title.config(text=f"| Party: {match['name']} ({match['code']})", fg="#FFD166")
                self.show_gateway_of_tally()

        tree.bind("<Double-1>", open_selected_party)
        tree.bind("<Return>", open_selected_party)
        tree.bind("<KP_Enter>", open_selected_party)

        self.bind("<Alt-c>", lambda e: self.show_create_party_dialog())
        self.bind("<Alt-C>", lambda e: self.show_create_party_dialog())
        self.active_delete_handler = delete_selected_party

        load_parties()
        tree.focus_set()

    # ================= 2. GATEWAY OF TALLY =================
    def show_gateway_of_tally(self):
        if not self.current_active_party:
            self.show_select_party_screen()
            return

        self.clear_main()
        self.current_screen = "GATEWAY_TALLY"
        p = self.current_active_party

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM sales_invoices WHERE client_id=?", (p['id'],))
        total_sale = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM receipts WHERE client_id=?", (p['id'],))
        total_rec = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sales_invoices WHERE client_id=?", (p['id'],))
        total_bills = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM items")
        total_stock_items = cur.fetchone()[0]
        conn.close()
        balance = total_sale - total_rec

        main_box = tk.Frame(self.main_container, bg="#0A1128", bd=0)
        main_box.pack(fill="both", expand=True, padx=0, pady=0)

        top_crest = tk.Frame(main_box, bg="#1E293B", height=42)
        top_crest.pack(fill="x", side="top")
        top_crest.pack_propagate(False)

        tk.Label(top_crest, text=f"🏢 {p['name']} ({p['code']})", font=("Segoe UI", 12, "bold"), fg="#FFD166", bg="#1E293B").pack(side="left", padx=15)
        tk.Label(top_crest, text=f"Billed: ₹ {total_sale:,.0f}   |   Received: ₹ {total_rec:,.0f}   |   Net Closing: ₹ {balance:,.0f} {'(DUE)' if balance > 0 else '(CLEAR)'}", font=("Segoe UI", 10, "bold"), fg="#38BDF8", bg="#1E293B").pack(side="right", padx=15)

        body_f = tk.Frame(main_box, bg="#0A1128")
        body_f.pack(fill="both", expand=True, padx=6, pady=4)
        body_f.columnconfigure(0, weight=3)
        body_f.columnconfigure(1, weight=5)
        body_f.columnconfigure(2, weight=3)
        body_f.rowconfigure(0, weight=1)

        # LEFT PANEL
        left_card = tk.Frame(body_f, bg="#0F172A", bd=2, relief="solid", padx=16, pady=16)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)

        tk.Label(left_card, text="🏛 CHAMBER & FIRM", font=("Segoe UI", 14, "bold"), fg="#38BDF8", bg="#0F172A").pack(anchor="w")
        tk.Label(left_card, text="SHREE RADHA CONSULTANT", font=("Segoe UI", 12, "bold"), fg="#FDE047", bg="#0F172A").pack(anchor="w", pady=(4, 0))
        tk.Label(left_card, text="Prop. Vinay Yadav | Tax Advocate", font=("Segoe UI", 10, "bold"), fg="#F1F5F9", bg="#0F172A").pack(anchor="w")
        tk.Label(left_card, text="Income Tax, GST & Financial Advisory", font=("Segoe UI", 9, "normal"), fg="#94A3B8", bg="#0F172A").pack(anchor="w", pady=(0, 10))

        tk.Frame(left_card, bg="#334155", height=2).pack(fill="x", pady=8)

        tk.Label(left_card, text="🌐 Key Compliance Filings:", font=("Segoe UI", 11, "bold"), fg="#34D399", bg="#0F172A").pack(anchor="w", pady=(2, 6))
        
        filings = [
            "✔ GST Returns & Monthly Billing",
            "✔ Income Tax Return Filings & Audit",
            "✔ Class-3 Digital Signatures (DSC)",
            "✔ Corporate & TDS Returns Compliance",
            "✔ New Commercial Entity Formations"
        ]
        for f_item in filings:
            tk.Label(left_card, text=f_item, font=("Segoe UI", 9, "bold"), fg="#CBD5E1", bg="#0F172A").pack(anchor="w", pady=3)

        tk.Frame(left_card, bg="#334155", height=2).pack(fill="x", pady=10)

        tk.Label(left_card, text="📍 Chamber Address:", font=("Segoe UI", 10, "bold"), fg="#FDE047", bg="#0F172A").pack(anchor="w")
        tk.Label(left_card, text="Jamalpur Station Road, Muhammadabad Gohna,\nMau District, Uttar Pradesh - 276403", font=("Segoe UI", 9, "normal"), fg="#CBD5E1", bg="#0F172A", justify="left").pack(anchor="w", pady=(3, 6))
        tk.Label(left_card, text="📞 Support: +91 8009844246", font=("Segoe UI", 9, "bold"), fg="#38BDF8", bg="#0F172A").pack(anchor="w")

        l_foot = tk.Frame(left_card, bg="#090E17", bd=1, relief="solid", padx=10, pady=8)
        l_foot.pack(fill="x", side="bottom")
        tk.Label(l_foot, text="● ACTIVE CONSULTANCY ENGINE: 2026-27", font=("Segoe UI", 8, "bold"), fg="#34D399", bg="#090E17").pack(anchor="center")

        # CENTER PANEL
        center_frame = tk.Frame(body_f, bg="#0A1128")
        center_frame.grid(row=0, column=1, sticky="nsew", pady=0)

        tally_box = tk.Frame(center_frame, bg="#0F172A", bd=3, relief="solid")
        tally_box.pack(fill="both", expand=True)

        t_header = tk.Frame(tally_box, bg="#1E40AF", height=42)
        t_header.pack(fill="x")
        t_header.pack_propagate(False)
        tk.Label(t_header, text="GATEWAY OF TALLY - ERP SUITE", font=("Trebuchet MS", 15, "bold"), fg="#FFFFFF", bg="#1E40AF").pack(pady=8)

        t_body = tk.Frame(tally_box, bg="#0F172A", padx=16, pady=4)
        t_body.pack(fill="both", expand=True)

        tally_menu = [
            ("MASTERS", "CREATE STOCK ITEM (ALT+C)", "C", lambda: self.show_create_item_dialog(), "#0284C7", "#0C2340", "#38BDF8"),
            ("MASTERS", "CHART OF ACCOUNTS / SERVICES", "A", lambda: self.show_create_item_dialog(), "#0369A1", "#082F49", "#7DD3FC"),
            ("TRANSACTIONS", "VOUCHERS: SALES BILLING (F8)", "V", self.show_sale_invoice, "#2563EB", "#172554", "#60A5FA"),
            ("TRANSACTIONS", "BANKING: FEES RECEIPT (F6)", "B", self.show_receipt_voucher, "#059669", "#064E3B", "#34D399"),
            ("REPORTS", "LEDGER ACCOUNT STATEMENT", "L", self.show_party_statement_view, "#7C3AED", "#2E1065", "#C084FC"),
            ("REPORTS", "DAY BOOK / BILL REGISTER", "D", self.show_party_statement_view, "#6D28D9", "#3B0764", "#DDD6FE"),
            ("REPORTS", "PRINT LEDGER / EXPORT (ALT+P)", "P", self.print_party_ledger_pdf, "#0D9488", "#134E4A", "#2DD4BF"),
            ("COMPANY", "SELECT / SWITCH PARTY (ESC)", "S", self.show_select_party_screen, "#D97706", "#451A03", "#FBBF24"),
            ("COMPANY", "QUIT ERP SYSTEM", "Q", lambda: self.handle_universal_escape(None), "#DC2626", "#450A0A", "#F87171")
        ]

        menu_widgets = []
        cur_idx = [2]

        current_head = None
        for i, (cat, title, hotkey, action_fn, border_col, bg_col, text_col) in enumerate(tally_menu):
            if cat != current_head:
                current_head = cat
                tk.Label(t_body, text=f"─── {cat} ───", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#0F172A").pack(anchor="center", pady=(3, 1))

            row_card = tk.Frame(t_body, bg=bg_col, bd=2, relief="solid", highlightthickness=1, highlightbackground=border_col, cursor="hand2")
            row_card.pack(fill="both", expand=True, pady=2, padx=6)

            lbl = tk.Label(row_card, text=title, font=("Segoe UI", 10, "bold"), fg=text_col, bg=bg_col, cursor="hand2")
            lbl.pack(anchor="center", expand=True)

            menu_widgets.append((row_card, lbl, action_fn, hotkey.lower(), bg_col, text_col, border_col))

        def update_cursor(new_pos):
            if 0 <= new_pos < len(menu_widgets):
                cur_idx[0] = new_pos
                for pos, (rw, lb, _, _, orig_bg, orig_fg, orig_bd) in enumerate(menu_widgets):
                    if pos == new_pos:
                        rw.configure(bg="#F59E0B", highlightbackground="#FFFFFF")
                        lb.configure(bg="#F59E0B", fg="#000000")
                    else:
                        rw.configure(bg=orig_bg, highlightbackground=orig_bd)
                        lb.configure(bg=orig_bg, fg=orig_fg)

        def on_down(e):
            update_cursor(min(len(menu_widgets) - 1, cur_idx[0] + 1))
            return "break"

        def on_up(e):
            update_cursor(max(0, cur_idx[0] - 1))
            return "break"

        def on_enter(e):
            menu_widgets[cur_idx[0]][2]()
            return "break"

        def on_key(e):
            ch = e.char.lower()
            for pos, (_, _, fn, hk, _, _, _) in enumerate(menu_widgets):
                if ch == hk:
                    update_cursor(pos)
                    fn()
                    return "break"

        for idx, (rw, lb, action_fn, _, _, _, _) in enumerate(menu_widgets):
            rw.bind("<Button-1>", lambda e, p=idx, fn=action_fn: (update_cursor(p), fn()))
            lb.bind("<Button-1>", lambda e, p=idx, fn=action_fn: (update_cursor(p), fn()))

        self.bind("<Down>", on_down)
        self.bind("<Up>", on_up)
        self.bind("<Return>", on_enter)
        self.bind("<KP_Enter>", on_enter)
        self.bind("<Key>", on_key)

        update_cursor(2)

        # RIGHT PANEL
        right_card = tk.Frame(body_f, bg="#0F172A", bd=2, relief="solid", padx=16, pady=16)
        right_card.grid(row=0, column=2, sticky="nsew", padx=(6, 0), pady=0)

        tk.Label(right_card, text="⚡ CLIENT & SESSION STATS", font=("Segoe UI", 13, "bold"), fg="#38BDF8", bg="#0F172A").pack(anchor="w")
        tk.Label(right_card, text=f"Party: {p['name']} ({p['code']})", font=("Segoe UI", 10, "bold"), fg="#FFD166", bg="#0F172A").pack(anchor="w", pady=(3, 10))

        tk.Frame(right_card, bg="#334155", height=2).pack(fill="x", pady=6)

        stats_rows = [
            ("Total Billed (Sales):", f"₹ {total_sale:,.0f} ({total_bills} Bills)", "#60A5FA"),
            ("Total Received (Fees):", f"₹ {total_rec:,.0f}", "#34D399"),
            ("Net Closing Due:", f"₹ {balance:,.0f} {'(PENDING)' if balance > 0 else '(SETTLED)'}", "#F87171" if balance > 0 else "#4ADE80"),
            ("Configured Stock Items:", f"{total_stock_items} Services", "#FDE047")
        ]
        for s_title, s_val, s_col in stats_rows:
            s_box = tk.Frame(right_card, bg="#1E293B", padx=8, pady=6)
            s_box.pack(fill="x", pady=3)
            tk.Label(s_box, text=s_title, font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#1E293B").pack(anchor="w")
            tk.Label(s_box, text=s_val, font=("Segoe UI", 11, "bold"), fg=s_col, bg="#1E293B").pack(anchor="w")

        tk.Frame(right_card, bg="#334155", height=2).pack(fill="x", pady=8)

        tk.Label(right_card, text="⌨ Fast Shortcut Keys:", font=("Segoe UI", 10, "bold"), fg="#38BDF8", bg="#0F172A").pack(anchor="w", pady=(0, 4))

        hotkey_list = [
            ("F8", "Sales / Billing"),
            ("F6", "Fees Receipt"),
            ("Alt + C", "Create Stock Item"),
            ("Alt + P", "Print Invoice / Ledger"),
            ("↓ / ↑", "Move Menu Cursor"),
            ("Esc", "Switch Company")
        ]
        for k_btn, k_act in hotkey_list:
            k_row = tk.Frame(right_card, bg="#0F172A")
            k_row.pack(fill="x", pady=2)
            tk.Label(k_row, text=k_btn, font=("Segoe UI", 8, "bold"), fg="#FDE047", bg="#1E293B", padx=6, pady=1, width=8).pack(side="left")
            tk.Label(k_row, text=f" {k_act}", font=("Segoe UI", 9, "normal"), fg="#E2E8F0", bg="#0F172A").pack(side="left", padx=4)

        r_foot = tk.Frame(right_card, bg="#090E17", bd=1, relief="solid", padx=10, pady=8)
        r_foot.pack(fill="x", side="bottom")
        tk.Label(r_foot, text="🔒 SECURE OFFLINE LOCAL DB", font=("Segoe UI", 8, "bold"), fg="#34D399", bg="#090E17").pack(anchor="center")

    # ================= 3. STATEMENT VIEW & PRINT =================
    def show_party_statement_view(self):
        self.clear_main()
        self.current_screen = "STATEMENT_VIEW"
        p = self.current_active_party

        v_frame = tk.Frame(self.main_container, bg="#FFFFFF", bd=2, relief="solid")
        v_frame.pack(fill="both", expand=True)

        header = tk.Frame(v_frame, bg="#0F4C81", height=40)
        header.pack(fill="x")
        tk.Label(header, text=f"📖 Ledger Statement & Bill Register: {p['name']}  [Select Row + Alt+P to Print Specific Bill]", font=("Segoe UI", 11, "bold"), fg="#FFFFFF", bg="#0F4C81").pack(side="left", padx=15, pady=6)
        
        btn_box = tk.Frame(header, bg="#0F4C81")
        btn_box.pack(side="right", padx=15)

        def print_selected_or_ledger():
            sel = stmt_tree.selection()
            if sel:
                item_val = stmt_tree.item(sel[0], "values")
                v_type_no = item_val[1]
                v_id = stmt_tree.item(sel[0], "tags")
                if "Sale" in v_type_no and v_id:
                    self.print_invoice_html(v_id[0])
                    return
            self.print_party_ledger_pdf()

        tk.Button(btn_box, text="🖨 Print Selected Bill / Ledger (Alt+P)", command=print_selected_or_ledger, bg="#10B981", fg="#FFFFFF", font=("Segoe UI", 9, "bold"), bd=0, padx=12, pady=4, cursor="hand2").pack(side="right")

        tree_f = tk.Frame(v_frame, bg="#FFFFFF", padx=15, pady=10)
        tree_f.pack(fill="both", expand=True)

        cols = ("Date", "Voucher Type & No", "Particulars", "Billing Month", "Debit (Sale)", "Credit (Rec)")
        stmt_tree = ttk.Treeview(tree_f, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            stmt_tree.heading(c, text=c)
            stmt_tree.column(c, width=130 if c in ["Date", "Debit (Sale)", "Credit (Rec)"] else (220 if "Voucher" in c else 320), anchor="center" if c in ["Date", "Billing Month", "Debit (Sale)", "Credit (Rec)"] else "w")

        sc = tk.Scrollbar(tree_f, orient="vertical", command=stmt_tree.yview)
        stmt_tree.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        stmt_tree.pack(fill="both", expand=True)

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id, invoice_date, invoice_no, particulars, for_month, amount FROM sales_invoices WHERE client_id=? ORDER BY invoice_date ASC, id ASC", (p['id'],))
        sales = cur.fetchall()
        cur.execute("SELECT id, receipt_date, receipt_no, remarks, towards_month, amount FROM receipts WHERE client_id=? ORDER BY receipt_date ASC, id ASC", (p['id'],))
        recs = cur.fetchall()
        conn.close()

        evts = []
        for s in sales: evts.append((s[1], f"Sale Inv: {s[2]}", s[3], s[4], s[5], 0.0, s[0], "SALE"))
        for r in recs: evts.append((r[1], f"Receipt: {r[2]}", r[3], r[4], 0.0, r[5], r[0], "REC"))
        evts.sort(key=lambda x: x[0])

        for dt, vno, part, mth, dr, cr, vid, vtype in evts:
            dr_s = f"₹ {dr:,.0f}" if dr > 0 else "-"
            cr_s = f"₹ {cr:,.0f}" if cr > 0 else "-"
            stmt_tree.insert("", "end", values=(dt, vno, part, mth, dr_s, cr_s), tags=(vid, vtype))

        def on_double_click(event):
            sel = stmt_tree.selection()
            if not sel: return
            item_val = stmt_tree.item(sel[0], "values")
            v_type_no = item_val[1]
            v_id = stmt_tree.item(sel[0], "tags")
            if "Sale" in v_type_no and v_id:
                self.print_invoice_html(v_id[0])

        stmt_tree.bind("<Double-1>", on_double_click)
        stmt_tree.bind("<Return>", on_double_click)
        self.active_print_handler = print_selected_or_ledger

    def print_party_ledger_pdf(self):
        p = self.current_active_party
        if not p: return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT invoice_date, invoice_no, for_month, particulars, amount FROM sales_invoices WHERE client_id=? ORDER BY invoice_date ASC, id ASC", (p['id'],))
        sales = cur.fetchall()
        cur.execute("SELECT receipt_date, receipt_no, towards_month, remarks, amount, payment_mode FROM receipts WHERE client_id=? ORDER BY receipt_date ASC, id ASC", (p['id'],))
        recs = cur.fetchall()
        conn.close()

        total_sale = sum(s[4] for s in sales)
        total_rec = sum(r[4] for r in recs)
        balance = total_sale - total_rec

        rows_html = ""
        evts = []
        for s in sales: evts.append((s[0], f"Sale Inv: {s[1]}", s[3], s[2], s[4], 0.0))
        for r in recs: evts.append((r[0], f"Receipt: {r[1]} ({r[5]})", r[3], r[2], 0.0, r[4]))
        evts.sort(key=lambda x: x[0])

        for dt, vno, part, mth, dr, cr in evts:
            dr_s = f"₹ {dr:,.2f}" if dr > 0 else "-"
            cr_s = f"₹ {cr:,.2f}" if cr > 0 else "-"
            rows_html += f"<tr><td>{dt}</td><td><b>{vno}</b></td><td>{part}</td><td>{mth}</td><td style='text-align:right;'>{dr_s}</td><td style='text-align:right;'>{cr_s}</td></tr>"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Ledger - {p['name']}</title>
<style>
  body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; padding: 25px; background: #525659; }}
  .box {{ max-width: 860px; margin: auto; padding: 30px; background: #fff; box-shadow: 0 0 15px rgba(0,0,0,0.2); border-radius: 4px; }}
  .header {{ text-align: center; border-bottom: 2px solid #0F2027; padding-bottom: 10px; margin-bottom: 15px; }}
  .header h2 {{ margin: 0; color: #0F2027; }}
  .meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 12px; }}
  .meta-table td {{ padding: 5px; }}
  .table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11px; }}
  .table th {{ background: #1E293B; color: #fff; padding: 8px; text-align: left; border: 1px solid #1E293B; }}
  .table td {{ padding: 8px; border: 1px solid #CBD5E1; }}
  .btn-print {{ background: #0284C7; color: #fff; border: none; padding: 12px 28px; font-size: 14px; font-weight: bold; border-radius: 5px; cursor: pointer; margin-bottom: 20px; }}
  @media print {{ body {{ background: #fff; padding: 0; }} .box {{ box-shadow: none; padding: 0; }} .no-print {{ display: none; }} }}
</style>
</head>
<body>
<div style="text-align:center;" class="no-print">
  <button class="btn-print" onclick="window.print()">🖨 Print / Save as PDF</button>
</div>
<div class="box">
  <div class="header">
    <h2>SHREE RADHA CONSULTANT</h2>
    <div style="font-size: 11px; color: #475569; margin-top: 4px;">Jamalpur Station Road, Muhammadabad Gohna, Mau (U.P.) - 276403</div>
    <div style="font-size: 13px; font-weight: bold; margin-top: 8px; color: #0369A1;">STATEMENT OF ACCOUNT / PARTY LEDGER</div>
  </div>
  <table class="meta-table">
    <tr>
      <td><b>Party Name:</b> {p['name']}</td>
      <td><b>Client Code:</b> {p['code']}</td>
    </tr>
    <tr>
      <td><b>Mobile:</b> {p['contact'] or 'N/A'}</td>
      <td><b>Period:</b> {p['period']}</td>
    </tr>
    <tr>
      <td><b>GSTIN:</b> {p['gstin'] or 'NOT APPLICABLE'}</td>
      <td><b>Address:</b> {p['address'] or 'LOCAL'}</td>
    </tr>
  </table>
  <table class="table">
    <thead>
      <tr>
        <th>Date</th>
        <th>Voucher No</th>
        <th>Particulars</th>
        <th>Month</th>
        <th style="text-align:right;">Debit (Sale)</th>
        <th style="text-align:right;">Credit (Rec)</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
      <tr style="font-weight:bold; background:#F8FAFC;">
        <td colspan="4" style="text-align:right;">TOTALS:</td>
        <td style="text-align:right; color:#2563EB;">₹ {total_sale:,.2f}</td>
        <td style="text-align:right; color:#059669;">₹ {total_rec:,.2f}</td>
      </tr>
      <tr style="font-weight:bold; background:#EFF6FF; font-size:12px;">
        <td colspan="4" style="text-align:right;">CLOSING BALANCE DUE:</td>
        <td colspan="2" style="text-align:right; color:#DC2626;">₹ {balance:,.2f} {'(PENDING DUE)' if balance > 0 else '(SETTLED)'}</td>
      </tr>
    </tbody>
  </table>
</div>
<script>
  window.onload = function() {{ window.print(); }};
</script>
</body>
</html>"""
        try:
            safe_name = p['name'].replace(' ', '_')
            temp_html = os.path.join(tempfile.gettempdir(), f"Ledger_{safe_name}.html")
            with open(temp_html, "w", encoding="utf-8") as f:
                f.write(html_content)
            webbrowser.open(f"file:///{temp_html.replace(os.sep, '/')}")
        except Exception as e:
            messagebox.showerror("Error", f"PDF open error: {str(e)}")

    # SINGLE INVOICE PRINT METHOD WITH SIGNATURE BLOCK
    def print_invoice_html(self, inv_id):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT s.invoice_no, s.invoice_date, c.name, c.contact, c.address, c.gstin, s.for_month, s.particulars, s.amount, s.narration FROM sales_invoices s JOIN clients c ON s.client_id=c.id WHERE s.id=?", (inv_id,))
        row = cur.fetchone()
        conn.close()
        if not row: return

        inv_no, inv_date, pname, pphone, paddr, pgstin, fmonth, part, amt, narr = row

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Invoice - {inv_no}</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; padding: 30px; background: #525659; margin: 0; }}
  .box {{ max-width: 800px; margin: auto; padding: 35px; background: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.15); }}
  .title {{ text-align: center; border-bottom: 2px solid #0F2027; padding-bottom: 10px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }}
  th, td {{ border: 1px solid #CBD5E1; padding: 10px; }}
  th {{ background: #1E293B; color: #fff; }}
  .footer-sign {{ margin-top: 50px; width: 100%; border-collapse: collapse; }}
  .footer-sign td {{ border: none; padding: 0; }}
</style>
</head>
<body>
<div style="text-align:center;" class="no-print">
  <button onclick="window.print()" style="padding:10px 24px; font-weight:bold; font-size:14px; background:#0284C7; color:#fff; border:none; border-radius:4px; cursor:pointer;">🖨 Print Invoice</button>
</div>
<div class="box">
  <div class="title">
    <h2 style="margin:0; color:#0F2027;">SHREE RADHA CONSULTANT</h2>
    <div style="font-size:12px; color:#555; margin-top:4px;">Station Road, Muhammadabad Gohna, Mau (U.P.)</div>
    <h3 style="color:#0284C7; margin:10px 0 0 0;">CONSULTANCY TAX INVOICE</h3>
  </div>
  <table style="border:none; margin-top:15px; font-size:13px;">
    <tr>
      <td style="border:none;"><b>Invoice No:</b> {inv_no}<br><b>Date:</b> {inv_date}</td>
      <td style="border:none; text-align:right;"><b>Party:</b> {pname}<br><b>GSTIN:</b> {pgstin or 'URP'}</td>
    </tr>
  </table>
  <table>
    <thead>
      <tr>
        <th>Description</th>
        <th>Period</th>
        <th style="text-align:right;">Amount (₹)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>{part}<br><small style="color:#64748B;">{narr}</small></td>
        <td style="text-align:center;">{fmonth}</td>
        <td style="text-align:right;">₹ {amt:,.2f}</td>
      </tr>
      <tr style="font-weight:bold;">
        <td colspan="2" style="text-align:right;">Total:</td>
        <td style="text-align:right; color:#2563EB;">₹ {amt:,.2f}</td>
      </tr>
    </tbody>
  </table>

  <!-- FIRM NAME & SIGNATURE SECTION -->
  <table class="footer-sign">
    <tr>
      <td style="vertical-align: bottom; font-size: 11px; color: #64748B;">
        <b>Terms & Conditions:</b><br>
        1. Subject to Mau (U.P.) jurisdiction.<br>
        2. Professional fees once paid are non-refundable.
      </td>
      <td style="text-align: right; vertical-align: bottom; width: 260px;">
        <div style="font-size: 12px; color: #1E293B; margin-bottom: 50px;">For <b>SHREE RADHA CONSULTANT</b></div>
        <div style="border-top: 1px dashed #64748B; padding-top: 6px; font-size: 13px; font-weight: bold; color: #0F2027;">
          Prop. Vinay Yadav<br>
          <span style="font-size: 11px; font-weight: normal; color: #64748B;">(Authorised Signatory)</span>
        </div>
      </td>
    </tr>
  </table>
</div>
<script>window.onload = function() {{ window.print(); }};</script>
</body>
</html>"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            temp_html = os.path.join(tempfile.gettempdir(), f"Invoice_{inv_id}_{timestamp}.html")
            with open(temp_html, "w", encoding="utf-8") as f:
                f.write(html)
            webbrowser.open(f"file:///{temp_html.replace(os.sep, '/')}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= 4. CREATE PARTY POPUP =================
    def show_create_party_dialog(self):
        win = tk.Toplevel(self)
        win.title("Ledger / Party Creation")
        win.geometry("520x420")
        win.configure(bg="#F0F9FF")
        win.grab_set()
        win.bind("<Escape>", lambda e: win.destroy())

        tk.Label(win, text="Party Master Creation", font=("Segoe UI", 12, "bold"), fg="#0369A1", bg="#F0F9FF").pack(pady=10)
        f = tk.Frame(win, bg="#F0F9FF", padx=20, pady=10)
        f.pack(fill="both", expand=True)

        tk.Label(f, text="Party Name*:", font=("Segoe UI", 10, "bold"), bg="#F0F9FF").grid(row=0, column=0, sticky="w", pady=6)
        n_var = UpperStringVar()
        n_e = tk.Entry(f, textvariable=n_var, width=28, font=("Segoe UI", 10, "bold"))
        n_e.grid(row=0, column=1, sticky="w", pady=6)
        bind_auto_select(n_e)

        tk.Label(f, text="Mobile Number:", font=("Segoe UI", 10, "bold"), bg="#F0F9FF").grid(row=1, column=0, sticky="w", pady=6)
        p_var = UpperStringVar()
        p_e = tk.Entry(f, textvariable=p_var, width=28, font=("Segoe UI", 10, "bold"))
        p_e.grid(row=1, column=1, sticky="w", pady=6)
        bind_auto_select(p_e)

        tk.Label(f, text="Address:", font=("Segoe UI", 10, "bold"), bg="#F0F9FF").grid(row=2, column=0, sticky="w", pady=6)
        a_var = UpperStringVar()
        a_e = tk.Entry(f, textvariable=a_var, width=28, font=("Segoe UI", 10, "bold"))
        a_e.grid(row=2, column=1, sticky="w", pady=6)
        bind_auto_select(a_e)

        tk.Label(f, text="GSTIN (Opt):", font=("Segoe UI", 10, "bold"), bg="#F0F9FF").grid(row=3, column=0, sticky="w", pady=6)
        g_var = UpperStringVar()
        g_e = tk.Entry(f, textvariable=g_var, width=28, font=("Segoe UI", 10, "bold"))
        g_e.grid(row=3, column=1, sticky="w", pady=6)
        bind_auto_select(g_e)

        tk.Label(f, text="Aadhaar No (Opt):", font=("Segoe UI", 10, "bold"), bg="#F0F9FF").grid(row=4, column=0, sticky="w", pady=6)
        aad_var = UpperStringVar()
        aad_e = tk.Entry(f, textvariable=aad_var, width=28, font=("Segoe UI", 10, "bold"))
        aad_e.grid(row=4, column=1, sticky="w", pady=6)
        bind_auto_select(aad_e)

        tk.Label(f, text="F.Y. Period:", font=("Segoe UI", 10, "bold"), bg="#F0F9FF").grid(row=5, column=0, sticky="w", pady=6)
        fy_var = tk.StringVar(value="1-Apr-26 to 31-Mar-27")
        fy_e = tk.Entry(f, textvariable=fy_var, width=28, font=("Segoe UI", 10, "bold"))
        fy_e.grid(row=5, column=1, sticky="w", pady=6)
        bind_auto_select(fy_e)

        btn_save = tk.Button(f, text="Accept / Save (Enter)", font=("Segoe UI", 10, "bold"), bg="#0284C7", fg="#FFFFFF", padx=16, pady=6, bd=0, cursor="hand2")
        btn_save.grid(row=6, column=1, sticky="e", pady=15)

        def do_save(event=None):
            name = n_var.get().strip().upper()
            phone = p_var.get().strip()
            addr = a_var.get().strip().upper()
            gst = g_var.get().strip().upper()
            aadhaar = aad_var.get().strip()
            fy = fy_var.get().strip()

            if not name:
                messagebox.showerror("Error", "Party Name likhna zaroori hai!")
                n_e.focus_set()
                return "break"

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT client_code FROM clients WHERE client_code LIKE '10%' OR client_code LIKE 'CL-%'")
            existing_codes = cur.fetchall()
            max_num = 100028
            for row in existing_codes:
                c_str = str(row[0]).replace("CL-", "")
                if c_str.isdigit():
                    max_num = max(max_num, int(c_str))
            code = str(max_num + 1)

            cur.execute("""
            INSERT INTO clients (client_code, name, contact, address, gstin, aadhaar_no, fy_period, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name, phone, addr, gst, aadhaar, fy, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            new_id = cur.lastrowid
            conn.close()

            win.destroy()
            self.current_active_party = {
                "id": new_id, "code": code, "name": name, "period": fy,
                "contact": phone, "address": addr, "gstin": gst, "aadhaar": aadhaar
            }
            self.lbl_ribbon_title.config(text=f"| Party: {name} ({code})", fg="#FFD166")
            self.show_gateway_of_tally()
            return "break"

        btn_save.config(command=do_save)
        btn_save.bind("<Return>", do_save)
        btn_save.bind("<KP_Enter>", do_save)

        n_e.bind("<Return>", lambda e: (p_e.focus_set(), "break")[-1])
        p_e.bind("<Return>", lambda e: (a_e.focus_set(), "break")[-1])
        a_e.bind("<Return>", lambda e: (g_e.focus_set(), "break")[-1])
        g_e.bind("<Return>", lambda e: (aad_e.focus_set(), "break")[-1])
        aad_e.bind("<Return>", lambda e: (fy_e.focus_set(), "break")[-1])
        fy_e.bind("<Return>", lambda e: (btn_save.focus_set(), "break")[-1])

        n_e.focus_set()

    # ================= 5. CREATE ITEM DIALOG (ALT + C IN SALES) =================
    def show_create_item_dialog(self, on_created_callback=None):
        win = tk.Toplevel(self)
        win.title("Stock Item / Service Creation (Alt+C)")
        win.geometry("460x280")
        win.configure(bg="#F0F9FF")
        win.grab_set()
        win.bind("<Escape>", lambda e: win.destroy())

        tk.Label(win, text="📦 Stock Item / Service Master (Alt+C)", font=("Segoe UI", 12, "bold"), fg="#0369A1", bg="#F0F9FF").pack(pady=12)
        f = tk.Frame(win, bg="#F0F9FF", padx=20, pady=10)
        f.pack(fill="both", expand=True)

        tk.Label(f, text="Item / Service Name*:", font=("Segoe UI", 10, "bold"), bg="#F0F9FF").grid(row=0, column=0, sticky="w", pady=8)
        name_var = UpperStringVar()
        name_e = tk.Entry(f, textvariable=name_var, width=24, font=("Segoe UI", 10, "bold"))
        name_e.grid(row=0, column=1, sticky="w", pady=8)
        bind_auto_select(name_e)

        tk.Label(f, text="Standard Rate (₹):", font=("Segoe UI", 10, "bold"), bg="#F0F9FF").grid(row=1, column=0, sticky="w", pady=8)
        rate_var = tk.StringVar(value="0")
        rate_e = tk.Entry(f, textvariable=rate_var, width=15, font=("Segoe UI", 10, "bold"))
        rate_e.grid(row=1, column=1, sticky="w", pady=8)
        bind_auto_select(rate_e)

        tk.Label(f, text="Unit (NOS/MTH/QTR):", font=("Segoe UI", 10, "bold"), bg="#F0F9FF").grid(row=2, column=0, sticky="w", pady=8)
        unit_var = UpperStringVar(value="NOS")
        unit_e = tk.Entry(f, textvariable=unit_var, width=15, font=("Segoe UI", 10, "bold"))
        unit_e.grid(row=2, column=1, sticky="w", pady=8)
        bind_auto_select(unit_e)

        btn_save = tk.Button(f, text="Save Item (Enter)", font=("Segoe UI", 10, "bold"), bg="#0284C7", fg="#FFFFFF", padx=16, pady=6, bd=0, cursor="hand2")
        btn_save.grid(row=3, column=1, sticky="e", pady=15)

        def save_item(event=None):
            iname = name_var.get().strip().upper()
            rstr = rate_var.get().strip()
            u_str = unit_var.get().strip().upper()
            if not iname:
                messagebox.showerror("Error", "Item Name likhna zaroori hai!")
                return "break"
            try:
                r_val = float(rstr)
            except ValueError:
                r_val = 0.0

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO items (item_name, default_rate, unit) VALUES (?, ?, ?)", (iname, r_val, u_str))
                conn.commit()
            except sqlite3.IntegrityError:
                messagebox.showwarning("Exists", "Yeh Item Name pehle se bana hua hai!")
                conn.close()
                return "break"
            conn.close()

            win.destroy()
            if on_created_callback:
                on_created_callback(iname, r_val)
            return "break"

        btn_save.config(command=save_item)
        btn_save.bind("<Return>", save_item)
        name_e.bind("<Return>", lambda e: (rate_e.focus_set(), "break")[-1])
        rate_e.bind("<Return>", lambda e: (unit_e.focus_set(), "break")[-1])
        unit_e.bind("<Return>", lambda e: (btn_save.focus_set(), "break")[-1])
        name_e.focus_set()

    # ================= 6. SALES VOUCHER =================
    def show_sale_invoice(self):
        self.clear_main()
        self.current_screen = "VOUCHER"
        
        v_frame = tk.Frame(self.main_container, bg="#FFFFFF", bd=2, relief="solid")
        v_frame.pack(fill="both", expand=True)

        p = self.current_active_party
        p_title = f"for '{p['name']}'" if p else "(Type/Select Party Below)"
        header = tk.Frame(v_frame, bg="#0F4C81", height=38)
        header.pack(fill="x")
        tk.Label(header, text=f"Accounting Voucher (F8: Sales) {p_title}  [Alt+C: New Item | ↓/↑: Select Item | Esc: Back]", font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#0F4C81").pack(side="left", padx=15, pady=8)

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sales_invoices")
        inv_cnt = cur.fetchone()[0] + 1
        conn.close()

        body_split = tk.Frame(v_frame, bg="#F0F9FF")
        body_split.pack(fill="both", expand=True, padx=15, pady=12)
        body_split.columnconfigure(0, weight=6)
        body_split.columnconfigure(1, weight=4)
        body_split.rowconfigure(0, weight=1)

        f_box = tk.Frame(body_split, bg="#F0F9FF", bd=1, relief="solid", padx=25, pady=25)
        f_box.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        for col_i in range(4):
            f_box.columnconfigure(col_i, weight=1 if col_i in [1, 3] else 0)

        tk.Label(f_box, text="Invoice No:", font=("Segoe UI", 11, "bold"), bg="#F0F9FF").grid(row=0, column=0, sticky="w", padx=8, pady=12)
        inv_var = UpperStringVar(value=f"SRC/26-27/{inv_cnt:03d}")
        inv_e = tk.Entry(f_box, textvariable=inv_var, font=("Segoe UI", 11, "bold"), width=16)
        inv_e.grid(row=0, column=1, sticky="w", padx=8, pady=12)
        bind_auto_select(inv_e)

        tk.Label(f_box, text="Date (DD-MM):", font=("Segoe UI", 11, "bold"), bg="#F0F9FF").grid(row=0, column=2, sticky="w", padx=8, pady=12)
        dt_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        dt_e = tk.Entry(f_box, textvariable=dt_var, font=("Segoe UI", 11, "bold"), width=16)
        dt_e.grid(row=0, column=3, sticky="w", padx=8, pady=12)

        tk.Label(f_box, text="Party A/c Name:", font=("Segoe UI", 11, "bold"), bg="#F0F9FF").grid(row=1, column=0, sticky="w", padx=8, pady=12)
        party_var = UpperStringVar(value=p['name'] if p else "")
        party_e = tk.Entry(f_box, textvariable=party_var, font=("Segoe UI", 11, "bold"), width=22)
        party_e.grid(row=1, column=1, sticky="w", padx=8, pady=12)
        bind_auto_select(party_e)

        tk.Label(f_box, text="Billing Month:", font=("Segoe UI", 11, "bold"), bg="#F0F9FF").grid(row=1, column=2, sticky="w", padx=8, pady=12)
        cur_m = datetime.now().strftime("%B %Y")
        m_var = tk.StringVar(value=cur_m)
        m_e = tk.Entry(f_box, textvariable=m_var, font=("Segoe UI", 11, "bold"), width=16)
        m_e.grid(row=1, column=3, sticky="w", padx=8, pady=12)

        tk.Label(f_box, text="Particulars / Item*:", font=("Segoe UI", 11, "bold"), fg="#0284C7", bg="#F0F9FF").grid(row=2, column=0, sticky="w", padx=8, pady=12)
        part_var = UpperStringVar(value="")
        part_e = tk.Entry(f_box, textvariable=part_var, font=("Segoe UI", 11, "bold"), width=28)
        part_e.grid(row=2, column=1, columnspan=2, sticky="w", padx=8, pady=12)
        bind_auto_select(part_e)

        tk.Label(f_box, text="Amount (₹):", font=("Segoe UI", 11, "bold"), bg="#F0F9FF").grid(row=2, column=2, sticky="e", padx=8, pady=12)
        amt_e = tk.Entry(f_box, font=("Segoe UI", 11, "bold"), width=16)
        amt_e.grid(row=2, column=3, sticky="w", padx=8, pady=12)
        bind_auto_select(amt_e)

        tk.Label(f_box, text="Narration:", font=("Segoe UI", 11, "bold"), bg="#F0F9FF").grid(row=3, column=0, sticky="w", padx=8, pady=12)
        nar_var = UpperStringVar(value="")
        nar_e = tk.Entry(f_box, textvariable=nar_var, font=("Segoe UI", 11, "bold"))
        nar_e.grid(row=3, column=1, columnspan=3, sticky="ew", padx=8, pady=12)
        bind_auto_select(nar_e)

        btn_box = tk.Frame(f_box, bg="#F0F9FF")
        btn_box.grid(row=4, column=0, columnspan=4, sticky="e", padx=8, pady=25)

        btn_save = tk.Button(btn_box, text="Accept (Enter)", font=("Segoe UI", 11, "bold"), bg="#0284C7", fg="#FFFFFF", padx=25, pady=8, bd=0, cursor="hand2", takefocus=1)
        btn_save.pack(side="right")

        stock_drawer = tk.Frame(body_split, bg="#FFFFFF", bd=2, relief="solid")
        stock_drawer.grid(row=0, column=1, sticky="nsew")

        s_hdr = tk.Frame(stock_drawer, bg="#1E293B", height=38)
        s_hdr.pack(fill="x")
        tk.Label(s_hdr, text="📦 List of Stock Items (Press ↓ Arrow to Select)", font=("Segoe UI", 10, "bold"), fg="#38BDF8", bg="#1E293B").pack(side="left", padx=12, pady=6)

        st_cols = ("Item Name", "Rate")
        stock_tree = ttk.Treeview(stock_drawer, columns=st_cols, show="headings", selectmode="browse")
        stock_tree.heading("Item Name", text="Item / Service")
        stock_tree.heading("Rate", text="Rate (₹)")
        stock_tree.column("Item Name", width=220, anchor="w")
        stock_tree.column("Rate", width=90, anchor="e")

        st_scroll = tk.Scrollbar(stock_drawer, orient="vertical", command=stock_tree.yview)
        stock_tree.configure(yscrollcommand=st_scroll.set)
        st_scroll.pack(side="right", fill="y")
        stock_tree.pack(fill="both", expand=True)

        def load_stock_items():
            for itm in stock_tree.get_children():
                stock_tree.delete(itm)
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT item_name, default_rate FROM items ORDER BY item_name ASC")
            for row in cur.fetchall():
                stock_tree.insert("", "end", values=(row[0], f"{row[1]:.0f}"))
            conn.close()

        load_stock_items()

        def show_drawer(event=None):
            stock_drawer.grid()

        def hide_drawer(event=None):
            if self.focus_get() not in [stock_tree, stock_drawer]:
                stock_drawer.grid_remove()

        stock_drawer.grid_remove()
        part_e.bind("<FocusIn>", show_drawer)

        def on_item_select(event=None):
            sel = stock_tree.selection()
            if not sel: return
            vals = stock_tree.item(sel[0], "values")
            part_var.set(vals[0])
            amt_e.delete(0, tk.END)
            amt_e.insert(0, str(vals[1]))
            amt_e.focus_set()
            stock_drawer.grid_remove()
            return "break"

        stock_tree.bind("<Double-1>", on_item_select)
        stock_tree.bind("<Return>", on_item_select)
        stock_tree.bind("<KP_Enter>", on_item_select)

        def jump_to_stock_list(event=None):
            stock_drawer.grid()
            children = stock_tree.get_children()
            if children:
                cur_sel = stock_tree.selection()
                if not cur_sel:
                    stock_tree.selection_set(children[0])
                    stock_tree.focus(children[0])
                stock_tree.focus_set()
            return "break"

        def back_to_entry_from_list(event=None):
            part_e.focus_set()
            return "break"

        part_e.bind("<Down>", jump_to_stock_list)
        stock_tree.bind("<Escape>", back_to_entry_from_list)

        def trigger_create_item(event=None):
            def after_create(item_name, item_rate):
                load_stock_items()
                part_var.set(item_name)
                amt_e.delete(0, tk.END)
                amt_e.insert(0, str(int(item_rate)))
                amt_e.focus_set()
                stock_drawer.grid_remove()
            self.show_create_item_dialog(on_created_callback=after_create)
            return "break"

        self.bind("<Alt-c>", trigger_create_item)
        self.bind("<Alt-C>", trigger_create_item)

        def save_sale(event=None):
            pname = party_var.get().strip().upper()
            amt_str = amt_e.get().strip()
            inum = inv_var.get().strip()
            idt = parse_smart_date(dt_var.get().strip())
            dt_var.set(idt)
            m_txt = parse_smart_month(m_var.get().strip())
            m_var.set(m_txt)
            prt = part_var.get().strip()
            nar = nar_var.get().strip()

            if not pname or not amt_str or not inum:
                messagebox.showerror("Error", "Party Name, Invoice No aur Amount bharein!")
                return "break"
            try:
                amt_val = float(amt_str)
            except ValueError:
                messagebox.showerror("Error", "Amount number me hona chahiye!")
                return "break"

            cid = self.get_or_create_client_id(pname)
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO sales_invoices (invoice_no, invoice_date, client_id, for_month, particulars, amount, narration) VALUES (?,?,?,?,?,?,?)",
                            (inum, idt, cid, m_txt, prt, amt_val, nar))
                conn.commit()
                last_id = cur.lastrowid
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Invoice Number pehle se maujood hai!")
                conn.close()
                return "break"
            conn.close()

            if messagebox.askyesno("Success", f"Invoice {inum} save ho gayi!\nPrint nikalna chahte hain?"):
                self.print_invoice_html(last_id)

            self.show_sale_invoice()
            return "break"

        btn_save.config(command=save_sale)
        btn_save.bind("<Return>", save_sale)
        btn_save.bind("<KP_Enter>", save_sale)

        inv_e.bind("<Return>", lambda e: (dt_e.focus_set(), "break")[-1])
        bind_smart_date(dt_e, dt_var, next_widget=m_e)
        bind_smart_month(m_e, m_var, next_widget=party_e)
        party_e.bind("<Return>", lambda e: (part_e.focus_set(), "break")[-1])
        part_e.bind("<Return>", lambda e: (amt_e.focus_set(), "break")[-1])
        amt_e.bind("<Return>", lambda e: (nar_e.focus_set(), "break")[-1])
        nar_e.bind("<Return>", lambda e: (btn_save.focus_set(), "break")[-1])

        amt_e.bind("<FocusIn>", hide_drawer)
        nar_e.bind("<FocusIn>", hide_drawer)

        dt_e.focus_set()

    # ================= 7. RECEIPT VOUCHER =================
    def show_receipt_voucher(self):
        self.clear_main()
        self.current_screen = "VOUCHER"
        v_frame = tk.Frame(self.main_container, bg="#FFFFFF", bd=2, relief="solid")
        v_frame.pack(fill="both", expand=True)

        p = self.current_active_party
        p_title = f"for '{p['name']}'" if p else "(Type/Select Party Below)"
        header = tk.Frame(v_frame, bg="#059669", height=38)
        header.pack(fill="x")
        tk.Label(header, text=f"Accounting Voucher (F6: Receipt) {p_title}  [Esc: Back to Heads | Alt+D: Delete]", font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#059669").pack(side="left", padx=15, pady=8)

        f_box = tk.Frame(v_frame, bg="#F8FAFC", bd=1, relief="solid", padx=25, pady=25)
        f_box.pack(fill="x", padx=15, pady=15)

        for col_i in range(6):
            f_box.columnconfigure(col_i, weight=1 if col_i in [1, 3, 5] else 0)

        tk.Label(f_box, text="Party A/c Name:", font=("Segoe UI", 10, "bold"), bg="#F8FAFC").grid(row=0, column=0, sticky="w", padx=6, pady=8)
        c_var = UpperStringVar(value=p['name'] if p else "")
        c_e = tk.Entry(f_box, textvariable=c_var, font=("Segoe UI", 10, "bold"), width=24)
        c_e.grid(row=0, column=1, sticky="w", padx=6, pady=8)
        bind_auto_select(c_e)

        tk.Label(f_box, text="Date (DD-MM):", font=("Segoe UI", 10, "bold"), bg="#F8FAFC").grid(row=0, column=2, sticky="w", padx=6, pady=8)
        dt_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        dt_e = tk.Entry(f_box, textvariable=dt_var, font=("Segoe UI", 10, "bold"), width=15)
        dt_e.grid(row=0, column=3, sticky="w", padx=6, pady=8)

        tk.Label(f_box, text="Towards Month:", font=("Segoe UI", 10, "bold"), bg="#F8FAFC").grid(row=0, column=4, sticky="w", padx=6, pady=8)
        cur_m = datetime.now().strftime("%B %Y")
        m_var = tk.StringVar(value=cur_m)
        m_e = tk.Entry(f_box, textvariable=m_var, font=("Segoe UI", 10, "bold"), width=18)
        m_e.grid(row=0, column=5, sticky="w", padx=6, pady=6)

        tk.Label(f_box, text="Fees Amount (₹):", font=("Segoe UI", 10, "bold"), bg="#F8FAFC").grid(row=1, column=0, sticky="w", padx=6, pady=8)
        amt_e = tk.Entry(f_box, font=("Segoe UI", 10, "bold"), width=18)
        amt_e.grid(row=1, column=1, sticky="w", padx=6, pady=8)
        bind_auto_select(amt_e)

        tk.Label(f_box, text="Payment Mode:", font=("Segoe UI", 10, "bold"), bg="#F8FAFC").grid(row=1, column=2, sticky="w", padx=6, pady=8)
        mode_var = UpperStringVar(value="CASH")
        mode_e = tk.Entry(f_box, textvariable=mode_var, font=("Segoe UI", 10, "bold"), width=16)
        mode_e.grid(row=1, column=3, sticky="w", padx=6, pady=8)
        bind_auto_select(mode_e)

        tk.Label(f_box, text="Ref / UTR No:", font=("Segoe UI", 10, "bold"), bg="#F8FAFC").grid(row=1, column=4, sticky="w", padx=6, pady=8)
        ref_var = UpperStringVar(value="")
        ref_e = tk.Entry(f_box, textvariable=ref_var, font=("Segoe UI", 10, "bold"), width=18)
        ref_e.grid(row=1, column=5, sticky="w", padx=6, pady=8)
        bind_auto_select(ref_e)

        tk.Label(f_box, text="Narration:", font=("Segoe UI", 10, "bold"), bg="#F8FAFC").grid(row=2, column=0, sticky="w", padx=6, pady=10)
        nar_var = UpperStringVar(value="")
        nar_e = tk.Entry(f_box, textvariable=nar_var, font=("Segoe UI", 10, "bold"))
        nar_e.grid(row=2, column=1, columnspan=3, sticky="ew", padx=6, pady=10)
        bind_auto_select(nar_e)

        btn_box = tk.Frame(f_box, bg="#F8FAFC")
        btn_box.grid(row=2, column=5, sticky="e", padx=6, pady=10)

        btn_save = tk.Button(btn_box, text="Accept (Enter)", font=("Segoe UI", 10, "bold"), bg="#059669", fg="#FFFFFF", padx=18, pady=6, bd=0, cursor="hand2", takefocus=1)
        btn_save.pack(side="right")

        def save_rec(event=None):
            pname = c_var.get().strip().upper()
            astr = amt_e.get().strip()
            mode_txt = mode_var.get().strip().upper()
            ref_txt = ref_var.get().strip().upper()
            mth_txt = parse_smart_month(m_var.get().strip())
            m_var.set(mth_txt)
            rdt = parse_smart_date(dt_var.get().strip())
            nar = nar_var.get().strip().upper()

            if not pname or not astr:
                messagebox.showerror("Error", "Party aur Amount bharein!")
                return "break"
            try:
                amt_val = float(astr)
            except ValueError:
                messagebox.showerror("Error", "Amount number me hona chahiye!")
                return "break"

            cid = self.get_or_create_client_id(pname)
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM receipts")
            next_id = cur.fetchone()[0]
            rno = f"SRC/REC/26-27/{next_id:03d}"
            cur.execute("INSERT INTO receipts (receipt_no, receipt_date, client_id, amount, payment_mode, ref_no, towards_month, remarks) VALUES (?,?,?,?,?,?,?,?)",
                        (rno, rdt, cid, amt_val, mode_txt, ref_txt, mth_txt, nar))
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", f"Receipt {rno} successfully save ho gayi!")
            self.show_receipt_voucher()
            return "break"

        btn_save.config(command=save_rec)
        btn_save.bind("<Return>", save_rec)
        btn_save.bind("<KP_Enter>", save_rec)

        c_e.bind("<Return>", lambda e: (dt_e.focus_set(), "break")[-1])
        bind_smart_date(dt_e, dt_var, next_widget=m_e)
        bind_smart_month(m_e, m_var, next_widget=amt_e)
        amt_e.bind("<Return>", lambda e: (mode_e.focus_set(), "break")[-1])
        mode_e.bind("<Return>", lambda e: (ref_e.focus_set(), "break")[-1])
        ref_e.bind("<Return>", lambda e: (nar_e.focus_set(), "break")[-1])
        nar_e.bind("<Return>", lambda e: (btn_save.focus_set(), "break")[-1])

        dt_e.focus_set()

if __name__ == "__main__":
    init_db()
    app = ShreeRadhaERP()
    app.mainloop()