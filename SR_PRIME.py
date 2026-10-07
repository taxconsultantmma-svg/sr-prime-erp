import os
import sqlite3
import urllib.parse
import pandas as pd
import streamlit as st
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="TALLY PRIME - SHREE RADHA CONSULTANT",
    page_icon="📊",
    layout="wide"
)

# ----------------- DATA SETUP -----------------
DATA_DIR = "SR_PRIME_DATA"
os.makedirs(DATA_DIR, exist_ok=True)
DB_NAME = os.path.join(DATA_DIR, "shree_radha_consultant.db")

CHAMBER_NAME = "SHREE RADHA CONSULTANT"
CHAMBER_PROP = "PROP. VINAY YADAV (TAX ADVOCATE)"
CHAMBER_ADDR = "STATION ROAD, MUHAMMADABAD GOHNA, MAU DISTRICT, UTTAR PRADESH - 276403"
CHAMBER_PHONE = "+91 9129607278"

def amount_to_words(n):
    try:
        n = int(round(float(n)))
    except Exception:
        return "ZERO RUPEES ONLY"
    if n <= 0:
        return "ZERO RUPEES ONLY"
    units = ["", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE",
             "TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN",
             "SEVENTEEN", "EIGHTEEN", "NINETEEN"]
    tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"]
    def c1k(num):
        o = ""
        if num >= 100:
            o += units[num // 100] + " HUNDRED "
            num %= 100
        if num >= 20:
            o += tens[num // 10] + " "
            num %= 10
        if num > 0:
            o += units[num] + " "
        return o.strip()
    parts = []
    if n >= 10000000:
        parts.append(c1k(n // 10000000) + " CRORE")
        n %= 10000000
    if n >= 100000:
        parts.append(c1k(n // 100000) + " LAKH")
        n %= 100000
    if n >= 1000:
        parts.append(c1k(n // 1000) + " THOUSAND")
        n %= 1000
    if n > 0:
        parts.append(c1k(n))
    return " ".join(parts).strip() + " RUPEES ONLY"

def init_db():
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
        fy_period TEXT DEFAULT '1-APR-26 TO 31-MAR-27'
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE,
        invoice_date TEXT,
        client_id INTEGER,
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
        remarks TEXT,
        FOREIGN KEY (client_id) REFERENCES clients (id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT UNIQUE,
        default_rate REAL DEFAULT 0.0
    )
    """)
    cur.execute("INSERT OR IGNORE INTO stock_items (item_name, default_rate) VALUES ('GST RETURN FILING', 1500.0)")
    cur.execute("INSERT OR IGNORE INTO stock_items (item_name, default_rate) VALUES ('INCOME TAX AUDIT & FILING', 5000.0)")
    cur.execute("INSERT OR IGNORE INTO stock_items (item_name, default_rate) VALUES ('CLASS 3 DSC TOKEN', 2000.0)")
    cur.execute("INSERT OR IGNORE INTO stock_items (item_name, default_rate) VALUES ('CONSULTANCY CHARGES', 1000.0)")
    
    cur.execute("SELECT COUNT(*) FROM clients")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO clients (client_code, name, contact, address, gstin) VALUES ('100001', 'AWADH TRADERS', '9129607278', 'STATION ROAD, MAU', 'URP')")
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect(DB_NAME)

def get_party_balance(client_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM sales_invoices WHERE client_id=?", (client_id,))
    tot_s = cur.fetchone()[0] or 0.0
    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM receipts WHERE client_id=?", (client_id,))
    tot_r = cur.fetchone()[0] or 0.0
    conn.close()
    bal = tot_s - tot_r
    if bal >= 0:
        return f"₹ {bal:,.2f} DR", bal
    return f"₹ {abs(bal):,.2f} CR", bal

# Styling
st.markdown("""
    <style>
    .main-head {
        background-color: #0E4268;
        padding: 12px 20px;
        color: white;
        border-radius: 8px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .head-title { font-size: 20px; font-weight: bold; color: #FFCC00; }
    .head-sub { font-size: 14px; font-weight: bold; }
    .wa-btn {
        display: inline-block;
        background-color: #25D366;
        color: white !important;
        font-weight: bold;
        padding: 10px 18px;
        border-radius: 6px;
        text-decoration: none;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown(f"""
    <div class="main-head">
        <span class="head-title">TALLY PRIME SILVER</span>
        <span class="head-sub">{CHAMBER_NAME} (F.Y. 2026-27)</span>
    </div>
""", unsafe_allow_html=True)

# Sidebar
menu = st.sidebar.radio(
    "📌 GATEWAY OF TALLY",
    ["VOUCHERS (BILLING / RECEIPT)", "SALES REGISTER", "STATEMENT / LEDGER", "CREATE MASTERS (PARTY / ITEM)"]
)

# ----------------- 1. VOUCHERS SCREEN -----------------
if menu == "VOUCHERS (BILLING / RECEIPT)":
    vch_type = st.radio("VOUCHER TYPE", ["SALES (F8)", "RECEIPT (F6)"], horizontal=True)
    is_sales = "SALES" in vch_type

    conn = get_db()
    parties = pd.read_sql("SELECT id, name, client_code, contact FROM clients ORDER BY name ASC", conn)
    items = pd.read_sql("SELECT item_name, default_rate FROM stock_items ORDER BY item_name ASC", conn)
    cur = conn.cursor()
    cnt = cur.execute(f"SELECT COUNT(*) FROM {'sales_invoices' if is_sales else 'receipts'}").fetchone()[0] + 1
    default_inv = f"SRC/{cnt:03d}"
    conn.close()

    party_dict = {f"{row['name']} (CL-{row['client_code']})": (row['id'], row['contact'], row['name']) for _, row in parties.iterrows()}
    item_dict = {row['item_name']: row['default_rate'] for _, row in items.iterrows()}

    with st.container():
        col1, col2 = st.columns([2, 1])
        with col1:
            inv_no = st.text_input("VOUCHER / INVOICE NO.", value=default_inv)
        with col2:
            v_date = st.text_input("DATE", value=datetime.now().strftime("%d-%m-%Y"))

        selected_party_label = st.selectbox("PARTY / CLIENT NAME", list(party_dict.keys()))
        selected_party_id, party_phone, party_raw_name = party_dict[selected_party_label]
        
        bal_str, bal_num = get_party_balance(selected_party_id)
        st.info(f"**CURRENT BALANCE:** {bal_str}")

        col3, col4 = st.columns([3, 1])
        with col3:
            selected_item = st.selectbox("NAME OF ITEM / SERVICE PARTICULARS", list(item_dict.keys()))
        with col4:
            def_rate = item_dict.get(selected_item, 0.0)
            amount = st.number_input("AMOUNT (INR)", value=float(def_rate), min_value=1.0, step=100.0)

        st.caption(f"**Amount In Words:** {amount_to_words(amount)}")

        if st.button("ACCEPT & SAVE VOUCHER", type="primary"):
            conn = get_db()
            cur = conn.cursor()
            try:
                if is_sales:
                    cur.execute("""INSERT INTO sales_invoices (invoice_no, invoice_date, client_id, particulars, amount, narration)
                                  VALUES (?, ?, ?, ?, ?, '')""",
                               (inv_no.upper(), v_date, selected_party_id, selected_item.upper(), amount))
                else:
                    cur.execute("""INSERT INTO receipts (receipt_no, receipt_date, client_id, amount, payment_mode, remarks)
                                  VALUES (?, ?, ?, ?, ?, '')""",
                               (inv_no.upper(), v_date, selected_party_id, amount, selected_item.upper()))
                conn.commit()
                st.success("✅ VOUCHER SUCCESSFULLY SAVED!")

                # --- WhatsApp Message Formatting ---
                clean_phone = "".join(filter(str.isdigit, str(party_phone or "")))
                if len(clean_phone) == 10:
                    clean_phone = "91" + clean_phone

                vch_title = "TAX INVOICE / BILL" if is_sales else "PAYMENT RECEIPT"
                wa_msg = (
                    f"*{CHAMBER_NAME}*\n"
                    f"{CHAMBER_PROP}\n"
                    f"{CHAMBER_ADDR}\n"
                    f"📞 {CHAMBER_PHONE}\n\n"
                    f"📄 *{vch_title}*\n"
                    f"-----------------------------\n"
                    f"👤 *Client:* {party_raw_name}\n"
                    f"🧾 *Voucher No:* {inv_no.upper()}\n"
                    f"📅 *Date:* {v_date}\n"
                    f"📌 *Particulars:* {selected_item.upper()}\n"
                    f"💰 *Amount:* ₹ {amount:,.2f}\n"
                    f"🔤 *In Words:* {amount_to_words(amount)}\n"
                    f"-----------------------------\n"
                    f"Thank you for choosing our professional services!"
                )
                encoded_msg = urllib.parse.quote(wa_msg)
                wa_url = f"https://wa.me/{clean_phone}?text={encoded_msg}" if clean_phone else f"https://wa.me/?text={encoded_msg}"

                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 Share on WhatsApp</a>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error saving voucher: {e}")
            finally:
                conn.close()

# ----------------- 2. SALES REGISTER -----------------
elif menu == "SALES REGISTER":
    st.subheader("📑 SALES REGISTER (ALL BILLS)")
    conn = get_db()
    df = pd.read_sql("""
        SELECT s.id AS ID, s.invoice_date AS DATE, s.invoice_no AS 'INVOICE NO', c.name AS 'PARTY NAME', s.particulars AS PARTICULARS, s.amount AS 'AMOUNT (₹)'
        FROM sales_invoices s
        JOIN clients c ON s.client_id = c.id
        ORDER BY s.id DESC
    """, conn)
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
        total_val = df['AMOUNT (₹)'].sum()
        st.success(f"**TOTAL BILLS:** {len(df)} | **TOTAL SALES VALUE:** ₹ {total_val:,.2f}")
    else:
        st.write("No sales invoices found.")

# ----------------- 3. STATEMENT / LEDGER -----------------
elif menu == "STATEMENT / LEDGER":
    st.subheader("📖 STATEMENT OF ACCOUNT (LEDGER)")
    conn = get_db()
    parties = pd.read_sql("SELECT id, name, client_code, contact FROM clients ORDER BY name ASC", conn)
    party_dict = {f"{row['name']} (CL-{row['client_code']})": (row['id'], row['contact'], row['name']) for _, row in parties.iterrows()}
    
    selected_p = st.selectbox("SELECT CLIENT / PARTY", list(party_dict.keys()))
    pid, pphone, pname = party_dict[selected_p]

    sales = pd.read_sql("SELECT id, invoice_date AS DATE, 'SALES' AS TYPE, invoice_no AS 'VCH NO', particulars AS PARTICULARS, amount AS 'DEBIT (₹)', 0.0 AS 'CREDIT (₹)' FROM sales_invoices WHERE client_id=?", conn, params=(pid,))
    recs = pd.read_sql("SELECT id, receipt_date AS DATE, 'RECEIPT' AS TYPE, receipt_no AS 'VCH NO', payment_mode AS PARTICULARS, 0.0 AS 'DEBIT (₹)', amount AS 'CREDIT (₹)' FROM receipts WHERE client_id=?", conn, params=(pid,))
    conn.close()

    combined = pd.concat([sales, recs]).sort_values(by="id")
    st.dataframe(combined, use_container_width=True)
    
    tot_dr = combined['DEBIT (₹)'].sum()
    tot_cr = combined['CREDIT (₹)'].sum()
    due = tot_dr - tot_cr
    bal_text = f"₹ {abs(due):,.2f} {'DR (DUE)' if due>=0 else 'CR (ADVANCE)'}"
    st.info(f"**TOTAL SALES:** ₹ {tot_dr:,.2f} | **RECEIVED:** ₹ {tot_cr:,.2f} | **NET BALANCE:** {bal_text}")

    # WhatsApp Ledger Statement Share
    clean_p = "".join(filter(str.isdigit, str(pphone or "")))
    if len(clean_p) == 10:
        clean_p = "91" + clean_p
    
    stmt_msg = (
        f"*{CHAMBER_NAME}*\n"
        f"📊 *ACCOUNT STATEMENT SUMMARY*\n"
        f"-----------------------------\n"
        f"👤 *Client:* {pname}\n"
        f"📈 *Total Billed:* ₹ {tot_dr:,.2f}\n"
        f"💵 *Total Paid:* ₹ {tot_cr:,.2f}\n"
        f"📌 *Outstanding Balance:* {bal_text}\n"
        f"-----------------------------\n"
        f"Regards,\n{CHAMBER_PROP}"
    )
    stmt_url = f"https://wa.me/{clean_p}?text={urllib.parse.quote(stmt_msg)}" if clean_p else f"https://wa.me/?text={urllib.parse.quote(stmt_msg)}"
    st.markdown(f'<a href="{stmt_url}" target="_blank" class="wa-btn">📲 Share Ledger Balance on WhatsApp</a>', unsafe_allow_html=True)

# ----------------- 4. CREATE MASTERS -----------------
elif menu == "CREATE MASTERS (PARTY / ITEM)":
    st.subheader("➕ CREATE NEW MASTER")
    opt = st.radio("SELECT MASTER TYPE", ["CLIENT / PARTY", "STOCK ITEM / SERVICE"], horizontal=True)

    if opt == "CLIENT / PARTY":
        c_name = st.text_input("PARTY / CLIENT NAME").upper()
        c_phone = st.text_input("WHATSAPP / PHONE NUMBER (10 Digits)", value="9129607278")
        c_addr = st.text_input("ADDRESS", value="STATION ROAD, MAU").upper()
        c_gstin = st.text_input("GSTIN", value="URP").upper()

        if st.button("SAVE PARTY", type="primary"):
            if c_name:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM clients")
                code = str(100001 + cur.fetchone()[0])
                cur.execute("INSERT INTO clients (client_code, name, contact, address, gstin) VALUES (?, ?, ?, ?, ?)", (code, c_name, c_phone, c_addr, c_gstin))
                conn.commit()
                conn.close()
                st.success(f"Party '{c_name}' created successfully with Code CL-{code}!")
            else:
                st.warning("Please enter a party name.")

    else:
        it_name = st.text_input("ITEM / SERVICE NAME").upper()
        it_rate = st.number_input("DEFAULT RATE (₹)", value=1000.0, step=100.0)

        if st.button("SAVE ITEM", type="primary"):
            if it_name:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("INSERT OR REPLACE INTO stock_items (item_name, default_rate) VALUES (?, ?)", (it_name, it_rate))
                conn.commit()
                conn.close()
                st.success(f"Stock Item '{it_name}' saved successfully!")
            else:
                st.warning("Please enter an item name.")
