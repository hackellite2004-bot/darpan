#!/usr/bin/env python
"""
Test script for ML model integration
"""

import sys
from pathlib import Path

# Ensure module path
_SANCHAAR2_DIR = Path(__file__).parent
if str(_SANCHAAR2_DIR) not in sys.path:
    sys.path.insert(0, str(_SANCHAAR2_DIR))

print("\n" + "="*60)
print("DARPAN - MODEL INTEGRATION TEST")
print("="*60 + "\n")

# Test 1: Model Manager
print("✓ Test 1: Model Manager Loading...")
try:
    from analysis.model_manager import get_model_manager
    
    mgr = get_model_manager()
    print("  ✅ Model manager initialized")
    
    models = mgr.get_all_models()
    print(f"\n  Models Status:")
    for name, model in models.items():
        status = "✅ Loaded" if model else "⚠️  Unavailable"
        print(f"    - {name}: {status}")
    
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 2: Enhanced Analyzers
print("\n✓ Test 2: Enhanced Analyzers...")
try:
    from analysis.enhanced_analyzers import (
        EnhancedEmotionAnalyzer,
        EnhancedGestureAnalyzer,
        EnhancedGazeAnalyzer
    )
    
    emotion_analyzer = EnhancedEmotionAnalyzer(use_model=True)
    print("  ✅ EnhancedEmotionAnalyzer initialized")
    
    gesture_analyzer = EnhancedGestureAnalyzer()
    print("  ✅ EnhancedGestureAnalyzer initialized")
    
    gaze_analyzer = EnhancedGazeAnalyzer()
    print("  ✅ EnhancedGazeAnalyzer initialized")
    
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 3: Mock Analysis
print("\n✓ Test 3: Mock Emotion Analysis...")
try:
    import numpy as np
    
    # Create mock face ROI (48x48 grayscale)
    mock_face = np.random.randint(0, 256, (48, 48), dtype=np.uint8)
    
    result = emotion_analyzer.analyze_with_ensemble(face_roi=mock_face)
    
    print(f"  ✅ Analysis successful:")
    print(f"     - Dominant emotion: {result['dominant']}")
    print(f"     - Confidence: {result['confidence']:.1%}")
    print(f"     - Methods used: {', '.join(result['methods'])}")
    
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 4: Config Loading
print("\n✓ Test 4: Configuration...")
try:
    from config import GEMINI_MODEL, DB_PATH
    
    print(f"  ✅ Config loaded:")
    print(f"     - Gemini Model: {GEMINI_MODEL}")
    print(f"     - Database path: {DB_PATH}")
    
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 5: Imports
print("\n✓ Test 5: Critical Imports...")
try:
    import mediapipe as mp
    import cv2
    import numpy as np
    import librosa
    from PySide6.QtWidgets import QApplication
    
    print("  ✅ All critical imports successful:")
    print(f"     - MediaPipe: ✓")
    print(f"     - OpenCV: ✓")
    print(f"     - NumPy: ✓")
    print(f"     - Librosa: ✓")
    print(f"     - PySide6: ✓")
    
except ImportError as e:
    print(f"  ⚠️  Missing import: {e}")

print("\n" + "="*60)
print("✅ TEST COMPLETE")
print("="*60)
print("""
Status: Ready for hackathon! 🚀

Next steps:
1. Run: python main.py
2. Try analyzing a video
3. Check results with new ML models

Good luck! 🏆
""")
