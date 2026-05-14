DROP DATABASE IF EXISTS DeliverySystem;
CREATE DATABASE DeliverySystem
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE DeliverySystem;

-- ============================================================
-- TABLE 1: Customers
-- ============================================================
CREATE TABLE Customers (
    CustomerID   INT AUTO_INCREMENT PRIMARY KEY,
    CustomerName VARCHAR(100)  NOT NULL,
    PhoneNumber  VARCHAR(15)   NOT NULL UNIQUE,
    Address      VARCHAR(255)  NOT NULL,
    Email        VARCHAR(100),
    CreatedAt    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_phone CHECK (PhoneNumber REGEXP '^[0-9]{10,15}$')
);

-- ============================================================
-- TABLE 2: Vehicles
-- ============================================================
CREATE TABLE Vehicles (
    VehicleID    INT AUTO_INCREMENT PRIMARY KEY,
    VehicleType  ENUM('Motorbike','Van','Truck','Electric Bike') NOT NULL,
    LicensePlate VARCHAR(20)  NOT NULL UNIQUE,
    Capacity     DECIMAL(6,2) NOT NULL COMMENT 'Max load in kg',
    Status       ENUM('Available','In Use','Maintenance') NOT NULL DEFAULT 'Available',
    CreatedAt    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 3: Orders
-- ============================================================
CREATE TABLE Orders (
    OrderID      INT AUTO_INCREMENT PRIMARY KEY,
    CustomerID   INT          NOT NULL,
    OrderDate    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Status       ENUM('Pending','Assigned','In Transit','Completed','Cancelled') NOT NULL DEFAULT 'Pending',
    TotalWeight  DECIMAL(8,2) COMMENT 'kg',
    Notes        TEXT,
    CONSTRAINT fk_orders_customer FOREIGN KEY (CustomerID)
        REFERENCES Customers(CustomerID)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================
-- TABLE 4: Deliveries
-- ============================================================
CREATE TABLE Deliveries (
    DeliveryID   INT AUTO_INCREMENT PRIMARY KEY,
    OrderID      INT          NOT NULL UNIQUE,
    VehicleID    INT          NOT NULL,
    DeliveryDate DATETIME     NOT NULL,
    DriverName   VARCHAR(100) NOT NULL,
    Status       ENUM('Scheduled','In Transit','Delivered','Failed') NOT NULL DEFAULT 'Scheduled',
    CreatedAt    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_deliveries_order   FOREIGN KEY (OrderID)
        REFERENCES Orders(OrderID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_deliveries_vehicle FOREIGN KEY (VehicleID)
        REFERENCES Vehicles(VehicleID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_delivery_date CHECK (DeliveryDate >= CreatedAt)
);

-- ============================================================
-- TABLE 5: Expenses
-- ============================================================
CREATE TABLE Expenses (
    ExpenseID    INT AUTO_INCREMENT PRIMARY KEY,
    DeliveryID   INT          NOT NULL,
    ExpenseType  ENUM('Fuel','Toll','Handling','Packaging','Other') NOT NULL,
    Amount       DECIMAL(12,2) NOT NULL,
    RecordedAt   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Description  VARCHAR(255),
    CONSTRAINT fk_expenses_delivery FOREIGN KEY (DeliveryID)
        REFERENCES Deliveries(DeliveryID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT chk_amount CHECK (Amount > 0)
);

