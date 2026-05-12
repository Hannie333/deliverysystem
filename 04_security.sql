-- ============================================================
-- PROJECT 10: DELIVERY SERVICE MANAGEMENT SYSTEM
-- File: 04_security.sql
-- Users, Roles, GRANT, Backup Procedure
-- ============================================================
USE DeliverySystem;

-- ============================================================
-- Drop users if they exist (for clean re-run)
-- ============================================================
DROP USER IF EXISTS 'manager_user'@'localhost';
DROP USER IF EXISTS 'dispatcher_user'@'localhost';
DROP USER IF EXISTS 'accountant_user'@'localhost';

-- ============================================================
-- Create users
-- ============================================================
CREATE USER 'manager_user'@'localhost'   IDENTIFIED BY 'Manager@2025!';
CREATE USER 'dispatcher_user'@'localhost' IDENTIFIED BY 'Dispatch@2025!';
CREATE USER 'accountant_user'@'localhost' IDENTIFIED BY 'Account@2025!';

-- ============================================================
-- ROLE 1: Manager — Full access
-- ============================================================
GRANT ALL PRIVILEGES ON DeliverySystem.* TO 'manager_user'@'localhost';

-- ============================================================
-- ROLE 2: Dispatcher — Manage orders & deliveries only
-- ============================================================
GRANT SELECT, INSERT, UPDATE ON DeliverySystem.Customers   TO 'dispatcher_user'@'localhost';
GRANT SELECT, INSERT, UPDATE ON DeliverySystem.Orders      TO 'dispatcher_user'@'localhost';
GRANT SELECT, INSERT, UPDATE ON DeliverySystem.Deliveries  TO 'dispatcher_user'@'localhost';
GRANT SELECT                 ON DeliverySystem.Vehicles    TO 'dispatcher_user'@'localhost';
GRANT SELECT                 ON DeliverySystem.vw_CurrentDeliveries  TO 'dispatcher_user'@'localhost';
GRANT SELECT                 ON DeliverySystem.vw_OutstandingOrders  TO 'dispatcher_user'@'localhost';
GRANT EXECUTE                ON PROCEDURE DeliverySystem.sp_CreateOrderAndAssign TO 'dispatcher_user'@'localhost';
GRANT EXECUTE                ON PROCEDURE DeliverySystem.sp_CompleteDelivery     TO 'dispatcher_user'@'localhost';
GRANT EXECUTE                ON PROCEDURE DeliverySystem.sp_AddCustomer          TO 'dispatcher_user'@'localhost';

-- ============================================================
-- ROLE 3: Accountant — Manage expenses and reports only
-- ============================================================
GRANT SELECT                 ON DeliverySystem.Orders     TO 'accountant_user'@'localhost';
GRANT SELECT                 ON DeliverySystem.Deliveries TO 'accountant_user'@'localhost';
GRANT SELECT, INSERT, UPDATE ON DeliverySystem.Expenses   TO 'accountant_user'@'localhost';
GRANT SELECT                 ON DeliverySystem.vw_CostPerOrder          TO 'accountant_user'@'localhost';
GRANT SELECT                 ON DeliverySystem.vw_MonthlyExpenseSummary TO 'accountant_user'@'localhost';
GRANT SELECT                 ON DeliverySystem.vw_VehiclePerformance    TO 'accountant_user'@'localhost';
GRANT EXECUTE                ON PROCEDURE DeliverySystem.sp_RecordExpense TO 'accountant_user'@'localhost';
GRANT EXECUTE                ON FUNCTION  DeliverySystem.fn_TotalExpenseByOrder TO 'accountant_user'@'localhost';
GRANT EXECUTE                ON FUNCTION  DeliverySystem.fn_AvgDeliveryCostByVehicle TO 'accountant_user'@'localhost';

FLUSH PRIVILEGES;

-- ============================================================
-- Query Optimization: EXPLAIN demonstration
-- ============================================================
-- These are the EXPLAIN queries to include in the report:

-- EXPLAIN 1: Without index (conceptual — before adding index)
-- EXPLAIN SELECT * FROM Orders WHERE CustomerID = 100;

-- EXPLAIN 2: With index (after CREATE INDEX idx_orders_customer)
-- EXPLAIN SELECT * FROM Orders WHERE CustomerID = 100;

-- EXPLAIN 3: Delivery lookup
-- EXPLAIN SELECT * FROM Deliveries WHERE VehicleID = 50 AND Status = 'Scheduled';

-- EXPLAIN 4: Customer phone lookup
-- EXPLAIN SELECT * FROM Customers WHERE PhoneNumber = '0987654321';

