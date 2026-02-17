import os
import json
import argparse
from loguru import logger
from src.config import settings
from src.engine.extractor import ShipmentExtractor
from src.connectors.json_connector import JSONConnector
from src.connectors.email_connector import EmailConnector

def main():
    parser = argparse.ArgumentParser(description="Shipment Extraction System - AI Engineering Demo")
    parser.add_argument("--source", choices=["json", "email"], default="json", help="Data source: 'json' for batch/dummy data, 'email' for live IMAP fetch (requires .env config)")
    parser.add_argument("--limit", type=int, default=10, help="Number of emails to fetch (if source is email)")
    args = parser.parse_args()

    logger.info("Initializing Shipment Extraction System Pipeline...")
    
    # 1. Initialize Engine
    extractor = ShipmentExtractor()
    
    # 2. Setup Connector based on source
    if args.source == "email":
        if not all([settings.EMAIL_HOST, settings.EMAIL_USER, settings.EMAIL_PASS]):
            logger.error("Missing Email Configuration in .env. Falling back to JSON source.")
            connector = JSONConnector(settings.INPUT_PATH)
        else:
            connector = EmailConnector(
                host=settings.EMAIL_HOST,
                user=settings.EMAIL_USER,
                password=settings.EMAIL_PASS,
                folder=settings.EMAIL_FOLDER
            )
            logger.info(f"Source set to LIVE EMAIL (IMAP: {settings.EMAIL_HOST})")
    else:
        connector = JSONConnector(settings.INPUT_PATH)
        logger.info(f"Source set to BATCH JSON ({settings.INPUT_PATH})")

    # 3. Data Ingestion
    emails = connector.fetch_emails() if args.source == "json" else connector.fetch_emails(limit=args.limit)
    
    if not emails:
        logger.warning("No emails retrieved. Check configurations.")
        return

    # 4. Processing Pipeline
    results = []
    logger.info(f"Found {len(emails)} items to process. Running extraction engine...")
    
    for i, email in enumerate(emails):
        email_id = email.get('id', f'item_{i}')
        logger.info(f"[{i+1}/{len(emails)}] Processing: {email_id}")
        
        result = extractor.process_item(email)
        results.append(result.model_dump())
        
        # Incremental save (Checkpointing)
        with open(settings.OUTPUT_PATH, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2)
            
    logger.info(f"Extraction Pipeline Complete. Results saved to {settings.OUTPUT_PATH}")

if __name__ == "__main__":
    main()
