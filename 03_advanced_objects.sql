-- ============================================================
-- PROJECT 10: DELIVERY SERVICE MANAGEMENT SYSTEM
-- File: 03_advanced_objects.sql
-- Indexes | Views | Stored Procedures | Functions | Triggers
-- ============================================================
USE DeliverySystem;

-- ============================================================
-- SECTION 1: INDEXES
-- ============================================================

-- Speed up order lookup by customer and status
CREATE INDEX idx_orders_customer  ON Orders(CustomerID);
CREATE INDEX idx_orders_status    ON Orders(Status);
CREATE INDEX idx_orders_date      ON Orders(OrderDate);

-- Speed up delivery lookup by vehicle and status
CREATE INDEX idx_deliveries_vehicle ON Deliveries(VehicleID);
CREATE INDEX idx_deliveries_status  ON Deliveries(Status);
CREATE INDEX idx_deliveries_date    ON Deliveries(DeliveryDate);

-- Speed up expense lookup by delivery
CREATE INDEX idx_expenses_delivery ON Expenses(DeliveryID);
CREATE INDEX idx_expenses_type     ON Expenses(ExpenseType);

-- Speed up customer search by phone and name
CREATE INDEX idx_customers_phone ON Customers(PhoneNumber);
CREATE INDEX idx_customers_name  ON Customers(CustomerName);

-- Speed up vehicle lookup by license plate and status
CREATE INDEX idx_vehicles_plate  ON Vehicles(LicensePlate);
CREATE INDEX idx_vehicles_status ON Vehicles(Status);


-- ============================================================
-- SECTION 2: VIEWS
-- ============================================================

-- View 1: Current Delivery Schedule (active deliveries)
CREATE OR REPLACE VIEW vw_CurrentDeliveries AS
SELECT
    d.DeliveryID,
    o.OrderID,
    c.CustomerName,
    c.PhoneNumber,
    v.VehicleType,
    v.LicensePlate,
    d.DriverName,
    d.DeliveryDate,
    d.Status       AS DeliveryStatus,
    o.Status       AS OrderStatus,
    o.TotalWeight
FROM Deliveries d
JOIN Orders   o ON d.OrderID   = o.OrderID
JOIN Customers c ON o.CustomerID = c.CustomerID
JOIN Vehicles  v ON d.VehicleID  = v.VehicleID
WHERE d.Status IN ('Scheduled','In Transit');


-- View 2: Cost Per Order summary
CREATE OR REPLACE VIEW vw_CostPerOrder AS
SELECT
    o.OrderID,
    c.CustomerName,
    o.OrderDate,
    o.Status       AS OrderStatus,
    d.DeliveryID,
    d.DriverName,
    COALESCE(SUM(e.Amount), 0)          AS TotalExpense,
    COUNT(e.ExpenseID)                  AS ExpenseCount
FROM Orders o
JOIN Customers  c ON o.CustomerID  = c.CustomerID
LEFT JOIN Deliveries d ON o.OrderID    = d.OrderID
LEFT JOIN Expenses   e ON d.DeliveryID = e.DeliveryID
GROUP BY o.OrderID, c.CustomerName, o.OrderDate, o.Status,
         d.DeliveryID, d.DriverName;


-- View 3: Vehicle Performance
CREATE OR REPLACE VIEW vw_VehiclePerformance AS
SELECT
    v.VehicleID,
    v.VehicleType,
    v.LicensePlate,
    v.Status        AS VehicleStatus,
    COUNT(DISTINCT d.DeliveryID)          AS TotalDeliveries,
    SUM(CASE WHEN d.Status='Delivered' THEN 1 ELSE 0 END) AS Completed,
    SUM(CASE WHEN d.Status='Failed'    THEN 1 ELSE 0 END) AS Failed,
    COALESCE(SUM(e.Amount), 0)            AS TotalExpenses
FROM Vehicles v
LEFT JOIN Deliveries d ON v.VehicleID   = d.VehicleID
LEFT JOIN Expenses   e ON d.DeliveryID  = e.DeliveryID
GROUP BY v.VehicleID, v.VehicleType, v.LicensePlate, v.Status;


-- View 4: Outstanding Orders (Pending or Assigned, not yet delivered)
CREATE OR REPLACE VIEW vw_OutstandingOrders AS
SELECT
    o.OrderID,
    c.CustomerName,
    c.PhoneNumber,
    o.OrderDate,
    o.Status,
    o.TotalWeight,
    DATEDIFF(NOW(), o.OrderDate) AS DaysSinceOrder
FROM Orders o
JOIN Customers c ON o.CustomerID = c.CustomerID
WHERE o.Status IN ('Pending','Assigned')
ORDER BY o.OrderDate ASC;


-- View 5: Monthly Revenue Report
CREATE OR REPLACE VIEW vw_MonthlyExpenseSummary AS
SELECT
    YEAR(e.RecordedAt)  AS Year,
    MONTH(e.RecordedAt) AS Month,
    e.ExpenseType,
    COUNT(*)            AS TotalRecords,
    SUM(e.Amount)       AS TotalAmount,
    AVG(e.Amount)       AS AvgAmount,
    MAX(e.Amount)       AS MaxAmount
FROM Expenses e
GROUP BY YEAR(e.RecordedAt), MONTH(e.RecordedAt), e.ExpenseType
ORDER BY Year, Month, ExpenseType;


-- ============================================================
-- SECTION 3: STORED PROCEDURES
-- ============================================================

DELIMITER $$

-- Procedure 1: Add a new customer
CREATE PROCEDURE sp_AddCustomer(
    IN  p_name    VARCHAR(100),
    IN  p_phone   VARCHAR(15),
    IN  p_address VARCHAR(255),
    IN  p_email   VARCHAR(100),
    OUT p_new_id  INT
)
BEGIN
    INSERT INTO Customers(CustomerName, PhoneNumber, Address, Email)
    VALUES (p_name, p_phone, p_address, p_email);
    SET p_new_id = LAST_INSERT_ID();
    SELECT CONCAT('Customer added with ID: ', p_new_id) AS Result;
END$$


-- Procedure 2: Create order and assign vehicle automatically
CREATE PROCEDURE sp_CreateOrderAndAssign(
    IN  p_customer_id  INT,
    IN  p_weight       DECIMAL(8,2),
    IN  p_notes        TEXT,
    IN  p_driver_name  VARCHAR(100),
    OUT p_order_id     INT,
    OUT p_delivery_id  INT
)
BEGIN
    DECLARE v_vehicle_id INT DEFAULT NULL;
    DECLARE v_delivery_date DATETIME;

    -- Auto-select an available vehicle with enough capacity
    SELECT VehicleID INTO v_vehicle_id
    FROM Vehicles
    WHERE Status = 'Available' AND Capacity >= p_weight
    ORDER BY Capacity ASC
    LIMIT 1;

    IF v_vehicle_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'No available vehicle with sufficient capacity.';
    END IF;

    SET v_delivery_date = DATE_ADD(NOW(), INTERVAL 1 DAY);

    -- Create order
    INSERT INTO Orders(CustomerID, Status, TotalWeight, Notes)
    VALUES (p_customer_id, 'Assigned', p_weight, p_notes);
    SET p_order_id = LAST_INSERT_ID();

    -- Create delivery
    INSERT INTO Deliveries(OrderID, VehicleID, DeliveryDate, DriverName, Status)
    VALUES (p_order_id, v_vehicle_id, v_delivery_date, p_driver_name, 'Scheduled');
    SET p_delivery_id = LAST_INSERT_ID();

    -- Mark vehicle as In Use
    UPDATE Vehicles SET Status = 'In Use' WHERE VehicleID = v_vehicle_id;

    SELECT CONCAT('Order #', p_order_id, ' created. Delivery #', p_delivery_id,
                  ' assigned to Vehicle #', v_vehicle_id) AS Result;
END$$


-- Procedure 3: Record an expense for a delivery
CREATE PROCEDURE sp_RecordExpense(
    IN p_delivery_id  INT,
    IN p_type         ENUM('Fuel','Toll','Handling','Packaging','Other'),
    IN p_amount       DECIMAL(12,2),
    IN p_description  VARCHAR(255)
)
BEGIN
    IF NOT EXISTS (SELECT 1 FROM Deliveries WHERE DeliveryID = p_delivery_id) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Delivery ID does not exist.';
    END IF;

    INSERT INTO Expenses(DeliveryID, ExpenseType, Amount, Description)
    VALUES (p_delivery_id, p_type, p_amount, p_description);

    SELECT CONCAT('Expense recorded: ', p_type, ' = ', FORMAT(p_amount,0), ' VND') AS Result;
END$$


-- Procedure 4: Complete a delivery (updates status + frees vehicle)
CREATE PROCEDURE sp_CompleteDelivery(
    IN p_delivery_id INT
)
BEGIN
    DECLARE v_order_id   INT;
    DECLARE v_vehicle_id INT;
    DECLARE v_cur_status VARCHAR(20);

    SELECT OrderID, VehicleID, Status
      INTO v_order_id, v_vehicle_id, v_cur_status
    FROM Deliveries WHERE DeliveryID = p_delivery_id;

    IF v_cur_status = 'Delivered' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Delivery is already marked as Delivered.';
    END IF;

    UPDATE Deliveries SET Status = 'Delivered' WHERE DeliveryID = p_delivery_id;
    UPDATE Orders     SET Status = 'Completed'  WHERE OrderID   = v_order_id;
    UPDATE Vehicles   SET Status = 'Available'  WHERE VehicleID = v_vehicle_id;

    SELECT 'Delivery completed successfully.' AS Result;
END$$


-- Procedure 5: Generate customer order history report
CREATE PROCEDURE sp_CustomerOrderHistory(
    IN p_customer_id INT
)
BEGIN
    SELECT
        o.OrderID,
        o.OrderDate,
        o.Status       AS OrderStatus,
        o.TotalWeight,
        d.DeliveryID,
        d.DriverName,
        d.DeliveryDate,
        d.Status       AS DeliveryStatus,
        COALESCE(SUM(e.Amount),0) AS TotalExpenses
    FROM Orders o
    LEFT JOIN Deliveries d ON o.OrderID    = d.OrderID
    LEFT JOIN Expenses   e ON d.DeliveryID = e.DeliveryID
    WHERE o.CustomerID = p_customer_id
    GROUP BY o.OrderID, o.OrderDate, o.Status, o.TotalWeight,
             d.DeliveryID, d.DriverName, d.DeliveryDate, d.Status
    ORDER BY o.OrderDate DESC;
END$$

DELIMITER ;


-- ============================================================
-- SECTION 4: USER DEFINED FUNCTIONS
-- ============================================================

DELIMITER $$

-- Function 1: Average delivery cost for a vehicle
CREATE FUNCTION fn_AvgDeliveryCostByVehicle(p_vehicle_id INT)
RETURNS DECIMAL(12,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE avg_cost DECIMAL(12,2);
    SELECT AVG(expense_total) INTO avg_cost
    FROM (
        SELECT d.DeliveryID, COALESCE(SUM(e.Amount),0) AS expense_total
        FROM Deliveries d
        LEFT JOIN Expenses e ON d.DeliveryID = e.DeliveryID
        WHERE d.VehicleID = p_vehicle_id
        GROUP BY d.DeliveryID
    ) sub;
    RETURN COALESCE(avg_cost, 0);
END$$


-- Function 2: Number of deliveries per vehicle
CREATE FUNCTION fn_DeliveryCountByVehicle(p_vehicle_id INT)
RETURNS INT
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE cnt INT;
    SELECT COUNT(*) INTO cnt FROM Deliveries WHERE VehicleID = p_vehicle_id;
    RETURN cnt;
END$$


-- Function 3: Total expense for a specific order
CREATE FUNCTION fn_TotalExpenseByOrder(p_order_id INT)
RETURNS DECIMAL(12,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(12,2);
    SELECT COALESCE(SUM(e.Amount),0) INTO total
    FROM Expenses e
    JOIN Deliveries d ON e.DeliveryID = d.DeliveryID
    WHERE d.OrderID = p_order_id;
    RETURN total;
END$$


-- Function 4: Customer total orders count
CREATE FUNCTION fn_CustomerOrderCount(p_customer_id INT)
RETURNS INT
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE cnt INT;
    SELECT COUNT(*) INTO cnt FROM Orders WHERE CustomerID = p_customer_id;
    RETURN cnt;
END$$

DELIMITER ;


-- ============================================================
-- SECTION 5: TRIGGERS
-- ============================================================

DELIMITER $$

-- Trigger 1: Auto set Order status to 'Completed' when Delivery is marked 'Delivered'
CREATE TRIGGER trg_AfterDeliveryUpdate
AFTER UPDATE ON Deliveries
FOR EACH ROW
BEGIN
    IF NEW.Status = 'Delivered' AND OLD.Status <> 'Delivered' THEN
        UPDATE Orders SET Status = 'Completed'
        WHERE OrderID = NEW.OrderID;
        -- Free the vehicle
        UPDATE Vehicles SET Status = 'Available'
        WHERE VehicleID = NEW.VehicleID;
    END IF;
    IF NEW.Status = 'Failed' AND OLD.Status <> 'Failed' THEN
        UPDATE Orders SET Status = 'Cancelled'
        WHERE OrderID = NEW.OrderID;
        UPDATE Vehicles SET Status = 'Available'
        WHERE VehicleID = NEW.VehicleID;
    END IF;
END$$


-- Trigger 2: Auto set vehicle 'In Use' when a new Delivery is inserted
CREATE TRIGGER trg_AfterDeliveryInsert
AFTER INSERT ON Deliveries
FOR EACH ROW
BEGIN
    UPDATE Vehicles SET Status = 'In Use'
    WHERE VehicleID = NEW.VehicleID AND Status = 'Available';
END$$


-- Trigger 3: Prevent inserting expense for a non-existent delivery
CREATE TRIGGER trg_BeforeExpenseInsert
BEFORE INSERT ON Expenses
FOR EACH ROW
BEGIN
    IF NOT EXISTS (SELECT 1 FROM Deliveries WHERE DeliveryID = NEW.DeliveryID) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid DeliveryID. Cannot record expense.';
    END IF;
    IF NEW.Amount <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Expense amount must be greater than 0.';
    END IF;
END$$


-- Trigger 4: Prevent DeliveryDate before OrderDate
CREATE TRIGGER trg_BeforeDeliveryInsert
BEFORE INSERT ON Deliveries
FOR EACH ROW
BEGIN
    DECLARE v_order_date DATETIME;
    SELECT OrderDate INTO v_order_date FROM Orders WHERE OrderID = NEW.OrderID;
    IF NEW.DeliveryDate < v_order_date THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'DeliveryDate cannot be earlier than OrderDate.';
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- SECTION 6: QUICK VERIFY QUERIES
-- ============================================================
-- Run these after loading all data to sanity-check:
-- SELECT * FROM vw_CurrentDeliveries    LIMIT 5;
-- SELECT * FROM vw_CostPerOrder         LIMIT 5;
-- SELECT * FROM vw_VehiclePerformance   LIMIT 5;
-- SELECT * FROM vw_OutstandingOrders    LIMIT 5;
-- SELECT * FROM vw_MonthlyExpenseSummary LIMIT 10;
-- SELECT fn_AvgDeliveryCostByVehicle(1);
-- SELECT fn_DeliveryCountByVehicle(1);
-- SELECT fn_TotalExpenseByOrder(1);
-- CALL sp_CustomerOrderHistory(1);

