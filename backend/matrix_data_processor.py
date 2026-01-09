"""
Data processing logic for complete matchup matrix.
Processes the comprehensive attacking vs defending ship data.
Supports multi-season data aggregation.
"""

import json
import csv
import glob
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from pathlib import Path


class MatrixDataProcessor:
    """Process complete matchup matrix data for all ship combinations with multi-season support."""

    def __init__(self, matrix_file_path: str = None, ships_tsv_path: str = None, data_dir: str = None):
        """
        Initialize the processor with complete matrix data.

        Args:
            matrix_file_path: Path to a single complete_matchup_matrix.json file (deprecated)
            ships_tsv_path: Optional path to ships.tsv file with ship names
            data_dir: Path to directory containing season data files (preferred)
        """
        self.data_dir = data_dir
        self.available_seasons = []
        self.season_data = {}  # Cache for loaded season data

        # Load ship names, factions, and images from TSV
        if ships_tsv_path and Path(ships_tsv_path).exists():
            self.ship_names, self.ship_factions, self.ship_images = self._load_ship_data_from_tsv(ships_tsv_path)
        else:
            self.ship_names = {}
            self.ship_factions = {}
            self.ship_images = {}

        # Discover available seasons if data_dir provided
        if data_dir:
            self._discover_seasons()

        # For backward compatibility, load single file if provided
        if matrix_file_path and Path(matrix_file_path).exists():
            with open(matrix_file_path, 'r', encoding='utf-8') as f:
                self.matrix_data = json.load(f)
            # Update ship names if not loaded from TSV
            if not self.ship_names:
                self.ship_names = self.matrix_data.get('ship_names', {})
        else:
            self.matrix_data = None

        # Get capital ships from first available season or matrix data
        if self.available_seasons:
            first_season_data = self._load_season_data(self.available_seasons[0]['id'])
            self.capital_ships = first_season_data.get('capital_ships', [])
            if not self.ship_names:
                self.ship_names.update(first_season_data.get('ship_names', {}))
        elif self.matrix_data:
            self.capital_ships = self.matrix_data.get('capital_ships', [])
        else:
            self.capital_ships = []

        self.processed_matrix = None

    def _discover_seasons(self):
        """Discover available season data files in the data directory."""
        if not self.data_dir:
            return

        pattern = str(Path(self.data_dir) / 'complete_matchup_matrix_*.json')
        season_files = glob.glob(pattern)

        for file_path in sorted(season_files):
            # Extract season number from filename
            filename = Path(file_path).name
            # Format: complete_matchup_matrix_73.json
            if filename.startswith('complete_matchup_matrix_') and filename.endswith('.json'):
                season_num = filename.replace('complete_matchup_matrix_', '').replace('.json', '')
                season_id = f'CHAMPIONSHIPS_GRAND_ARENA_GA2_EVENT_SEASON_{season_num}'

                self.available_seasons.append({
                    'id': season_id,
                    'number': season_num,
                    'file_path': file_path,
                    'display_name': f'Season {season_num}'
                })

    def _load_season_data(self, season_id: str) -> Dict:
        """Load data for a specific season (with caching)."""
        if season_id in self.season_data:
            return self.season_data[season_id]

        # Find the season file
        season_info = next((s for s in self.available_seasons if s['id'] == season_id), None)
        if not season_info:
            return {}

        with open(season_info['file_path'], 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.season_data[season_id] = data
        return data

    def get_available_seasons(self) -> List[Dict]:
        """Get list of available seasons."""
        return self.available_seasons

    def _load_ship_data_from_tsv(self, tsv_path: str) -> tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """Load ship names, factions, and images from TSV file."""
        ship_names = {}
        ship_factions = {}
        ship_images = {}
        with open(tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                ship_id = row.get('ship_id', '').strip()
                ship_name = row.get('ship_name', '').strip()
                faction = row.get('faction', '').strip()
                image = row.get('image', '').strip()
                if ship_id and ship_name:
                    ship_names[ship_id] = ship_name
                    # Also add lowercase version for matching
                    ship_names[ship_id.lower()] = ship_name
                    if faction:
                        ship_factions[ship_id] = faction
                        ship_factions[ship_id.lower()] = faction
                    if image:
                        ship_images[ship_id] = image
                        ship_images[ship_id.lower()] = image
        return ship_names, ship_factions, ship_images

    def _map_ship_name(self, ship_id_or_name: str, is_capital_ship: bool = False) -> str:
        """
        Map a ship ID or formatted name to its proper display name.

        Args:
            ship_id_or_name: Ship ID (e.g., 'PUNISHINGONE') or formatted name (e.g., 'Punishingone')
            is_capital_ship: Whether this is a capital ship (needs CAPITAL prefix)

        Returns:
            Proper ship name from ships.tsv or the input if not found
        """
        if not ship_id_or_name:
            return ship_id_or_name

        # Try exact match first
        if ship_id_or_name in self.ship_names:
            return self.ship_names[ship_id_or_name]

        # Try uppercase match
        upper_id = ship_id_or_name.upper()
        if upper_id in self.ship_names:
            return self.ship_names[upper_id]

        # For capital ships, try adding CAPITAL prefix
        if is_capital_ship:
            capital_id = f"CAPITAL{upper_id}"
            if capital_id in self.ship_names:
                return self.ship_names[capital_id]

        # Try lowercase match
        lower_id = ship_id_or_name.lower()
        if lower_id in self.ship_names:
            return self.ship_names[lower_id]

        # Return original if no match found
        return ship_id_or_name

    def _map_fleet_names(self, fleet: Optional[Dict]) -> Optional[Dict]:
        """
        Map all ship IDs in a fleet composition to proper names.

        Args:
            fleet: Fleet dictionary with capital_ship, starting_ships, reinforcements

        Returns:
            Fleet dictionary with proper ship names
        """
        if not fleet:
            return None

        mapped_fleet = {}

        # Map capital ship (needs CAPITAL prefix)
        if 'capital_ship' in fleet:
            mapped_fleet['capital_ship'] = self._map_ship_name(fleet['capital_ship'], is_capital_ship=True)

        # Map starting ships (regular ships)
        if 'starting_ships' in fleet:
            mapped_fleet['starting_ships'] = [
                self._map_ship_name(ship, is_capital_ship=False) for ship in fleet['starting_ships']
            ]

        # Map reinforcements (regular ships)
        if 'reinforcements' in fleet:
            mapped_fleet['reinforcements'] = [
                self._map_ship_name(ship, is_capital_ship=False) for ship in fleet['reinforcements']
            ]

        return mapped_fleet
    
    def _parse_win_rate(self, win_rate_str: str) -> float:
        """Convert win rate string (e.g., '95.5%') to float (0.955)."""
        if not win_rate_str or win_rate_str == 'N/A':
            return 0.0
        try:
            return float(win_rate_str.rstrip('%')) / 100.0
        except (ValueError, AttributeError):
            return 0.0
    
    def _parse_times_seen(self, times_seen_str: str) -> int:
        """Convert times seen string to integer."""
        if not times_seen_str:
            return 0
        try:
            return int(times_seen_str)
        except (ValueError, TypeError):
            return 0
    
    def _aggregate_lineups_across_seasons(
        self,
        season_ids: List[str],
        attacking_id: str,
        defending_id: str,
        defending_starting_ships: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Aggregate lineups across multiple seasons.
        Combines lineups with same fleet composition, summing times_seen and calculating weighted win rates.

        Args:
            season_ids: List of season IDs to aggregate
            attacking_id: ID of the attacking capital ship
            defending_id: ID of the defending capital ship
            defending_starting_ships: Optional list of defending starting ship IDs to filter by

        Returns:
            List of aggregated lineups
        """
        # Dictionary to store aggregated lineups by fleet composition signature
        lineup_aggregates = {}

        for season_id in season_ids:
            season_data = self._load_season_data(season_id)
            matchup_data = season_data.get('matchups', {}).get(defending_id, {}).get(attacking_id)

            if not matchup_data or 'error' in matchup_data:
                continue

            lineups = matchup_data.get('counter_lineups', [])
            for lineup in lineups:
                # Apply defending starting ships filter if specified
                if defending_starting_ships:
                    defending_fleet = lineup.get('defending_fleet', {})
                    lineup_starting_ships = defending_fleet.get('starting_ships', [])

                    if not all(ship in lineup_starting_ships for ship in defending_starting_ships):
                        continue

                    if len(defending_starting_ships) == 3:
                        if len(lineup_starting_ships) != 3 or set(lineup_starting_ships) != set(defending_starting_ships):
                            continue

                # Create a signature for this lineup based on fleet composition
                attacking_fleet = lineup.get('attacking_fleet', {})
                defending_fleet = lineup.get('defending_fleet', {})

                signature = (
                    attacking_fleet.get('capital_ship', ''),
                    tuple(sorted(attacking_fleet.get('starting_ships', []))),
                    tuple(sorted(attacking_fleet.get('reinforcements', []))),
                    defending_fleet.get('capital_ship', ''),
                    tuple(sorted(defending_fleet.get('starting_ships', []))),
                    tuple(sorted(defending_fleet.get('reinforcements', [])))
                )

                times_seen = self._parse_times_seen(lineup.get('times_seen', '0'))
                win_rate = self._parse_win_rate(lineup.get('win_rate', '0%'))

                if signature in lineup_aggregates:
                    # Aggregate with existing lineup
                    agg = lineup_aggregates[signature]
                    agg['total_times_seen'] += times_seen
                    agg['weighted_win_rate_sum'] += win_rate * times_seen
                else:
                    # New lineup
                    lineup_aggregates[signature] = {
                        'lineup': lineup,
                        'total_times_seen': times_seen,
                        'weighted_win_rate_sum': win_rate * times_seen
                    }

        # Convert aggregates to final lineup format
        aggregated_lineups = []
        for agg in lineup_aggregates.values():
            if agg['total_times_seen'] > 0:
                combined_win_rate = agg['weighted_win_rate_sum'] / agg['total_times_seen']
                lineup_copy = agg['lineup'].copy()
                lineup_copy['times_seen'] = str(agg['total_times_seen'])
                lineup_copy['win_rate'] = f"{combined_win_rate * 100:.0f}%"
                aggregated_lineups.append(lineup_copy)

        return aggregated_lineups

    def _calculate_best_matchup(
        self,
        attacking_id: str,
        defending_id: str,
        min_battles: int = 10,
        defending_starting_ships: Optional[List[str]] = None,
        season_ids: Optional[List[str]] = None
    ) -> Tuple[float, int, Optional[Dict]]:
        """
        Calculate the best win rate for a specific matchup.

        Args:
            attacking_id: ID of the attacking capital ship
            defending_id: ID of the defending capital ship
            min_battles: Minimum number of battles for statistical significance
            defending_starting_ships: Optional list of defending starting ship IDs to filter by
            season_ids: Optional list of season IDs to aggregate data from

        Returns:
            Tuple of (win_rate, battle_count, best_lineup)
        """
        # If season_ids provided, aggregate across seasons
        if season_ids:
            lineups = self._aggregate_lineups_across_seasons(
                season_ids, attacking_id, defending_id, defending_starting_ships
            )
        else:
            # Use single matrix data (backward compatibility)
            matchup_data = self.matrix_data.get('matchups', {}).get(defending_id, {}).get(attacking_id)

            if not matchup_data or 'error' in matchup_data:
                return 0.0, 0, None

            lineups = matchup_data.get('counter_lineups', [])

        if not lineups:
            return 0.0, 0, None

        # Find the best lineup (highest win rate with sufficient battles)
        best_lineup = None
        best_win_rate = 0.0
        best_battle_count = 0

        for lineup in lineups:
            times_seen = self._parse_times_seen(lineup.get('times_seen', '0'))
            if times_seen < min_battles:
                continue

            # If defending starting ships filter is specified and not already filtered, check it
            if defending_starting_ships and not season_ids:
                defending_fleet = lineup.get('defending_fleet', {})
                lineup_starting_ships = defending_fleet.get('starting_ships', [])

                # Check if all specified ships are in the lineup's starting ships
                if not all(ship in lineup_starting_ships for ship in defending_starting_ships):
                    continue

                # If 3 ships specified, require exact match
                if len(defending_starting_ships) == 3:
                    if len(lineup_starting_ships) != 3 or set(lineup_starting_ships) != set(defending_starting_ships):
                        continue

            win_rate = self._parse_win_rate(lineup.get('win_rate', '0%'))
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                best_battle_count = times_seen
                best_lineup = lineup

        return best_win_rate, best_battle_count, best_lineup
    
    def build_processed_matrix(self, min_battles: int = 10, season_ids: Optional[List[str]] = None) -> Dict:
        """
        Build a processed matrix with best win rates for each matchup.

        Args:
            min_battles: Minimum number of battles for statistical significance
            season_ids: Optional list of season IDs to aggregate data from

        Returns:
            Dictionary with processed matchup data
        """
        matrix = {
            'ship_ids': self.capital_ships,
            'ship_names': self.ship_names,
            'matchups': {},
            'seasons': season_ids if season_ids else []
        }

        for defending_id in self.capital_ships:
            matrix['matchups'][defending_id] = {}

            for attacking_id in self.capital_ships:
                win_rate, battle_count, lineup = self._calculate_best_matchup(
                    attacking_id, defending_id, min_battles, season_ids=season_ids
                )

                matrix['matchups'][defending_id][attacking_id] = {
                    'win_rate': win_rate,
                    'win_rate_percent': f"{win_rate * 100:.1f}%",
                    'battle_count': battle_count,
                    'has_data': battle_count >= min_battles,
                    'lineup': lineup
                }

        self.processed_matrix = matrix
        return matrix
    
    def get_matchup_summary(self, attacking_id: str, defending_id: str) -> Optional[Dict]:
        """
        Get summary information for a specific matchup.
        
        Args:
            attacking_id: ID of the attacking capital ship
            defending_id: ID of the defending capital ship
            
        Returns:
            Dictionary with matchup summary
        """
        if not self.processed_matrix:
            self.build_processed_matrix()
        
        if defending_id not in self.processed_matrix['matchups']:
            return None
        
        if attacking_id not in self.processed_matrix['matchups'][defending_id]:
            return None
        
        matchup = self.processed_matrix['matchups'][defending_id][attacking_id]

        # Map fleet ship names to proper display names
        attacking_fleet = self._map_fleet_names(
            matchup['lineup'].get('attacking_fleet') if matchup['lineup'] else None
        )
        defending_fleet = self._map_fleet_names(
            matchup['lineup'].get('defending_fleet') if matchup['lineup'] else None
        )

        return {
            'attacking_ship': self.ship_names.get(attacking_id, attacking_id),
            'defending_ship': self.ship_names.get(defending_id, defending_id),
            'win_rate': matchup['win_rate'],
            'win_rate_percent': matchup['win_rate_percent'],
            'battle_count': matchup['battle_count'],
            'has_data': matchup['has_data'],
            'attacking_fleet': attacking_fleet,
            'defending_fleet': defending_fleet
        }

    def get_common_starting_ships(self, capital_ship_id: str, top_n: int = 10) -> List[Dict[str, str]]:
        """
        Get the most common starting ships for a capital ship across all matchups.
        This looks at defending fleet data since it's used for defense configuration.

        Args:
            capital_ship_id: ID of the capital ship
            top_n: Number of top ships to return

        Returns:
            List of dicts with ship_id and ship_name sorted by frequency
        """
        if not self.processed_matrix:
            self.build_processed_matrix()

        ship_counts = {}

        # Look through all matchups where this ship is defending
        for attacking_id in self.capital_ships:
            matchup = self.processed_matrix['matchups'][capital_ship_id].get(attacking_id)
            if matchup and matchup['lineup']:
                defending_fleet = matchup['lineup'].get('defending_fleet', {})
                starting_ships = defending_fleet.get('starting_ships', [])

                for ship in starting_ships:
                    # Convert to uppercase ID format
                    ship_id = ship.upper()
                    ship_counts[ship_id] = ship_counts.get(ship_id, 0) + 1

        # Sort by frequency and return top N with ID, name, and image
        sorted_ships = sorted(ship_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {
                'ship_id': ship_id,
                'ship_name': self.ship_names.get(ship_id, ship_id),
                'image': self.ship_images.get(ship_id, '')
            }
            for ship_id, _ in sorted_ships[:top_n]
        ]

    def get_all_regular_ships(self) -> List[str]:
        """
        Get all unique regular (non-capital) ships from the data.

        Returns:
            List of unique ship names
        """
        if not self.processed_matrix:
            self.build_processed_matrix()

        ships = set()

        # Collect all ships from all lineups
        for defending_id in self.capital_ships:
            for attacking_id in self.capital_ships:
                matchup = self.processed_matrix['matchups'][defending_id][attacking_id]
                if matchup['lineup']:
                    for fleet_key in ['attacking_fleet', 'defending_fleet']:
                        fleet = matchup['lineup'].get(fleet_key, {})
                        for ship_list_key in ['starting_ships', 'reinforcements']:
                            ship_list = fleet.get(ship_list_key, [])
                            for ship in ship_list:
                                ship_name = self._map_ship_name(ship, is_capital_ship=False)
                                ships.add(ship_name)

        return sorted(list(ships))

    def get_all_regular_ships_with_factions(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get all unique regular (non-capital) ships organized by faction.

        Returns:
            Dictionary mapping faction names to lists of ship objects with name, id, and image
        """
        if not self.processed_matrix:
            self.build_processed_matrix()

        ships_by_faction = {}
        ship_set = set()

        # Collect all ships from all lineups
        for defending_id in self.capital_ships:
            for attacking_id in self.capital_ships:
                matchup = self.processed_matrix['matchups'][defending_id][attacking_id]
                if matchup['lineup']:
                    for fleet_key in ['attacking_fleet', 'defending_fleet']:
                        fleet = matchup['lineup'].get(fleet_key, {})
                        for ship_list_key in ['starting_ships', 'reinforcements']:
                            ship_list = fleet.get(ship_list_key, [])
                            for ship in ship_list:
                                ship_name = self._map_ship_name(ship, is_capital_ship=False)
                                if ship_name not in ship_set:
                                    ship_set.add(ship_name)

                                    # Find the ship ID to get faction and image
                                    ship_id = None
                                    for sid, sname in self.ship_names.items():
                                        if sname == ship_name and not sid.startswith('CAPITAL'):
                                            ship_id = sid
                                            break

                                    if ship_id:
                                        faction = self.ship_factions.get(ship_id, 'Other')
                                        image = self.ship_images.get(ship_id, '')
                                    else:
                                        faction = 'Other'
                                        image = ''

                                    if faction not in ships_by_faction:
                                        ships_by_faction[faction] = []
                                    ships_by_faction[faction].append({
                                        'name': ship_name,
                                        'id': ship_id if ship_id else ship_name,
                                        'image': image
                                    })

        # Sort ships within each faction by name
        for faction in ships_by_faction:
            ships_by_faction[faction].sort(key=lambda x: x['name'])

        return ships_by_faction

