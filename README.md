# Exasol MEVShield

MEVShield is a real-time MEV (Miner Extractable Value) monitoring and protection system built for the Exasol blockchain ecosystem.

## Overview

This project consists of:
- A FastAPI backend server that processes blockchain transactions and detects MEV opportunities
- A React frontend dashboard for visualizing transaction data, statistics, and controlling the monitoring stream
- Machine learning models for predicting and classifying MEV transactions

## Architecture

MEVShield follows a three-tier architecture:

1. **Backend (API Server)**: Built with FastAPI, it handles:
   - Receiving and processing blockchain transactions
   - Running machine learning models for MEV detection
   - Managing the transaction stream and state
   - Providing RESTful endpoints for the frontend

2. **Frontend (Dashboard)**: Built with React and Vite, it provides:
   - Real-time visualization of transaction data
   - Controls to start/pause/reset the monitoring stream
   - Statistics and charts for MEV analysis

3. **Machine Learning Models**: Stored and loaded by the backend, these models:
   - Classify transactions as MEV or non-MEV
   - Predict potential MEV opportunities

The frontend communicates with the backend via HTTP requests to the API endpoints.

## Features

- Real-time transaction monitoring
- MEV detection and classification
- Interactive dashboard with transaction tables and statistics
- Stream control (start/pause/reset)
- RESTful API for data access
- Docker-ready setup

## Project Structure

```
Exasol_MEVShield-main/
├── backend/                 # Python/FastAPI backend
│   ├── main.py              # Entry point for the API server
│   ├── model.py             # Machine learning model handling
│   ├── stream.py            # Transaction streaming logic
│   ├── database.py          # Database interactions
│   ├── requirements.txt     # Python dependencies
│   └── ...                  # Other backend files
├── frontend/                # React frontend
│   ├── src/                 # Source code
│   │   ├── api/             # API service functions
│   │   ├── components/      # React components
│   │   └── ...              # Other frontend files
│   ├── package.json         # Frontend dependencies
│   └── vite.config.js       # Vite configuration
└── README.md                # This file
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+ and npm
- (Optional) Docker and Docker Compose

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the server:
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`

### Docker Setup (Alternative)

1. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```
   (Note: You may need to create a docker-compose.yml file first)

## API Endpoints

- `GET /` - Root endpoint with welcome message
- `GET /api/health` - Health check endpoint
- `POST /api/start` - Start the transaction stream
- `POST /api/pause` - Pause the transaction stream
- `POST /api/reset` - Reset the stream and clear data
- `GET /api/status` - Get current stream status
- `GET /api/transactions` - Get list of transactions (advances stream by one if running)
- `GET /api/statistics` - Get transaction statistics

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Your Name - [your.email@example.com](mailto:your.email@example.com)

Project Link: [https://github.com/yourusername/Exasol_MEVShield](https://github.com/yourusername/Exasol_MEVShield)