import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class WindVoiceLogger:
    """Enhanced logging system for WindVoice with detailed audio workflow tracking"""
    
    def __init__(self, log_level: str = "DEBUG", log_to_file: bool = True):
        self.log_level = getattr(logging, log_level.upper(), logging.DEBUG)
        self.log_to_file = log_to_file
        self.logger = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup comprehensive logging configuration"""
        # Create logger
        self.logger = logging.getLogger("windvoice")
        self.logger.setLevel(self.log_level)
        
        # Clear any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '[%(asctime)s] %(name)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)8s] %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Console handler with UTF-8 encoding
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Try to set UTF-8 encoding for Windows console
        try:
            import codecs
            sys.stdout.reconfigure(encoding='utf-8')
        except (AttributeError, UnicodeError):
            # Fallback for older Python versions or encoding issues
            pass
            
        self.logger.addHandler(console_handler)
        
        # File handler (if enabled)
        if self.log_to_file:
            try:
                log_dir = Path.home() / ".windvoice" / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                
                log_file = log_dir / f"windvoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(detailed_formatter)
                self.logger.addHandler(file_handler)
                
                # Keep only last 10 log files
                self._cleanup_old_logs(log_dir)
                
                print(f"Detailed logs are being written to: {log_file}")
                
            except Exception as e:
                print(f"Warning: Could not setup file logging: {e}")
    
    def _cleanup_old_logs(self, log_dir: Path, keep_files: int = 10):
        """Remove old log files, keeping only the most recent ones"""
        try:
            log_files = sorted(log_dir.glob("windvoice_*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
            for old_file in log_files[keep_files:]:
                old_file.unlink()
        except Exception:
            pass  # Ignore cleanup errors
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance"""
        if name:
            return logging.getLogger(f"windvoice.{name}")
        return self.logger
    
    @staticmethod
    def log_audio_workflow_step(logger: logging.Logger, step: str, details: dict = None):
        """Log audio workflow steps with consistent formatting"""
        details_str = ""
        if details:
            detail_items = []
            for key, value in details.items():
                if isinstance(value, float):
                    detail_items.append(f"{key}={value:.4f}")
                else:
                    detail_items.append(f"{key}={value}")
            details_str = f" | {', '.join(detail_items)}"
        
        logger.info(f"[AUDIO] {step}{details_str}")
    
    @staticmethod
    def log_hotkey_event(logger: logging.Logger, event: str, details: dict = None):
        """Log hotkey events with consistent formatting"""
        details_str = ""
        if details:
            detail_items = [f"{k}={v}" for k, v in details.items()]
            details_str = f" | {', '.join(detail_items)}"
        
        logger.info(f"[HOTKEY] {event}{details_str}")
    
    @staticmethod
    def log_validation_result(logger: logging.Logger, validation_type: str, result: dict):
        """Log validation results with detailed metrics"""
        logger.info(f"✅ VALIDATION: {validation_type}")
        for key, value in result.items():
            if isinstance(value, float):
                logger.info(f"   {key}: {value:.4f}")
            elif isinstance(value, bool):
                logger.info(f"   {key}: {'✓' if value else '✗'}")
            else:
                logger.info(f"   {key}: {value}")


# Global logger instance
_logger_instance: Optional[WindVoiceLogger] = None

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get the global WindVoice logger"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = WindVoiceLogger()
    return _logger_instance.get_logger(name)

def setup_logging(log_level: str = "DEBUG", log_to_file: bool = True):
    """Setup the global logging system"""
    global _logger_instance
    _logger_instance = WindVoiceLogger(log_level, log_to_file)
    return _logger_instance.get_logger()