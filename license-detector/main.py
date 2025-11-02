"""
License Plate Detection using YOLO11 for ANPR
Based on Ultralytics official approach:
https://www.ultralytics.com/blog/using-ultralytics-yolo11-for-automatic-number-plate-recognition
"""


import cv2
import requests
import numpy as np
from pathlib import Path
import re
from ultralytics import YOLO
import easyocr



class LicensePlateDetector:
    """ANPR System using YOLO11 for license plate detection and OCR for plate reading"""

    def __init__(self):
        print("Initializing ANPR System...")
        model_path = Path(__file__).parent / 'license-plate-finetune-v1n.pt'
        if model_path.exists():
            self.plate_model = YOLO(str(model_path))
            print(f"✓ Loaded pretrained plate model: {model_path}")
        else:
            raise FileNotFoundError(f"license-plate-finetune-v1n.pt not found at {model_path}")
        self.reader = easyocr.Reader(['en'], gpu=False)
        print("✓ System ready\n")

    def fetch_esp32_image(self, esp32_url):
        try:
            response = requests.get(f"{esp32_url}/capture", timeout=5)
            if response.status_code == 200:
                img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
                return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"Error fetching from ESP32: {e}")
        return None

    def load_local_image(self, image_path):
        return cv2.imread(str(image_path))

    def detect_license_plates(self, image):
        results = self.plate_model(image, conf=0.3, verbose=False)
        plates = []
        if len(results) > 0 and results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                plates.append({
                    'bbox': (x1, y1, x2, y2),
                    'confidence': float(box.conf[0])
                })
        return plates

    def extract_text_from_plate(self, plate_image):
        """Extract text from license plate using OCR"""
        try:
            h, w = plate_image.shape[:2]
            if h < 60:
                plate_image = cv2.resize(plate_image, None, fx=60/h, fy=60/h, 
                                        interpolation=cv2.INTER_CUBIC)
            
            gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
            ocr_results = []
            
            # Try multiple preprocessing methods
            methods = [
                plate_image,  # Original
                cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],  # OTSU
                cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(gray)  # CLAHE
            ]
            
            for img in methods:
                result = self.reader.readtext(img, detail=0, paragraph=False,
                                             allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ ')
                if result:
                    text = ' '.join(result).strip()
                    if self.is_valid_plate_text(text):
                        ocr_results.append(text)
            
            if ocr_results:
                best = max(ocr_results, key=len)
                return re.sub(r'[^A-Z0-9\s]', '', best.upper()).strip()
            
            return ""
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    def is_valid_plate_text(self, text):
        """Validate if text looks like a license plate"""
        if not text or len(text) < 4:
            return False
        
        text_clean = text.replace(' ', '')
        has_letter = any(c.isalpha() for c in text_clean)
        has_number = any(c.isdigit() for c in text_clean)
        
        if not (has_letter and has_number and 5 <= len(text_clean) <= 12):
            return False
        
        alnum_ratio = sum(c.isalnum() for c in text_clean) / len(text_clean)
        return alnum_ratio >= 0.8
    
    
    def process_image(self, image, save_result=False, output_path=None):
        if image is None:
            return []
        print(f"Processing image ({image.shape[1]}x{image.shape[0]})...")
        plate_candidates = self.detect_license_plates(image)
        print(f"Found {len(plate_candidates)} plate candidate(s) using YOLO")
        results = []
        for idx, plate_info in enumerate(plate_candidates):
            x1, y1, x2, y2 = plate_info['bbox']
            plate_img = image[y1:y2, x1:x2]
            license_text = self.extract_text_from_plate(plate_img)
            if license_text and self.is_valid_plate_text(license_text):
                print(f"  ✓ Plate {idx+1}: {license_text} (conf: {plate_info['confidence']:.2f})")
                results.append({
                    'plate_number': license_text,
                    'bbox': (x1, y1, x2, y2),
                    'confidence': plate_info['confidence']
                })
                if save_result:
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    cv2.putText(image, license_text, (x1, max(y1-10, 20)),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        if save_result and output_path:
            cv2.imwrite(output_path, image)
            print(f"✓ Saved to: {output_path}")
        unique_results = []
        seen = set()
        for r in results:
            if r['plate_number'] not in seen:
                seen.add(r['plate_number'])
                unique_results.append(r)
        return unique_results


def main():
    """Run ANPR system"""
    print("\n" + "="*70)
    print("YOLO11 Automatic Number Plate Recognition")
    print("="*70 + "\n")
    
    detector = LicensePlateDetector()
    test_folder = Path(__file__).parent / "test"
    
    if not test_folder.exists():
        test_folder.mkdir()
        print("Created test folder. Add images and run again.")
        return
    
    # Get test images
    image_files = [f for f in test_folder.glob("*.jpg") 
                  if not f.name.startswith('result_')]
    image_files += [f for f in test_folder.glob("*.png") 
                   if not f.name.startswith('result_')]
    
    if not image_files:
        print("No images found in test folder")
        return
    
    # Process each image
    for img_path in image_files:
        print(f"\n{'='*70}\nImage: {img_path.name}\n{'='*70}")
        
        image = detector.load_local_image(img_path)
        if image is None:
            continue
        
        output_path = str(test_folder / f"result_{img_path.name}")
        results = detector.process_image(image, save_result=True, output_path=output_path)
        
        if results:
            print(f"\n{'='*70}\n✓ DETECTED {len(results)} LICENSE PLATE(S)\n{'='*70}")
            for idx, r in enumerate(results, 1):
                print(f"  {idx}. {r['plate_number']}")
            print("="*70 + "\n")
        else:
            print("\n✗ No valid plates detected\n")


if __name__ == "__main__":
    main()
