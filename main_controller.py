import sys
import logging
from dotenv import load_dotenv
from backend.detection.vision_node import AdamsVisionPipeline

# Load API keys from .env before anything else starts
load_dotenv()

# Setup high-level logging for the controller
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ADAMS-Main")

def start_system():
    print("=" * 55)
    print("   ADAMS — Advanced Driver Alertness Monitoring System")
    print("=" * 55)
    
    pipeline = None
    
    try:
        logger.info("Initializing subsystems...")
        pipeline = AdamsVisionPipeline()
        
        logger.info("Starting Vision Node...")
        pipeline.run()
        
    except KeyboardInterrupt:
        print("\n" + "-" * 55)
        logger.info("Manual shutdown initiated by user.")
        
    except Exception as e:
        logger.error(f"A critical error occurred: {e}")
        
    finally:
        print("-" * 55)
        logger.info("ADAMS is shutting down safely. Goodbye!")
        # Add any global cleanup here (like closing open log files)

if __name__ == "__main__":
    start_system()