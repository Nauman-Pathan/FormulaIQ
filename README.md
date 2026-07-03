# 🏎️ FormulaIQ — AI-Powered F1 Analytics Platform

FormulaIQ is a full-stack Formula 1 analytics platform that combines real-time telemetry data (via FastF1), machine learning race predictions (XGBoost), and an advanced **Deep Reinforcement Learning (PPO) AI Race Strategist**.

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 📊 **Dashboard** | Season overview, race calendar, key stats |
| 🧠 **Race Predictor** | XGBoost model predicting finishing positions with win/podium/DNF probabilities |
| 📡 **Telemetry Analyzer** | Speed, throttle, brake, gear, DRS, lap delta, track map |
| 👥 **Driver Comparison** | Consistency score, overtaking efficiency, racecraft radar |
| 🔄 **Strategy Simulator** | Pit timing optimizer with tyre degradation model |
| 🤖 **AI Strategy Engine** | Deep RL (PPO) agent for optimal pitstop timing — simulates full races + live recommendations |
| 📅 **Historical Analytics** | Query 2022–2026 race data with Plotly charts |

---

## 🗂️ Project Structure

```
formulaIQ/
├── backend/
│   ├── app/              # Config, logging
│   ├── api/              # FastAPI routers
│   ├── data_pipeline/    # FastF1 ETL (fetch → preprocess → save)
│   ├── database/         # SQLAlchemy engine, Alembic migrations
│   ├── ml/               # Feature engineering, XGBoost training, inference
│   ├── models/           # ORM models + Pydantic schemas
│   ├── rl_strategy/      # PPO Deep RL race strategy agent (Gymnasium + custom env)
│   │   ├── env.py            # F1StrategyEnv — custom Gymnasium environment
│   │   ├── reward.py         # Reward function (position gain, tyre life, SC windows)
│   │   ├── train_agent.py    # PPO training loop
│   │   ├── simulate_agent.py # Full race simulation using trained agent
│   │   ├── state_encoder.py  # 15-dim observation vector encoder
│   │   └── config.py         # Hyperparameters
│   ├── services/         # Telemetry, strategy, driver analytics
│   ├── utils/            # Redis cache helpers
│   └── main.py           # FastAPI app entry
│
└── frontend/
    └── src/
        ├── pages/        # Dashboard, RacePredictor, Telemetry, Drivers, Strategy, AIStrategist, Historical
        ├── components/   # Layout, LoadingSpinner
        ├── services/     # Axios API layer
        └── hooks/        # React Query hooks
```

---

## 🚀 Quick Start

### Backend

```bash
cd backend

# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure env
cp .env.example .env
# Edit .env with your PostgreSQL + Redis credentials

# 4. Create database schema
python -c "from database.db import sync_engine; from models.orm import Base; Base.metadata.create_all(sync_engine)"

# 5. Run ETL pipeline (fetches 2022–2026 data)
python data_pipeline/save_to_db.py --season 2024 --rounds 1 2 3

# 6. Train ML model
python ml/train_model.py --seasons 2022 2023 2024 2025

# 7. (Optional) Train the RL agent
python rl_strategy/train_agent.py

# 8. Start API server
python main.py
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start dev server
npm run dev
# App available at http://localhost:3000
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/races` | List all races |
| `GET` | `/api/v1/races/{id}/results` | Race results |
| `GET` | `/api/v1/drivers` | List all drivers |
| `GET` | `/api/v1/circuits` | List all circuits |
| `GET` | `/api/v1/telemetry/{year}/{gp}/{d1}/{d2}` | Telemetry comparison |
| `POST` | `/api/v1/predict-race` | Race outcome prediction |
| `POST` | `/api/v1/simulate-strategy` | Rule-based strategy simulation |
| `GET` | `/api/v1/driver-analysis/{code}` | Driver analytics |
| `GET` | `/api/v1/historical-results` | Filtered historical data |
| `POST` | `/api/v1/rl-strategy/simulate` | Full race simulation using PPO agent |
| `POST` | `/api/v1/rl-strategy/recommend` | Live lap-by-lap RL recommendation |
| `POST` | `/api/v1/rl-strategy/train` | Trigger RL agent background training |
| `GET` | `/api/v1/rl-strategy/status` | Check agent training/checkpoint status |

---

## 🤖 AI Strategy Engine (RL)

The **AI Strategy Engine** is a deep reinforcement learning agent trained using **PPO (Proximal Policy Optimization)** on a custom Gymnasium F1 race environment.

### Observation Space (15 dims)
| Feature | Range |
|---------|-------|
| Current lap | 1–80 |
| Total laps | 1–80 |
| Tyre compound | Soft/Medium/Hard |
| Tyre age | 0–80 laps |
| Tyre degradation | 0–100% |
| Track temperature | 15–55°C |
| Weather condition | Dry / Wet |
| Safety car probability | 0–50% |
| Competitor avg tyre age | 0–80 laps |
| Competitor pit status | 0/1 |
| Current position | P1–P20 |
| Lap delta ahead | seconds |
| Lap delta behind | seconds |
| Fuel load | 0–110kg |
| Track type | Permanent / Street |

### Action Space
`0` = Stay Out | `1` = Pit for Soft | `2` = Pit for Medium | `3` = Pit for Hard

### Rule-Based Fallback Guardrail
The RL policy is constrained by a safety window rule-base to prevent:
- Pitting within first 8 laps of a stint
- Pitting in the final 3 laps of a race
- Pitting on fresh tyres with <45% degradation (unless safety car active)

---

## 🧠 ML Race Predictor

- **Algorithm**: XGBoost (position regression + DNF binary classifier)
- **Features**: Grid position, qualifying time, prev-3-race avg finish, cumulative points, tyre strategy, weather, circuit type, pit stop data
- **Training**: 2022–2025 seasons with 5-fold cross-validation
- **Output**: Predicted position + win/podium/top10/DNF probabilities per driver

```bash
# Retrain with latest data
python ml/train_model.py --seasons 2022 2023 2024 2025 --version v2
```

---

## 🚢 Deployment

### Backend → Render
1. Connect GitHub repo on [render.com](https://render.com)
2. Create new Web Service, point to `backend/`
3. Set env vars: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`
4. Deploy

### Frontend → Vercel
1. Connect GitHub repo on [vercel.com](https://vercel.com)
2. Set root directory to `frontend/`
3. Set `VITE_API_URL` → your Render backend URL
4. Deploy

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2, asyncpg |
| **Data** | FastF1 3.x, Pandas, NumPy |
| **ML** | XGBoost, Scikit-learn, Joblib |
| **RL Agent** | Gymnasium, PPO (custom implementation) |
| **Database** | PostgreSQL 15, Redis 7 |
| **Frontend** | React 18, TypeScript, Vite |
| **Styling** | TailwindCSS 3, Framer Motion |
| **Charts** | Plotly.js (react-plotly.js) |
| **State** | TanStack Query v5 |
| **Deploy** | Render (backend) + Vercel (frontend) |
