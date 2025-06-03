# 📈 StockiNews

**StockiNews** is a robust, full-stack web application that leverages **Vite + React** for a high-performance frontend and **Flask** for a scalable backend. The platform is tailored for Indian stock market enthusiasts, offering a comprehensive suite of tools for portfolio management, real-time stock monitoring, sentiment analysis, and curated news aggregation—all within a modern, responsive interface.

---

## 🧭 Purpose

StockiNews aims to empower retail investors by unifying personal portfolio insights, live stock updates, and market news sentiment analysis. The goal is to simplify financial decision-making and help users track investments and market trends at a glance.

---

## 🌟 Features

### 🔐 Authentication
- **JWT-based authentication** for secure, tokenized sessions.
- Protected routes and user-specific data access.
- All authentication flows handled via RESTful endpoints.

### 📊 Dashboard Components
- **💼 Portfolio Panel**
  - Real-time summary of holdings, values, and returns.
  - Interactive: click-through for detailed stock breakdown.
- **📈 Market Watch**
  - Live updates on major indices and commodities.
- **👀 Watchlist**
  - Track shortlisted stocks with live prices and daily percentage changes.
  - Clickable for in-depth stock details.
- **📰 News Panel**
  - Aggregated, real-time news specific to Indian markets.
  - Direct links to original news sources.

### 📂 Portfolio Management
- Add, sell, and track stocks in real time.
- Automatic P&L (Profit & Loss) calculations.
- Downloadable **PDF reports** for record-keeping.
- Visual performance analytics and interactive charts.
- Clickable portfolio items for granular analysis.

### 📄 Stock Detail Page
- **Live Chart**: Interactive, 6-month price chart powered by **Chart.js**.
- **Sentiment Analysis**: Real-time news sentiment gauge and categorized headlines.
- **News Feed**: Expandable news items, sentiment tags, and direct links.

---

## 🏗️ Project Structure
STOCKINEWS/
│
├── public/
│ └── images/
│ ├── logo.png
│ └── vite.svg
│
├── src/
│ ├── assets/
│ ├── backend/ # Flask backend, DB, .env, app.py (API routes)
│ ├── banner/
│ ├── Chartgen/
│ ├── dashboard/ # Portfolio, watchlist, market watch, news
│ ├── home/ # Landing page
│ ├── Login/ # Auth components & styles
│ ├── Portfolio/ # Portfolio management logic & UI
│ ├── Sentiment/ # Sentiment gauge & logic
│ ├── Stock/ # Stock detail: chart, news, sentiment
│ ├── App.css # Shared CSS
│ ├── App.jsx # Main React app, routing
│ ├── App.test.js # Unit tests
│ ├── index.css # Global styles
│ ├── index.js # React entry point
│ ├── logo.svg
│ ├── main.jsx # Vite entry
│ ├── reportWebVitals.js
│ └── setupTests.js
│
├── .gitignore
├── eslint.config.js
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
└── README.md


- **Frontend** and **backend** code are organized for modularity and scalability, following best practices for React and Flask integration.
- The **src/backend/** directory contains the Flask API, database models, environment configuration, and core backend logic.
- Feature-based subfolders in **src/** (e.g., Portfolio, Sentiment, Stock) promote separation of concerns and ease of maintenance.

---

## 🔧 Technologies Used

### 🖼️ Frontend
- **Vite + React** for a fast, modern development experience.
- **Bootstrap 5** for responsive, accessible UI components.
- **Chart.js** for dynamic, interactive data visualization.
- **Custom CSS** with variables for theming and maintainability.

### 🧪 Backend
- **Python Flask**: Lightweight, extensible API server.
- **SQLite**: Simple, file-based relational database.
- **JWT Authentication**: Secure, stateless sessions via `PyJWT`.
- **CORS**: Cross-origin resource sharing for API consumption.
- **REST API**: Clean, resource-oriented endpoints.

---

## 🔐 Authentication Flow

1. User logs in via the `/login` route on the frontend.
2. Flask backend verifies credentials and issues a **JWT token**.
3. The token is stored client-side (e.g., localStorage) and attached to all authenticated API requests.
4. The backend decodes the token to authorize and serve user-specific resources.
5. Protected routes and sensitive data are only accessible with a valid token.

---

## 🚀 Development Workflow

### Backend (Flask)
cd src/backend
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py


### Frontend (Vite + React)
npm install
npm run dev


- The frontend runs on `localhost:5173` (default Vite port).
- The backend API is typically served on `localhost:5000`.
- Ensure CORS is enabled in Flask for local development.

---

## 🧩 Best Practices & Architecture

- **Two-Tier Architecture**: React frontend and Flask backend are decoupled, communicating over RESTful APIs. This separation improves development speed, testability, and deployment flexibility.
- **Modular Codebase**: Both frontend and backend are organized into feature-based modules, making it easy to scale and maintain.
- **Security**: JWT tokens, secure password handling, and protected API endpoints safeguard user data.
- **Testing**: Unit and integration tests for both frontend (Jest/React Testing Library) and backend (pytest/Flask-Testing) ensure reliability.
- **Error Handling**: Robust error handling on both client and server for a smooth user experience.

---

## 🛣️ Roadmap & Future Enhancements

- Real-time updates via WebSockets for live stock prices and news.
- User customization: theme switching, notification preferences.
- Advanced analytics: technical indicators, backtesting tools.
- Multi-user support with roles and permissions.
- Deployment automation with Docker and CI/CD pipelines.
- Add indicators with real time forecasting with buy and sell calls.

---

## 🤝 Contributing

Contributions are welcome! Please open issues or submit pull requests for feature requests, bug fixes, or documentation improvements.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 📚 References & Further Reading

- [Full-Stack Flask and React (Packt)](https://imp.dayawisesa.com/wp-content/uploads/2024/03/Full_Stack_Flask_and_React_Learn_code_and_deploy_powerful_web.pdf)
- [Flask & React Full Stack Seed Projects (AppSeed)](https://blog.appseed.us/flask-react-full-stack-seed-projects/)

---