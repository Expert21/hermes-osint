"""
Structured logging for scan events and failures.
Creates a detailed log of what was checked, what failed, and why.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger("OSINT_Tool")


class EventType(Enum):
    """Types of scan events to log"""
    SCAN_START = "scan_start"
    SCAN_END = "scan_end"
    MODULE_START = "module_start"
    MODULE_END = "module_end"
    API_REQUEST = "api_request"
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"
    SUCCESS = "success"
    FAILURE = "failure"


class ScanLogger:
    """
    Structured logger for tracking scan events and failures.
    Outputs to both console logger and structured log file.
    """
    
    def __init__(self, output_format: str = "json"):
        """
        Initialize scan logger.
        
        Args:
            output_format: Format for log file ('json' or 'csv')
        """
        self.output_format = output_format
        self.events: List[Dict[str, Any]] = []
        self.scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def log_event(
        self,
        event_type: EventType,
        module: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ):
        """
        Log a scan event with structured data.
        
        Args:
            event_type: Type of event
            module: Module name (e.g., 'passive_intelligence', 'email_enumeration')
            message: Human-readable message
            details: Additional structured data
            error: Exception object if applicable
        """
        import traceback
        
        error_str = None
        if error:
            if hasattr(error, '__traceback__') and error.__traceback__:
                error_str = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            else:
                error_str = str(error)

        event = {
            "timestamp": datetime.now().isoformat(),
            "scan_id": self.scan_id,
            "event_type": event_type.value,
            "module": module,
            "message": message,
            "details": details or {},
            "error": error_str,
            "error_type": type(error).__name__ if error else None
        }
        
        self.events.append(event)
        
        # Also log to console
        if event_type in [EventType.API_ERROR, EventType.FAILURE, EventType.TIMEOUT]:
            logger.error(f"[{module}] {message}" + (f" - {error}" if error else ""))
        elif event_type == EventType.RATE_LIMIT:
            logger.warning(f"[{module}] {message}")
        else:
            logger.debug(f"[{module}] {message}")
    
    def save_log(self, output_file: str):
        """
        Save structured log to file.
        
        Args:
            output_file: Path to output file
        """
        output_path = Path(output_file)
        
        if self.output_format == "json":
            self._save_json(output_path)
        elif self.output_format == "csv":
            self._save_csv(output_path)
        else:
            logger.warning(f"Unknown output format: {self.output_format}, defaulting to JSON")
            self._save_json(output_path)
    
    def _save_json(self, output_path: Path):
        """Save log as JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "scan_id": self.scan_id,
                "total_events": len(self.events),
                "events": self.events
            }, f, indent=2)
        logger.info(f"✓ Scan log saved to {output_path}")
    
    def _save_csv(self, output_path: Path):
        """Save log as CSV"""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['timestamp', 'scan_id', 'event_type', 'module', 'message', 'error', 'error_type']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for event in self.events:
                row = {k: event.get(k, '') for k in fieldnames}
                writer.writerow(row)
        
        logger.info(f"✓ Scan log saved to {output_path}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of the scan.
        
        Returns:
            Dictionary with event counts and error summary
        """
        summary = {
            "total_events": len(self.events),
            "errors": sum(1 for e in self.events if e['event_type'] in ['api_error', 'failure']),
            "rate_limits": sum(1 for e in self.events if e['event_type'] == 'rate_limit'),
            "timeouts": sum(1 for e in self.events if e['event_type'] == 'timeout'),
            "successes": sum(1 for e in self.events if e['event_type'] == 'success')
        }
        
        # Group errors by module
        errors_by_module = {}
        for event in self.events:
            if event['event_type'] in ['api_error', 'failure']:
                module = event['module']
                errors_by_module[module] = errors_by_module.get(module, 0) + 1
        
        summary['errors_by_module'] = errors_by_module
        
        return summary
    
    def print_summary(self):
        """Print summary to console"""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("SCAN EVENT SUMMARY")
        print("="*60)
        print(f"Total Events: {summary['total_events']}")
        print(f"Successes: {summary['successes']}")
        print(f"Errors: {summary['errors']}")
        print(f"Rate Limits: {summary['rate_limits']}")
        print(f"Timeouts: {summary['timeouts']}")
        
        if summary['errors_by_module']:
            print("\nErrors by Module:")
            for module, count in summary['errors_by_module'].items():
                print(f"  - {module}: {count}")
        print("="*60 + "\n")
