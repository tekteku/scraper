"""
Test script for the main Tunisian Property Scraper using only Remax for speed
"""

import sys
import os
import logging
from datetime import datetime
from tunisian_property_scraper import main as full_scraper_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RemaxMainScraperTest")

def test_main_scraper_with_remax_only():
    """
    Run the main property scraper but only with Remax.com.tn to test the integration
    """
    logger.info("Starting main scraper test with only Remax.com.tn")
    
    # Import the SITE_CONFIGS to modify it
    from tunisian_property_scraper import SITE_CONFIGS as ALL_CONFIGS
    
    # Find the Remax config
    remax_config = next((config for config in ALL_CONFIGS if config["name"] == "remax.com.tn"), None)
    
    if not remax_config:
        logger.error("Remax configuration not found in SITE_CONFIGS")
        return
    
    # Make a copy with only Remax and modify for quicker testing
    test_config = remax_config.copy()
    test_config["max_pages"] = 3  # Just test 3 pages max
    
    # Backup the original sys.argv
    original_argv = sys.argv.copy()
    
    try:
        # Modify sys.argv to pass arguments to the main script
        sys.argv = [
            "tunisian_property_scraper.py",
            "--site", "remax.com.tn",
            "--max-pages", "3",
            "--no-clean"  # Skip data cleaning step to run faster
        ]
        
        # Run the main scraper
        full_scraper_main()
        
        logger.info("Main scraper completed successfully with Remax.com.tn")
        
    except Exception as e:
        logger.error(f"Error running main scraper: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        # Restore original sys.argv
        sys.argv = original_argv

if __name__ == "__main__":
    test_main_scraper_with_remax_only()
