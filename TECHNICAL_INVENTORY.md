# Sanchar 2.0: Comprehensive Technical Inventory
## Complete Analysis of Techniques, Algorithms, Heuristics, and ML Models

**Date**: April 13, 2026  
**Codebase Version**: Sanchar 2.0 (sanchaar2/)

---

## TABLE OF CONTENTS
1. [Face Analysis](#face-analysis)
2. [Emotion Analysis](#emotion-analysis)
3. [Eye Analysis](#eye-analysis)
4. [Gaze Analysis](#gaze-analysis)
5. [Posture Analysis](#posture-analysis)
6. [Gesture Analysis](#gesture-analysis)
7. [Speech Analysis](#speech-analysis)
8. [Voice Analysis](#voice-analysis)
9. [Video Processing](#video-processing)
10. [Model Integration & Scoring](#model-integration--scoring)

---

## 1. FACE ANALYSIS

### **Face Detection & Landmark Extraction**

**Pre-trained Model**: MediaPipe Face Mesh  
**Model Details**:
- Detects up to 478 face landmarks with sub-millimeter accuracy
- Lightweight, runs on CPU efficiently
- Outputs 3D coordinates (x, y, z) in normalized space [0, 1]
- Configuration: `refine_landmarks=True`, `max_num_faces=1`

**Face Landmarks Used** (File: `emotion_analyzer.py`):
```
Landmark 0    : Nose tip
Landmark 6    : Upper nose
Landmark 13   : Top lip
Landmark 14   : Bottom lip
Landmark 33   : Left eye outer corner
Landmark 70   : Left eyebrow
Landmark 133  : Left eye inner corner
Landmark 145  : Left eye lower
Landmark 153  : Left eye lower (inner)
Landmark 159  : Left eye upper
Landmark 160  : Left eye upper (inner)
Landmark 168  : Center eyebrow
Landmark 205  : Left cheek
Landmark 263  : Right eye outer corner
Landmark 291  : Right mouth corner
Landmark 300  : Right eyebrow
Landmark 362  : Right eye inner corner
Landmark 374  : Right eye lower
Landmark 380  : Right eye lower (inner)
Landmark 386  : Right eye upper
Landmark 387  : Right eye upper (inner)
Landmark 425  : Right cheek
Landmark 468  : Left iris center
Landmark 473  : Right iris center
```

**Features Extracted**:
1. **Lip Opening**: `bottom_lip.y - top_lip.y` (vertical distance in normalized coordinates)
2. **Mouth Width**: Distance between left and right mouth corners (Euclidean)
3. **Eye Width**: Distance between left and right eyes
4. **Brow Height**: Distance between eyebrows and eye midline
5. **Cheek Raise**: Distance between eye level and cheek level
6. **Lip Corner Pull Ratio**: `mouth_width / eye_width` (indicators of smile/tension)
7. **Brow Depression**: Downward displacement of brows from resting position
8. **Eye Openness**: Distance from nose to eye midline
9. **Mouth Corner Drop**: Downward displacement of mouth corners
10. **Inner Brow Raise**: Inner brow height relative to eye level
11. **Mouth Tension**: `max(0, 1.02 - lip_corner_pull)` (inverted normalization)

**Algorithm**: Feature-based geometric analysis using inter-landmark distances and ratios

---

## 2. EMOTION ANALYSIS

### **Emotion Detection Engine**

**File**: `analysis/emotion_analyzer.py`  
**Emotions Detected**: Happy, Neutral, Sad, Anxious, Surprised, Angry (6 classes)

### **Emotion Scoring Formula**

Each emotion is computed as a clipped [0, 1] score using weighted combinations:

#### **Happy Score**
```python
happy = clip((cheek_raise * 8.0) + max(0, lip_corner_pull - 1.15) * 1.7)
```
**Triggers**:
- Cheek raising (Duchenne marker): coefficient 8.0
- Lip corner elevation above 1.15 ratio: coefficient 1.7

#### **Sad Score**
```python
sad = clip(
    (brow_inner_raise * 6.0) +     # Inner brow rises
    (corner_drop * 9.0) +           # Mouth corners drop
    (mouth_tension * 2.0)           # Lips tense
)
```
**Triggers**:
- Inner brow raise: coefficient 6.0
- Mouth corner drop: coefficient 9.0
- Mouth tension: coefficient 2.0

#### **Anxious Score**
```python
anxious = clip((eye_open * 8.0) + (brow_height * 2.5))
```
**Triggers**:
- Wide eyes (eye_open > threshold): coefficient 8.0
- High brows (brow_height > threshold): coefficient 2.5

#### **Surprised Score**
```python
surprised = clip((lip_open * 9.0) + (brow_height * 3.2))
```
**Triggers**:
- Open mouth (lip_open > threshold): coefficient 9.0
- Raised brows: coefficient 3.2

#### **Angry Score**
```python
angry = clip((brow_low * 6.0) + max(0, 1.1 - lip_corner_pull) * 1.2)
```
**Triggers**:
- Lowered/furrowed brows (brow_low > 0): coefficient 6.0
- Lip corners pulled down (lip_corner_pull < 1.1): coefficient 1.2

#### **Neutral Score**
```python
neutral = clip(1.0 - max(happy, sad, anxious, surprised, angry) * 0.92)
```
**Logic**: Neutral is 1 minus the maximum emotion scaled by 0.92 (allowing for stable neutral even with minor expressions)

**Clipping Function**: `clip01(value) = np.clip(value, 0.0, 1.0)`

**Dominant Emotion**: Emotion with highest score; ties broken by max() function

**Output Format** (`EmotionResult` dataclass):
```python
{
    'happy': float [0, 1],
    'neutral': float [0, 1],
    'sad': float [0, 1],
    'anxious': float [0, 1],
    'surprised': float [0, 1],
    'angry': float [0, 1],
    'dominant': str (emotion name)
}
```

---

## 3. EYE ANALYSIS

### **Blink Detection**

**File**: `analysis/eye_gaze_analyzer.py`  
**Algorithm**: Eye Aspect Ratio (EAR)

#### **EAR Calculation**
```python
def eye_aspect_ratio(landmarks, indices:(p1,p2,p3,p4,p5,p6)) -> float:
    vertical_1 = ||p2 - p6||  # Distance between eyelid points
    vertical_2 = ||p3 - p5||  # Distance between eyelid points
    horizontal = ||p1 - p4||  # Distance between eye corners
    
    return (vertical_1 + vertical_2) / (2 * horizontal)
```

**Landmarks Used**:
- **Left Eye**: `(33, 160, 158, 133, 153, 144)`
  - 33: Left eye outer corner
  - 160: Left upper-middle
  - 158: Left upper-inner
  - 133: Left eye inner corner
  - 153: Left lower-inner
  - 144: Left lower-middle

- **Right Eye**: `(362, 385, 387, 263, 373, 380)`
  - 362: Right eye inner corner
  - 385: Right upper-middle
  - 387: Right upper-inner
  - 263: Right eye outer corner
  - 373: Right lower-inner
  - 380: Right lower-middle

#### **Blink Detection Threshold**
- **BLINK_EAR_THRESHOLD**: 0.20 (config.py)
- **Blink Trigger**: EAR < 0.20

#### **Blink Event Detection Strategy**
```
State Machine:
- _blink_frames: Counter for consecutive frames below threshold
- _blink_active: State flag

Logic:
- If EAR < 0.20: increment _blink_frames
- If EAR >= 0.20: reset _blink_frames to 0
- If _blink_frames >= 2 AND NOT _blink_active:
    - Fire BLINK_EVENT = True
    - Set _blink_active = True
- If NOT blink_now: reset _blink_active = False
```

**Blink Validation**: Requires 2+ consecutive frames of low EAR to prevent false positives

**Output**:
```python
{
    'ear': float (average of left + right EAR),
    'blink': bool (true if blink event detected this frame)
}
```

---

## 4. GAZE ANALYSIS

### **Gaze Direction Estimation**

**Algorithm**: Normalized iris position within eye bounds

#### **Iris Position Calculation**
```
Normalize iris X position:
left_x = (left_iris.x - left_corner_outer.x) / (left_corner_inner.x - left_corner_outer.x)
right_x = (right_iris.x - right_corner_inner.x) / (right_corner_outer.x - right_corner_inner.x)
center_x = (left_x + right_x) / 2.0

Normalize iris Y position:
left_y = (left_iris.y - left_upper.y) / |left_lower.y - left_upper.y|
right_y = (right_iris.y - right_upper.y) / |right_lower.y - right_upper.y|
center_y = (left_y + right_y) / 2.0
```

**Iris Deviation from Center**:
```
offset_x = center_x - 0.5
offset_y = center_y - 0.5
```

### **Gaze Zones** (5-point classification)

**Configuration**: `GAZE_CENTER_THRESHOLD = 0.20` (config.py)

**Classification Logic**:
```
if |offset_x| ≤ 0.20 AND |offset_y| ≤ 0.20:
    gaze = "center"
elif offset_x < -0.20:
    gaze = "left"
elif offset_x > 0.20:
    gaze = "right"
elif offset_y > 0.20:
    gaze = "down"
else:
    gaze = "center" (fallback)
```

**Gaze Zones**:
- **"center"**: Looking at camera/audience (±0.20 from center)
- **"left"**: Looking left (offset_x < -0.20)
- **"right"**: Looking right (offset_x > 0.20)
- **"down"**: Looking down (offset_y > 0.20)
- **"away"**: Not detected/no face landmarks

**Iris Landmarks**:
- Left iris: landmark 468
- Right iris: landmark 473

---

## 5. POSTURE ANALYSIS

### **Posture Scoring System**

**File**: `analysis/pose_analyzer.py`  
**Pre-trained Model**: MediaPipe Pose  
**Model Config**: `model_complexity=1` (lite version for speed)

**Body Landmarks Used**:
- Landmark 0: Nose
- Landmark 7: Left ear
- Landmark 8: Right ear
- Landmark 11: Left shoulder
- Landmark 12: Right shoulder

### **Posture Components**

#### **1. Slouching Detection**
```
shoulder_y = (left_shoulder.y + right_shoulder.y) / 2.0
SLOUCH_Y_THRESHOLD = 0.60 (config.py)
slouching = shoulder_y > 0.60
```
**Interpretation**: Shoulders below y=0.60 (in normalized coords) indicate slouching

#### **2. Forward Head Posture**
```
shoulder_z = (left_shoulder.z + right_shoulder.z) / 2.0
head_forward = (nose.z - shoulder_z) < -0.08
```
**Interpretation**: Nose forward of shoulders by > 0.08 units indicates forward head posture

#### **3. Shoulder Level**
```
shoulder_level = |left_shoulder.y - right_shoulder.y| ≤ 0.05
```
**Interpretation**: Shoulders at similar height (±0.05) indicates balanced posture

#### **4. Head Tilt**
```
ear_line_delta = |left_ear.y - right_ear.y|
head_tilt = ear_line_delta > 0.03
```
**Interpretation**: Ears at different heights (> 0.03) indicates head tilt

### **Posture Scoring Formula**
```python
posture_score = 1.0
posture_score -= 0.40 if slouching else 0.0       # -40 pts
posture_score -= 0.22 if head_forward else 0.0    # -22 pts
posture_score -= 0.18 if not shoulder_level else 0.0  # -18 pts
posture_score -= 0.12 if head_tilt else 0.0       # -12 pts
posture_score = clip(posture_score, 0.0, 1.0)
```

**Weighting Priority**: Slouching > Forward Head > Shoulder Level > Head Tilt

**Output**:
```python
{
    'posture_good': bool (score >= 0.7),
    'slouching': bool,
    'head_forward': bool,
    'shoulder_level': bool,
    'posture_score': float [0, 1]
}
```

---

## 6. GESTURE ANALYSIS

### **Hand Detection & Classification**

**File**: `analysis/gesture_analyzer.py`  
**Pre-trained Model**: MediaPipe Hands  
**Model Config**: `max_num_hands=2`, `min_detection_confidence=0.5`

### **Hand Landmarks** (21 per hand)
```
Fingertip indices: [4, 8, 12, 16, 20]
- 4: Thumb tip
- 8: Index tip
- 12: Middle tip
- 16: Ring tip
- 20: Pinky tip

Wrist: landmark 0
```

### **Gesture Features**

#### **1. Tip Spread (Hand Openness)**
```python
def tip_spread(landmarks) -> float:
    fingertips = [landmarks[i] for i in [4, 8, 12, 16, 20]]
    distances = []
    for i in range(len(fingertips)-1):
        for j in range(i+1, len(fingertips)):
            distances.append(||fingertips[i] - fingertips[j]||)
    return mean(distances)
```
**Purpose**: Measures how spread apart fingertips are (open hand vs closed)

#### **2. Palm Open Ratio**
```python
def palm_open_ratio(landmarks) -> float:
    wrist = landmarks[0]
    middle_tip = landmarks[12]
    index_tip = landmarks[8]
    pinky_tip = landmarks[20]
    
    palm_span = ||index_tip - pinky_tip||
    wrist_to_middle = ||wrist - middle_tip||
    
    return wrist_to_middle / palm_span
```
**Purpose**: Ratio of hand height to width (open hand has ratio > 1.0)

#### **3. Hand Hidden Detection**
```
_hidden_streak = counter for frames without hand detection
if no hands detected:
    _hidden_streak += 1
    if _hidden_streak >= 10:
        gesture_type = "hidden"
        _nervous_frames += 1
```
**Purpose**: Detect when hands are hidden (nervous behavior indicator)

### **Gesture Classification**

**Thresholds**:
- `spread_score > 0.11`: Indicates open fingertips
- `open_score > 1.0`: Indicates open palm
- `spread_score < 0.045`: Indicates closed/tense hand
- `open_score < 0.78`: Indicates collapsed hand

**Classification Logic**:
```python
if spread_score > 0.11 AND open_score > 1.0:
    gesture_type = "expressive"  # Open hand gestures
elif spread_score < 0.045 OR open_score < 0.78:
    gesture_type = "nervous"     # Closed/defensive gestures
else:
    gesture_type = "neutral"     # Neutral hand position
```

### **Gesture Tracking**
```
_positive_frames: Count of "expressive" or "neutral" gestures (0.4x weight for neutral)
_nervous_frames: Count of "nervous" or "hidden" gestures
_total_frames: Total frames processed

positive_pct = (_positive_frames / _total_frames) * 100
nervous_pct = (_nervous_frames / _total_frames) * 100
```

### **Gesture Confidence**
```python
confidence = clip(spread_score * 5.0 + open_score * 0.5, 0.0, 1.0)
```

**Output**:
```python
{
    'gesture_type': str ("expressive" | "neutral" | "nervous" | "hidden"),
    'confidence': float [0, 1],
    'positive_pct': float (percentage of positive gesture frames),
    'nervous_pct': float (percentage of nervous gesture frames)
}
```

---

## 7. SPEECH ANALYSIS

### **Speech-to-Text & Metrics**

**File**: `analysis/speech_analyzer.py`  
**ASR Model**: OpenAI Whisper  
**Model Size**: `"base"` (config: `WHISPER_MODEL_SIZE`)
**Model Params**: ~140M parameters
**Language Support**: Multilingual (auto-detected)

**Preprocessing**:
- Dependency check: ffmpeg required for audio processing
- Input: Audio file path (supports most audio formats via ffmpeg)

### **Transcription Output**
```python
result = whisper.transcribe(audio_path, word_timestamps=True)
{
    'text': str (full transcript),
    'duration': float (seconds),
    'segments': [
        {
            'text': str,
            'start': float (segment start time),
            'end': float (segment end time),
            'words': [
                {
                    'word': str,
                    'start': float,
                    'end': float
                },
                ...
            ]
        },
        ...
    ]
}
```

### **WPM Calculation**
```
word_count = number of regex matches for \b\w+\b (word boundaries)
duration = max(last_word_end_time, 0.01) or result.duration
wpm = (word_count / duration) * 60
```

**Config Range**: `IDEAL_WPM_MIN = 110`, `IDEAL_WPM_MAX = 150`

### **Filler Word Detection**

**Predefined Filler List** (14 fillers):
```python
FILLERS = [
    "umm", "um", "uh",
    "like", "basically", "you know", "sort of", "kind of",
    "right", "okay so", "so yeah",
    "actually", "literally", "honestly"
]
```

**Detection Algorithm**:
```
For each filler:
    pattern = r"\b" + filler + r"\b"  # Word boundaries
    count = len(re.findall(pattern, transcript.lower()))
    
Result: dict[filler] = count (only non-zero counts included)
```

**Statistics**:
- `total_fillers = sum(filler_counts.values())`

### **Pause Detection**

**Long Pause Threshold**: `LONG_PAUSE_THRESHOLD = 2.0` seconds

**Algorithm**:
```
For each adjacent word pair (i, i+1):
    gap = word[i+1].start - word[i].end
    if gap > 2.0:
        record as pause: {'at': word[i].end, 'duration': gap}
        
pause_count = number of detected pauses
```

**Pause Characteristics**:
- Captures unplanned silence (hesitations, thinking pauses)
- Excludes natural punctuation pauses (typically < 2.0s)

### **Speech Analysis Output**
```python
{
    'transcript': str,
    'word_count': int,
    'duration': float (seconds),
    'wpm': float,
    'filler_words': dict[str, int],
    'total_fillers': int,
    'long_pauses': list[{'at': float, 'duration': float}],
    'wpm_ideal': bool (within 110-150),
    'pause_count': int
}
```

---

## 8. VOICE ANALYSIS

### **Vocal Characteristics Analysis**

**File**: `analysis/voice_tone_analyzer.py`  
**Libraries**: librosa (for audio analysis)

**Audio Loading**:
```
y, sr = librosa.load(audio_path, sr=None, mono=True)
```

### **Pitch Analysis**

#### **Fundamental Frequency (F0) Estimation**
```python
f0, voiced_flag, voiced_probs = librosa.pyin(
    y, 
    fmin=80,     # Minimum frequency (Hz)
    fmax=400,    # Maximum frequency (Hz)
)
```

**Algorithm**: PYIN (Probabilistic YIN)
- Tracks fundamental frequency over time
- Returns confidence scores for voicing

**Voiced Value Extraction**:
```
voiced_values = f0[voiced_flag]  # Select voiced frames
Remove NaN values
```

#### **Pitch Statistics**
```
pitch_mean = mean(voiced_values)      # Average fundamental frequency
pitch_variation = std(voiced_values)   # Standard deviation (Hz)
```

### **Energy Analysis**

#### **Root Mean Square (RMS)**
```python
rms = librosa.feature.rms(y=y)[0]
```

**RMS Properties**:
- Hop length: Default (typically 512 samples)
- Frame-based energy measurement
- Normalized to [0, 1]

#### **Energy Statistics**
```
energy_mean = mean(rms)           # Average energy level
energy_variation = std(rms)       # Variability in energy
```

### **Voice Quality Classification**

#### **Monotone Detection**
```
MONOTONE_THRESHOLD = 15.0  (Hz, config.py)
is_monotone = pitch_variation < 15.0
```
**Interpretation**: Pitch std dev < 15 Hz indicates monotone voice (flat, no variation)

#### **Loudness Classification**
```
is_too_quiet = energy_mean < 0.02
is_too_loud = energy_mean > 0.15
```

#### **Pitch Variation Rate** (Zero-Crossing Rate)
```python
chunk_size = max(sr, 1)  # chunks of ~1 second
For each 1-second chunk:
    zero_crossing_count = count of sign changes in waveform
    chunk_rates.append(zero_crossing_count)
    
rate_variation = std(chunk_rates)
```
**Purpose**: Measures speech articulation clarity

### **Voice Score Calculation**
```python
voice_score = 1.0
if is_monotone:
    voice_score -= 0.3          # -30 pts
if is_too_quiet OR is_too_loud:
    voice_score -= 0.2          # -20 pts
voice_score -= min(0.2, rate_variation / 250.0)  # Up to -20 pts
voice_score = clip(voice_score, 0.0, 1.0)
```

**Scoring Rationale**:
- Monotone is most critical (-30%)
- Loudness extremes secondary (-20%)
- Articulation variation supports overall quality (up to -20%)

### **Voice Analysis Output**
```python
{
    'pitch_mean': float (Hz),
    'pitch_variation': float (Hz std dev),
    'energy_mean': float [0, 1],
    'energy_variation': float [0, 1],
    'is_monotone': bool,
    'is_too_quiet': bool,
    'is_too_loud': bool,
    'voice_score': float [0, 1]
}
```

### **Spectral Analysis** (Visualization)

**File**: `analysis/voice_spectral_analyzer.py`

#### **Spectrogram**
```python
from scipy.signal import spectrogram
f, t, Sxx = spectrogram(
    audio_data,
    fs=sr,
    window='hann',
    nperseg=2048,      # ~46ms window at 44.1kHz
    noverlap=1024      # 50% overlap
)
```
**Visualization**: Mel-scale spectrogram (frequency vs time heatmap)

#### **Chromagram (Pitch Class Distribution)**
```python
chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
```
**Output**: 12 × T matrix (12 chromatic notes vs time)
**Notes**: C, C#, D, D#, E, F, F#, G, G#, A, A#, B

#### **Pitch Contour**
```python
pitches, magnitudes = librosa.piptrack(
    y=y, sr=sr,
    fmin=librosa.midi_to_hz(36),  # C1
    fmax=fmin * 24,
    threshold=0.1
)
times, frequencies = track_maximum_magnitude_pitch(pitches, magnitudes)
```
**Purpose**: Visualize fundamental frequency trajectory

---

## 9. VIDEO PROCESSING

### **Frame Sampling Strategy**

**File**: `analysis/session_video_analyzer.py`

#### **Target Frame Rate**
```
Default: target_fps = 8.0 (frames per second for analysis)
```

**Sampling Calculation**:
```
video_fps = capture.get(cv2.CAP_PROP_FPS)  # Actual video FPS
total_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
duration = total_frames / video_fps

sample_every = max(1, round(video_fps / target_fps))
```

**Purpose**: Reduce computational load while preserving temporal information  
**Example**: 30 FPS video → 8 FPS sampling = process every 4th frame (30/8=3.75≈4)

### **Temporal Smoothing**

#### **Emotion Smoothing**
```
emotion_window = deque(maxlen=5)  # Last 5 sampled frames
For each frame:
    emotion_window.append(current_emotion)
    smoothed_emotion = mean(emotion_window) per emotion type
```
**Purpose**: Reduce jitter in frame-to-frame emotion changes

#### **Posture Smoothing**
```
posture_window = deque(maxlen=5)
For each frame:
    posture_window.append(current_posture_score)
    smoothed_posture = mean(posture_window)
```

### **Session Aggregation Algorithm**

**Counters & Collectors**:
```
gaze_counts: Counter (center, left, right, down, away)
gesture_counts: Counter (expressive, neutral, nervous, hidden)
emotion_history: list of smoothed emotion dicts
posture_scores: list of smoothed posture values
blink_count: integer accumulator
slouch_frames: integer accumulator
frame_scores: list of (timestamp, score) tuples
```

### **Frame-Level Scoring**

Each frame receives a composite score:
```
eye_center_component = 100.0 if gaze == "center" else 0.0
emotion_component = (happy + neutral * 0.7) * 100
posture_component = posture_score * 100
gesture_component = 
    100.0 if gesture == "expressive"
    55.0 if gesture == "neutral"
    30.0 if gesture == "nervous"

frame_score = clip(
    eye_center * 0.35 +      # 35% weight
    emotion * 0.25 +          # 25% weight
    posture * 0.25 +          # 25% weight
    gesture * 0.15,           # 15% weight
    0.0, 100.0
)

timestamp = frame_index / fps
frame_scores.append((round(timestamp, 2), round(frame_score, 2)))
```

### **Session-Level Aggregation**

#### **Emotion Averaging**
```
emotion_avg = {
    'happy': mean([e['happy'] for e in emotion_history]),
    'neutral': mean([e['neutral'] for e in emotion_history]),
    'sad': mean([e['sad'] for e in emotion_history]),
    'anxious': mean([e['anxious'] for e in emotion_history]),
    'surprised': mean([e['surprised'] for e in emotion_history])
}
dominant_emotion = argmax(emotion_avg)
```

#### **Gaze Statistics**
```
analyzed_frames = sum(gaze_counts.values())
center_pct = (gaze_counts['center'] / analyzed_frames) * 100
away_pct = (gaze_counts['away'] / analyzed_frames) * 100
```

#### **Gesture Statistics**
```
gesture_positive_pct = (
    (gaze_counts['expressive'] + gaze_counts['neutral'] * 0.4)
    / analyzed_frames
) * 100

gesture_nervous_pct = (
    (gaze_counts['nervous'] + gaze_counts['hidden'])
    / analyzed_frames
) * 100
```

#### **Frame Score Statistics**
```
frame_values = [score for _, score in frame_scores]
frame_mean = mean(frame_values)
frame_min = min(frame_values)
frame_max = max(frame_values)
frame_std = std(frame_values)
frame_stability = (count(|value - mean| ≤ 12) / len(values)) * 100
```

**Frame Stability Threshold**: ±12 points from mean

---

## 10. MODEL INTEGRATION & SCORING

### **Pre-trained Models Summary**

| Model | Purpose | Library | Config | Input |
|-------|---------|---------|--------|-------|
| MediaPipe Face Mesh | 478 face landmarks | mediapipe | refine_landmarks=True | RGB frame |
| MediaPipe Pose | 33 body landmarks | mediapipe | complexity=1 | RGB frame |
| MediaPipe Hands | 21 hand landmarks × 2 | mediapipe | confidence=0.5 | RGB frame |
| OpenAI Whisper | Speech-to-text | openai-whisper | "base" model | Audio file |
| librosa PYIN | Fundamental frequency | librosa | fmin=80, fmax=400 | Audio array |
| Google Gemini 1.5 Flash | AI coaching/feedback | google-generativeai | Temperature=0.7-1.0 | Metrics + images |

### **Confidence Scoring System**

**File**: `analysis/score_engine.py`

#### **Component Scores** (6 dimensions)

1. **Eye Score** (0-100):
   ```
   eye_score = eye_center_pct [0, 100]
   ```

2. **Emotion Score** (0-100):
   ```
   calmness = max(0, 1 - max(anxious, surprised) * 0.9)
   emotion_score = (
       neutral * 0.50 +     # 50% weight
       happy * 0.15 +       # 15% weight
       sad * 0.20 +         # 20% weight
       calmness * 0.15      # 15% weight
   ) * 100
   ```

3. **Posture Score** (0-100):
   ```
   posture_score = posture_score * 100
   ```

4. **Gesture Score** (0-100):
   ```
   gesture_score = gesture_positive_pct
   ```

5. **Speech Score** (0-100):
   ```
   wpm_score = 
       100 if 110 ≤ wpm ≤ 150
       else max(0, 100 - |wpm - 130| * 1.5)
       
   filler_score = max(0, 100 - filler_count * 5.0)
   pause_score = max(0, 100 - pause_count * 10.0)
   
   speech_score = (wpm_score + filler_score + pause_score) / 3
   ```

6. **Voice Score** (0-100):
   ```
   voice_score = voice_score * 100
   ```

#### **Quality Score** (Reliability Indicator)
```python
quality_score = clip(
    eye * 0.18 +
    emotion * 0.16 +
    posture * 0.22 +
    gesture * 0.14 +
    speech * 0.18 +
    voice * 0.12,
    0, 100
)
```

#### **Overall Confidence Score**

**Weight Configuration** (config.py):
```python
WEIGHT_EYE_CONTACT = 0.25
WEIGHT_EMOTION = 0.20
WEIGHT_POSTURE = 0.15
WEIGHT_GESTURE = 0.15
WEIGHT_SPEECH = 0.15
WEIGHT_VOICE = 0.10
```

**Calculation**:
```python
score = (
    eye_score * 0.25 +
    emotion_score * 0.20 +
    posture_score * 0.15 +
    gesture_score * 0.15 +
    speech_score * 0.15 +
    voice_score * 0.10
)
```

#### **Grade Assignment**
```
if score >= 85: grade = "A"
elif score >= 70: grade = "B"
elif score >= 55: grade = "C"
else: grade = "D"
```

#### **Confidence Classification**
```
if score < 55 OR quality_score < 45:
    label = "uncertain"
elif score >= 80 AND quality_score >= 70:
    label = "confident"
else:
    label = "moderate"
```

### **Analysis Profile & Signal Quality**

**File**: `analysis/analysis_strategy.py`

#### **Frame Stability Metrics**
```
frame_mean, frame_std, frame_min, frame_max = aggregate from frame_scores
frame_range = frame_max - frame_min
steady_frames = count(|value - mean| ≤ 12)
frame_stability = (steady_frames / total_frames) * 100

temporal_confidence = clip(
    100 - (frame_std * 1.6) - (frame_range * 0.35),
    0, 100
)
```

#### **Component Fit Scores** (Normalized)

**Speech Fit**:
```
wpm_mid = (lower_wpm + upper_wpm) / 2
wpm_distance = |wpm - wpm_mid|
speech_fit = clip(
    100 - wpm_distance * 1.3 - filler_count * 2.2 - pause_count * 4.0,
    0, 100
)
```

**Vision Fit**:
```
vision_fit = clip(
    eye_center * 0.38 +
    posture * 0.24 +
    (100 - slouch) * 0.18 +
    gesture_positive * 0.10 -
    gesture_nervous * 0.12,
    0, 100
)
```

**Vocal Fit**:
```
vocal_fit = clip(
    voice_score * 0.7 +
    (100 - min(100, pitch_variation * 120)) * 0.3,
    0, 100
)
```

**Emotion Balance**:
```
emotion_balance = clip(
    100 - (
        anxiety * 55 +           # 55% penalty
        surprise * 35            # 35% penalty
    ),
    0, 100
)
```

#### **Overall Signal Quality (Reliability)**
```python
reliability = clip(
    frame_stability * 0.22 +          # 22% weight
    temporal_confidence * 0.18 +      # 18% weight
    vision_fit * 0.24 +               # 24% weight
    speech_fit * 0.18 +               # 18% weight
    vocal_fit * 0.10 +                # 10% weight
    emotion_balance * 0.08,           # 8% weight
    0, 100
)
```

#### **Analysis Mode Classification**
```
if reliability >= 75 AND frame_stability >= 65:
    analysis_mode = "high-confidence"
elif reliability >= 50:
    analysis_mode = "guarded"
else:
    analysis_mode = "uncertain"
```

#### **Pattern Detection**
```
if gesture_nervous > 35 OR slouch > 40 OR eye_center < 40:
    dominant_pattern = "needs_attention"
elif emotion_dominant in {happy, neutral} AND reliability >= 60:
    dominant_pattern = "balanced"
else:
    dominant_pattern = "steady"
```

### **AI Coaching Integration**

**File**: `ai/coaching.py`  
**LLM Model**: Google Gemini 1.5 Flash

#### **Coaching Contexts** (Randomly Selected):
```
1. "presentation in a classroom"
2. "answering a job interview question"
3. "speaking up in a team meeting"
4. "introducing yourself to a new person"
5. "explaining an idea to a parent or teacher"
```

#### **Interview Question Generation** (Scenario-based)
```
Scenario Map:
1. Opening self-introduction
2. Handling pressure or deadlines
3. Working with a teammate or classmate
4. Solving a conflict or disagreement
5. Showing motivation or future goals
```

#### **Coaching Tips Generation**
**Inputs**: User name, age group, session metrics  
**Output**: 4 personalized tips as JSON array  
**Gemini Config**:
```
temperature=0.9 (creative variation)
top_p=0.95
top_k=40
max_output_tokens=500
```

#### **Face Impression Analysis** (Image-based)
**Inputs**: Face frame (optional), session metrics  
**Gemini Config**:
```
temperature=0.7
top_p=0.9
top_k=32
max_output_tokens=220
```
**Output**:
```json
{
    "summary": "1 short sentence",
    "confidence": float [0, 1],
    "what_it_says": "Real-life interpretation",
    "real_life_example": "Practical context"
}
```

#### **Session Assessment** (Comprehensive)
**Inputs**: All metrics, face frames (3 max), transcript, analysis profile  
**Purpose**: Final verdict on session quality and confidence level

### **Fallback Mechanisms**

All AI functions have fallback implementations:
1. **Coaching tips** → Pre-written general tips
2. **Interview questions** → Template questions
3. **Face impression** → Metric-based description
4. **Session assessment** → Heuristic-only evaluation

**Trigger**: If Gemini API unavailable or fails

---

## TECHNICAL ARCHITECTURE SUMMARY

### **Data Flow**
```
Video + Audio Input
    ↓
Frame-by-frame Analysis
    ├─ Emotion (Face Mesh → 11 landmarks → 6 emotions)
    ├─ Eye Contact (Face Mesh + iris → 4 gaze zones)
    ├─ Blinks (Eye landmarks → EAR → blink detection)
    ├─ Posture (Pose → 5 landmarks → 4 components)
    └─ Gestures (Hands → 21 landmarks × 2 → 3 gesture types)
    ↓
Speech Analysis (Whisper ASR + librosa)
    ├─ Transcription + WPM
    ├─ Filler words
    └─ Pause detection
    ↓
Voice Analysis (librosa PYIN + energy)
    ├─ Pitch statistics
    ├─ Energy metrics
    └─ Voice quality flags
    ↓
Aggregation & Scoring
    ├─ Component scores (6 dimensions)
    ├─ Signal quality metrics
    └─ Pattern analysis
    ↓
AI Enhancement (Gemini 1.5 Flash)
    ├─ Coaching tips
    ├─ Face impression
    └─ Session assessment
    ↓
Report Generation (Excel + JSON)
```

### **Performance Characteristics**

**Computation**:
- Face/Pose/Hands detection: ~30-50ms per frame (CPU)
- Emotion analysis: ~5-10ms per frame
- Video processing: Sampled at 8 FPS (reduces to ~12.5% of full processing)
- Whisper transcription: Real-time or near-real-time (< video duration)
- Voice analysis: < 1 second

**Thresholds Customizable** via `config.py`:
- Blink EAR: 0.20
- Gaze center: ±0.20
- Slouch Y: 0.60
- WPM range: 110-150
- Pause duration: 2.0s
- Monotone pitch variation: 15 Hz
- Energy loudness: 0.02-0.15 RMS

---

## APPENDIX: Configuration Constants

**File**: `config.py`

```python
# Vision Analysis
BLINK_EAR_THRESHOLD = 0.20
GAZE_CENTER_THRESHOLD = 0.20
SLOUCH_Y_THRESHOLD = 0.60

# Speech Analysis
IDEAL_WPM_MIN = 110
IDEAL_WPM_MAX = 150
LONG_PAUSE_THRESHOLD = 2.0  # seconds

# Voice Analysis
MONOTONE_THRESHOLD = 15.0  # Hz

# Scoring Weights
WEIGHT_EYE_CONTACT = 0.25
WEIGHT_EMOTION = 0.20
WEIGHT_POSTURE = 0.15
WEIGHT_GESTURE = 0.15
WEIGHT_SPEECH = 0.15
WEIGHT_VOICE = 0.10

# Models
WHISPER_MODEL_SIZE = "base"  # ~140M params
GEMINI_MODEL = "gemini-1.5-flash"

# Age-Based WPM Bands
foundational (5-8):   85-115 WPM
preparatory (9-12):   95-125 WPM
middle (13-16):      105-140 WPM
secondary (16-19):   110-150 WPM
college (19+):       120-160 WPM
```

---

## KEY INSIGHTS

1. **Multi-Modal Analysis**: Combines vision (face, pose, hands), speech (ASR), and voice (F0 tracking)
2. **Real-time Capable**: Designed for live processing at 8 FPS
3. **Age-Aware Scoring**: Adjusts expectations by age group (WPM bands)
4. **Confidence Transparency**: Clear signal quality metrics and analysis modes
5. **Graceful Degradation**: Fallbacks for all AI/ML dependencies
6. **Interpretable Features**: All metrics map to observable communication behaviors

---

**Document Generated**: April 13, 2026  
**Total Pages**: ~ 15 comprehensive sections  
**Last Updated**: Post-complete codebase review
