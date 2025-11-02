# License Plate Detection with YOLO11

Automatic Number Plate Recognition (ANPR) system using YOLO11 and OCR.

Based on [Ultralytics YOLO11 ANPR approach](https://www.ultralytics.com/blog/using-ultralytics-yolo11-for-automatic-number-plate-recognition).

## Features

- Vehicle detection using YOLO11
- License plate detection (traditional CV or custom YOLO model)
- OCR text extraction with EasyOCR
- ESP32 camera support
- Local image processing

## Installation

```bash
pip install ultralytics opencv-python easyocr numpy requests
```

## Usage

### Process Test Images

Place images in `test/` folder and run:

```bash
python main.py
```

### Fetch from ESP32 Camera

Update `ESP32_IP` in `main.py` and use:

```python
detector = LicensePlateDetector()
image = detector.fetch_esp32_image()
results = detector.process_image(image, save_result=True, output_path="result.jpg")
```

### Use Custom YOLO Model

Train a custom license plate detection model and use:

```python
detector = LicensePlateDetector('path/to/plate_model.pt')
```

## Output

Results are saved as `result_*.jpg` with:
- Green bounding boxes around detected plates
- License plate numbers annotated above boxes
- Console output with detected plate numbers

## Configuration

- `ESP32_IP`: ESP32 camera URL (default: `http://192.168.5.32:81`)
- Vehicle classes: cars (2), buses (5), trucks (7)
- Confidence threshold: 0.25

## How It Works

1. **Vehicle Detection**: YOLO11 detects vehicles to focus search area
2. **Plate Detection**: Traditional CV or custom YOLO model finds plates
3. **OCR Extraction**: EasyOCR reads text from detected plates
4. **Validation**: Filters results based on typical plate characteristics
