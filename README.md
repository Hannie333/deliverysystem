# Delivery Service Management System
**PROJECT 10 — NEU College of Technology | DATCOM Lab**

---

## File Structure

```
deliverysystem/
├── 01_schema.sql          ← Create database & all 5 tables
├── 02_sample_data.sql     ← 510 rows × 5 tables (auto-generated)
├── 02_sample_data.py      ← Python Faker script to regenerate data
├── 03_advanced_objects.sql ← Indexes, Views, Procedures, Functions, Triggers
├── 04_security.sql        ← Users, GRANT, roles
├── 05_python_app.py       ← Console application (full CRUD + reports)
└── README.md
```

---

## Quick Start (Run in order)

```bash
# 1. Load schema
mysql -u root -p < 01_schema.sql

# 2. Load sample data (510 rows per table)
mysql -u root -p < 02_sample_data.sql

# 3. Load advanced objects
mysql -u root -p < 03_advanced_objects.sql

# 4. Load security & users
mysql -u root -p < 04_security.sql

# 5. Run Python app (update DB_CONFIG first)
pip install mysql-connector-python faker
python 05_python_app.py
```

---

## Database Design

### Tables

| Table | Primary Key | Description |
|-------|------------|-------------|
| Customers | CustomerID | Stores customer profiles |
| Vehicles | VehicleID | Fleet registry |
| Orders | OrderID | Customer delivery orders |
| Deliveries | DeliveryID | Assigned delivery records |
| Expenses | ExpenseID | Per-delivery cost tracking |

### Relationships
- 1 Customer → many Orders (1-N)
- 1 Order → 1 Delivery (1-1)
- 1 Vehicle → many Deliveries (1-N)
- 1 Delivery → many Expenses (1-N)

---

## Advanced Objects Summary

### Indexes (11 total)
- Orders: CustomerID, Status, OrderDate
- Deliveries: VehicleID, Status, DeliveryDate
- Expenses: DeliveryID, ExpenseType
- Customers: PhoneNumber, CustomerName
- Vehicles: LicensePlate, Status

### Views (5 total)
| View | Purpose |
|------|---------|
| vw_CurrentDeliveries | Active in-progress deliveries |
| vw_CostPerOrder | Total expense per order |
| vw_VehiclePerformance | Delivery stats per vehicle |
| vw_OutstandingOrders | Pending/assigned orders |
| vw_MonthlyExpenseSummary | Monthly cost by type |

### Stored Procedures (5 total)
| Procedure | Description |
|-----------|------------|
| sp_AddCustomer | Insert new customer |
| sp_CreateOrderAndAssign | Create order + auto-assign vehicle |
| sp_RecordExpense | Log a delivery expense |
| sp_CompleteDelivery | Mark delivered, free vehicle |
| sp_CustomerOrderHistory | Full history for one customer |

### User Defined Functions (4 total)
| Function | Returns |
|----------|---------|
| fn_AvgDeliveryCostByVehicle(id) | Avg expense per delivery |
| fn_DeliveryCountByVehicle(id) | Total deliveries |
| fn_TotalExpenseByOrder(id) | Sum of all expenses |
| fn_CustomerOrderCount(id) | Number of orders |

### Triggers (4 total)
| Trigger | Event | Action |
|---------|-------|--------|
| trg_AfterDeliveryUpdate | AFTER UPDATE Deliveries | Auto-complete order, free vehicle |
| trg_AfterDeliveryInsert | AFTER INSERT Deliveries | Set vehicle In Use |
| trg_BeforeExpenseInsert | BEFORE INSERT Expenses | Validate delivery + amount |
| trg_BeforeDeliveryInsert | BEFORE INSERT Deliveries | Validate delivery date |

---

## Database Users & Roles

| User | Role | Permissions |
|------|------|------------|
| manager_user | Manager | ALL PRIVILEGES |
| dispatcher_user | Dispatcher | Orders, Deliveries, Customers |
| accountant_user | Accountant | Expenses, Reports |

---

## Python App Features

- Add/Search/View Customers
- Create Orders with auto vehicle assignment
- Complete Deliveries (triggers status updates)
- Record & View Expenses
- 5 Report modules (Cost, Vehicle, Monthly, Customer, Top 10)
- Color-coded terminal UI (pink & cyan theme)
- Error handling with try/except for all DB calls

