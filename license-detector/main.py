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

# Configuration
ESP32_IP = "http://192.168.5.32:81"



class LicensePlateDetector:
    """ANPR System using YOLO11 for vehicle detection and OCR for plate reading"""
    
    def __init__(self, plate_model_path=None):
        """Initialize detector with optional custom YOLO11 plate detection model"""
        print("Initializing ANPR System...")
        
        # Load custom plate detection model if provided
        if plate_model_path and Path(plate_model_path).exists():
            self.plate_model = YOLO(plate_model_path)
            self.use_plate_model = True
            print(f"✓ Loaded custom plate model: {plate_model_path}")
        else:
            self.plate_model = None
            self.use_plate_model = False
            print("Using traditional CV for plate detection")
        
        # Load YOLO11 for vehicle detection
        self.vehicle_model = YOLO('yolo11n.pt')
        
        # Initialize OCR
        self.reader = easyocr.Reader(['en'], gpu=False)
        print("✓ System ready\n")
    
    def fetch_esp32_image(self, esp32_url=ESP32_IP):
        """Fetch image from ESP32 camera"""
        try:
            response = requests.get(f"{esp32_url}/capture", timeout=5)
            if response.status_code == 200:
                img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
                return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"Error fetching from ESP32: {e}")
        return None
    
    def load_local_image(self, image_path):
        """Load image from local file"""
        return cv2.imread(str(image_path))
    
    def detect_vehicles(self, image):
        """Detect vehicles using YOLO11 (cars, trucks, buses)"""
        results = self.vehicle_model(image, conf=0.25, classes=[2, 5, 7], verbose=False)
        
        vehicles = []
        if len(results) > 0 and results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                vehicles.append({
                    'bbox': (x1, y1, x2, y2),
                    'confidence': float(box.conf[0])
                })
        return vehicles
    
    
    def detect_license_plates_with_yolo(self, image):
        """Detect plates using custom YOLO11 model"""
        if not self.use_plate_model:
            return []
        
        results = self.plate_model(image, conf=0.25, verbose=False)
        plates = []
        
        if len(results) > 0 and results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                plates.append({
                    'bbox': (x1, y1, x2, y2),
                    'confidence': float(box.conf[0])
                })
        return plates
    
    def detect_license_plates_traditional(self, image, vehicle_region=None):
        """Detect plates using traditional CV (fallback method)"""
        # Focus on vehicle region if provided
        if vehicle_region:
            x1, y1, x2, y2 = vehicle_region
            y1 = int(y1 + (y2 - y1) * 0.3)  # Lower 70% of vehicle
            search_img = image[y1:y2, x1:x2]
            offset_x, offset_y = x1, y1
        else:
            search_img = image.copy()
            offset_x, offset_y = 0, 0
        
        gray = cv2.cvtColor(search_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        
        candidates = []
        
        # Morphological blackhat
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 7))
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
        _, thresh = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5))
        dilated = cv2.dilate(thresh, kernel2, iterations=1)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h) if h > 0 else 0
            area = w * h
            
            if 2.0 <= aspect_ratio <= 6.0 and w > 80 and h > 20 and 2000 < area < 50000:
                x, y = max(0, x - 10), max(0, y - 10)
                w = min(search_img.shape[1] - x, w + 20)
                h = min(search_img.shape[0] - y, h + 20)
                
                candidates.append({
                    'bbox': (x + offset_x, y + offset_y, x + w + offset_x, y + h + offset_y),
                    'confidence': 0.0,
                    'score': area * aspect_ratio
                })
        
        # Edge detection
        edges = cv2.Canny(gray, 100, 200)
        kernel3 = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel3)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h) if h > 0 else 0
            area = w * h
            
            if 2.0 <= aspect_ratio <= 6.0 and w > 80 and h > 20 and 2000 < area < 50000:
                x, y = max(0, x - 10), max(0, y - 10)
                w = min(search_img.shape[1] - x, w + 20)
                h = min(search_img.shape[0] - y, h + 20)
                bbox = (x + offset_x, y + offset_y, x + w + offset_x, y + h + offset_y)
                
                # Check duplicates
                if not any(abs(bbox[0] - c['bbox'][0]) < 30 and abs(bbox[1] - c['bbox'][1]) < 30 
                          for c in candidates):
                    candidates.append({
                        'bbox': bbox,
                        'confidence': 0.0,
                        'score': area * aspect_ratio
                    })
        
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:5]
    
    
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
        """Main ANPR processing pipeline"""
        if image is None:
            return []
        
        print(f"Processing image ({image.shape[1]}x{image.shape[0]})...")
        
        # Detect vehicles
        vehicles = self.detect_vehicles(image)
        print(f"Found {len(vehicles)} vehicle(s)")
        
        # Detect license plates
        if self.use_plate_model:
            plate_candidates = self.detect_license_plates_with_yolo(image)
        else:
            plate_candidates = []
            if vehicles:
                for vehicle in vehicles:
                    plate_candidates.extend(
                        self.detect_license_plates_traditional(image, vehicle['bbox'])
                    )
            
            if not plate_candidates:
                plate_candidates = self.detect_license_plates_traditional(image)
        
        print(f"Found {len(plate_candidates)} plate candidate(s)")
        
        # Extract text from plates
        results = []
        for idx, plate_info in enumerate(plate_candidates):
            x1, y1, x2, y2 = plate_info['bbox']
            plate_img = image[y1:y2, x1:x2]
            license_text = self.extract_text_from_plate(plate_img)
            
            if license_text and self.is_valid_plate_text(license_text):
                print(f"  ✓ Plate {idx+1}: {license_text}")
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
        
        # Remove duplicates
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
