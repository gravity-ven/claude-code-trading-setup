import logging
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import io

# Configure logging
logger = logging.getLogger(__name__)

class YOLOInference:
    def __init__(self, model_path='yolov8n.pt'):
        """
        Initialize the YOLO model.
        Args:
            model_path (str): Path to the YOLO model file (default: 'yolov8n.pt').
        """
        try:
            logger.info(f"Loading YOLO model from {model_path}...")
            self.model = YOLO(model_path)
            logger.info("YOLO model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise

    def detect_objects(self, image_source, conf_threshold=0.25):
        """
        Detect objects in an image.
        Args:
            image_source (str, bytes, PIL.Image, or np.ndarray): The image to process.
            conf_threshold (float): Confidence threshold for detections.
        Returns:
            list: A list of dictionaries containing detection results.
        """
        try:
            # Perform inference
            results = self.model.predict(image_source, conf=conf_threshold)
            
            detections = []
            for result in results:
                # Process each detection
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]
                    
                    detections.append({
                        'box': [x1, y1, x2, y2],
                        'confidence': confidence,
                        'class_id': class_id,
                        'class_name': class_name
                    })
            
            return detections
        except Exception as e:
            logger.error(f"Error during object detection: {e}")
            return []

if __name__ == "__main__":
    # Simple test
    try:
        yolo = YOLOInference()
        print("Model initialized successfully.")
    except Exception as e:
        print(f"Initialization failed: {e}")
