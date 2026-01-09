# SWGOH Fleet Analysis Dashboard

> A comprehensive full-stack web application for analyzing Star Wars Galaxy of Heroes fleet matchups in Grand Arena Championship.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)
![Vue.js](https://img.shields.io/badge/Vue.js-3.4.15-brightgreen.svg)
![Vite](https://img.shields.io/badge/Vite-5.0.11-purple.svg)

## 🚀 Quick Start

### Backend
```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173` in your browser (Vite default port).

## 🎯 Features

- **Interactive Heatmap**: Visual representation of capital ship matchup win rates across all 10x10 combinations
- **Multi-Season Analysis**: Compare and analyze data across multiple GAC seasons (73, 74, and more)
- **Detailed Fleet Compositions**: Click any cell to view attacking and defending fleet lineups
- **Defense Configuration Tool**: Build custom defense setups and see optimal counters
- **Attack Strategy Planner**: Analyze attack rosters and find best matchups
- **Real GAC Data**: Based on actual battle statistics from SWGOH.GG
- **Responsive Design**: Works on desktop and mobile devices
- **Statistical Filtering**: Only shows matchups with 10+ battles for reliability
- **Ship Roster Management**: Browse all capital and regular ships organized by faction
- **Data Scraping Tools**: Python scripts to collect and update data from SWGOH.GG

## 📁 Project Structure

```
fleet-analysis/
├── backend/                          # FastAPI application
│   ├── main.py                      # API endpoints (v2.0.0)
│   └── matrix_data_processor.py     # Multi-season data processing
├── frontend/                         # Vue.js 3 + Vite application
│   ├── src/
│   │   ├── components/              # Vue components
│   │   │   ├── HeatmapTable.vue
│   │   │   ├── DefenseSetup.vue
│   │   │   ├── AttackStrategy.vue
│   │   │   ├── AttackRoster.vue
│   │   │   ├── SeasonSelector.vue
│   │   │   └── ...
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── style.css
│   ├── vite.config.js
│   └── package.json
├── scripts/                          # Data scraping tools
│   ├── scrape_matchup_data.py       # Main scraper
│   └── swgoh_fleet_scraper.py       # Scraper library
├── data/                             # Data files
│   ├── complete_matchup_matrix_*.json
│   ├── ships.tsv                    # Ship metadata
│   └── ships.sql
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

## 🛠️ Technology Stack

- **Backend**: FastAPI 0.109.0, Python 3.8+, Uvicorn 0.27.0
- **Frontend**: Vue.js 3.4.15, Vite 5.0.11, Axios 1.6.5
- **Data Processing**: BeautifulSoup4, Requests, Pydantic
- **Data Source**: SWGOH.GG GAC statistics
- **Data Format**: JSON (matchup matrices), TSV (ship metadata)

## 📊 Data Methodology

The application analyzes real GAC battle data across multiple seasons to determine optimal fleet matchups:

1. **Multi-Season Support**: Aggregates data from multiple GAC seasons (currently seasons 73-74)
2. **Statistical Filtering**: Only includes matchups with 10+ battles for statistical significance
3. **Complete Matrix**: Analyzes all 10x10 capital ship combinations (100 total matchups)
4. **Win Rate Calculation**: Identifies the highest win rate for each attacking vs defending ship combination
5. **Fleet Composition Tracking**: Records detailed lineup information including starting ships and reinforcements
6. **Interactive Visualization**: Displays results in a color-coded heatmap with drill-down capabilities
7. **Defense Configuration**: Allows filtering by specific defense starting ship combinations

## 🔧 Data Scraping

The project includes Python scripts to scrape fleet data from SWGOH.GG:

```bash
cd scripts
python scrape_matchup_data.py
```

This will collect detailed matchup data for all capital ships and save it to the `data/` directory with season-specific filenames.

**Configuration** (in `.env`):
```
SWGOH_API_KEY=your_api_key_here
SEASON_NUMBERS=73,74
MIN_BATTLES=10
```

## 📡 API Endpoints

The backend provides the following REST API endpoints:

- `GET /` - API information and available endpoints
- `GET /seasons` - List available GAC seasons
- `GET /ships` - Get all capital ships with names and images
- `GET /matchup-matrix` - Get complete matchup matrix (supports season filtering)
- `GET /matchup/{attacking_id}/{defending_id}` - Get specific matchup details
- `POST /matchup-matrix/filtered` - Get filtered matrix by defense configuration
- `POST /defense-lineup-info` - Get most common defense lineups
- `GET /roster/common-starting-ships/{capital_ship_id}` - Get common starting ships
- `GET /roster/all-ships` - Get all ships organized by faction

See [API Documentation](docs/README.md) for detailed endpoint specifications.

## 🧪 Development

### Running Locally

1. **Backend**:
   ```bash
   pip install -r requirements.txt
   python -m uvicorn backend.main:app --reload
   ```
   Backend runs on `http://localhost:8000`

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Frontend runs on `http://localhost:5173`

### Project Status

- ✅ Multi-season data support (seasons 73-74)
- ✅ Complete 10x10 matchup matrix
- ✅ Defense configuration filtering
- ✅ Attack strategy planning
- ✅ Ship roster management
- ✅ Responsive UI with Vue.js 3
- ✅ RESTful API with FastAPI

## 🤝 Contributing

Contributions welcome! Please check the [documentation](docs/README.md) for development guidelines.

## 📝 License

Educational and analytical purposes only. SWGOH is owned by Electronic Arts and Capital Games.

## 🙏 Acknowledgments

Data sourced from [SWGOH.GG](https://swgoh.gg) - built for the SWGOH community.

