# Sanchar 2.0: Quick Reference Guide

## QUICK THRESHOLD LOOKUP TABLE

### Critical Thresholds by Analysis Type

| Analysis Type | Parameter | Value | Interpretation |
|---|---|---|---|
| **Eye Contact** | GAZE_CENTER_THRESHOLD | 0.20 | ±0.20 normalized range = "center" |
| **Eye Contact** | BLINK_EAR_THRESHOLD | 0.20 | Eye Aspect Ratio < 0.20 = blink |
| **Posture** | SLOUCH_Y_THRESHOLD | 0.60 | Shoulder Y > 0.60 = slouching |
| **Speech** | IDEAL_WPM_MIN | 110 | Minimum comfortable speech speed |
| **Speech** | IDEAL_WPM_MAX | 150 | Maximum comfortable speech speed |
| **Speech** | LONG_PAUSE_THRESHOLD | 2.0s | Pauses > 2.0s are "long pauses" |
| **Voice** | MONOTONE_THRESHOLD | 15.0 Hz | Pitch variation < 15 Hz = monotone |
| **Voice** | QUIET_ENERGY | 0.02 | Energy < 0.02 = too quiet |
| **Voice** | LOUD_ENERGY | 0.15 | Energy > 0.15 = too loud |
| **Gesture** | TIP_SPREAD_OPEN | 0.11 | Spread > 0.11 = open hand |
| **Gesture** | PALM_RATIO_OPEN | 1.0 | Height/Width ratio > 1.0 = open |
| **Gesture** | HIDDEN_STREAK | 10 frames | 10 consecutive frames = "hidden" |

---

## EMOTION SCORING FORMULAS - QUICK REFERENCE

### All Emotions Use This Template
```
emotion_score = CLIP([coefficient1 * feature1 + coefficient2 * feature2 + ...], 0, 1)
```

### The 6 Emotions

#### 1. HAPPY 😊
```
Formula: CLIP([cheek_raise × 8.0 + MAX(0, lip_corner_pull - 1.15) × 1.7])
Features:
  - cheek_raise: distance between eye level and cheek level
  - lip_corner_pull: mouth_width / eye_width ratio
Threshold: lip_corner_pull must exceed 1.15 to activate smile component
Primary trigger: Raised cheeks (Duchenne marker) [coefficient 8.0]
```

#### 2. SAD 😢
```
Formula: CLIP([brow_inner_raise × 6.0 + corner_drop × 9.0 + mouth_tension × 2.0])
Features:
  - brow_inner_raise: inner brow vertical position relative to eyes
  - corner_drop: downward displacement of mouth corners
  - mouth_tension: MAX(0, 1.02 - lip_corner_pull)
Strongest trigger: Mouth corner drop [coefficient 9.0]
Secondary trigger: Inner brow raise [coefficient 6.0]
```

#### 3. ANXIOUS 😰
```
Formula: CLIP([eye_open × 8.0 + brow_height × 2.5])
Features:
  - eye_open: distance from nose tip to eye midline
  - brow_height: distance between eyebrows and eye midline
Primary trigger: Wide eyes [coefficient 8.0]
Secondary trigger: Raised brows [coefficient 2.5]
```

#### 4. SURPRISED 😲
```
Formula: CLIP([lip_open × 9.0 + brow_height × 3.2])
Features:
  - lip_open: bottom_lip.y - top_lip.y (vertical mm)
  - brow_height: vertical distance from brow to eye level
Strongest trigger: Open mouth [coefficient 9.0]
Elevated brow contribution: Higher than anxious [coefficient 3.2 vs 2.5]
```

#### 5. ANGRY 😠
```
Formula: CLIP([brow_low × 6.0 + MAX(0, 1.1 - lip_corner_pull) × 1.2])
Features:
  - brow_low: downward displacement from resting position
  - lip_corner_pull: mouth width / eye width ratio
Primary trigger: Furrowed/lowered brows [coefficient 6.0]
Secondary trigger: Tight lips [coefficient 1.2, activated when ratio < 1.1]
```

#### 6. NEUTRAL 😐
```
Formula: CLIP([1.0 - MAX(happy, sad, anxious, surprised, angry) × 0.92])
Logic: Neutral score derives from absence of strong emotions
Damping factor: 0.92 (allows stable neutral even with minor expressions)
Stays high (~0.7+) even when one emotion scores 0.3
```

---

## GAZE ZONE CLASSIFICATION TREE

```
START: Calculate (offset_x, offset_y) from iris position

├─ Is |offset_x| ≤ 0.20 AND |offset_y| ≤ 0.20?
│  └─ YES → "CENTER"
│
├─ Is offset_x < -0.20?
│  └─ YES → "LEFT"
│
├─ Is offset_x > 0.20?
│  └─ YES → "RIGHT"
│
├─ Is offset_y > 0.20?
│  └─ YES → "DOWN"
│
└─ NO → "CENTER" (default fallback)

RESULT: One of 5 zones (center, left, right, down, away)
```

---

## EAR (EYE ASPECT RATIO) DETAILED FORMULA

```
LEFT EYE LANDMARKS: (33, 160, 158, 133, 153, 144)
RIGHT EYE LANDMARKS: (362, 385, 387, 263, 373, 380)

For each eye:
    vertical_1 = || p2 - p6 ||    (eyelid separation 1)
    vertical_2 = || p3 - p5 ||    (eyelid separation 2)
    horizontal = || p1 - p4 ||    (eye corner distance)
    
    EAR = (vertical_1 + vertical_2) / (2 × horizontal)

Session EAR = (LEFT_EAR + RIGHT_EAR) / 2

Blink Detection:
    if EAR < 0.20 for 2+ consecutive frames:
        fire BLINK_EVENT = true
    else:
        fire BLINK_EVENT = false
```

**Why EAR Works**:
- When eyes are open: EAR ≈ 0.4-0.6 (large vertical distance)
- When eyes are closed: EAR ≈ 0.0-0.2 (minimal vertical distance)
- Threshold of 0.20 provides reliable blink detection

---

## POSTURE SCORING BREAKDOWN

```python
# Start with perfect score
score = 1.0

# Apply penalties (order-independent as they're all subtractive)
score -= 0.40 if slouching else 0      # -40% if shoulders too low
score -= 0.22 if head_forward else 0   # -22% if head protrudes
score -= 0.18 if not shoulder_level    # -18% if shoulders uneven
score -= 0.12 if head_tilt else 0      # -12% if head tilted

# Final range
score = CLIP(score, 0.0, 1.0)

# Quality classification
if score >= 0.7:
    posture_good = true    # "Good posture"
else:
    posture_good = false   # "Needs improvement"
```

**Maximum Penalty Distribution**:
- Slouching alone: -40% (most impactful)
- All four issues combined: max -92% (capped at 0.0)

**Minimum Good Posture Score**: 0.7 (can have one ~0.12 penalty)

---

## GESTURE CLASSIFICATION LOGIC

```
INPUT: Hand landmarks for each detected hand

COMPUTE FOR EACH HAND:
    spread = mean distance between all fingertip pair combinations
    open_ratio = wrist_to_middle_distance / palm_span_width

AGGREGATE (if multiple hands):
    spread_score = mean(spreads across hands)
    open_score = mean(open_ratios across hands)

CLASSIFY:
    if spread_score > 0.11 AND open_score > 1.0:
        → "EXPRESSIVE" (open, animated gestures)
    elif spread_score < 0.045 OR open_score < 0.78:
        → "NERVOUS" (closed, defensive posture)
    else:
        → "NEUTRAL" (natural resting position)

CONFIDENCE SCORE:
    confidence = CLIP(spread_score × 5.0 + open_score × 0.5, 0, 1)

TRACKING:
    if gesture_type == "expressive":
        positive_frames += 1
    if gesture_type in {"nervous", "hidden"}:
        nervous_frames += 1
    
    positive_pct = (positive_frames / total_frames) × 100
    nervous_pct = (nervous_frames / total_frames) × 100

HAND HIDDEN DETECTION:
    if no hands detected for 10+ frames:
        gesture_type = "HIDDEN"
        nervous_frames += 1
```

**Key Thresholds**:
- Spread > 0.11: clearly open fingers
- Open ratio > 1.0: hand height > hand width
- Spread < 0.045: fist-like closure
- Open ratio < 0.78: collapsed/defensive

---

## SPEECH ANALYSIS FORMULAS

### WPM Calculation
```
word_count = number of regex matches for \b\w+\b
duration = max(last_word_time, 0.01) in seconds
WPM = (word_count / duration) × 60

Ideal range by age group:
    foundational (5-8):   85-115 WPM
    preparatory (9-12):   95-125 WPM
    middle (13-16):      105-140 WPM
    secondary (16-19):   110-150 WPM
    college (19+):       120-160 WPM
```

### Filler Word Penalty
```
Each filler word instance: -5 points from speech score
Pattern matching: case-insensitive, word boundary regex

14 fillers tracked: umm, um, uh, like, basically, you know, sort of, 
                    kind of, right, okay so, so yeah, actually, 
                    literally, honestly
```

### Pause Detection
```
LONG_PAUSE = gap > 2.0 seconds between words

Algorithm:
    for each adjacent word pair (i, i+1):
        gap = word[i+1].start - word[i].end
        if gap >= 2.0:
            pause_count += 1
            record_pause(at_time=word[i].end, duration=gap)

Output: List of {at: float, duration: float}
```

### Speech Score (Per-Session)
```
wpm_score = 
    100 if 110 ≤ wpm ≤ 150
    else MAX(0, 100 - |wpm - 130| × 1.5)

filler_score = MAX(0, 100 - filler_count × 5.0)
pause_score = MAX(0, 100 - pause_count × 10.0)

speech_score = (wpm_score + filler_score + pause_score) / 3
```

---

## VOICE ANALYSIS FORMULAS

### Pitch Analysis (from librosa.pyin)
```
PYIN Algorithm:
    - fmin = 80 Hz (male voices minimum)
    - fmax = 400 Hz (female/child voices)
    - Returns: f0 (fundamental frequency), voiced_flag, voiced_probabilities

Metrics:
    pitch_mean = mean(f0[voiced_flag])           # Hz
    pitch_variation = std(f0[voiced_flag])       # Hz

Monotone Detection:
    is_monotone = pitch_variation < 15.0 Hz
```

### Energy Analysis
```
RMS per frame:
    rms = librosa.feature.rms(y=y)[0]

Metrics:
    energy_mean = mean(rms)                      # [0, 1]
    energy_variation = std(rms)                  # [0, 1]

Loudness Classification:
    is_too_quiet = energy_mean < 0.02
    is_too_loud = energy_mean > 0.15
```

### Voice Score Calculation
```
score = 1.0  # Start perfect

Penalties:
    if is_monotone:
        score -= 0.3                    # -30%
    
    if is_too_quiet OR is_too_loud:
        score -= 0.2                    # -20%
    
    rate_variation = std(zero_crossing_rates_per_chunk)
    score -= MIN(0.2, rate_variation / 250.0)  # -0 to -20%

voice_score = CLIP(score, 0, 1)
```

**Maximum penalties**: -30% (monotone) + -20% (loudness) + -20% (articulation) = -70%

---

## COMPOSITE SCORING SYSTEM

### Component Score Calculation

#### Eye Score
```
eye_score = eye_center_pct  [0, 100]
Weight in overall: 25%
```

#### Emotion Score
```
calmness = MAX(0, 1 - MAX(anxious, surprised) × 0.9)

emotion_score = (
    neutral × 0.50 +
    happy × 0.15 +
    sad × 0.20 +
    calmness × 0.15
) × 100

Weight in overall: 20%
```

#### Posture Score
```
posture_score = posture_score × 100  [0, 100]
Weight in overall: 15%
```

#### Gesture Score
```
gesture_score = gesture_positive_pct  [0, 100]
Weight in overall: 15%
```

#### Speech Score
```
As per section above
Weight in overall: 15%
```

#### Voice Score
```
voice_score = voice_score × 100  [0, 100]
Weight in overall: 10%
```

### Final Confidence Score
```
score = (
    eye_score × 0.25 +
    emotion_score × 0.20 +
    posture_score × 0.15 +
    gesture_score × 0.15 +
    speech_score × 0.15 +
    voice_score × 0.10
)

Grade Assignment:
    score >= 85  → A
    score >= 70  → B
    score >= 55  → C
    score <  55  → D

Confidence Level:
    if score < 55 OR quality < 45  → "uncertain"
    if score >= 80 AND quality >= 70  → "confident"
    else  → "moderate"
```

---

## FRAME SAMPLING & SMOOTHING

### Frame Sampling
```
video_fps = actual video frame rate (e.g., 30)
target_fps = 8.0 (configurable)

sample_every = MAX(1, ROUND(video_fps / target_fps))

For each frame_index:
    if frame_index % sample_every == 0:
        process_frame()
    else:
        skip_frame()

# Example: 30 FPS video
# sample_every = ROUND(30/8) = ROUND(3.75) = 4
# Process frames 0, 4, 8, 12, ... (every 4th frame)
```

### Temporal Smoothing (5-Frame Window)
```
emotion_window = deque(maxlen=5)
posture_window = deque(maxlen=5)

For each processed frame:
    emotion_window.append(current_emotion_scores)
    posture_window.append(current_posture_score)
    
    smoothed_emotion = {
        'happy': mean([e['happy'] for e in emotion_window]),
        'neutral': mean([e['neutral'] for e in emotion_window]),
        ...
    }
    
    smoothed_posture = mean(posture_window)
```

**Effect**: Reduces jitter, creates 0.625-second averaging window at 8 FPS

---

## FRAME-LEVEL SCORING FORMULA

```python
Each frame receives these 4 components:

eye_component = 100.0 if gaze == "center" else 0.0

emotion_component = (
    smoothed_happy + 
    smoothed_neutral × 0.7
) × 100

posture_component = smoothed_posture × 100

gesture_component = {
    100.0 if gesture == "expressive",
    55.0 if gesture == "neutral",
    30.0 if gesture == "nervous"
}

# COMBINED FRAME SCORE
frame_score = CLIP(
    eye_component × 0.35 +          # 35% weight
    emotion_component × 0.25 +      # 25% weight
    posture_component × 0.25 +      # 25% weight
    gesture_component × 0.15,       # 15% weight
    0, 100
)

# Frame stability metric
stable_frames = count(|frame_score - mean| ≤ 12)
frame_stability = (stable_frames / total_frames) × 100
```

---

## SIGNAL QUALITY CALCULATION

### Temporal Confidence
```
Uses frame-level score statistics:
    frame_mean: average frame score
    frame_std: standard deviation
    frame_range: max - min

temporal_confidence = CLIP(
    100 - (frame_std × 1.6) - (frame_range × 0.35),
    0, 100
)
```

### Overall Reliability (Signal Quality Score)
```
reliability = CLIP(
    frame_stability × 0.22 +        # 22%
    temporal_confidence × 0.18 +    # 18%
    vision_fit × 0.24 +            # 24%
    speech_fit × 0.18 +            # 18%
    vocal_fit × 0.10 +             # 10%
    emotion_balance × 0.08,        # 8%
    0, 100
)

Interpretation:
    reliability >= 75  AND frame_stability >= 65  → "HIGH-CONFIDENCE"
    reliability >= 50                              → "GUARDED"
    reliability < 50                               → "UNCERTAIN"
```

---

## GEMINI AI INTEGRATION

### Coaching Tip Generation Context
```
Input Data Provided to LLM:
- User name & age group
- Confidence score (0-100)
- Dominant emotion predicted
- Specific metrics:
    - Eye contact: eye_center_pct
    - Posture: posture_score × 100
    - Speaking speed: WPM
    - Filler count: total_fillers
    - Top filler word
    - Pause count
    - Voice monotone: bool
    - Gesture style: classification

Output: JSON array of 4 strings (coaching tips)

Temperature: 0.9 (creative, varied)
Top-P: 0.95
Top-K: 40
Max tokens: 500
```

### Face Impression Analysis
```
Input: Single face frame + all metrics
Processing: Vision model analyzes facial expression
Output JSON:
{
    "summary": "1-sentence impression",
    "confidence": float [0, 1],
    "what_it_says": "Interpretation in communication context",
    "real_life_example": "Practical scenario reference"
}

Temperature: 0.7 (factual but creative)
Max tokens: 220
```

---

## LEGEND: ABBREVIATIONS & SYMBOLS

| Abbreviation | Meaning |
|---|---|
| EAR | Eye Aspect Ratio |
| WPM | Words Per Minute |
| F0 | Fundamental Frequency (pitch) |
| RMS | Root Mean Square (energy) |
| FPS | Frames Per Second |
| CLIP() | Bound value to range [0, 1] or [0, 100] |
| MAX/MIN | Maximum / Minimum function |
| STD | Standard Deviation |
| MEAN | Arithmetic Average |
| \|\| | Euclidean Distance (norm) |
| × | Multiplication (coefficient/weight) |
| ≈ | Approximately equal to |
| < > ≤ ≥ | Comparison operators |

---

## QUICK DECISION TREES

### Is This Emotion Score Valid?

```
emotion_score in [0.0, 1.0]?
├─ YES → Valid emotion score
└─ NO → Clipping function failed; report bug

Are all 6 emotions normalized?
├─ YES → Can compare directly
└─ NO → Scales differ; requires investigation

Does dominant emotion match highest score?
├─ YES → Consistency check passed
└─ NO → Logic error in argmax function
```

### How Good Is Eye Contact?

```
eye_center_pct = ?

├─ > 60%  → EXCELLENT (professional presenter level)
├─ 40-60% → GOOD (acceptable for beginners)
├─ 20-40% → NEEDS WORK (frequent gaze avoidance)
└─ < 20%  → POOR (consistently looking away)
```

### How's the Speaking Pace?

```
WPM = ?
Age group = ?  (determines range)

├─ Below min  → TOO SLOW (lacks confidence, loses audience)
├─ Within range → OPTIMAL (professional pace)
└─ Above max  → TOO FAST (hard to follow, rushed)

For secondary (16-19): should be 110-150 WPM
```

### Voice Quality Summary

```
is_monotone = ?  pitch_variation < 15 Hz
is_too_quiet = ?  energy_mean < 0.02
is_too_loud = ?  energy_mean > 0.15

Score impact:
├─ If monotone ONLY:     voice_score = 0.7 (-30%)
├─ If loudness issue:    voice_score -= 0.2 (-20%)
├─ If articulation poor: voice_score -= 0-20%
└─ Combination:          Could drop to 0.3-0.4
```

---

## PRACTICAL INTERPRETATION EXAMPLES

### Example Session Analysis

```
INPUT METRICS:
- eye_center_pct: 65%
- emotion_dominant: "happy"
- posture_score: 0.85
- gesture_type: "expressive"
- WPM: 132
- pitch_variation: 28 Hz
- voice_score: 0.8

COMPONENT SCORES:
- eye_score = 65
- emotion_score = (0.2 happy + 0.5 neutral × 0.7 + ...) × 100 ≈ 60
- posture_score = 85
- gesture_score = 75+ (expressive)
- speech_score = ((100 - |132-130|×1.5) + 100 + 100) / 3 ≈ 99
- voice_score = 80

OVERALL SCORE:
= 65×0.25 + 60×0.20 + 85×0.15 + 75×0.15 + 99×0.15 + 80×0.10
= 16.25 + 12 + 12.75 + 11.25 + 14.85 + 8
= 75.1 → GRADE B

CONFIDENCE LEVEL:
- score = 75.1 (>55) ✓
- quality_score ≈ 75 (>45) ✓
→ "MODERATE" to "CONFIDENT"
```

---

**Last Updated**: April 13, 2026  
**Use this guide alongside TECHNICAL_INVENTORY.md for comprehensive understanding**
