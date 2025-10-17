"""
Configuration management module for the real-time OCR application.

This module defines the application configuration using a dataclass and provides
validation logic to ensure configuration values are valid.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import os


@dataclass
class AppConfig:
    """
    Application configuration dataclass.
    
    Attributes:
        model_path: Path to the YOLOv8 model file (best.pt)
        confidence_threshold: Detection confidence threshold (0.0-1.0)
        target_window_title: Title of the window to capture (partial match)
        ocr_lang: OCR language code (e.g., 'jpn' for Japanese)
        ocr_margin: Margin in pixels to add when cropping detected regions
        min_text_length: Minimum text length to consider valid
        output_csv: Path to the output CSV file
        display_window_name: Name of the display window for visualization
        performance_mode: Performance mode preset ("fast", "balanced", "accurate")
        detection_cache_ttl: Detection cache time-to-live in seconds
        detection_cache_similarity: Frame similarity threshold for cache hit (0.0-1.0)
        ocr_cache_position_tolerance: Position tolerance in pixels for OCR cache matching
        queue_max_size: Maximum size for processing queues
        display_queue_max_size: Maximum size for display queue
        hierarchical_model_path: Path to the hierarchical detection model (5 classes)
        use_hierarchical_detection: Enable hierarchical detection mode
        iou_threshold: IoU threshold for parent-child relationship determination (0.0-1.0)
        similarity_threshold: Text similarity threshold for duplicate detection (0.0-1.0)
        session_output_dir: Directory for session-based image output
        hierarchical_csv_output: Path to the hierarchical detection CSV output file
    """
    
    # Model settings
    model_path: str = "models/best.pt"
    confidence_threshold: float = 0.65  # 検出率とパフォーマンスのバランス（0.6→0.65に微調整）
    
    # Window capture settings
    target_window_title: str = "iPhone"
    
    # OCR settings
    ocr_lang: str = "jpn"
    ocr_margin: int = 5
    min_text_length: int = 2
    
    # Output settings
    output_csv: str = "book_data_realtime.csv"
    
    # Display settings
    display_window_name: str = "Real-time Detection"
    
    # Performance settings
    performance_mode: str = "balanced"
    detection_cache_ttl: float = 0.7  # キャッシュ有効期限（1.0→0.7秒に短縮、新規検出を優先）
    detection_cache_similarity: float = 0.93  # 類似度しきい値（0.90→0.93に調整、より厳密に）
    ocr_cache_position_tolerance: int = 12  # 位置許容範囲（15→12ピクセルに調整）
    queue_max_size: int = 5
    display_queue_max_size: int = 2
    
    # Hierarchical detection settings
    hierarchical_model_path: str = "models/hierarchical_best.pt"
    use_hierarchical_detection: bool = False
    iou_threshold: float = 0.5
    similarity_threshold: float = 0.75
    session_output_dir: str = "output/sessions"
    hierarchical_csv_output: str = "output/hierarchical_data.csv"
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the configuration values.
        
        Returns:
            A tuple of (is_valid, error_message).
            If valid, returns (True, None).
            If invalid, returns (False, error_message).
        """
        # Validate confidence threshold
        if not 0.0 <= self.confidence_threshold <= 1.0:
            return False, f"confidence_threshold must be between 0.0 and 1.0, got {self.confidence_threshold}"
        
        # Validate model path exists
        if not Path(self.model_path).exists():
            return False, f"Model file not found: {self.model_path}"
        
        # Validate model path is a file
        if not Path(self.model_path).is_file():
            return False, f"Model path is not a file: {self.model_path}"
        
        # Validate OCR margin is non-negative
        if self.ocr_margin < 0:
            return False, f"ocr_margin must be non-negative, got {self.ocr_margin}"
        
        # Validate min_text_length is positive
        if self.min_text_length < 1:
            return False, f"min_text_length must be at least 1, got {self.min_text_length}"
        
        # Validate target_window_title is not empty
        if not self.target_window_title or not self.target_window_title.strip():
            return False, "target_window_title cannot be empty"
        
        # Validate ocr_lang is not empty
        if not self.ocr_lang or not self.ocr_lang.strip():
            return False, "ocr_lang cannot be empty"
        
        # Validate output_csv is not empty
        if not self.output_csv or not self.output_csv.strip():
            return False, "output_csv cannot be empty"
        
        # Validate output directory exists or can be created
        output_dir = Path(self.output_csv).parent
        if output_dir != Path('.') and not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create output directory {output_dir}: {e}"
        
        # Validate display_window_name is not empty
        if not self.display_window_name or not self.display_window_name.strip():
            return False, "display_window_name cannot be empty"
        
        # Validate performance mode
        valid_modes = ["fast", "balanced", "accurate"]
        if self.performance_mode not in valid_modes:
            return False, f"performance_mode must be one of {valid_modes}, got '{self.performance_mode}'"
        
        # Validate detection cache TTL
        if self.detection_cache_ttl <= 0:
            return False, f"detection_cache_ttl must be positive, got {self.detection_cache_ttl}"
        
        # Validate detection cache similarity threshold
        if not 0.0 <= self.detection_cache_similarity <= 1.0:
            return False, f"detection_cache_similarity must be between 0.0 and 1.0, got {self.detection_cache_similarity}"
        
        # Validate OCR cache position tolerance
        if self.ocr_cache_position_tolerance < 0:
            return False, f"ocr_cache_position_tolerance must be non-negative, got {self.ocr_cache_position_tolerance}"
        
        # Validate queue sizes
        if self.queue_max_size < 1:
            return False, f"queue_max_size must be at least 1, got {self.queue_max_size}"
        
        if self.display_queue_max_size < 1:
            return False, f"display_queue_max_size must be at least 1, got {self.display_queue_max_size}"
        
        # Validate hierarchical detection settings
        if self.use_hierarchical_detection:
            # Validate hierarchical model path exists
            if not Path(self.hierarchical_model_path).exists():
                return False, f"Hierarchical model file not found: {self.hierarchical_model_path}"
            
            # Validate hierarchical model path is a file
            if not Path(self.hierarchical_model_path).is_file():
                return False, f"Hierarchical model path is not a file: {self.hierarchical_model_path}"
        
        # Validate IoU threshold
        if not 0.0 <= self.iou_threshold <= 1.0:
            return False, f"iou_threshold must be between 0.0 and 1.0, got {self.iou_threshold}"
        
        # Validate similarity threshold
        if not 0.0 <= self.similarity_threshold <= 1.0:
            return False, f"similarity_threshold must be between 0.0 and 1.0, got {self.similarity_threshold}"
        
        # Validate session output directory
        if not self.session_output_dir or not self.session_output_dir.strip():
            return False, "session_output_dir cannot be empty"
        
        # Validate hierarchical CSV output
        if not self.hierarchical_csv_output or not self.hierarchical_csv_output.strip():
            return False, "hierarchical_csv_output cannot be empty"
        
        # Validate hierarchical CSV output directory exists or can be created
        hierarchical_output_dir = Path(self.hierarchical_csv_output).parent
        if hierarchical_output_dir != Path('.') and not hierarchical_output_dir.exists():
            try:
                hierarchical_output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create hierarchical output directory {hierarchical_output_dir}: {e}"
        
        return True, None
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """
        Create configuration from environment variables.
        
        Environment variables:
            OCR_MODEL_PATH: Path to YOLOv8 model
            OCR_CONFIDENCE_THRESHOLD: Detection confidence threshold
            OCR_WINDOW_TITLE: Target window title
            OCR_LANG: OCR language
            OCR_MARGIN: OCR margin in pixels
            OCR_MIN_TEXT_LENGTH: Minimum text length
            OCR_OUTPUT_CSV: Output CSV file path
            OCR_DISPLAY_WINDOW: Display window name
            OCR_PERFORMANCE_MODE: Performance mode preset (fast/balanced/accurate)
            OCR_DETECTION_CACHE_TTL: Detection cache TTL in seconds
            OCR_DETECTION_CACHE_SIMILARITY: Detection cache similarity threshold
            OCR_OCR_CACHE_POSITION_TOLERANCE: OCR cache position tolerance in pixels
            OCR_QUEUE_MAX_SIZE: Maximum queue size
            OCR_DISPLAY_QUEUE_MAX_SIZE: Maximum display queue size
            OCR_HIERARCHICAL_MODEL_PATH: Path to hierarchical detection model
            OCR_USE_HIERARCHICAL_DETECTION: Enable hierarchical detection mode (true/false)
            OCR_IOU_THRESHOLD: IoU threshold for parent-child relationship
            OCR_SIMILARITY_THRESHOLD: Text similarity threshold for duplicate detection
            OCR_SESSION_OUTPUT_DIR: Directory for session-based image output
            OCR_HIERARCHICAL_CSV_OUTPUT: Path to hierarchical detection CSV output
        
        Returns:
            AppConfig instance with values from environment variables or defaults
        """
        # Get default values from class
        defaults = cls()
        
        return cls(
            model_path=os.getenv('OCR_MODEL_PATH', defaults.model_path),
            confidence_threshold=float(os.getenv('OCR_CONFIDENCE_THRESHOLD', str(defaults.confidence_threshold))),
            target_window_title=os.getenv('OCR_WINDOW_TITLE', defaults.target_window_title),
            ocr_lang=os.getenv('OCR_LANG', defaults.ocr_lang),
            ocr_margin=int(os.getenv('OCR_MARGIN', str(defaults.ocr_margin))),
            min_text_length=int(os.getenv('OCR_MIN_TEXT_LENGTH', str(defaults.min_text_length))),
            output_csv=os.getenv('OCR_OUTPUT_CSV', defaults.output_csv),
            display_window_name=os.getenv('OCR_DISPLAY_WINDOW', defaults.display_window_name),
            performance_mode=os.getenv('OCR_PERFORMANCE_MODE', defaults.performance_mode),
            detection_cache_ttl=float(os.getenv('OCR_DETECTION_CACHE_TTL', str(defaults.detection_cache_ttl))),
            detection_cache_similarity=float(os.getenv('OCR_DETECTION_CACHE_SIMILARITY', str(defaults.detection_cache_similarity))),
            ocr_cache_position_tolerance=int(os.getenv('OCR_OCR_CACHE_POSITION_TOLERANCE', str(defaults.ocr_cache_position_tolerance))),
            queue_max_size=int(os.getenv('OCR_QUEUE_MAX_SIZE', str(defaults.queue_max_size))),
            display_queue_max_size=int(os.getenv('OCR_DISPLAY_QUEUE_MAX_SIZE', str(defaults.display_queue_max_size))),
            hierarchical_model_path=os.getenv('OCR_HIERARCHICAL_MODEL_PATH', defaults.hierarchical_model_path),
            use_hierarchical_detection=os.getenv('OCR_USE_HIERARCHICAL_DETECTION', str(defaults.use_hierarchical_detection)).lower() in ('true', '1', 'yes'),
            iou_threshold=float(os.getenv('OCR_IOU_THRESHOLD', str(defaults.iou_threshold))),
            similarity_threshold=float(os.getenv('OCR_SIMILARITY_THRESHOLD', str(defaults.similarity_threshold))),
            session_output_dir=os.getenv('OCR_SESSION_OUTPUT_DIR', defaults.session_output_dir),
            hierarchical_csv_output=os.getenv('OCR_HIERARCHICAL_CSV_OUTPUT', defaults.hierarchical_csv_output),
        )
    
    def __str__(self) -> str:
        """Return a string representation of the configuration."""
        return (
            f"AppConfig(\n"
            f"  model_path='{self.model_path}',\n"
            f"  confidence_threshold={self.confidence_threshold},\n"
            f"  target_window_title='{self.target_window_title}',\n"
            f"  ocr_lang='{self.ocr_lang}',\n"
            f"  ocr_margin={self.ocr_margin},\n"
            f"  min_text_length={self.min_text_length},\n"
            f"  output_csv='{self.output_csv}',\n"
            f"  display_window_name='{self.display_window_name}',\n"
            f"  performance_mode='{self.performance_mode}',\n"
            f"  detection_cache_ttl={self.detection_cache_ttl},\n"
            f"  detection_cache_similarity={self.detection_cache_similarity},\n"
            f"  ocr_cache_position_tolerance={self.ocr_cache_position_tolerance},\n"
            f"  queue_max_size={self.queue_max_size},\n"
            f"  display_queue_max_size={self.display_queue_max_size},\n"
            f"  hierarchical_model_path='{self.hierarchical_model_path}',\n"
            f"  use_hierarchical_detection={self.use_hierarchical_detection},\n"
            f"  iou_threshold={self.iou_threshold},\n"
            f"  similarity_threshold={self.similarity_threshold},\n"
            f"  session_output_dir='{self.session_output_dir}',\n"
            f"  hierarchical_csv_output='{self.hierarchical_csv_output}'\n"
            f")"
        )


def load_config() -> AppConfig:
    """
    Load configuration with the following priority:
    1. Environment variables
    2. Default values
    
    Returns:
        AppConfig instance
    """
    return AppConfig.from_env()
