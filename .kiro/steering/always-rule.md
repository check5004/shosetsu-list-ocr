---
inclusion: always
---

## Project Overview

This is a real-time OCR application for macOS that captures iPhone simulator/mirroring windows, detects novel list items using YOLOv8, extracts Japanese text with Tesseract OCR, and exports to CSV with duplicate filtering.

## Code Style & Conventions

- Use Python 3.9+ with type hints for all function signatures
- Follow dataclass pattern for configuration and data structures
- Use descriptive Japanese docstrings for modules and classes
- Prefer explicit error handling with custom error messages over silent failures
- Use pathlib.Path for file operations instead of string paths
- Keep functions focused and single-purpose

## Architecture Patterns

- Modular design: separate concerns into dedicated modules (capture, detection, OCR, data management, visualization)
- Configuration management: centralize all settings in `src/config.py` using dataclass with validation
- Error handling: dedicated error handler module for consistent error management
- Resource cleanup: implement `__del__` methods for classes managing system resources (mss, OpenCV windows)

## macOS-Specific Requirements

- Use Quartz framework (pyobjc-framework-Quartz) for window management
- Use mss library for screen capture (requires Screen Recording permission)
- Handle BGRA to BGR conversion for OpenCV compatibility
- Always check and document macOS permission requirements

## Model & Performance

- YOLOv8 model path: `models/best.pt` (configurable via AppConfig)
- Leverage Apple Silicon MPS acceleration when available
- Use confidence thresholds to filter detections (default: 0.6)
- Sort detections by Y-coordinate (top to bottom) before OCR processing

## Data Management

- Use Set-based O(1) duplicate checking for extracted text
- Export to CSV with pandas using "extracted_text" column
- Print new entries to terminal in real-time
- Default output: `output/book_data_realtime.csv`

## Testing & Validation

- Use getDiagnostics tool for syntax/type checking instead of bash commands
- Validate configuration on load using AppConfig.validate() method
- Test with actual iPhone simulator windows for integration testing
- Handle missing dependencies gracefully with informative error messages

## Dependencies

- Core: ultralytics (YOLOv8), opencv-python, pytesseract, pandas, mss
- macOS: pyobjc-framework-Quartz
- ML: torch with MPS support for Apple Silicon

## Common Patterns

- Window title matching: case-insensitive partial match
- OCR margin: add configurable pixel margin when cropping detected regions
- Text cleanup: normalize whitespace, filter texts shorter than min_text_length
- Graceful shutdown: handle 'q' key and Ctrl+C with proper resource cleanup and CSV export
- ユーザへの回答・指示・提案は全て日本語で行うこと。
