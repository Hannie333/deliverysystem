from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Cho phép frontend gọi API

# Cấu hình database (giống file 05_python_app.py)
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "30092006",
    "database": "DeliverySystem",
    "charset": "utf8mb4"
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Lỗi kết nối DB: {e}")
        return None

# -------------------- CUSTOMERS --------------------
@app.route('/api/customers', methods=['GET'])
def get_customers():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT CustomerID as id, CustomerName as name, PhoneNumber as phone,
               Address as address, Email as email, DATE_FORMAT(CreatedAt,'%Y-%m-%d') as createdAt
        FROM Customers ORDER BY CustomerID DESC
    """)
    customers = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(customers)

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    address = data.get('address')
    email = data.get('email')
    if not all([name, phone, address]):
        return jsonify({"error": "Missing required fields"}), 400
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Customers (CustomerName, PhoneNumber, Address, Email)
            VALUES (%s, %s, %s, %s)
        """, (name, phone, address, email))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"id": new_id, "message": "Customer added"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 400

# -------------------- VEHICLES --------------------
@app.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT VehicleID as id, VehicleType as type, LicensePlate as plate,
               Capacity as capacity, Status as status, CreatedAt as createdAt
        FROM Vehicles ORDER BY VehicleID DESC
    """)
    vehicles = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(vehicles)

@app.route('/api/vehicles', methods=['POST'])
def add_vehicle():
    data = request.json
    vtype = data.get('type')
    plate = data.get('plate')
    capacity = data.get('capacity')
    if not all([vtype, plate, capacity]):
        return jsonify({"error": "Missing fields"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Vehicles (VehicleType, LicensePlate, Capacity, Status)
            VALUES (%s, %s, %s, 'Available')
        """, (vtype, plate, capacity))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"id": new_id, "message": "Vehicle added"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 400

# -------------------- ORDERS --------------------
@app.route('/api/orders', methods=['GET'])
def get_orders():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT o.OrderID as id, o.CustomerID as customerId, c.CustomerName as customerName,
               DATE_FORMAT(o.OrderDate,'%Y-%m-%d') as orderDate,
               o.Status as status, o.TotalWeight as weight, o.Notes as notes
        FROM Orders o
        JOIN Customers c ON o.CustomerID = c.CustomerID
        ORDER BY o.OrderID DESC
    """)
    orders = cursor.fetchall()
    # Thêm cost (tổng chi phí) cho mỗi order
    for order in orders:
        cursor.execute("""
            SELECT COALESCE(SUM(e.Amount),0) as total
            FROM Expenses e
            JOIN Deliveries d ON e.DeliveryID = d.DeliveryID
            WHERE d.OrderID = %s
        """, (order['id'],))
        cost = cursor.fetchone()['total']
        order['cost'] = float(cost)
    cursor.close()
    conn.close()
    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    customer_id = data.get('customerId')
    weight = data.get('weight')
    driver = data.get('driver')
    delivery_date = data.get('deliveryDate')
    notes = data.get('notes', '')
    if not all([customer_id, weight, driver, delivery_date]):
        return jsonify({"error": "Missing fields"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Gọi stored procedure sp_CreateOrderAndAssign
        args = (customer_id, weight, notes, driver, 0, 0)
        cursor.callproc('sp_CreateOrderAndAssign', args)
        conn.commit()
        # Lấy order_id và delivery_id từ output variables
        # Cách đơn giản: query lấy order mới nhất của customer
        cursor.execute("SELECT LAST_INSERT_ID()")
        order_id = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return jsonify({"orderId": order_id, "message": "Order created"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/orders/<int:order_id>/complete', methods=['PUT'])
def complete_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Tìm delivery liên quan
        cursor.execute("SELECT DeliveryID FROM Deliveries WHERE OrderID = %s", (order_id,))
        row = cursor.fetchone()
        if row:
            delivery_id = row[0]
            cursor.callproc('sp_CompleteDelivery', (delivery_id,))
            conn.commit()
        else:
            # Nếu chưa có delivery, chỉ cập nhật order status
            cursor.execute("UPDATE Orders SET Status = 'Completed' WHERE OrderID = %s", (order_id,))
            conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Order completed"})
    except Error as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/orders/<int:order_id>/cancel', methods=['PUT'])
def cancel_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Orders SET Status = 'Cancelled' WHERE OrderID = %s", (order_id,))
        conn.commit()
        # Cập nhật delivery nếu có
        cursor.execute("UPDATE Deliveries SET Status = 'Failed' WHERE OrderID = %s", (order_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Order cancelled"})
    except Error as e:
        return jsonify({"error": str(e)}), 400

# -------------------- DELIVERIES --------------------
@app.route('/api/deliveries', methods=['GET'])
def get_deliveries():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DeliveryID as id, OrderID as orderId, VehicleID as vehicleId,
               VehicleType as vehicleType, LicensePlate as vehiclePlate,
               DriverName as driverName, DATE_FORMAT(DeliveryDate,'%Y-%m-%d') as deliveryDate,
               Status as status, CreatedAt as createdAt
        FROM Deliveries
        ORDER BY DeliveryID DESC
    """)
    deliveries = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(deliveries)

@app.route('/api/deliveries/<int:delivery_id>/complete', methods=['PUT'])
def complete_delivery(delivery_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.callproc('sp_CompleteDelivery', (delivery_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Delivery completed"})
    except Error as e:
        return jsonify({"error": str(e)}), 400

# -------------------- EXPENSES --------------------
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ExpenseID as id, DeliveryID as deliveryId, ExpenseType as type,
               Amount as amount, Description as description,
               DATE_FORMAT(RecordedAt,'%Y-%m-%d') as recordedAt
        FROM Expenses
        ORDER BY ExpenseID DESC
    """)
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(expenses)

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    data = request.json
    delivery_id = data.get('deliveryId')
    exp_type = data.get('type')
    amount = data.get('amount')
    description = data.get('description', '')
    if not all([delivery_id, exp_type, amount]):
        return jsonify({"error": "Missing fields"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.callproc('sp_RecordExpense', (delivery_id, exp_type, amount, description))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Expense recorded"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 400

# -------------------- REPORTS / DASHBOARD --------------------
@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as total FROM Customers")
    customers = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM Orders")
    orders = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM Deliveries")
    deliveries = cursor.fetchone()['total']
    cursor.execute("SELECT COALESCE(SUM(Amount),0) as total FROM Expenses")
    total_exp = cursor.fetchone()['total']
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) as total FROM Orders WHERE DATE(OrderDate) = %s", (today,))
    today_orders = cursor.fetchone()['total']
    cursor.close()
    conn.close()
    return jsonify({
        "customers": customers,
        "orders": orders,
        "deliveries": deliveries,
        "totalExpenses": float(total_exp),
        "todayOrders": today_orders
    })

@app.route('/api/dashboard/weekly-expenses', methods=['GET'])
def weekly_expenses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Lấy 7 ngày gần nhất
    cursor.execute("""
        SELECT DATE(RecordedAt) as date, SUM(Amount) as total
        FROM Expenses
        WHERE RecordedAt >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY DATE(RecordedAt)
        ORDER BY date
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    # Tạo mảng đủ 7 ngày
    result = []
    for i in range(7):
        day = (datetime.now() - timedelta(days=6-i)).strftime('%Y-%m-%d')
        total = next((r['total'] for r in rows if r['date'].strftime('%Y-%m-%d') == day), 0)
        result.append({"date": day, "total": float(total)})
    return jsonify(result)

@app.route('/api/orders/status-counts', methods=['GET'])
def order_status_counts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT Status, COUNT(*) as count
        FROM Orders
        GROUP BY Status
    """)
    counts = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(counts)

@app.route('/api/reports/top-customers', methods=['GET'])
def top_customers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.CustomerName as name, COUNT(o.OrderID) as orders,
               COALESCE(SUM(e.Amount),0) as totalSpent
        FROM Customers c
        LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
        LEFT JOIN Deliveries d ON o.OrderID = d.OrderID
        LEFT JOIN Expenses e ON d.DeliveryID = e.DeliveryID
        GROUP BY c.CustomerID
        ORDER BY orders DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

@app.route('/api/reports/vehicle-performance', methods=['GET'])
def vehicle_performance():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT v.LicensePlate as plate, v.VehicleType as type,
               COUNT(d.DeliveryID) as totalDeliveries,
               SUM(CASE WHEN d.Status = 'Delivered' THEN 1 ELSE 0 END) as completed
        FROM Vehicles v
        LEFT JOIN Deliveries d ON v.VehicleID = d.VehicleID
        GROUP BY v.VehicleID
        ORDER BY totalDeliveries DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    from datetime import timedelta
    app.run(host='0.0.0.0', port=5001, debug=True)