#!/usr/bin/env python3
"""
Scrape complete matchup matrix for all capital ship combinations.
This script collects data for every attacking ship vs every defending ship,
creating a comprehensive 11x11 matrix of matchup data.
"""

import json
import time
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Add parent directory to path to import the scraper
sys.path.insert(0, str(Path(__file__).parent))
from swgoh_fleet_scraper import SWGOHFleetScraper

# Capital ships to scrape
CAPITAL_SHIPS = [
    'CAPITALEXECUTOR',
    'CAPITALPROFUNDITY',
    'CAPITALLEVIATHAN',
    'CAPITALFINALIZER',
    'CAPITALNEGOTIATOR',
    'CAPITALMALEVOLENCE',
    'CAPITALRADDUS',
    'CAPITALMONCALAMARICRUISER',
    'CAPITALCHIMAERA',
    'CAPITALSTARDESTROYER',
    'CAPITALJEDICRUISER'
]

# Load configuration from environment variables
# SEASON_NUMBERS can be a comma-separated list of season numbers (e.g., "73,74,75")
SEASON_NUMBERS_STR = os.getenv('SEASON_NUMBERS', '74')
SEASON_NUMBERS = [s.strip() for s in SEASON_NUMBERS_STR.split(',')]
# Build full season IDs from season numbers
SEASON_IDS = [f'CHAMPIONSHIPS_GRAND_ARENA_GA2_EVENT_SEASON_{num}' for num in SEASON_NUMBERS]
API_KEY = os.getenv('SWGOH_API_KEY', 'SWGOHGG_API_KEY')


def setup_logging() -> logging.Logger:
    """
    Set up logging to file with timestamps.

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'scraper_{timestamp}.log'

    # Configure logging
    logger = logging.getLogger('fleet_scraper')
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    logger.handlers = []

    # File handler with detailed formatting
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler for errors only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("="*70)
    logger.info("SWGOH Fleet Scraper - Logging Started")
    logger.info(f"Log file: {log_file}")
    logger.info("="*70)

    return logger


def format_ship_name(ship_id: str) -> str:
    """Format ship ID to readable name."""
    return ship_id.replace('CAPITAL', '').title()


def scrape_season(season_id: str, season_number: str, scraper: SWGOHFleetScraper, logger: logging.Logger, season_idx: int, total_seasons: int) -> tuple:
    """
    Scrape complete matchup matrix for a single season.

    Args:
        season_id: The GAC season identifier
        season_number: The season number (for filename)
        scraper: Initialized SWGOHFleetScraper instance
        logger: Logger instance
        season_idx: Current season index (1-based)
        total_seasons: Total number of seasons to scrape

    Returns:
        Tuple of (complete_matrix dict, successful_scrapes count, failed_scrapes count)
    """
    logger.info("="*70)
    logger.info(f"Starting Season {season_idx}/{total_seasons}: {season_id}")
    logger.info("="*70)

    # Data structure: defending_ship -> attacking_ship -> matchup_data
    complete_matrix = {
        'season_id': season_id,
        'scraped_at': datetime.now().isoformat(),
        'capital_ships': CAPITAL_SHIPS,
        'ship_names': {ship_id: format_ship_name(ship_id) for ship_id in CAPITAL_SHIPS},
        'matchups': {}
    }

    total_combinations = len(CAPITAL_SHIPS) * len(CAPITAL_SHIPS)
    successful_scrapes = 0
    failed_scrapes = 0

    # Create progress bar
    desc = f"Season {season_idx}/{total_seasons} (S{season_number})"
    pbar = tqdm(
        total=total_combinations,
        desc=desc,
        unit=" matchup",
        ncols=100,
        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
    )

    # Iterate through all combinations
    for defending_ship in CAPITAL_SHIPS:
        defending_name = format_ship_name(defending_ship)
        complete_matrix['matchups'][defending_ship] = {}

        for attacking_ship in CAPITAL_SHIPS:
            attacking_name = format_ship_name(attacking_ship)

            logger.debug(f"Scraping: {attacking_name} vs {defending_name}")

            try:
                # Scrape the specific matchup
                matchup_data = scraper.extract_detailed_counters(
                    defending_ship_id=defending_ship,
                    season_id=season_id,
                    attacking_ship_id=attacking_ship,
                    debug=False
                )

                # Store the data
                complete_matrix['matchups'][defending_ship][attacking_ship] = matchup_data

                lineup_count = len(matchup_data.get('counter_lineups', []))
                if 'error' in matchup_data:
                    logger.warning(f"Error scraping {attacking_name} vs {defending_name}: {matchup_data['error']}")
                    failed_scrapes += 1
                else:
                    logger.info(f"Success: {attacking_name} vs {defending_name} - {lineup_count} lineups found")
                    successful_scrapes += 1

                # Update progress bar with success/failure counts
                pbar.set_description(f"{desc} [✓{successful_scrapes} ✗{failed_scrapes}]")
                pbar.update(1)

                # Rate limiting - be respectful to the server
                # Already handled by scraper, but add extra delay every 10 requests
                if (pbar.n % 10) == 0:
                    logger.debug("Checkpoint: Pausing for 5 seconds...")
                    time.sleep(5)

            except Exception as e:
                logger.error(f"Exception scraping {attacking_name} vs {defending_name}: {e}", exc_info=True)
                failed_scrapes += 1
                complete_matrix['matchups'][defending_ship][attacking_ship] = {
                    'error': str(e),
                    'defending_ship_id': defending_ship,
                    'attacking_ship_id': attacking_ship
                }
                pbar.set_description(f"{desc} [✓{successful_scrapes} ✗{failed_scrapes}]")
                pbar.update(1)

    pbar.close()

    # Save the complete matrix with simplified filename
    output_file = Path(__file__).parent.parent / 'data' / f'complete_matchup_matrix_{season_number}.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(complete_matrix, f, indent=2)

    logger.info("="*70)
    logger.info(f"Season {season_id} Complete")
    logger.info(f"Total Combinations: {total_combinations}")
    logger.info(f"Successful: {successful_scrapes}")
    logger.info(f"Failed: {failed_scrapes}")
    logger.info(f"Success Rate: {(successful_scrapes/total_combinations)*100:.1f}%")
    logger.info(f"Data saved to: {output_file}")
    logger.info("="*70)

    return complete_matrix, successful_scrapes, failed_scrapes


def main():
    """Main function to scrape complete matchup matrix for all seasons."""
    # Set up logging
    logger = setup_logging()

    # Print header to console
    print("="*70)
    print("SWGOH Fleet Complete Matchup Matrix Scraper")
    print("="*70)
    print(f"Seasons to scrape: {len(SEASON_IDS)}")
    for i, (season_num, season_id) in enumerate(zip(SEASON_NUMBERS, SEASON_IDS), 1):
        print(f"  {i}. Season {season_num}")
    print(f"Capital Ships: {len(CAPITAL_SHIPS)}")
    print(f"Total Combinations per Season: {len(CAPITAL_SHIPS) * len(CAPITAL_SHIPS)}")
    print(f"Estimated Time per Season: ~{len(CAPITAL_SHIPS) * len(CAPITAL_SHIPS) * 2 / 60:.1f} minutes")
    print(f"Total Estimated Time: ~{len(SEASON_IDS) * len(CAPITAL_SHIPS) * len(CAPITAL_SHIPS) * 2 / 60:.1f} minutes")
    print(f"Log file: logs/scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    print("="*70)
    print()

    # Log configuration
    logger.info(f"Seasons to scrape: {len(SEASON_IDS)}")
    for i, (season_num, season_id) in enumerate(zip(SEASON_NUMBERS, SEASON_IDS), 1):
        logger.info(f"  {i}. Season {season_num}: {season_id}")
    logger.info(f"Capital Ships: {len(CAPITAL_SHIPS)}")
    logger.info(f"Total Combinations per Season: {len(CAPITAL_SHIPS) * len(CAPITAL_SHIPS)}")
    logger.info(f"API Key: {API_KEY[:5]}...")

    # Initialize scraper
    logger.info("Initializing scraper...")
    scraper = SWGOHFleetScraper(API_KEY, logger=logger)

    # Track overall statistics
    all_results = []
    total_successful = 0
    total_failed = 0

    # Iterate through all seasons
    for season_idx, (season_num, season_id) in enumerate(zip(SEASON_NUMBERS, SEASON_IDS), 1):
        logger.info(f"\nProcessing Season {season_idx}/{len(SEASON_IDS)}: {season_id}")

        _, successful, failed = scrape_season(
            season_id=season_id,
            season_number=season_num,
            scraper=scraper,
            logger=logger,
            season_idx=season_idx,
            total_seasons=len(SEASON_IDS)
        )

        all_results.append({
            'season_number': season_num,
            'season_id': season_id,
            'successful': successful,
            'failed': failed,
            'total': successful + failed
        })
        total_successful += successful
        total_failed += failed

        # Add delay between seasons
        if season_idx < len(SEASON_IDS):
            logger.info("Pausing 10 seconds before next season...")
            time.sleep(10)

    # Print final summary to console
    print("\n" + "="*70)
    print("ALL SEASONS COMPLETE")
    print("="*70)
    print(f"Total Seasons Processed: {len(SEASON_IDS)}")
    print(f"Total Successful Scrapes: {total_successful}")
    print(f"Total Failed Scrapes: {total_failed}")
    if total_successful + total_failed > 0:
        print(f"Overall Success Rate: {(total_successful/(total_successful + total_failed))*100:.1f}%")
    print("\nPer-Season Results:")
    for result in all_results:
        success_rate = (result['successful']/result['total'])*100 if result['total'] > 0 else 0
        print(f"  Season {result['season_number']}: {result['successful']}/{result['total']} ({success_rate:.1f}%)")
    print("="*70)

    # Log final summary
    logger.info("="*70)
    logger.info("ALL SEASONS COMPLETE")
    logger.info("="*70)
    logger.info(f"Total Seasons Processed: {len(SEASON_IDS)}")
    logger.info(f"Total Successful Scrapes: {total_successful}")
    logger.info(f"Total Failed Scrapes: {total_failed}")
    if total_successful + total_failed > 0:
        logger.info(f"Overall Success Rate: {(total_successful/(total_successful + total_failed))*100:.1f}%")
    logger.info("\nPer-Season Results:")
    for result in all_results:
        success_rate = (result['successful']/result['total'])*100 if result['total'] > 0 else 0
        logger.info(f"  Season {result['season_number']} ({result['season_id']}): {result['successful']}/{result['total']} ({success_rate:.1f}%)")
    logger.info("="*70)


if __name__ == '__main__':
    main()

