import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Nsurya@321",
        database="slot_booking"
    )


def ensure_schema():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SHOW COLUMNS FROM bookings LIKE 'email'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE bookings ADD COLUMN email VARCHAR(120) NULL AFTER name")

        cursor.execute("SHOW COLUMNS FROM bookings LIKE 'phone'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE bookings ADD COLUMN phone VARCHAR(20) NULL AFTER email")

        cursor.execute("SHOW COLUMNS FROM bookings LIKE 'status'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE bookings ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'booked' AFTER slot_id")

        cursor.execute("SHOW COLUMNS FROM bookings LIKE 'created_at'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE bookings ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP")

        cursor.execute("UPDATE bookings SET status='booked' WHERE status IS NULL OR status='' ")
        conn.commit()
    finally:
        conn.close()
