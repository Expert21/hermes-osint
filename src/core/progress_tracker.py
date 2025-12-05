
import logging
import time
from typing import Optional
from tqdm import tqdm
from contextlib import contextmanager

logger = logging.getLogger("OSINT_Tool")


class ProgressTracker:
    """
    Progress tracking system with real-time indicators and ETA calculation.
    Uses tqdm for visual progress bars and status updates.
    """
    
    def __init__(self):
        self.current_operation = None
        self.start_time = None
        self.progress_bar = None
    
    @contextmanager
    def track_operation(
        self,
        operation_name: str,
        total_steps: int,
        desc: Optional[str] = None
    ):
        """
        Context manager for tracking a multi-step operation.
        
        Args:
            operation_name: Name of the operation
            total_steps: Total number of steps
            desc: Optional description for progress bar
            
        Usage:
            with tracker.track_operation("Social Media Scan", 8) as progress:
                for platform in platforms:
                    # Do work
                    progress.update(1)
        """
        self.current_operation = operation_name
        self.start_time = time.time()
        
        # Create progress bar
        self.progress_bar = tqdm(
            total=total_steps,
            desc=desc or operation_name,
            unit="step",
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
            ncols=100
        )
        
        try:
            yield self.progress_bar
        finally:
            if self.progress_bar:
                self.progress_bar.close()
            
            elapsed = time.time() - self.start_time
            logger.info(f"✓ {operation_name} completed in {elapsed:.2f}s")
            
            self.current_operation = None
            self.start_time = None
            self.progress_bar = None
    
    def update_status(self, message: str):
        """
        Update the current status message.
        
        Args:
            message: Status message to display
        """
        if self.progress_bar:
            self.progress_bar.set_postfix_str(message)
        else:
            logger.info(f"Status: {message}")
    
    def log_step(self, step_name: str):
        """
        Log a specific step within an operation.
        
        Args:
            step_name: Name of the step being executed
        """
        if self.progress_bar:
            self.progress_bar.set_description(f"{self.current_operation}: {step_name}")
        logger.debug(f"Step: {step_name}")


class SimpleProgressTracker:
    """
    Simplified progress tracker for operations without tqdm.
    Provides basic status updates and timing.
    """
    
    def __init__(self):
        self.operations = []
    
    def start_operation(self, operation_name: str, total_steps: int):
        """Start tracking an operation."""
        self.operations.append({
            'name': operation_name,
            'total': total_steps,
            'current': 0,
            'start_time': time.time()
        })
        logger.info(f"Starting: {operation_name} ({total_steps} steps)")
    
    def update(self, steps: int = 1):
        """Update progress for current operation."""
        if not self.operations:
            return
        
        op = self.operations[-1]
        op['current'] += steps
        
        # Calculate progress percentage
        progress_pct = (op['current'] / op['total']) * 100 if op['total'] > 0 else 0
        
        # Calculate ETA
        elapsed = time.time() - op['start_time']
        if op['current'] > 0:
            eta = (elapsed / op['current']) * (op['total'] - op['current'])
            logger.info(f"Progress: {op['current']}/{op['total']} ({progress_pct:.1f}%) - ETA: {eta:.1f}s")
        else:
            logger.info(f"Progress: {op['current']}/{op['total']} ({progress_pct:.1f}%)")
    
    def complete_operation(self):
        """Mark current operation as complete."""
        if not self.operations:
            return
        
        op = self.operations.pop()
        elapsed = time.time() - op['start_time']
        logger.info(f"✓ {op['name']} completed in {elapsed:.2f}s")


# Global progress tracker instance
_global_tracker = None


def get_progress_tracker(use_tqdm: bool = True) -> ProgressTracker:
    """
    Get or create the global progress tracker instance.
    
    Args:
        use_tqdm: Whether to use tqdm-based tracker (default: True)
        
    Returns:
        ProgressTracker instance
    """
    global _global_tracker
    
    if _global_tracker is None:
        if use_tqdm:
            _global_tracker = ProgressTracker()
        else:
            _global_tracker = SimpleProgressTracker()
    
    return _global_tracker
