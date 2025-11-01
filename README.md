✈️ Flight Booking Simulator with Dynamic Pricing

A full-stack project that simulates the process of flight booking, seat selection, and payment — with dynamic fare updates based on demand.
Built using FastAPI (Backend) and HTML, CSS, JavaScript (Frontend).

🚀 Features

Search Flights: Search for available flights by route, date, and class.

Dynamic Pricing: Flight fares update automatically based on availability and demand.

Seat Selection: Choose preferred seats and see real-time fare changes.

Booking & Payment Simulation: Mock payment system generates unique PNR numbers.

Booking History & Cancellation: Retrieve or cancel previous bookings.

CORS-enabled Backend: Secure connection between frontend and backend.

🧩 Tech Stack

Frontend - HTML, CSS, JavaScript
Backend - FastAPI
Database - SQLite
Environment - Python 3.x
API Docs - Swagger UI (http://127.0.0.1:8000/docs

⚙️ Installation & Setup

Clone the repository

git clone https://github.com/mohammedVajim/flight_booking.git
cd flight_booking

Create a virtual environment

python -m venv venv
source venv/bin/activate      # For Linux/Mac
venv\Scripts\activate         # For Windows

Install dependencies

pip install -r requirements.txt

Run the FastAPI server

uvicorn backend.main:app --reload

Open the Frontend

Simply open the index.html file in your browser.
(Default backend URL: http://127.0.0.1:8000)

💡 Future Enhancements

Integration with live airline APIs

Authentication & user login

Payment gateway support

Enhanced UI with React or Vue

🏁 Conclusion

This project demonstrates a simplified model of a flight booking system with dynamic pricing, combining clean UI, modular APIs, and a robust backend — offering a complete real-world simulation of airline booking logic.
