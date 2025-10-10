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
    """
    
    # Model settings
    model_path: str = "models/best.pt"
    confidence_threshold: float = 0.6
    
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
        
        Returns:
            AppConfig instance with values from environment variables or defaults
        """
        return cls(
            model_path=os.getenv('OCR_MODEL_PATH', cls.model_path),
            confidence_threshold=float(os.getenv('OCR_CONFIDENCE_THRESHOLD', cls.confidence_threshold)),
            target_window_title=os.getenv('OCR_WINDOW_TITLE', cls.target_window_title),
            ocr_lang=os.getenv('OCR_LANG', cls.ocr_lang),
            ocr_margin=int(os.getenv('OCR_MARGIN', cls.ocr_margin)),
            min_text_length=int(os.getenv('OCR_MIN_TEXT_LENGTH', cls.min_text_length)),
            output_csv=os.getenv('OCR_OUTPUT_CSV', cls.output_csv),
            display_window_name=os.getenv('OCR_DISPLAY_WINDOW', cls.display_window_name),
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
            f"  display_window_name='{self.display_window_name}'\n"
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
