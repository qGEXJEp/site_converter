import argparse
import asyncio
import logging
from .parser import SiteParser

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Convert a website into an offline-ready format asynchronously.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "url",
        type=str,
        help="The target website URL (e.g., https://example.com) or local HTML file path."
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default="site_offline",
        help="Target output directory for offline assets."
    )

    args = parser.parse_args()
    parser_logic = SiteParser(output_dir=args.output)

    try:
        asyncio.run(parser_logic.process_site(args.url))
    except KeyboardInterrupt:
        logging.info("Process interrupted by user.")
    except Exception as e:
        logging.error(f"Execution failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()