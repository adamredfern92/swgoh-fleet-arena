#!/usr/bin/env python3
"""
SWGOH Fleet Data Scraper
Extracts fleet counter data from SWGOH.gg for a specific GAC season.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import sys
import logging
from typing import Dict, List, Optional
from datetime import datetime


class SWGOHFleetScraper:
    """Scraper for SWGOH.gg fleet counter data."""

    def __init__(self, api_key: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the scraper with API credentials.

        Args:
            api_key: The API key for SWGOH.gg bot access
            logger: Optional logger instance for logging
        """
        self.base_url = "https://swgoh.gg"
        self.headers = {
            "x-gg-bot-access": api_key,
            "User-Agent": "SWGOH Fleet Analysis Bot/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        # Rate limiting: minimum seconds between requests
        self.rate_limit_delay = 2
        self.last_request_time = 0
        # Logger
        self.logger = logger or logging.getLogger(__name__)
    
    def _rate_limit(self):
        """Implement rate limiting to be respectful to the server."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def fetch_page(self, url: str, debug: bool = False) -> Optional[BeautifulSoup]:
        """
        Fetch a page with error handling and rate limiting.

        Args:
            url: The URL to fetch
            debug: If True, save the HTML response for debugging

        Returns:
            BeautifulSoup object if successful, None otherwise
        """
        self._rate_limit()

        try:
            self.logger.debug(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Ensure content is decoded properly
            response.encoding = response.apparent_encoding or 'utf-8'
            html_content = response.text

            # Debug: Save the response
            if debug:
                with open('debug_response.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.logger.debug("Debug: Response saved to debug_response.html")
                self.logger.debug(f"Response encoding: {response.encoding}")
                self.logger.debug(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                self.logger.debug(f"Content-Encoding: {response.headers.get('Content-Encoding', 'N/A')}")

            # Check if we got a Cloudflare challenge page
            if "challenge-platform" in html_content or "Just a moment" in html_content:
                self.logger.warning("Received Cloudflare challenge page. API key may be required.")
                self.logger.debug(f"Response length: {len(html_content)} characters")
                if debug:
                    self.logger.debug("First 500 characters of response:")
                    self.logger.debug(html_content[:500])
                return None

            self.logger.debug(f"Successfully fetched page ({len(html_content)} characters)")
            return BeautifulSoup(html_content, 'html.parser')

        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP Error: {e}")
            if e.response.status_code == 403:
                self.logger.error("Access forbidden. Check if API key is valid.")
            elif e.response.status_code == 429:
                self.logger.warning("Rate limited. Waiting 60 seconds...")
                time.sleep(60)
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return None
    
    def extract_fleet_counters(self, season_id: str, debug: bool = False) -> Dict:
        """
        Extract fleet counter data for a specific GAC season.

        Args:
            season_id: The GAC season identifier
            debug: If True, enable debug output

        Returns:
            Dictionary containing fleet counter data
        """
        url = f"{self.base_url}/gac/ship-counters/season/{season_id}/"
        soup = self.fetch_page(url, debug=debug)
        
        if not soup:
            return {"error": "Failed to fetch page", "season_id": season_id}
        
        fleet_data = {
            "season_id": season_id,
            "scraped_at": datetime.now().isoformat(),
            "capital_ships": []
        }
        
        # Extract capital ship data
        # Look for paper containers that hold each capital ship's data
        ship_containers = soup.find_all('div', class_='paper')

        self.logger.debug(f"Found {len(ship_containers)} paper containers")

        # Filter containers that have capital ships
        for container in ship_containers:
            # Check if this container has a capital ship
            capital_ship_elem = container.find('div', class_='ship-portrait--is-capital-ship')
            if capital_ship_elem:
                ship_info = self._extract_ship_counter_info(container)
                if ship_info and ship_info.get('capital_ship'):
                    fleet_data["capital_ships"].append(ship_info)

        # If no data found, try fallback method
        if not fleet_data["capital_ships"]:
            self.logger.debug("No data found in paper containers, using fallback method")
            capital_ship_elements = soup.find_all('div', attrs={'data-unit-def-tooltip-app': True})
            for element in capital_ship_elements:
                ship_id = element.get('data-unit-def-tooltip-app', '')
                if ship_id.startswith('CAPITAL'):
                    ship_name = self._format_ship_name(ship_id)
                    fleet_data["capital_ships"].append({
                        'capital_ship': ship_name,
                        'ship_id': ship_id
                    })
        
        return fleet_data

    def extract_detailed_counters(
        self,
        defending_ship_id: str,
        season_id: str,
        attacking_ship_id: Optional[str] = None,
        debug: bool = False
    ) -> Dict:
        """
        Extract detailed counter lineup data for a specific capital ship matchup.

        Args:
            defending_ship_id: The defending capital ship ID (e.g., 'CAPITALEXECUTOR')
            season_id: The GAC season identifier
            attacking_ship_id: Optional attacking capital ship ID to filter results
            debug: If True, enable debug output

        Returns:
            Dictionary containing detailed counter lineup data
        """
        counter_data = {
            "defending_ship_id": defending_ship_id,
            "defending_ship": self._format_ship_name(defending_ship_id),
            "attacking_ship_id": attacking_ship_id,
            "attacking_ship": self._format_ship_name(attacking_ship_id) if attacking_ship_id else None,
            "season_id": season_id,
            "scraped_at": datetime.now().isoformat(),
            "counter_lineups": []
        }

        # Iterate through all pages
        page = 1
        while True:
            # Build URL with optional attacking ship filter and sort by count
            url = f"{self.base_url}/gac/ship-counters/{defending_ship_id}/?season_id={season_id}"
            if attacking_ship_id:
                url += f"&a_lead={attacking_ship_id}"
            # Add sort by count to get most common matchups first
            url += f"&page={page}&sort=count"

            soup = self.fetch_page(url, debug=debug)

            if not soup:
                if page == 1:
                    # Failed to fetch first page
                    return {
                        "error": "Failed to fetch page",
                        "defending_ship_id": defending_ship_id,
                        "attacking_ship_id": attacking_ship_id
                    }
                else:
                    # Failed to fetch subsequent page, break the loop
                    self.logger.debug(f"Failed to fetch page {page}, stopping pagination")
                    break

            # Find all counter lineup rows
            # Look for paper containers with lineup data
            lineup_containers = soup.find_all('div', class_='paper')

            self.logger.debug(f"Page {page}: Found {len(lineup_containers)} potential lineup containers")

            if not lineup_containers:
                # No more lineups found, we've reached the end
                self.logger.debug(f"No lineups found on page {page}, stopping pagination")
                break

            lineups_added = 0
            for idx, container in enumerate(lineup_containers):
                lineup_info = self._extract_lineup_info(container)
                if lineup_info:
                    counter_data["counter_lineups"].append(lineup_info)
                    lineups_added += 1
                    self.logger.debug(f"Page {page}, Container {idx}: Valid lineup found")
                else:
                    self.logger.debug(f"Page {page}, Container {idx}: Skipped (no valid lineup data)")

            self.logger.debug(f"Page {page}: Added {lineups_added} lineups out of {len(lineup_containers)} containers")

            # Check if there's a next page by looking for pagination controls
            pagination = soup.find('nav', attrs={'aria-label': 'pagination'})
            if not pagination:
                # Try alternative pagination detection
                pagination = soup.find('ul', class_='pagination')

            has_next_page = False
            if pagination:
                # Look for "next" button or page number links
                next_button = pagination.find('a', attrs={'aria-label': 'Next'})
                if next_button and not next_button.get('disabled'):
                    has_next_page = True
                else:
                    # Check if there are page links beyond current page
                    page_links = pagination.find_all('a', href=True)
                    for link in page_links:
                        href = link.get('href', '')
                        if f'page={page + 1}' in href:
                            has_next_page = True
                            break

            if not has_next_page:
                self.logger.debug(f"No more pages found after page {page}")
                break

            page += 1

        self.logger.debug(f"Total lineups collected: {len(counter_data['counter_lineups'])} across {page} page(s)")

        return counter_data

    def _format_ship_name(self, ship_id: str) -> str:
        """
        Format ship ID into a readable name.

        Args:
            ship_id: The ship ID (e.g., 'CAPITALEXECUTOR')

        Returns:
            Formatted ship name (e.g., 'Executor')
        """
        # Remove 'CAPITAL' prefix
        name = ship_id.replace('CAPITAL', '')
        # Convert to title case
        return name.title()

    def _extract_ship_counter_info(self, container) -> Optional[Dict]:
        """
        Extract information about a capital ship counter from a container.

        Args:
            container: BeautifulSoup element containing ship counter data

        Returns:
            Dictionary with ship counter information or None
        """
        ship_info = {}

        # Find the capital ship (first ship in the container)
        capital_ship_elem = container.find('div', class_='ship-portrait--is-capital-ship')
        if not capital_ship_elem:
            return None

        ship_id = capital_ship_elem.get('data-unit-def-tooltip-app', '')
        if ship_id:
            ship_info['capital_ship'] = self._format_ship_name(ship_id)
            ship_info['ship_id'] = ship_id
        else:
            return None

        # Extract counter link
        counter_link = container.find('a', class_='button')
        if counter_link:
            ship_info['counter_url'] = self.base_url + counter_link.get('href', '')
            ship_info['counter_link_text'] = counter_link.get_text(strip=True)

        # Extract win rate (look for percentage in fw-bold divs)
        win_rate_elem = container.find('div', class_='fw-bold')
        if win_rate_elem:
            win_rate_text = win_rate_elem.get_text(strip=True)
            if '%' in win_rate_text:
                ship_info['win_rate'] = win_rate_text

        # Extract all text statistics with better labeling
        stats_divs = container.find_all('div', class_='fw-bold')
        if stats_divs and len(stats_divs) >= 2:
            # Typically first stat is battles count, second is win rate
            battles = stats_divs[0].get_text(strip=True)
            win_rate = stats_divs[1].get_text(strip=True)

            ship_info['battles'] = battles
            if '%' in win_rate:
                ship_info['win_rate'] = win_rate

            # Collect any additional stats
            if len(stats_divs) > 2:
                additional_stats = []
                for stat_div in stats_divs[2:]:
                    stat_text = stat_div.get_text(strip=True)
                    if stat_text:
                        additional_stats.append(stat_text)
                if additional_stats:
                    ship_info['additional_stats'] = additional_stats

        # Extract fleet composition (supporting ships)
        all_ships = container.find_all('div', attrs={'data-unit-def-tooltip-app': True})
        fleet_ships = []
        for ship in all_ships:
            ship_id_attr = ship.get('data-unit-def-tooltip-app', '')
            # Skip the capital ship itself
            if ship_id_attr and ship_id_attr != ship_id:
                formatted_name = self._format_ship_name(ship_id_attr)
                if formatted_name not in fleet_ships:
                    fleet_ships.append(formatted_name)

        if fleet_ships:
            ship_info['fleet_composition'] = fleet_ships

        return ship_info if ship_info else None

    def _extract_lineup_info(self, container) -> Optional[Dict]:
        """
        Extract detailed lineup information including attacking and defending fleets.

        Args:
            container: BeautifulSoup element containing lineup data

        Returns:
            Dictionary with lineup information including ships, stats, etc.
        """
        lineup_info = {}

        # Extract all ships in this container
        all_ships = container.find_all('div', attrs={'data-unit-def-tooltip-app': True})

        if len(all_ships) < 2:
            # Not a valid lineup container
            self.logger.debug(f"Container skipped: only {len(all_ships)} ships found (need at least 2)")
            return None

        # Find capital ships first
        capital_ships = container.find_all('div', class_='ship-portrait--is-capital-ship')

        if len(capital_ships) < 2:
            self.logger.debug(f"Container skipped: only {len(capital_ships)} capital ships found (need 2)")
            return None

        # Find links to identify attacking vs defending ships
        a_member_links = container.find_all('a', href=lambda x: x and 'a_member=' in x)
        d_member_links = container.find_all('a', href=lambda x: x and 'd_member=' in x)
        a_reinf_links = container.find_all('a', href=lambda x: x and 'a_reinforcement=' in x)
        d_reinf_links = container.find_all('a', href=lambda x: x and 'd_reinforcement=' in x)

        # Extract attacking fleet
        attacking_fleet = {
            'capital_ship': None,
            'starting_ships': [],
            'reinforcements': []
        }

        # Extract defending fleet
        defending_fleet = {
            'capital_ship': None,
            'starting_ships': [],
            'reinforcements': []
        }

        # Assign capital ships (first is attacking, second is defending)
        if len(capital_ships) >= 2:
            attacking_capital_id = capital_ships[0].get('data-unit-def-tooltip-app', '')
            defending_capital_id = capital_ships[1].get('data-unit-def-tooltip-app', '')

            if attacking_capital_id:
                # Store ship IDs in uppercase
                attacking_fleet['capital_ship'] = attacking_capital_id.upper()
            if defending_capital_id:
                # Store ship IDs in uppercase
                defending_fleet['capital_ship'] = defending_capital_id.upper()

        # Get attacking members (starting ships)
        for link in a_member_links:
            ship_elem = link.find('div', attrs={'data-unit-def-tooltip-app': True})
            if ship_elem:
                ship_id = ship_elem.get('data-unit-def-tooltip-app', '')
                if ship_id and not ship_id.startswith('CAPITAL'):
                    # Store ship IDs in uppercase
                    ship_id_upper = ship_id.upper()
                    if ship_id_upper not in attacking_fleet['starting_ships']:
                        attacking_fleet['starting_ships'].append(ship_id_upper)

        # Get attacking reinforcements
        for link in a_reinf_links:
            ship_elem = link.find('div', attrs={'data-unit-def-tooltip-app': True})
            if ship_elem:
                ship_id = ship_elem.get('data-unit-def-tooltip-app', '')
                if ship_id:
                    # Store ship IDs in uppercase
                    ship_id_upper = ship_id.upper()
                    if ship_id_upper not in attacking_fleet['reinforcements']:
                        attacking_fleet['reinforcements'].append(ship_id_upper)

        # Get defending members (starting ships)
        for link in d_member_links:
            ship_elem = link.find('div', attrs={'data-unit-def-tooltip-app': True})
            if ship_elem:
                ship_id = ship_elem.get('data-unit-def-tooltip-app', '')
                if ship_id and not ship_id.startswith('CAPITAL'):
                    # Store ship IDs in uppercase
                    ship_id_upper = ship_id.upper()
                    if ship_id_upper not in defending_fleet['starting_ships']:
                        defending_fleet['starting_ships'].append(ship_id_upper)

        # Get defending reinforcements
        for link in d_reinf_links:
            ship_elem = link.find('div', attrs={'data-unit-def-tooltip-app': True})
            if ship_elem:
                ship_id = ship_elem.get('data-unit-def-tooltip-app', '')
                if ship_id:
                    # Store ship IDs in uppercase
                    ship_id_upper = ship_id.upper()
                    if ship_id_upper not in defending_fleet['reinforcements']:
                        defending_fleet['reinforcements'].append(ship_id_upper)

        lineup_info['attacking_fleet'] = attacking_fleet
        lineup_info['defending_fleet'] = defending_fleet

        # Extract statistics (times seen, win rate, banners)
        stats_elements = container.find_all('div', class_='fw-bold')
        stats = []
        for stat_elem in stats_elements:
            stat_text = stat_elem.get_text(strip=True)
            if stat_text:
                stats.append(stat_text)

        # Parse common statistics
        if len(stats) >= 3:
            lineup_info['times_seen'] = stats[0]
            lineup_info['win_rate'] = stats[1] if '%' in stats[1] else None
            lineup_info['banners'] = stats[2]

            # Store any additional stats
            if len(stats) > 3:
                lineup_info['additional_stats'] = stats[3:]

        # Only return lineup info if it has both capital ships
        # This ensures we're only capturing actual matchup data
        if (attacking_fleet.get('capital_ship') and
            defending_fleet.get('capital_ship')):
            return lineup_info

        return None

    def _extract_from_table(self, table) -> List[Dict]:
        """
        Extract fleet data from HTML tables.

        Args:
            table: BeautifulSoup table element

        Returns:
            List of dictionaries containing fleet data
        """
        fleet_data = []

        try:
            headers = []
            header_row = table.find('thead')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]

            rows = table.find('tbody')
            if not rows:
                rows = table

            for row in rows.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) > 0:
                    row_data = {}

                    # Extract text from each cell
                    for idx, cell in enumerate(cells):
                        header = headers[idx] if idx < len(headers) else f"column_{idx}"
                        cell_text = cell.get_text(strip=True)

                        # Try to extract ship names from images
                        img = cell.find('img')
                        if img and img.get('alt'):
                            cell_text = img.get('alt')

                        row_data[header] = cell_text

                    if row_data:
                        fleet_data.append(row_data)

        except Exception as e:
            print(f"Error extracting from table: {e}")

        return fleet_data

    def save_to_json(self, data: Dict, filename: str = "fleet_data.json"):
        """
        Save extracted data to a JSON file.

        Args:
            data: Dictionary containing fleet data
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")

    def save_to_csv(self, data: Dict, filename: str = "fleet_data.csv"):
        """
        Save extracted data to a CSV file.

        Args:
            data: Dictionary containing fleet data
            filename: Output filename
        """
        try:
            import csv

            if not data.get('capital_ships'):
                print("No capital ship data to save")
                return

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                # Determine all possible fields
                all_fields = set()
                for ship in data['capital_ships']:
                    all_fields.update(ship.keys())

                fieldnames = sorted(list(all_fields))
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                writer.writeheader()
                for ship in data['capital_ships']:
                    # Flatten nested dictionaries for CSV
                    flat_ship = {}
                    for key, value in ship.items():
                        if isinstance(value, (dict, list)):
                            flat_ship[key] = json.dumps(value)
                        else:
                            flat_ship[key] = value
                    writer.writerow(flat_ship)

            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving to CSV: {e}")


def main():
    """Main function to run the scraper."""
    # API key for SWGOH.gg
    API_KEY = "SWGOHGG_API_KEY"

    # GAC Season ID
    SEASON_ID = "CHAMPIONSHIPS_GRAND_ARENA_GA2_EVENT_SEASON_74"

    print("=" * 60)
    print("SWGOH Fleet Data Scraper")
    print("=" * 60)
    print(f"Season: {SEASON_ID}")
    print(f"API Key: {API_KEY[:5]}...")
    print("=" * 60)

    # Initialize scraper
    scraper = SWGOHFleetScraper(API_KEY)

    # Extract fleet counter data
    print("\nExtracting fleet counter data...")
    # Set debug=True to save HTML response for debugging
    fleet_data = scraper.extract_fleet_counters(SEASON_ID, debug=True)

    # Display summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    if "error" in fleet_data:
        print(f"Error: {fleet_data['error']}")
    else:
        print(f"Capital ships found: {len(fleet_data.get('capital_ships', []))}")
        print(f"Scraped at: {fleet_data.get('scraped_at', 'N/A')}")

    # Save data in multiple formats
    print("\nSaving data...")
    scraper.save_to_json(fleet_data, "fleet_data.json")
    scraper.save_to_csv(fleet_data, "fleet_data.csv")

    # Display sample data
    if fleet_data.get('capital_ships'):
        print("\n" + "=" * 60)
        print("SAMPLE DATA (First Capital Ship)")
        print("=" * 60)
        print(json.dumps(fleet_data['capital_ships'][0], indent=2))

    print("\n" + "=" * 60)
    print("Scraping complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

