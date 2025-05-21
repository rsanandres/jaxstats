# JaxStats - League of Legends Stats Analysis Tool

A Python-based League of Legends stats analysis tool that uses Jax for machine learning-powered performance analysis.

## Features

- Riot Games API integration for fetching match data
- Detailed player statistics analysis
- Machine learning-powered performance rating using Jax
- Interactive web interface
- Match history analysis with highlights and lowlights

## Setup

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your Riot Games API key using one of these methods:

   **Option 1 - Using .env file:**
   Create a `.env` file in the root directory and add your Riot Games API key:
   ```
   RIOT_API_KEY=your_api_key_here
   ```

   **Option 2 - Using export command:**
   Set the environment variable in your terminal:
   ```bash
   export RIOT_API_KEY=your_api_key_here
   ```
   Note: This method only persists for your current terminal session.

5. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```
6. Open your browser and navigate to `http://localhost:8000`

## Usage

1. Enter a summoner name and select your region
2. View overall statistics and recent matches
3. Click on individual matches to see detailed analysis
4. Review the ML-powered performance rating and analysis

## Project Structure

- `app/` - Main application directory
  - `api/` - Riot Games API client
  - `analysis/` - Data processing and analysis
  - `ml/` - Jax-based machine learning models
  - `static/` - Frontend assets
  - `templates/` - HTML templates
  - `main.py` - FastAPI application entry point

## Note

This application requires a valid Riot Games API key. You can obtain one from the [Riot Games Developer Portal](https://developer.riotgames.com/).

## Local Kubernetes Deployment

For step-by-step instructions on running JaxStats locally with Kubernetes and KinD, see [DEPLOYMENT.md](./DEPLOYMENT.md). 