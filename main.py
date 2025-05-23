# automated_skeptic_mvp/main.py
"""
Automated Skeptic MVP (Version 1.0)
Main entry point for the truth verification pipeline
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from typing import List, Dict, Any

from pipeline.orchestrator import SkepticPipeline
from data.models import Claim, VerificationResult
from config.settings import Settings

def setup_logging():
    """Configure UTF-8 logging for Windows"""
    # Force UTF-8 encoding for logging
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('automated_skeptic.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_claims_from_file(filepath: str) -> List[str]:
    """Load claims from CSV file"""
    claims = []
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                if row:  # Skip empty rows
                    claims.append(row[0])  # Assume claim is in first column
    except FileNotFoundError:
        logging.error(f"Claims file not found: {filepath}")
        sys.exit(1)
    return claims

def save_results(results: List[VerificationResult], output_file: str):
    """Save verification results to JSON file"""
    results_data = []
    for result in results:
        results_data.append({
            'claim': result.original_claim,
            'verdict': result.verdict,
            'confidence': result.confidence,
            'evidence_summary': result.evidence_summary,
            'sources': [{'url': s.url, 'title': s.title, 'credibility': s.credibility_score} 
                       for s in result.sources],
            'processing_time': result.processing_time,
            'timestamp': result.timestamp.isoformat()
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Automated Skeptic MVP - Truth Verification System')
    parser.add_argument('--claim', type=str, help='Single claim to verify')
    parser.add_argument('--file', type=str, help='CSV file containing claims to verify')
    parser.add_argument('--output', type=str, default='results.json', help='Output file for results')
    parser.add_argument('--config', type=str, default='config/config.ini', help='Configuration file path')
    
    args = parser.parse_args()
    
    if not args.claim and not args.file:
        parser.error("Either --claim or --file must be specified")
    
    # Setup
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load configuration
    settings = Settings(args.config)
    
    # Initialize pipeline
    pipeline = SkepticPipeline(settings)
    
    # Prepare claims
    claims = []
    if args.claim:
        claims = [args.claim]
    elif args.file:
        claims = load_claims_from_file(args.file)
    
    logger.info(f"Processing {len(claims)} claim(s)")
    
    # Process claims
    results = []
    start_time = time.time()
    
    for i, claim_text in enumerate(claims, 1):
        logger.info(f"Processing claim {i}/{len(claims)}: {claim_text}")
        
        claim = Claim(text=claim_text)
        try:
            result = pipeline.process_claim(claim)
            results.append(result)
            logger.info(f"Completed claim {i}: {result.verdict}")
        except Exception as e:
            logger.error(f"Error processing claim {i}: {str(e)}")
            # Create error result
            error_result = VerificationResult(
                original_claim=claim_text,
                verdict="ERROR",
                confidence=0.0,
                evidence_summary=f"Processing error: {str(e)}",
                sources=[],
                processing_time=0.0
            )
            results.append(error_result)
    
    total_time = time.time() - start_time
    
    # Save results
    save_results(results, args.output)
    
    # Summary statistics
    successful_results = [r for r in results if r.verdict != "ERROR"]
    accuracy_data = {
        'total_claims': len(claims),
        'successful_processed': len(successful_results),
        'error_count': len(results) - len(successful_results),
        'average_processing_time': sum(r.processing_time for r in successful_results) / len(successful_results) if successful_results else 0,
        'total_processing_time': total_time
    }
    
    logger.info("=== PROCESSING SUMMARY ===")
    logger.info(f"Total claims processed: {accuracy_data['total_claims']}")
    logger.info(f"Successfully processed: {accuracy_data['successful_processed']}")
    logger.info(f"Errors: {accuracy_data['error_count']}")
    logger.info(f"Average processing time: {accuracy_data['average_processing_time']:.2f}s")
    logger.info(f"Total time: {accuracy_data['total_processing_time']:.2f}s")
    logger.info(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()
