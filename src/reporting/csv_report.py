import csv
import logging
from src.core.input_validator import InputValidator

logger = logging.getLogger("OSINT_Tool")

def generate_csv_report(results, output_file):
    """
    Generate a CSV report from the results.
    
    Args:
        results: Dictionary containing scan results
        output_file: Path to the output CSV file
    """
    try:
        # Validate path and prevent TOCTOU/Symlink attacks
        safe_path = InputValidator.validate_output_path(output_file, allowed_extensions=['.csv'])
        
        # Write to temp file first
        temp_file = safe_path.with_suffix('.tmp')
        
        try:
            with open(temp_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Module", "Source/Platform", "Title/Status", "URL", "Description/Details"])
                
                # Process Search Engine Results
                if 'search_engines' in results:
                    for item in results['search_engines']:
                        writer.writerow([
                            "Search Engine",
                            item.get('source', 'N/A'),
                            item.get('title', 'N/A'),
                            item.get('url', 'N/A'),
                            item.get('description', 'N/A')
                        ])
                
                # Process Social Media Results
                if 'social_media' in results:
                    for item in results['social_media']:
                        writer.writerow([
                            "Social Media",
                            item.get('platform', 'N/A'),
                            item.get('status', 'N/A'),
                            item.get('url', 'N/A'),
                            ""
                        ])
                
                # Process Connections
                if 'connections' in results:
                    for item in results['connections']:
                        writer.writerow([
                            "Connection",
                            item.get('relationship', 'N/A'),
                            item.get('type', 'N/A'),
                            f"{item.get('source_entity', {}).get('value', 'N/A')} -> {item.get('target_entity', {}).get('value', 'N/A')}",
                            item.get('metadata', {}).get('description', '')
                        ])
            
            # Check BEFORE writing anything
            if safe_path.exists():
                if safe_path.is_symlink():
                    raise ValueError("Target is a symlink - possible attack")
                # Also verify it's not a special file
                if not safe_path.is_file():
                    raise ValueError("Target is not a regular file")

            # Revalidate target isn't a symlink before replacing
            if safe_path.exists() and safe_path.is_symlink():
                # Cleanup temp file if it exists before raising error
                if temp_file.exists():
                    temp_file.unlink()
                raise ValueError("Target became a symlink during write - possible attack attempt")
                
            # Atomic rename
            temp_file.replace(safe_path)
            logger.info(f"CSV report saved to {safe_path}")
            
        finally:
            # Cleanup temp file if it still exists
            if temp_file.exists():
                temp_file.unlink()
                
    except Exception as e:
        logger.error(f"Failed to save CSV report: {e}")
