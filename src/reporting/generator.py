
import json
import logging
from src.reporting.html_report import generate_html_report
from src.reporting.markdown_report import generate_markdown_report
from src.reporting.pdf_report import generate_pdf_report
from src.reporting.stix_export import generate_stix_report
from src.reporting.csv_report import generate_csv_report
from src.core.input_validator import InputValidator

logger = logging.getLogger("OSINT_Tool")

def generate_report(results, output_file):
    """
    Generates a report from the results.
    Supports JSON, CSV, HTML, Markdown, PDF, and STIX formats.
    """
    # Check for compound extensions first (e.g., .stix.json before .json)
    if output_file.endswith('.stix.json') or output_file.endswith('.stix'):
        generate_stix_report(results, output_file)
    elif output_file.endswith('.html'):
        generate_html_report(results, output_file)
    elif output_file.endswith('.md') or output_file.endswith('.markdown'):
        generate_markdown_report(results, output_file)
    elif output_file.endswith('.pdf'):
        generate_pdf_report(results, output_file)
    elif output_file.endswith('.csv'):
        generate_csv_report(results, output_file)
    elif output_file.endswith('.json'):
        _generate_json_report(results, output_file)
    else:
        logger.warning("Unknown file extension. Defaulting to JSON.")
        _generate_json_report(results, output_file + ".json")

def _generate_json_report(results, output_file):
    try:
        # Validate path and prevent TOCTOU/Symlink attacks
        safe_path = InputValidator.validate_output_path(output_file, allowed_extensions=['.json'])
        
        # Write to temp file first
        temp_file = safe_path.with_suffix('.tmp')
        
        try:
            with open(temp_file, 'w') as f:
                json.dump(results, f, indent=4)
            
            # Revalidate target isn't a symlink before replacing
            if safe_path.exists() and safe_path.is_symlink():
                raise ValueError("Target is a symlink - possible attack attempt")
                
            # Atomic rename
            temp_file.replace(safe_path)
            logger.info(f"JSON report saved to {safe_path}")
            
        finally:
            # Cleanup temp file if it still exists
            if temp_file.exists():
                temp_file.unlink()
                
    except Exception as e:
        logger.error(f"Failed to save JSON report: {e}")

