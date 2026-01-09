"""
FastAPI backend for SWGOH Fleet Analysis application.
Provides API endpoints for fleet matchup data and analysis.
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict
from pydantic import BaseModel
import os
from pathlib import Path
from dotenv import load_dotenv

from backend.matrix_data_processor import MatrixDataProcessor

# Pydantic models for request bodies
class DefenseSlot(BaseModel):
    capitalShip: str  # Ship ID (e.g., "CAPITALMONCALAMARICRUISER")
    startingShips: List[str]  # Ship IDs (e.g., ["RAVENSCLAW", "XWINGRED3", "UWINGROGUEONE"])

class FilteredMatrixRequest(BaseModel):
    defenseConfig: List[DefenseSlot]
    minBattles: Optional[int] = None
    seasons: Optional[List[str]] = None  # List of season IDs

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Initialize FastAPI app
app = FastAPI(
    title="SWGOH Fleet Analysis API",
    description="API for analyzing Star Wars Galaxy of Heroes fleet matchups",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data processor with multi-season support
DATA_DIR = Path(__file__).parent.parent / "data"
SHIPS_TSV = DATA_DIR / "ships.tsv"
MIN_BATTLES = int(os.getenv('MIN_BATTLES', '10'))
processor = MatrixDataProcessor(ships_tsv_path=str(SHIPS_TSV), data_dir=str(DATA_DIR))


@app.on_event("startup")
async def startup_event():
    """Initialize data on startup."""
    print("Loading fleet matchup data...")
    print(f"Found {len(processor.available_seasons)} seasons")
    for season in processor.available_seasons:
        print(f"  - {season['display_name']} ({season['id']})")

    # Build default matrix with all seasons
    if processor.available_seasons:
        all_season_ids = [s['id'] for s in processor.available_seasons]
        processor.build_processed_matrix(min_battles=MIN_BATTLES, season_ids=all_season_ids)
        print(f"Default matrix built with all {len(all_season_ids)} seasons")

    print(f"Loaded {len(processor.capital_ships)} capital ships")
    print(f"Total matchups: {len(processor.capital_ships) * len(processor.capital_ships)}")
    print(f"Minimum battles threshold: {MIN_BATTLES}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "SWGOH Fleet Analysis API - Complete Matrix Edition",
        "version": "2.0.0",
        "data_source": "Complete 10x10 matchup matrix",
        "total_matchups": len(processor.capital_ships) * len(processor.capital_ships) if processor.capital_ships else 0,
        "endpoints": {
            "/ships": "Get list of all capital ships",
            "/matchup-matrix": "Get complete matchup matrix (all attacking vs defending combinations)",
            "/matchup/{attacking_id}/{defending_id}": "Get specific matchup details"
        }
    }


@app.get("/seasons")
async def get_seasons():
    """Get list of available seasons."""
    try:
        return {
            "seasons": processor.get_available_seasons()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching seasons: {str(e)}")


@app.get("/ships")
async def get_ships():
    """Get list of all capital ships."""
    try:
        return {
            "ships": [
                {
                    "id": ship_id,
                    "name": processor.ship_names[ship_id],
                    "image": processor.ship_images.get(ship_id, '')
                }
                for ship_id in processor.capital_ships
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ships: {str(e)}")


@app.get("/matchup-matrix")
async def get_matchup_matrix(
    min_battles: int = Query(None, description="Minimum number of battles for statistical significance"),
    seasons: Optional[str] = Query(None, description="Comma-separated list of season IDs")
):
    """
    Get the complete matchup matrix for all capital ships.
    Uses the complete 10x10 matrix data with all attacking vs defending combinations.

    Args:
        min_battles: Minimum number of battles required for a matchup to be considered valid
        seasons: Comma-separated list of season IDs to include (e.g., "CHAMPIONSHIPS_GRAND_ARENA_GA2_EVENT_SEASON_73,CHAMPIONSHIPS_GRAND_ARENA_GA2_EVENT_SEASON_74")

    Returns:
        Complete matchup matrix with win rates for all ship combinations
    """
    try:
        # Use provided min_battles or default from env
        if min_battles is None:
            min_battles = MIN_BATTLES

        # Parse season IDs
        season_ids = None
        if seasons:
            season_ids = [s.strip() for s in seasons.split(',') if s.strip()]
        else:
            # Default to all seasons
            season_ids = [s['id'] for s in processor.available_seasons]

        # Rebuild matrix with specified parameters
        matrix = processor.build_processed_matrix(min_battles=min_battles, season_ids=season_ids)

        # Simplify the response for the heatmap
        simplified_matrix = {
            'ship_ids': matrix['ship_ids'],
            'ship_names': matrix['ship_names'],
            'data': []
        }

        # Convert to array format for easier frontend consumption
        for defending_id in matrix['ship_ids']:
            row = {
                'defending_ship_id': defending_id,
                'defending_ship_name': matrix['ship_names'].get(defending_id, defending_id),
                'matchups': []
            }

            for attacking_id in matrix['ship_ids']:
                matchup = matrix['matchups'][defending_id][attacking_id]

                # Map fleet names if lineup exists
                attacking_fleet = None
                defending_fleet = None
                if matchup.get('lineup'):
                    attacking_fleet = processor._map_fleet_names(matchup['lineup'].get('attacking_fleet'))
                    defending_fleet = processor._map_fleet_names(matchup['lineup'].get('defending_fleet'))

                row['matchups'].append({
                    'attacking_ship_id': attacking_id,
                    'attacking_ship_name': matrix['ship_names'].get(attacking_id, attacking_id),
                    'win_rate': matchup['win_rate'],
                    'win_rate_percent': matchup['win_rate_percent'],
                    'battle_count': matchup['battle_count'],
                    'has_data': matchup['has_data'],
                    'attacking_fleet': attacking_fleet,
                    'defending_fleet': defending_fleet
                })

            simplified_matrix['data'].append(row)

        return simplified_matrix

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building matchup matrix: {str(e)}")


@app.post("/matchup-matrix/filtered")
async def get_filtered_matchup_matrix(request: FilteredMatrixRequest):
    """
    Get matchup matrix filtered by specific defense configurations.
    This endpoint finds the best lineups that match the specified defending starting ships.

    Args:
        request: Defense configuration with capital ships and starting ships

    Returns:
        Filtered matchup matrix with lineups matching the defense configuration
    """
    try:
        min_battles = request.minBattles if request.minBattles is not None else MIN_BATTLES

        # Get season IDs
        season_ids = request.seasons if request.seasons else [s['id'] for s in processor.available_seasons]

        # Build a custom matrix based on defense configuration
        matrix = {
            'ship_ids': processor.capital_ships,
            'ship_names': processor.ship_names,
            'ship_images': processor.ship_images,
            'data': [],
            'seasons': season_ids
        }

        # Process each defense configuration
        for defense_slot in request.defenseConfig:
            if not defense_slot.capitalShip:
                continue

            defending_id = defense_slot.capitalShip

            # Filter starting ships to non-empty values
            # These are already ship IDs from the frontend in uppercase format
            selected_starting_ship_ids = [ship for ship in defense_slot.startingShips if ship]

            # Ship IDs should already be in uppercase format to match raw data
            starting_ship_ids = selected_starting_ship_ids

            row = {
                'defending_ship_id': defending_id,
                'defending_ship_name': processor.ship_names.get(defending_id, defending_id),
                'matchups': []
            }

            # Get matchups for each attacking ship
            for attacking_id in processor.capital_ships:
                # Calculate best matchup with defense starting ship filter
                win_rate, battle_count, lineup = processor._calculate_best_matchup(
                    attacking_id,
                    defending_id,
                    min_battles=min_battles,
                    defending_starting_ships=starting_ship_ids if starting_ship_ids else None,
                    season_ids=season_ids
                )

                # Map fleet names if lineup exists
                attacking_fleet = None
                defending_fleet = None
                if lineup:
                    attacking_fleet = processor._map_fleet_names(lineup.get('attacking_fleet'))
                    defending_fleet = processor._map_fleet_names(lineup.get('defending_fleet'))

                row['matchups'].append({
                    'attacking_ship_id': attacking_id,
                    'attacking_ship_name': processor.ship_names.get(attacking_id, attacking_id),
                    'win_rate': win_rate,
                    'win_rate_percent': f"{win_rate * 100:.1f}%",
                    'battle_count': battle_count,
                    'has_data': battle_count >= min_battles,
                    'attacking_fleet': attacking_fleet,
                    'defending_fleet': defending_fleet
                })

            matrix['data'].append(row)

        return matrix

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building filtered matchup matrix: {str(e)}")


@app.get("/matchup/{attacking_id}/{defending_id}")
async def get_matchup_details(
    attacking_id: str,
    defending_id: str,
    seasons: Optional[str] = Query(None, description="Comma-separated list of season IDs")
):
    """
    Get detailed information about a specific matchup.

    Args:
        attacking_id: ID of the attacking capital ship
        defending_id: ID of the defending capital ship
        seasons: Comma-separated list of season IDs to include

    Returns:
        Detailed matchup information including fleet compositions
    """
    try:
        # Parse season IDs
        season_ids = None
        if seasons:
            season_ids = [s.strip() for s in seasons.split(',') if s.strip()]
        else:
            # Default to all seasons
            season_ids = [s['id'] for s in processor.available_seasons]

        # Rebuild matrix with specified seasons if needed
        if season_ids:
            processor.build_processed_matrix(min_battles=MIN_BATTLES, season_ids=season_ids)

        summary = processor.get_matchup_summary(attacking_id, defending_id)

        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"Matchup not found for {attacking_id} vs {defending_id}"
            )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching matchup details: {str(e)}")


@app.post("/defense-lineup-info")
async def get_defense_lineup_info(request: FilteredMatrixRequest):
    """
    Get the most common defending lineup information for specific defense configurations.
    Returns the reinforcements and total battles for each defense slot.

    Args:
        request: Defense configuration with capital ships and starting ships

    Returns:
        List of defense lineup information including reinforcements and battle counts
    """
    try:
        min_battles = request.minBattles if request.minBattles is not None else MIN_BATTLES

        # Get season IDs
        season_ids = request.seasons if request.seasons else [s['id'] for s in processor.available_seasons]

        lineup_info = []

        for defense_slot in request.defenseConfig:
            if not defense_slot.capitalShip:
                continue

            defending_id = defense_slot.capitalShip

            # Filter starting ships to non-empty values
            selected_starting_ship_ids = [ship for ship in defense_slot.startingShips if ship]

            if len(selected_starting_ship_ids) != 3:
                # Only provide info when all 3 starting ships are selected
                continue

            # Ship IDs should already be in uppercase format to match raw data
            starting_ship_ids = selected_starting_ship_ids

            # Find the most common defending lineup across all attacking matchups
            # We'll aggregate data from all attacking ships to find the most common defending setup
            defending_lineups = {}

            for attacking_id in processor.capital_ships:
                _, battle_count, lineup = processor._calculate_best_matchup(
                    attacking_id,
                    defending_id,
                    min_battles=min_battles,
                    defending_starting_ships=starting_ship_ids,
                    season_ids=season_ids
                )

                if lineup and battle_count > 0:
                    defending_fleet = lineup.get('defending_fleet', {})
                    reinforcements = defending_fleet.get('reinforcements', [])

                    # Create a key for this reinforcement setup
                    reinforcement_key = tuple(sorted(reinforcements))

                    if reinforcement_key not in defending_lineups:
                        defending_lineups[reinforcement_key] = {
                            'reinforcements': reinforcements,
                            'total_battles': 0
                        }

                    defending_lineups[reinforcement_key]['total_battles'] += battle_count

            # Find the most common reinforcement setup
            if defending_lineups:
                most_common = max(defending_lineups.values(), key=lambda x: x['total_battles'])

                # Map ship names and images - try uppercase first, then lowercase, then capitalized
                reinforcement_names = []
                reinforcement_images = []
                for ship_id in most_common['reinforcements']:
                    # Try uppercase (standard format)
                    name = processor.ship_names.get(ship_id.upper())
                    image = processor.ship_images.get(ship_id.upper(), '')
                    if not name:
                        # Try lowercase
                        name = processor.ship_names.get(ship_id.lower())
                        image = processor.ship_images.get(ship_id.lower(), '')
                    if not name:
                        # Try as-is
                        name = processor.ship_names.get(ship_id)
                        image = processor.ship_images.get(ship_id, '')
                    reinforcement_names.append(name or ship_id)
                    reinforcement_images.append(image)

                lineup_info.append({
                    'capitalShip': defending_id,
                    'capitalShipName': processor.ship_names.get(defending_id, defending_id),
                    'startingShips': selected_starting_ship_ids,
                    'reinforcements': most_common['reinforcements'],
                    'reinforcementNames': reinforcement_names,
                    'reinforcementImages': reinforcement_images,
                    'totalBattles': most_common['total_battles']
                })

        return {'lineups': lineup_info}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching defense lineup info: {str(e)}")


@app.get("/roster/common-starting-ships/{capital_ship_id}")
async def get_common_starting_ships(capital_ship_id: str, top_n: int = Query(10, description="Number of top ships to return")):
    """
    Get the most common starting ships for a specific capital ship.

    Args:
        capital_ship_id: ID of the capital ship
        top_n: Number of top ships to return

    Returns:
        List of most common starting ships
    """
    try:
        ships = processor.get_common_starting_ships(capital_ship_id, top_n)
        return {
            "capital_ship_id": capital_ship_id,
            "capital_ship_name": processor.ship_names.get(capital_ship_id, capital_ship_id),
            "common_starting_ships": ships
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching common starting ships: {str(e)}")


@app.get("/roster/all-ships")
async def get_all_ships_roster():
    """
    Get all available ships organized by type and faction.

    Returns:
        Dictionary with capital ships and regular ships organized by faction
    """
    try:
        capital_ships = [
            {
                "id": ship_id,
                "name": processor.ship_names.get(ship_id, ship_id),
                "faction": processor.ship_factions.get(ship_id, "Other"),
                "image": processor.ship_images.get(ship_id, '')
            }
            for ship_id in processor.capital_ships
        ]

        regular_ships_by_faction = processor.get_all_regular_ships_with_factions()

        return {
            "capital_ships": capital_ships,
            "regular_ships": processor.get_all_regular_ships(),  # Keep for backward compatibility
            "regular_ships_by_faction": regular_ships_by_faction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ship roster: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    backend_host = os.getenv('BACKEND_HOST', '0.0.0.0')
    backend_port = int(os.getenv('BACKEND_PORT', '8000'))
    uvicorn.run(app, host=backend_host, port=backend_port)

