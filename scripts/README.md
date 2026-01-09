# SWGOH Fleet Analysis - Data Scraping Scripts

This directory contains scripts for scraping fleet matchup data from SWGOH.GG.

## Scripts

### `scrape_matchup_data.py`
Main script for scraping the complete matchup matrix data for all capital ships.

**Usage:**
```bash
cd scripts
python scrape_matchup_data.py
```

**What it does:**
- Scrapes matchup data for all 11 capital ships (121 total matchups)
- For each matchup, gets the best counter lineups with win rates
- Filters lineups by minimum battle count (configurable via `.env`)
- Saves data to `data/complete_matchup_matrix.json`

**Configuration:**
Set these in the `.env` file in the project root:
- `SWGOH_API_KEY` - Your SWGOH.GG API key
- `SEASON_ID` - Current GAC season ID
- `MIN_BATTLES` - Minimum battles for statistical significance (default: 10)

### `swgoh_fleet_scraper.py`
Core scraper library used by the main script. Contains the `SWGOHFleetScraper` class with methods for:
- Extracting fleet counter data
- Parsing lineup information
- Formatting ship names

## Data Output

The scraper generates `data/complete_matchup_matrix.json` with this structure:
```json
{
  "capital_ships": ["CAPITALEXECUTOR", "CAPITALLEVIATHAN", ...],
  "ship_names": {"CAPITALEXECUTOR": "Executor", ...},
  "matchups": {
    "DEFENDING_SHIP_ID": {
      "ATTACKING_SHIP_ID": {
        "counter_lineups": [
          {
            "win_rate": "95.5%",
            "times_seen": "42",
            "attacking_fleet": {...},
            "defending_fleet": {...}
          }
        ]
      }
    }
  }
}
```

## Requirements

Install dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- beautifulsoup4
- requests
- python-dotenv

## Notes

- The scraper respects rate limits with delays between requests
- Progress is shown during scraping
- Data is saved incrementally to prevent loss on errors
- Ship names are mapped using `data/ships.tsv`

