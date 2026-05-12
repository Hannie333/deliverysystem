"""
PROJECT 10: DELIVERY SERVICE MANAGEMENT SYSTEM
File: 05_python_app.py
Console Application — Full CRUD + Reports
NEU - College of Technology | DATCOM Lab
"""
#!/usr/bin/env python3
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import sys

# ─────────────────────────────────────────────────────────────
# Database connection configuration
# Update DB_CONFIG with your MySQL credentials before running
# ─────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",           # ← change to your MySQL user
    "password": "30092006",  # ← change to your MySQL password
    "database": "DeliverySystem",
    "charset":  "utf8mb4",
}

PINK  = "\033[38;5;212m"
CYAN  = "\033[38;5;51m"
RESET = "\033[0m"
BOLD  = "\033[1m"
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW= "\033[93m"

def header(title):
    print(f"\n{CYAN}{'═'*60}{RESET}")
    print(f"{PINK}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{'═'*60}{RESET}")

def success(msg):  print(f"{GREEN}✓ {msg}{RESET}")
def error(msg):    print(f"{RED}✗ {msg}{RESET}")
def info(msg):     print(f"{YELLOW}➜ {msg}{RESET}")

def print_table(cursor):
    """Pretty-print a query result as an ASCII table."""
    rows = cursor.fetchall()
    cols = [desc[0] for desc in cursor.description] if cursor.description else []
    if not rows:
        info("No records found.")
        return
    # Column widths
    widths = [max(len(str(c)), max(len(str(r[i])) for r in rows))
              for i, c in enumerate(cols)]
    sep = "+" + "+".join("-"*(w+2) for w in widths) + "+"
    print(f"{CYAN}{sep}{RESET}")
    header_row = "|" + "|".join(f" {BOLD}{PINK}{c.ljust(w)}{RESET} "
                                 for c, w in zip(cols, widths)) + "|"
    print(header_row)
    print(f"{CYAN}{sep}{RESET}")
    for row in rows:
        print("|" + "|".join(f" {str(v).ljust(w)} " for v, w in zip(row, widths)) + "|")
    print(f"{CYAN}{sep}{RESET}")
    print(f"{YELLOW}  Total: {len(rows)} row(s){RESET}\n")

# ─────────────────────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────────────────────
def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        error(f"Connection failed: {e}")
        sys.exit(1)

# ─────────────────────────────────────────────────────────────
# MODULE 1: Customer Management
# ─────────────────────────────────────────────────────────────
def add_customer(conn):
    header("ADD NEW CUSTOMER")
    name    = input("  Customer Name : ").strip()
    phone   = input("  Phone Number  : ").strip()
    address = input("  Address       : ").strip()
    email   = input("  Email         : ").strip() or None
    try:
        cur = conn.cursor()
        cur.callproc("sp_AddCustomer", [name, phone, address, email, 0])
        conn.commit()
        for result in cur.stored_results():
            print_table(result)
        success("Customer added successfully.")
    except Error as e:
        error(f"Failed: {e}")

def view_customers(conn):
    header("ALL CUSTOMERS")
    cur = conn.cursor()
    cur.execute("""
        SELECT CustomerID, CustomerName, PhoneNumber, Address, Email,
               DATE_FORMAT(CreatedAt,'%Y-%m-%d') AS Joined
        FROM Customers ORDER BY CustomerID DESC LIMIT 20
    """)
    print_table(cur)

def search_customer(conn):
    header("SEARCH CUSTOMER")
    keyword = input("  Enter name or phone: ").strip()
    cur = conn.cursor()
    cur.execute("""
        SELECT CustomerID, CustomerName, PhoneNumber, Address,
               fn_CustomerOrderCount(CustomerID) AS TotalOrders
        FROM Customers
        WHERE CustomerName LIKE %s OR PhoneNumber LIKE %s
        LIMIT 15
    """, (f"%{keyword}%", f"%{keyword}%"))
    print_table(cur)

# ─────────────────────────────────────────────────────────────
# MODULE 2: Order & Delivery Management
# ─────────────────────────────────────────────────────────────
def create_order(conn):
    header("CREATE ORDER & AUTO-ASSIGN VEHICLE")
    cid    = int(input("  Customer ID   : "))
    weight = float(input("  Weight (kg)   : "))
    notes  = input("  Notes         : ").strip() or None
    driver = input("  Driver Name   : ").strip()
    try:
        cur = conn.cursor()
        cur.callproc("sp_CreateOrderAndAssign", [cid, weight, notes, driver, 0, 0])
        conn.commit()
        for result in cur.stored_results():
            print_table(result)
    except Error as e:
        error(f"Failed: {e}")

def view_outstanding_orders(conn):
    header("OUTSTANDING ORDERS")
    cur = conn.cursor()
    cur.execute("SELECT * FROM vw_OutstandingOrders LIMIT 20")
    print_table(cur)

def complete_delivery(conn):
    header("COMPLETE A DELIVERY")
    did = int(input("  Delivery ID: "))
    try:
        cur = conn.cursor()
        cur.callproc("sp_CompleteDelivery", [did])
        conn.commit()
        for result in cur.stored_results():
            print_table(result)
    except Error as e:
        error(f"Failed: {e}")

def view_current_deliveries(conn):
    header("CURRENT ACTIVE DELIVERIES")
    cur = conn.cursor()
    cur.execute("SELECT * FROM vw_CurrentDeliveries LIMIT 20")
    print_table(cur)

# ─────────────────────────────────────────────────────────────
# MODULE 3: Expense Management
# ─────────────────────────────────────────────────────────────
def add_expense(conn):
    header("RECORD EXPENSE")
    did   = int(input("  Delivery ID       : "))
    print("  Types: Fuel | Toll | Handling | Packaging | Other")
    etype = input("  Expense Type      : ").strip()
    amt   = float(input("  Amount (VND)      : "))
    desc  = input("  Description       : ").strip() or None
    try:
        cur = conn.cursor()
        cur.callproc("sp_RecordExpense", [did, etype, amt, desc])
        conn.commit()
        for result in cur.stored_results():
            print_table(result)
    except Error as e:
        error(f"Failed: {e}")

def view_expenses_by_delivery(conn):
    header("EXPENSES BY DELIVERY")
    did = int(input("  Delivery ID: "))
    cur = conn.cursor()
    cur.execute("""
        SELECT ExpenseID, ExpenseType,
               FORMAT(Amount,0) AS Amount_VND,
               Description,
               DATE_FORMAT(RecordedAt,'%Y-%m-%d %H:%i') AS RecordedAt
        FROM Expenses
        WHERE DeliveryID = %s ORDER BY RecordedAt
    """, (did,))
    print_table(cur)
    cur.execute("SELECT FORMAT(fn_TotalExpenseByOrder(%s), 0) AS TotalOrderExpense", (did,))
    # Get order from delivery
    cur2 = conn.cursor()
    cur2.execute("SELECT OrderID FROM Deliveries WHERE DeliveryID=%s", (did,))
    row = cur2.fetchone()
    if row:
        cur3 = conn.cursor()
        cur3.execute("SELECT FORMAT(fn_TotalExpenseByOrder(%s), 0) AS `Total Expense (VND)`", (row[0],))
        print_table(cur3)

# ─────────────────────────────────────────────────────────────
# MODULE 4: Reports
# ─────────────────────────────────────────────────────────────
def report_cost_per_order(conn):
    header("REPORT: COST PER ORDER (Top 20)")
    cur = conn.cursor()
    cur.execute("""
        SELECT OrderID, CustomerName,
               DATE_FORMAT(OrderDate,'%Y-%m-%d') AS OrderDate,
               OrderStatus,
               FORMAT(TotalExpense,0) AS TotalExpense_VND,
               ExpenseCount
        FROM vw_CostPerOrder
        ORDER BY TotalExpense DESC LIMIT 20
    """)
    print_table(cur)

def report_vehicle_performance(conn):
    header("REPORT: VEHICLE PERFORMANCE")
    cur = conn.cursor()
    cur.execute("""
        SELECT VehicleType, LicensePlate, VehicleStatus,
               TotalDeliveries, Completed, Failed,
               FORMAT(TotalExpenses,0) AS TotalExpenses_VND,
               FORMAT(fn_AvgDeliveryCostByVehicle(VehicleID),0) AS AvgCost_VND
        FROM vw_VehiclePerformance
        ORDER BY TotalDeliveries DESC LIMIT 20
    """)
    print_table(cur)

def report_monthly_expenses(conn):
    header("REPORT: MONTHLY EXPENSE SUMMARY")
    cur = conn.cursor()
    cur.execute("""
        SELECT Year, Month, ExpenseType,
               TotalRecords,
               FORMAT(TotalAmount,0) AS TotalAmount_VND,
               FORMAT(AvgAmount,0)   AS AvgAmount_VND
        FROM vw_MonthlyExpenseSummary
        ORDER BY Year DESC, Month DESC, ExpenseType
        LIMIT 30
    """)
    print_table(cur)

def report_customer_history(conn):
    header("REPORT: CUSTOMER ORDER HISTORY")
    cid = int(input("  Customer ID: "))
    cur = conn.cursor()
    cur.callproc("sp_CustomerOrderHistory", [cid])
    for result in cur.stored_results():
        print_table(result)

def report_top_customers(conn):
    header("REPORT: TOP 10 CUSTOMERS BY ORDER COUNT")
    cur = conn.cursor()
    cur.execute("""
        SELECT c.CustomerID, c.CustomerName, c.PhoneNumber,
               COUNT(o.OrderID) AS TotalOrders,
               SUM(CASE WHEN o.Status='Completed' THEN 1 ELSE 0 END) AS Completed,
               FORMAT(SUM(fn_TotalExpenseByOrder(o.OrderID)),0) AS TotalSpent_VND
        FROM Customers c
        JOIN Orders o ON c.CustomerID = o.CustomerID
        GROUP BY c.CustomerID, c.CustomerName, c.PhoneNumber
        ORDER BY TotalOrders DESC LIMIT 10
    """)
    print_table(cur)

# ─────────────────────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────────────────────
def main():
    conn = get_connection()
    success("Connected to DeliverySystem database.")

    menu = {
        "1":  ("Add Customer",              add_customer),
        "2":  ("View Customers (last 20)",   view_customers),
        "3":  ("Search Customer",            search_customer),
        "4":  ("Create Order & Auto-Assign", create_order),
        "5":  ("View Outstanding Orders",    view_outstanding_orders),
        "6":  ("View Active Deliveries",     view_current_deliveries),
        "7":  ("Complete a Delivery",        complete_delivery),
        "8":  ("Record Expense",             add_expense),
        "9":  ("View Expenses by Delivery",  view_expenses_by_delivery),
        "10": ("Report: Cost Per Order",     report_cost_per_order),
        "11": ("Report: Vehicle Performance",report_vehicle_performance),
        "12": ("Report: Monthly Expenses",   report_monthly_expenses),
        "13": ("Report: Customer History",   report_customer_history),
        "14": ("Report: Top Customers",      report_top_customers),
        "0":  ("Exit",                       None),
    }

    while True:
        print(f"\n{CYAN}{'═'*60}{RESET}")
        print(f"{PINK}{BOLD}  🚚 DELIVERY MANAGEMENT SYSTEM — MAIN MENU{RESET}")
        print(f"{CYAN}{'═'*60}{RESET}")
        for key, (label, _) in menu.items():
            color = RED if key == "0" else YELLOW
            print(f"  {color}[{key:>2}]{RESET} {label}")
        print(f"{CYAN}{'─'*60}{RESET}")
        choice = input(f"  {PINK}Choose option: {RESET}").strip()

        if choice not in menu:
            error("Invalid option. Try again.")
            continue
        label, fn = menu[choice]
        if fn is None:
            info("Goodbye! 👋")
            break
        try:
            fn(conn)
        except KeyboardInterrupt:
            print()
        except Exception as e:
            error(f"Unexpected error: {e}")

    conn.close()

if __name__ == "__main__":
    main()
