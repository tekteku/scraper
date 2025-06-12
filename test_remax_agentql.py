"""
Test script for the AgentQL-based Remax pagination

This script tests the AgentQL approach for handling Remax.com.tn's pagination
and compares it to the previous hash-based URL approach.
"""

import logging
import os
import time
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RemaxAgentQLTest")

# Make sure the required modules are installed
try:
    import agentql
except ImportError:
    logger.error("AgentQL not installed. Installing now...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "agentql"])
    import agentql

# Import our updated Remax AgentQL pagination module
try:
    # First try to import the updated version
    from remax_agentql_updated import scrape_remax_with_agentql
    logger.info("Using updated remax_agentql_updated.py for testing")
except ImportError:
    try:
        # Fall back to the original module if the updated one is not available
        from remax_agentql_pagination import scrape_remax_with_agentql
        logger.warning("Using original remax_agentql_pagination.py for testing")
    except ImportError:
        logger.error("No Remax AgentQL module found in the current directory.")
        sys.exit(1)

# Also import our existing hash-based pagination for comparison
try:
    from remax_hash_pagination import handle_remax_hash_pagination
except ImportError:
    logger.error("remax_hash_pagination.py not found in the current directory.")
    sys.exit(1)

def test_remax_agentql_vs_hash():
    """Compare AgentQL-based pagination with our hash-based URL approach"""
    logger.info("Testing Remax.com.tn pagination methods...")
    
    base_url = "https://www.remax.com.tn/PublicListingList.aspx"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create a results directory
    os.makedirs("tests", exist_ok=True)
    output_file = f"tests/remax_agentql_test_{timestamp}.txt"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=== REMAX.COM.TN PAGINATION METHODS COMPARISON ===\n\n")
        
        # Test hash-based URL generation
        f.write("1. Hash-based URL Generation Test\n")
        f.write("--------------------------------\n")
        for page in range(1, 4):
            url = handle_remax_hash_pagination(base_url, page)
            f.write(f"Page {page}: {url}\n")
        f.write("\n")
        
        # Test AgentQL-based pagination
        f.write("2. AgentQL-based Pagination Test\n")
        f.write("--------------------------------\n")
        f.write("Starting AgentQL scraping with max 2 pages...\n")
        
        def log_callback(properties, page_number):
            """Callback to log properties found in each page"""
            msg = f"Page {page_number}: Found {len(properties)} properties\n"
            f.write(msg)
            
            # Log first 2 properties as sample
            for i, prop in enumerate(properties[:2]):
                prop_details = f"  Property {i+1}: {prop.get('title', 'No title')} - {prop.get('price', 'No price')}\n"
                f.write(prop_details)
        
        # Run the test scrape with only 2 pages maximum
        try:
            start_time = time.time()
            properties = scrape_remax_with_agentql(base_url, max_pages=2, output_callback=log_callback)
            end_time = time.time()
            
            f.write(f"\nTotal properties found: {len(properties)}\n")
            f.write(f"Time taken: {end_time - start_time:.2f} seconds\n\n")
            
            # Write sample property data 
            f.write("3. Sample Property Data (First property)\n")
            f.write("--------------------------------\n")
            if properties:
                sample_prop = properties[0]
                for key, value in sample_prop.items():
                    f.write(f"{key}: {value}\n")
            else:
                f.write("No properties found.\n")
                
        except Exception as e:
            f.write(f"Error during AgentQL test: {str(e)}\n")
            logger.error(f"Error during AgentQL test: {str(e)}")
        
        f.write("\n=== TEST COMPLETED ===\n")
    
    logger.info(f"Test completed. Results saved to {output_file}")
    return output_file

if __name__ == "__main__":
    result_file = test_remax_agentql_vs_hash()
    print(f"Test completed. Results available in {result_file}")
    
    # Print a summary of the results
    try:
        with open(result_file, "r", encoding="utf-8") as f:
            print("\nSummary:")
            print("========")
            lines = f.readlines()
            for line in lines[:10]:  # Print the first 10 lines
                print(line.strip())
            print("...")
            for line in lines[-5:]:  # Print the last 5 lines
                print(line.strip())
    except Exception as e:
        print(f"Error reading results: {e}")
