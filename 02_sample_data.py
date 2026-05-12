"""
PROJECT 10: DELIVERY SERVICE MANAGEMENT SYSTEM
File: 02_sample_data.py
Generate 510 rows per table using Faker, output as SQL INSERT file.
"""

from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker('vi_VN')
random.seed(42)

lines = []
lines.append("USE DeliverySystem;\n")
lines.append("SET FOREIGN_KEY_CHECKS = 0;\n")
lines.append("TRUNCATE TABLE Expenses;\n")
lines.append("TRUNCATE TABLE Deliveries;\n")
lines.append("TRUNCATE TABLE Orders;\n")
lines.append("TRUNCATE TABLE Vehicles;\n")
lines.append("TRUNCATE TABLE Customers;\n")
lines.append("SET FOREIGN_KEY_CHECKS = 1;\n\n")

N = 510

# ── Helpers ──────────────────────────────────────────────────
def esc(s):
    return str(s).replace("'", "''")

def rdate(start='2023-01-01', end='2025-12-31'):
    s = datetime.strptime(start, '%Y-%m-%d')
    e = datetime.strptime(end,   '%Y-%m-%d')
    return s + timedelta(seconds=random.randint(0, int((e-s).total_seconds())))

# ── 1. Customers (510) ────────────────────────────────────────
lines.append("-- ============================================================\n")
lines.append("-- INSERT: Customers\n")
lines.append("-- ============================================================\n")
lines.append("INSERT INTO Customers (CustomerName, PhoneNumber, Address, Email, CreatedAt) VALUES\n")

vn_prefixes = ['032','033','034','035','036','037','038','039',
               '086','096','097','098','070','079','077','076','078',
               '089','090','093','058','056']
used_phones = set()

customer_rows = []
for i in range(1, N+1):
    name = esc(fake.name())
    while True:
        phone = random.choice(vn_prefixes) + ''.join([str(random.randint(0,9)) for _ in range(7)])
        if phone not in used_phones:
            used_phones.add(phone)
            break
    addr = esc(fake.address().replace('\n', ', '))
    email = f"customer{i}@{'gmail.com' if i%2==0 else 'yahoo.com'}"
    dt = rdate('2022-01-01','2024-06-30').strftime('%Y-%m-%d %H:%M:%S')
    customer_rows.append(f"  ('{name}', '{phone}', '{addr}', '{email}', '{dt}')")

lines.append(',\n'.join(customer_rows) + ';\n\n')

# ── 2. Vehicles (510) ─────────────────────────────────────────
lines.append("-- ============================================================\n")
lines.append("-- INSERT: Vehicles\n")
lines.append("-- ============================================================\n")
lines.append("INSERT INTO Vehicles (VehicleType, LicensePlate, Capacity, Status, CreatedAt) VALUES\n")

vtypes   = ['Motorbike','Van','Truck','Electric Bike']
vweights = {'Motorbike':50,'Van':500,'Truck':5000,'Electric Bike':30}
vstatus  = ['Available','In Use','Maintenance']
used_plates = set()

provinces = ['29','30','31','33','36','37','38','43','47','48','49',
             '51','52','59','60','61','63','65','66','67','68','69',
             '71','72','73','74','75','76','77','78','79','80','81',
             '82','83','84','85','86','88','89','90','92','93','94',
             '95','97','98','99']

vehicle_rows = []
for i in range(1, N+1):
    vtype = random.choice(vtypes)
    cap   = round(vweights[vtype] * random.uniform(0.5, 1.0), 2)
    st    = random.choices(vstatus, weights=[60,30,10])[0]
    dt    = rdate('2020-01-01','2024-01-01').strftime('%Y-%m-%d %H:%M:%S')
    while True:
        prov   = random.choice(provinces)
        letter = random.choice('ABCDEFGHJKLMNPSTUVXY')
        num    = ''.join([str(random.randint(0,9)) for _ in range(5)])
        plate  = f"{prov}{letter}-{num[:3]}.{num[3:]}"
        if plate not in used_plates:
            used_plates.add(plate)
            break
    vehicle_rows.append(f"  ('{vtype}', '{plate}', {cap}, '{st}', '{dt}')")

lines.append(',\n'.join(vehicle_rows) + ';\n\n')

# ── 3. Orders (510) ───────────────────────────────────────────
lines.append("-- ============================================================\n")
lines.append("-- INSERT: Orders\n")
lines.append("-- ============================================================\n")
lines.append("INSERT INTO Orders (CustomerID, OrderDate, Status, TotalWeight, Notes) VALUES\n")

ostatus = ['Pending','Assigned','In Transit','Completed','Cancelled']
oweights= [5,15,30,40,10]
notes_pool = [
    'Handle with care','Fragile items','Refrigerate during transit',
    'Call before delivery','Leave at door','Signature required',
    'No special instructions','Urgent delivery','Heavy package',
    'Contains electronics','Deliver to reception','Weekend delivery ok',
    None, None, None
]

order_rows = []
order_dates = {}
for i in range(1, N+1):
    cid   = random.randint(1, N)
    odate = rdate('2023-01-01','2025-06-30')
    st    = random.choices(ostatus, weights=oweights)[0]
    w     = round(random.uniform(0.5, 200), 2)
    note  = random.choice(notes_pool)
    note_val = f"'{esc(note)}'" if note else 'NULL'
    order_dates[i] = odate
    order_rows.append(
        f"  ({cid}, '{odate.strftime('%Y-%m-%d %H:%M:%S')}', '{st}', {w}, {note_val})"
    )

lines.append(',\n'.join(order_rows) + ';\n\n')

# ── 4. Deliveries (510) ───────────────────────────────────────
lines.append("-- ============================================================\n")
lines.append("-- INSERT: Deliveries\n")
lines.append("-- ============================================================\n")
lines.append("INSERT INTO Deliveries (OrderID, VehicleID, DeliveryDate, DriverName, Status, CreatedAt) VALUES\n")

dstatus   = ['Scheduled','In Transit','Delivered','Failed']
dweights  = [10,15,65,10]
driver_pool = [fake.name() for _ in range(80)]

delivery_rows = []
for i in range(1, N+1):
    vid   = random.randint(1, N)
    odate = order_dates[i]
    cdate = odate + timedelta(hours=random.randint(1, 12))
    ddate = cdate + timedelta(hours=random.randint(2, 72))
    st    = random.choices(dstatus, weights=dweights)[0]
    driver = esc(random.choice(driver_pool))
    delivery_rows.append(
        f"  ({i}, {vid}, '{ddate.strftime('%Y-%m-%d %H:%M:%S')}', "
        f"'{driver}', '{st}', '{cdate.strftime('%Y-%m-%d %H:%M:%S')}')"
    )

lines.append(',\n'.join(delivery_rows) + ';\n\n')

# ── 5. Expenses (510) ─────────────────────────────────────────
lines.append("-- ============================================================\n")
lines.append("-- INSERT: Expenses\n")
lines.append("-- ============================================================\n")
lines.append("INSERT INTO Expenses (DeliveryID, ExpenseType, Amount, RecordedAt, Description) VALUES\n")

etypes = ['Fuel','Toll','Handling','Packaging','Other']
edescs = {
    'Fuel':      ['Petrol refill','Diesel fill-up','Electric charge','Fuel top-up'],
    'Toll':      ['Highway toll','Bridge fee','City toll gate','Tunnel fee'],
    'Handling':  ['Loading fee','Unloading fee','Manual handling','Crane usage'],
    'Packaging': ['Bubble wrap','Box cost','Tape & labels','Packing service'],
    'Other':     ['Parking fee','Driver meal','Overtime fee','Emergency fee'],
}
eranges = {'Fuel':(20000,500000),'Toll':(5000,100000),
           'Handling':(10000,200000),'Packaging':(5000,80000),'Other':(5000,150000)}

expense_rows = []
for i in range(1, N+1):
    did   = random.randint(1, N)
    etype = random.choice(etypes)
    lo, hi = eranges[etype]
    amt   = round(random.randint(lo // 1000, hi // 1000) * 1000, 0)
    desc  = esc(random.choice(edescs[etype]))
    rdate_val = rdate('2023-01-01','2025-06-30').strftime('%Y-%m-%d %H:%M:%S')
    expense_rows.append(
        f"  ({did}, '{etype}', {amt}, '{rdate_val}', '{desc}')"
    )

lines.append(',\n'.join(expense_rows) + ';\n\n')

# Write output
with open('/home/claude/02_sample_data.sql', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Done! SQL file written: 02_sample_data.sql")
print(f"Rows per table: {N}")
