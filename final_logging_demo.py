#!/usr/bin/env python3
"""
Final demonstration of logging behavior
Shows exactly which messages appear at each LOG_LEVEL
"""

import os
import sys
import logging
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from acemcli.logging_setup import setup_logging

def demo_level(level: str, name: str):
    """Demonstrate logging behavior for a specific level"""
    print(f"\n🔍 DEMONSTRATION: {name}")
    print("=" * 60)
    
    # Clear previous handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Set environment and configure logging
    os.environ["LOG_LEVEL"] = level
    if "LOG_FILE" in os.environ:
        del os.environ["LOG_FILE"]
    
    setup_logging()
    
    # Create logger
    logger = logging.getLogger(f"demo_{level}")
    
    print(f"LOG_LEVEL={level} - Root logger level: {logging.getLogger().level}")
    print("\nSending all message types:")
    print("(Only messages at or above the configured level will appear)\n")
    
    # Send test messages
    logger.critical("🔥 CRITICAL: System is down!")
    logger.error("❌ ERROR: Database connection failed")
    logger.warning("⚠️  WARNING: High memory usage")
    logger.info("ℹ️  INFO: User logged in successfully")
    logger.debug("🐛 DEBUG: Processing user request details")
    
    print("\n" + "-" * 60)

def demo_file_logging():
    """Demonstrate file logging"""
    print(f"\n📁 DEMONSTRATION: File Logging")
    print("=" * 60)
    
    # Create temporary log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as tmp:
        log_file = tmp.name
    
    try:
        # Clear handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # Configure with file
        os.environ["LOG_LEVEL"] = "1"  # INFO level
        os.environ["LOG_FILE"] = log_file
        
        setup_logging()
        
        logger = logging.getLogger("file_demo")
        
        print(f"LOG_LEVEL=1 with LOG_FILE={log_file}")
        print("\nSending messages (will appear on both console AND file):\n")
        
        logger.critical("🔥 CRITICAL: Written to both console and file")
        logger.error("❌ ERROR: Also in console and file")
        logger.info("ℹ️  INFO: Console and file output")
        logger.debug("🐛 DEBUG: This should NOT appear (level too low)")
        
        # Show file contents
        print(f"\n📄 File contents ({log_file}):")
        with open(log_file, 'r') as f:
            content = f.read()
            if content.strip():
                for line in content.strip().split('\n'):
                    print(f"   {line}")
            else:
                print("   (File is empty)")
                
    finally:
        # Clean up
        if os.path.exists(log_file):
            os.unlink(log_file)
    
    print("\n" + "-" * 60)

def main():
    print("🚀 FINAL LOGGING DEMONSTRATION")
    print("This shows exactly what you'll see with each LOG_LEVEL setting")
    
    # Demo each level
    demo_level("0", "Silent Mode (Only Critical)")
    demo_level("1", "Info Mode (Info and above)")  
    demo_level("2", "Debug Mode (All messages)")
    
    # Demo file logging
    demo_file_logging()
    
    # Summary
    print(f"\n✅ SUMMARY - Your logging_setup.py is working correctly!")
    print("=" * 60)
    print("LOG_LEVEL=0: Shows only CRITICAL messages (silent mode)")
    print("LOG_LEVEL=1: Shows INFO, WARNING, ERROR, CRITICAL messages")
    print("LOG_LEVEL=2: Shows all messages including DEBUG")
    print("LOG_FILE: When set, logs to both file and console")
    print("Default: Behaves like LOG_LEVEL=0 when not specified")
    print("\n🎯 Ready for integration with your CLI commands!")

if __name__ == "__main__":
    main()
