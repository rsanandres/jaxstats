# JaxStats

JaxStats is a League of Legends replay analysis tool that allows users to upload and analyze their game replays.

## Features

- Upload and manage League of Legends replay files (.rofl)
- View replay data in an interactive visualization
- Track champion positions and game events
- Analyze player performance and game statistics

## Prerequisites

- Docker and Docker Compose
- Node.js 16+ (for local frontend development)
- Python 3.9+ (for local backend development)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/jaxstats.git
cd jaxstats
```

2. Build and start the services using Docker Compose:
```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost
- Backend API: http://localhost:8000

## Development

### Backend

The backend is built with FastAPI and provides the following API endpoints:

- `GET /api/replays` - List all available replays
- `GET /api/replays/{match_id}` - Get replay data for a specific match
- `POST /api/replays/upload` - Upload a new replay file

To run the backend locally:

```bash
cd jaxstats
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

The frontend is built with React and Material-UI. To run it locally:

```bash
cd jaxstats/frontend
npm install
npm start
```

## Project Structure

```
jaxstats/
├── app/                    # Backend application
│   ├── api/               # API routes and clients
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   └── main.py           # FastAPI application
├── frontend/              # Frontend application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── types/        # TypeScript types
│   │   └── App.tsx       # Main application
│   └── package.json
├── data/                  # Data storage
│   └── replays/          # Replay files
├── Dockerfile            # Backend Dockerfile
├── docker-compose.yml    # Docker Compose configuration
└── requirements.txt      # Python dependencies
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 