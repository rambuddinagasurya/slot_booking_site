from flask import Flask, render_template, request, redirect, url_for
from db import get_connection, ensure_schema
from datetime import datetime

app = Flask(__name__)


def get_dashboard_stats(conn):
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_bookings FROM bookings")
    total = cursor.fetchone()["total_bookings"]

    cursor.execute("SELECT COUNT(*) AS completed_bookings FROM bookings WHERE status='completed'")
    completed = cursor.fetchone()["completed_bookings"]

    cursor.execute("SELECT COUNT(*) AS pending_bookings FROM bookings WHERE status='booked'")
    pending = cursor.fetchone()["pending_bookings"]

    cursor.execute("SELECT COUNT(*) AS available_slots FROM slots WHERE status='available'")
    available = cursor.fetchone()["available_slots"]

    return {
        "total_bookings": total,
        "completed_bookings": completed,
        "pending_bookings": pending,
        "available_slots": available,
    }


@app.route("/")
def home():
    ensure_schema()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            slots.id,
            slots.slot_time,
            slots.status,
            latest_booking.name AS booked_name
        FROM slots
        LEFT JOIN (
            SELECT b1.slot_id, b1.name
            FROM bookings b1
            INNER JOIN (
                SELECT slot_id, MAX(id) AS max_id
                FROM bookings
                GROUP BY slot_id
            ) b2 ON b1.id = b2.max_id
        ) latest_booking ON latest_booking.slot_id = slots.id
        ORDER BY slots.id
        """
    )
    slots = cursor.fetchall()

    stats = get_dashboard_stats(conn)

    cursor.execute(
        """
        SELECT bookings.name, bookings.email, bookings.phone, slots.slot_time, bookings.status
        FROM bookings
        JOIN slots ON bookings.slot_id = slots.id
        ORDER BY bookings.id DESC
        LIMIT 5
        """
    )
    recent_bookings = cursor.fetchall()

    total_slots = len(slots)
    available_slots = sum(1 for slot in slots if slot["status"] == "available")
    occupied_slots = total_slots - available_slots
    occupancy_percent = round((occupied_slots / total_slots) * 100) if total_slots else 0

    next_free_slot = "No slots"
    for slot in slots:
        if slot["status"] == "available":
            next_free_slot = slot["slot_time"]
            break

    selected_slot_id = request.args.get("slot_id", "")
    if selected_slot_id and not any(
        str(slot["id"]) == selected_slot_id and slot["status"] == "available"
        for slot in slots
    ):
        selected_slot_id = ""

    if not selected_slot_id:
        for slot in slots:
            if slot["status"] == "available":
                selected_slot_id = str(slot["id"])
                break

    today_display = datetime.now().strftime("%A, %b %d, %Y").replace(" 0", " ")

    conn.close()
    return render_template(
        "index.html",
        slots=slots,
        stats=stats,
        recent_bookings=recent_bookings,
        occupancy_percent=occupancy_percent,
        next_free_slot=next_free_slot,
        selected_slot_id=selected_slot_id,
        today_display=today_display,
    )


@app.route("/book", methods=["POST"])
def book_slot():
    ensure_schema()

    name = request.form["name"].strip()
    email = request.form["email"].strip()
    phone = request.form["phone"].strip()
    slot_id = request.form["slot_id"]

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT status FROM slots WHERE id=%s", (slot_id,))
        slot = cursor.fetchone()

        if not slot or slot[0] != "available":
            conn.rollback()
            return redirect(url_for("home"))

        cursor.execute(
            "INSERT INTO bookings(name, email, phone, slot_id, status) VALUES(%s, %s, %s, %s, 'booked')",
            (name, email, phone, slot_id),
        )

        cursor.execute(
            "UPDATE slots SET status='booked' WHERE id=%s",
            (slot_id,),
        )

        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("home"))


@app.route("/bookings")
def view_bookings():
    ensure_schema()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            bookings.id,
            bookings.name,
            bookings.email,
            bookings.phone,
            slots.slot_time,
            bookings.status,
            DATE_FORMAT(bookings.created_at, '%d %b %Y %h:%i %p') AS booked_on
        FROM bookings
        JOIN slots ON bookings.slot_id = slots.id
        ORDER BY bookings.id DESC
        """
    )

    data = cursor.fetchall()
    stats = get_dashboard_stats(conn)

    conn.close()

    return render_template("bookings.html", bookings=data, stats=stats)


@app.route("/bookings/<int:booking_id>/complete", methods=["POST"])
def complete_booking(booking_id):
    ensure_schema()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE bookings SET status='completed' WHERE id=%s AND status!='completed'",
            (booking_id,),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("view_bookings"))


if __name__ == "__main__":
    app.run(debug=True)
