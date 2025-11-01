-- ASSIGNMENT 1
-- Objective - Set up the foundational database
-- Tasks:
-- 1. Design and implement database schema for flights.
-- 2. Set up a database(SQLite) and populate with simulated data.
-- 3. Practice all SQL queries.


-- DB Setup(SQLite)
CREATE DATABASE flight_booking;

USE flight_booking 

-- DB Schema Design and Implementation

-- Airports table to store airports details
CREATE TABLE Airports (
    airport_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL -- IATA code
);


-- Flights table to store flight info
CREATE TABLE Flights (
    flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    flight_code TEXT NOT NULL,
    origin_airport_id INTEGER NOT NULL,
    destination_airport_id INTEGER NOT NULL,
    departure_time TEXT NOT NULL, -- ISO datetime
    arrival_time TEXT NOT NULL,   -- ISO datetime
    duration_minutes INTEGER NOT NULL,
    stops INTEGER NOT NULL,
    base_fare REAL NOT NULL,
    travel_class TEXT NOT NULL CHECK (travel_class IN ('Economy', 'Business', 'First')),
    FOREIGN KEY (origin_airport_id) REFERENCES Airports(airport_id),
    FOREIGN KEY (destination_airport_id) REFERENCES Airports(airport_id),
    CHECK (origin_airport_id != destination_airport_id)
);


-- Users table: 
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    phone TEXT UNIQUE,
    password_hash TEXT,
    google_id TEXT UNIQUE
);

-- Bookings table: 
CREATE TABLE Bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    flight_id INTEGER NOT NULL,
    booking_date TEXT NOT NULL,
    trip_type TEXT CHECK (trip_type IN ('One Way', 'Round Trip')) NOT NULL,
    return_date TEXT, -- nullable if 'One Way'
    travellers_count INTEGER NOT NULL,
    travel_class TEXT NOT NULL,
    total_price REAL NOT NULL,
    status TEXT NOT NULL,
    pnr TEXT UNIQUE,
    timer_expiry TEXT, -- payment timer
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id)
);


-- Travellers table: 
CREATE TABLE Travellers (
    traveller_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    last_name TEXT NOT NULL,
    dob TEXT,
    government_id_type TEXT,
    government_id_number TEXT,
    email TEXT,
    phone TEXT,
    FOREIGN KEY (booking_id) REFERENCES Bookings(booking_id)
);


-- Billing Address:
CREATE TABLE Billing_Address (
    address_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    pin_code TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES Bookings(booking_id)
);


-- Seats table: 
CREATE TABLE Seats (
    seat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_id INTEGER NOT NULL,
    seat_number TEXT NOT NULL,
    travel_class TEXT NOT NULL CHECK (travel_class IN ('Economy', 'Business', 'First')),
    is_booked INTEGER NOT NULL DEFAULT 0, -- 0 = available, 1 = booked
    seat_price REAL NOT NULL,
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id)
);

-- Booking_Seats table: 
CREATE TABLE Booking_Seats (
    booking_seat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    traveller_id INTEGER NOT NULL,
    seat_id INTEGER NOT NULL,
    seat_price REAL NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES Bookings(booking_id),
    FOREIGN KEY (traveller_id) REFERENCES Travellers(traveller_id),
    FOREIGN KEY (seat_id) REFERENCES Seats(seat_id)
);


-- Meals table:
CREATE TABLE Meals (
    meal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL
);

-- Booking_Meals table:
CREATE TABLE Booking_Meals (
    booking_meal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    traveller_id INTEGER NOT NULL,
    meal_id INTEGER NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES Bookings(booking_id),
    FOREIGN KEY (traveller_id) REFERENCES Travellers(traveller_id),
    FOREIGN KEY (meal_id) REFERENCES Meals(meal_id)
);


-- Payment table: 
CREATE TABLE Payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    payment_time TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES Bookings(booking_id)
);

-- Reference
-- The above entities and attribute creation are based on the ixigo website.
-- I referred to the site to map out the user journey flow and then converted this into entities and attributes.

-- Populating Sample data
 -- Airports data
INSERT INTO Airports (name, city, country, code) VALUES
('Indira Gandhi International Airport', 'Delhi', 'India', 'DEL'),
('Chhatrapati Shivaji Maharaj International Airport', 'Mumbai', 'India', 'BOM'),
('Kempegowda International Airport', 'Bengaluru', 'India', 'BLR'),
('Chennai International Airport', 'Chennai', 'India', 'MAA'),
('Rajiv Gandhi International Airport', 'Hyderabad', 'India', 'HYD'),
('Heathrow Airport', 'London', 'United Kingdom', 'LHR'),
('John F. Kennedy International Airport', 'New York', 'United States', 'JFK'),
('Dubai International Airport', 'Dubai', 'United Arab Emirates', 'DXB'),
('Singapore Changi Airport', 'Singapore', 'Singapore', 'SIN'),
('Tokyo Haneda Airport', 'Tokyo', 'Japan', 'HND');


-- Flights data
INSERT INTO Flights 
(company_name, flight_code, origin_airport_id, destination_airport_id, departure_time, arrival_time, duration_minutes, stops, base_fare, travel_class) 
VALUES
('Air India', 'AI101', 1, 2, '2025-10-11T06:00:00', '2025-10-11T08:10:00', 130, 0, 5500.00, 'Economy'),
('IndiGo', '6E202', 3, 4, '2025-10-11T09:30:00', '2025-10-11T11:45:00', 135, 0, 4800.00, 'Economy'),
('Vistara', 'UK303', 5, 1, '2025-10-11T14:00:00', '2025-10-11T16:30:00', 150, 0, 6200.00, 'Business'),
('SpiceJet', 'SG404', 2, 5, '2025-10-11T18:20:00', '2025-10-11T20:40:00', 140, 0, 5100.00, 'Economy'),
('Go First', 'G815', 4, 3, '2025-10-11T21:00:00', '2025-10-11T23:15:00', 135, 0, 4700.00, 'Economy'),
('Emirates', 'EK501', 1, 8, '2025-10-12T04:00:00', '2025-10-12T06:20:00', 200, 0, 25000.00, 'Economy'),
('British Airways', 'BA256', 2, 6, '2025-10-12T10:00:00', '2025-10-12T14:45:00', 285, 1, 42000.00, 'Business'),
('Singapore Airlines', 'SQ403', 4, 9, '2025-10-12T15:30:00', '2025-10-12T22:30:00', 420, 0, 38000.00, 'First'),
('All Nippon Airways', 'NH882', 3, 10, '2025-10-12T23:00:00', '2025-10-13T07:00:00', 480, 0, 45000.00, 'Business'),
('United Airlines', 'UA827', 5, 7, '2025-10-13T08:00:00', '2025-10-13T16:00:00', 480, 1, 39000.00, 'Economy');


-- Seats data 
INSERT INTO Seats (flight_id, seat_number, travel_class, is_booked, seat_price) VALUES
(1, '1A', 'Economy', 0, 5600.00),
(1, '1B', 'Economy', 1, 5600.00),
(2, '3C', 'Economy', 0, 4900.00),
(2, '3D', 'Economy', 0, 4900.00),
(3, '5A', 'Business', 0, 6400.00),
(4, '10F', 'Economy', 1, 5200.00),
(5, '12A', 'Economy', 0, 4700.00),
(6, '2B', 'Economy', 0, 25500.00),
(7, '4A', 'Business', 0, 43000.00),
(8, '1C', 'First', 1, 38500.00);


--  Meals data
INSERT INTO Meals (meal_name, description, price) VALUES
('Vegetarian Meal', 'A balanced vegetarian option with rice, dal, and vegetables.', 350.00),
('Non-Vegetarian Meal', 'Includes chicken curry, rice, bread, and dessert.', 450.00),
('Vegan Meal', 'Plant-based meal with salad, fruits, and grains.', 400.00),
('Kids Meal', 'Child-friendly meal with pasta, juice, and dessert.', 300.00),
('Gluten-Free Meal', 'Meal with rice, grilled chicken, and vegetables.', 420.00),
('Seafood Meal', 'Includes grilled fish, rice, and salad.', 480.00),
('Diabetic Meal', 'Low-sugar meal with whole grains and vegetables.', 400.00),
('Kosher Meal', 'Prepared according to kosher dietary rules.', 500.00),
('Halal Meal', 'Prepared as per halal standards with chicken/rice.', 450.00),
('Snack Box', 'Light snacks including sandwich, chips, and drink.', 250.00);


-- SQL Query Practice

-- Basic Queries → SELECT, UPDATE, DELETE, ORDER BY, WHERE, LIMIT

-- AIRPORTS TABLE - airport_id | name | city | country | code

-- SELECT
-- SELECT all airports
SELECT * FROM Airports;

-- SELECT specific columns
SELECT name, city, code FROM Airports;

-- SELECT with WHERE
-- Airports in India
SELECT * FROM Airports
WHERE country = 'India';

-- Airports in a specific city
SELECT name, code FROM Airports
WHERE city = 'Mumbai';

-- ORDER BY
-- Airports sorted by city name ascending
SELECT name, city FROM Airports
ORDER BY city ASC;

-- Airports sorted by airport code descending
SELECT name, code FROM Airports
ORDER BY code DESC;

-- LIMIT
-- Get first 5 airports
SELECT * FROM Airports
LIMIT 5;

-- Get top 3 airports in India sorted by city
SELECT name, city FROM Airports
WHERE country = 'India'
ORDER BY city ASC
LIMIT 3;

-- UPDATE
-- Change the name of an airport
UPDATE Airports
SET name = 'New Mumbai Airport'
WHERE airport_id = 2;

-- Change city for all airports in India to uppercase
UPDATE Airports
SET city = UPPER(city)
WHERE country = 'India';

-- DELETE
-- Delete an airport by code
DELETE FROM Airports
WHERE code = 'DEL';

-- Delete all airports in a specific city
DELETE FROM Airports
WHERE city = 'Bengaluru';

-- SELECT with WHERE , ORDER , LIMIT
-- Top 3 international airports (non-India) sorted by name
SELECT name, city, country FROM Airports
WHERE country != 'India'
ORDER BY name ASC
LIMIT 3;


-- Aggregate Queries → COUNT, AVG, SUM, MIN/MAX, GROUP BY, HAVING

-- SEATS TABLE - seat_id | flight_id | seat_number | travel_class | is_booked | seat_price

-- COUNT
-- Count total seats
SELECT COUNT(*) AS total_seats
FROM Seats;

-- Count seats by travel class
SELECT travel_class, COUNT(*) AS seats_count
FROM Seats
GROUP BY travel_class;

-- Count booked vs available seats
SELECT is_booked, COUNT(*) AS seat_count
FROM Seats
GROUP BY is_booked;

-- AVG (average)
-- Average seat price overall
SELECT AVG(seat_price) AS avg_seat_price
FROM Seats;

-- Average seat price by travel class
SELECT travel_class, AVG(seat_price) AS avg_price
FROM Seats
GROUP BY travel_class;

-- SUM
-- Total revenue if all seats were booked
SELECT SUM(seat_price) AS potential_revenue
FROM Seats;

-- Total revenue by travel class
SELECT travel_class, SUM(seat_price) AS total_revenue
FROM Seats
GROUP BY travel_class;

-- MIN / MAX
-- Cheapest seat
SELECT MIN(seat_price) AS cheapest_seat
FROM Seats;

-- Most expensive seat in each class
SELECT travel_class, MAX(seat_price) AS max_price
FROM Seats
GROUP BY travel_class;

-- HAVING
-- Classes with average price > 5000
SELECT travel_class, AVG(seat_price) AS avg_price
FROM Seats
GROUP BY travel_class
HAVING AVG(seat_price) > 5000;

-- Classes with more than 3 seats
SELECT travel_class, COUNT(*) AS seat_count
FROM Seats
GROUP BY travel_class
HAVING COUNT(*) > 3;


-- Schema Changes (DDL) → ALTER TABLE

-- AIRPORTS TABLE - airport_id | name | city | country | code

-- ALTER TABLE
ALTER TABLE Airports
ADD COLUMN timezone TEXT;

-- Add a default column
ALTER TABLE Airports
ADD COLUMN is_international INTEGER DEFAULT 1;

-- Add a nullable column
ALTER TABLE Airports
ADD COLUMN short_name TEXT;

-- Check the schema after altering
PRAGMA table_info(Airports);


-- Constraints → PRIMARY KEY, NOT NULL, UNIQUE, CHECK, DEFAULT

-- MEALS TABLE -  meal_id | meal_name | description | price

-- PRIMARY KEY
INSERT INTO Meals (meal_id, meal_name, price) VALUES (1, 'Veg Sandwich', 200);
-- This will fail if meal_id 1 already exists

-- NOT NULL
INSERT INTO Meals (meal_name, price) VALUES (NULL, 150); 
-- Error

-- UNIQUE
-- ALTER TABLE Meals ADD COLUMN meal_code TEXT UNIQUE
INSERT INTO Meals (meal_name, price, meal_code) VALUES ('Veg Sandwich', 200, 'MS01');
INSERT INTO Meals (meal_name, price, meal_code) VALUES ('Veg Sandwich', 250, 'MS02'); 
-- Fails

-- CHECK
-- Ensure price is positive
ALTER TABLE Meals ADD COLUMN discount_price REAL CHECK(discount_price >= 0);

-- DEFAULT
-- Add a default column
ALTER TABLE Meals ADD COLUMN is_veg INTEGER DEFAULT 1;

-- Check result
SELECT * FROM Meals;


-- Joins → INNER JOIN, LEFT JOIN

-- AIRPORTS TABLE - airport_id | name | city | country | code

-- FLIGHTS TABLE - flight_id | company_name | flight_code | origin_airport_id | destination_airport_id | departure_time | arrival_time | duration_minutes | stops | base_fare | travel_class

-- INNER JOIN
-- Get flight info with origin airport name
SELECT f.flight_code, f.company_name, a.name AS origin_airport, a.city AS origin_city
FROM Flights f
INNER JOIN Airports a ON f.origin_airport_id = a.airport_id;

-- Flight info with both origin & destination airport names
SELECT f.flight_code, 
       f.company_name, 
       ao.name AS origin_airport, 
       ad.name AS destination_airport
FROM Flights f
INNER JOIN Airports ao ON f.origin_airport_id = ao.airport_id
INNER JOIN Airports ad ON f.destination_airport_id = ad.airport_id;

-- LEFT JOIN
-- All flights with origin airport info
SELECT f.flight_code, f.company_name, a.name AS origin_airport
FROM Flights f
LEFT JOIN Airports a ON f.origin_airport_id = a.airport_id;


-- Transactions → BEGIN / START TRANSACTION, COMMIT, ROLLBACK

-- Sample Transaction Scenario (Flights and Seats)
-- Book a seat on a flight

-- Start transaction
BEGIN TRANSACTION;

-- Check seat availability
SELECT seat_id, is_booked 
FROM Seats
WHERE flight_id = 1 AND seat_number = 'A1';

-- Update seat as booked
UPDATE Seats
SET is_booked = 1
WHERE flight_id = 1 AND seat_number = 'A1' AND is_booked = 0;

-- Add a meal
INSERT INTO Meals (meal_name, description, price)
VALUES ('Veg Sandwich', 'Delicious sandwich', 200);

-- commit
COMMIT;

-- rollback
ROLLBACK;







