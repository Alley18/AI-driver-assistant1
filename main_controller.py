# main_controller.py
# Entry point for ADAMS — run this file to start the full system
# Make sure all files are in the SAME folder before running.

from backend.detection.vision_node import AdamsVisionPipeline

if __name__ == "__main__":
    print("=" * 50)
    print("  ADAMS — Advanced Driver Alertness Monitor")
    print("=" * 50)
    pipeline = AdamsVisionPipeline()
    pipeline.run()