CREATE DATABASE slot_booking;

USE slot_booking;

CREATE TABLE slots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slot_time VARCHAR(50),
    status VARCHAR(20) DEFAULT 'available'
);

CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    slot_id INT,
    FOREIGN KEY (slot_id) REFERENCES slots(id)
);
INSERT INTO slots(slot_time) VALUES
('10:00 AM'),
('11:00 AM'),
('12:00 PM'),
('1:00 PM'),
('2:00 PM');
