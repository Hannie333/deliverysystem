USE DeliverySystem;

DROP USER IF EXISTS 'manager_user'@'localhost';
DROP USER IF EXISTS 'dispatcher_user'@'localhost';
DROP USER IF EXISTS 'accountant_user'@'localhost';

CREATE USER 'manager_user'@'localhost'   IDENTIFIED BY 'Manager@2025!';
CREATE USER 'dispatcher_user'@'localhost' IDENTIFIED BY 'Dispatch@2025!';
CREATE USER 'accountant_user'@'localhost' IDENTIFIED BY 'Account@2025!';

GRANT ALL PRIVILEGES ON DeliverySystem.* TO 'manager_user'@'localhost';


GRANT SELECT, INSERT, UPDATE ON DeliverySystem.Customers   TO 'dispatcher_user'@'localhost';
GRANT SELECT, INSERT, UPDATE ON DeliverySystem.Orders      TO 'dispatcher_user'@'localhost';
GRANT SELECT, INSERT, UPDATE ON DeliverySystem.Deliveries  TO 'dispatcher_user'@'localhost';
GRANT SELECT                 ON DeliverySystem.Vehicles    TO 'dispatcher_user'@'localhost';
GRANT SELECT                 ON DeliverySystem.vw_CurrentDeliveries  TO 'dispatcher_user'@'localhost';
GRANT SELECT                 ON DeliverySystem.vw_OutstandingOrders  TO 'dispatcher_user'@'localhost';
GRANT EXECUTE                ON PROCEDURE DeliverySystem.sp_CreateOrderAndAssign TO 'dispatcher_user'@'localhost';
GRANT EXECUTE                ON PROCEDURE DeliverySystem.sp_CompleteDelivery     TO 'dispatcher_user'@'localhost';
GRANT EXECUTE                ON PROCEDURE DeliverySystem.sp_AddCustomer          TO 'dispatcher_user'@'localhost';

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

