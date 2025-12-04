import sys
import os
import logging
from PIL import Image
import numpy as np

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from yolo_inference import YOLOInference
except ImportError:
    print("Could not import YOLOInference. Make sure you are in the correct directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_dummy_image():
    """Create a dummy image for testing."""
    # Create a 640x640 black image
    img = Image.new('RGB', (640, 640), color='black')
    return img

def test_yolo():
    print("Initializing YOLO model...")
    try:
        yolo = YOLOInference()
        print("Model initialized.")
    except Exception as e:
        print(f"Failed to initialize model: {e}")
        return

    print("Running inference on dummy image...")
    try:
        img = create_dummy_image()
        detections = yolo.detect_objects(img)
        print(f"Detections: {detections}")
        print("Inference successful.")
    except Exception as e:
        print(f"Inference failed: {e}")

if __name__ == "__main__":
    test_yolo()
