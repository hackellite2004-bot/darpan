# Sanchar 2.0: Analysis Metrics Summary & Decision Matrix

## METRIC RANGE & INTERPRETATION MATRIX

### Emotion Scores (All 0.0-1.0 scale)

| Emotion | Range | Low (<0.1) | Medium (0.3-0.6) | High (>0.7) | Diagnostic |
|---------|-------|-----------|-----------------|-----------|-----------|
| **Happy** | [0,1] | No smile | Some positivity | Bright smile, high energy | Cheek raise + mouth corners up |
| **Neutral** | [0,1] | Shows emotion | Balanced | Composed, calm | Default when others low |
| **Sad** | [0,1] | Positive mood | Slight downturn | Depressed expression | Inner brows up, mouth corners down |
| **Anxious** | [0,1] | Relaxed | Some tension | Visibly nervous | Wide eyes + raised brows |
| **Surprised** | [0,1] | Unsurprised | Mild shock | Shocked expression | Open mouth + raised brows |
| **Angry** | [0,1] | Calm | Slightly annoyed | Furious | Furrowed brows + tight lips |

---

### Eye Contact Metrics (All 0-100%)

| Metric | Optimal | Good | Fair | Poor | Issue |
|--------|---------|------|------|------|-------|
| **Eye Center %** | >60% | 40-60% | 20-40% | <20% | Gaze avoidance |
| **Eye Away %** | <40% | 40-60% | 60-80% | >80% | Not looking at camera/audience |
| **Blink Count** | 30-50 blinks | 25-60 | 10-80 | <10 or >100 | Stress or distraction |

---

### Face Analysis Metrics

| Metric | Normal | Concerning | Critical | Landmark IDs |
|--------|--------|-----------|----------|--------------|
| **Lip Opening (mm)** | <5 | 5-8 | >8 | 13, 14 |
| **Mouth Width/Eye Width** | 1.0-1.1 | 0.9-1.2 | <0.9 or >1.3 | 61,291,33,263 |
| **Cheek Raise (mm)** | >0.05 | 0.02-0.05 | <0.02 | 205,425,left/right eye |
| **Brow Height (mm)** | >0.03 | 0.01-0.03 | <0.01 | 70,300,33,263 |

---

### Posture Metrics (0.0-1.0, then ×100%)

| Component | Good (>0.7) | Acceptable (0.5-0.7) | Poor (<0.5) | Penalty |
|-----------|-----------|------------------|-----------|---------|
| **Overall Score** | Excellent posture | Needs minor adjustment | Watch slouching | 0 to -92% |
| **Slouching** | NO (shoulder Y ≤0.60) | Borderline (Y 0.55-0.65) | YES (Y >0.65) | -40% |
| **Head Forward** | NO (Z diff >-0.08) | Borderline | YES (Z diff <-0.08) | -22% |
| **Shoulder Level** | YES (ΔY ≤0.05) | Slight tilt | NO (ΔY >0.08) | -18% |
| **Head Tilt** | NO (ear ΔY ≤0.03) | Minor | YES (ΔY >0.05) | -12% |

---

### Gesture Metrics

| Metric | Expressive | Neutral | Nervous | Hidden |
|--------|-----------|---------|---------|--------|
| **Tip Spread** | >0.11 | 0.045-0.11 | <0.045 | - |
| **Palm Open Ratio** | >1.0 | 0.78-1.0 | <0.78 | - |
| **Hand Detection** | Both visible | One or both | Minimal | 10+ frames absent |
| **Interpretation** | Open, animated | Natural | Closed, tense | Hiding, nervous |
| **Session Impact** | Positive | Neutral | Nervous | Nervous |

---

## SPEECH ANALYSIS DECISION MATRIX

### WPM Interpretation by Age Group

| Age Group | Slow (<min) | Optimal | Fast (>max) | Ideal Range |
|-----------|------------|---------|-----------|-------------|
| Foundational (5-8) | <85 WPM | 85-115 | >115 | 85-115 WPM |
| Preparatory (9-12) | <95 WPM | 95-125 | >125 | 95-125 WPM |
| Middle (13-16) | <105 WPM | 105-140 | >140 | 105-140 WPM |
| Secondary (16-19) | <110 WPM | 110-150 | >150 | 110-150 WPM |
| College (19+) | <120 WPM | 120-160 | >160 | 120-160 WPM |

### Filler Count Impact

| Count | Rating | Score Penalty | Interpretation |
|-------|--------|---------------|-----------------|
| 0-2 | Excellent | 0-10 pts | Nearly filler-free |
| 3-5 | Good | 15-25 pts | Occasional fillers |
| 6-10 | Fair | 30-50 pts | Noticeable fillers |
| 11-15 | Poor | 55-75 pts | Frequent fillers |
| 16+ | Critical | 80+ pts | Severe filler dependency |

### Pause Detection

| Pause Count | Result | Interpretation |
|-------------|--------|-----------------|
| 0 | Ideal | Fluent, no hesitations |
| 1-2 | Good | Natural thinking pauses |
| 3-5 | Acceptable | Some nervousness |
| 6-10 | Concerning | Frequent hesitations |
| 11+ | Poor | Severe lack of confidence |

---

## VOICE ANALYSIS INTERPRETATION MATRIX

### Pitch Analysis

| Pitch Mean (Hz) | Gender Indicator | Range |
|----------------|-----------------|-------|
| 80-100 Hz | Low male voice | Bass |
| 100-130 Hz | Average male | Midrange |
| 130-180 Hz | Female/child | Soprano |
| 180-250 Hz | High female/child | Alto |

| Pitch Variation (Hz) | Status | Monotone | Interpretation |
|------------------|--------|----------|-----------------|
| >30 Hz | Expressive | NO | Rich vocal variation |
| 15-30 Hz | Acceptable | NO | Moderate variation |
| <15 Hz | Monotone | YES | Flat, lacking expression |

### Energy Levels

| Energy Mean | RMS Value | Loudness | Interpretation |
|-------------|-----------|----------|-----------------|
| Too Quiet | <0.02 | -20% penalty | Inaudible, whisper |
| Quiet | 0.02-0.05 | Reduced | Timid, hard to hear |
| Optimal | 0.05-0.15 | Normal | Clear, projecting |
| Loud | 0.15-0.25 | Elevated | Shouting, aggressive |
| Too Loud | >0.25 | -20% penalty | Uncomfortable volume |

### Voice Quality Score Components

| Factor | Full Points | If Failing | Combined |
|--------|------------|-----------|----------|
| Not Monotone | ✓ (0 penalty) | -30% | Base: 100 |
| Good Loudness | ✓ (0 penalty) | -20% | 100 or 80 |
| Good Articulation | ✓ (0 penalty) | -0 to 20% | 80-100 final |

---

## COMPOSITE CONFIDENCE SCORING

### Component Contribution to Final Score

```
COMPONENT          SCORE RANGE    WEIGHT    CONTRIBUTION (max)
Eye Contact        0-100          0.25      25 points
Emotion            0-100          0.20      20 points
Posture            0-100          0.15      15 points
Gesture            0-100          0.15      15 points
Speech             0-100          0.15      15 points
Voice              0-100          0.10      10 points
                                           ────────
                                  TOTAL:    100 points
```

### Score-to-Grade Translation

| Score | Grade | Confidence | Interpretation |
|-------|-------|-----------|-----------------|
| 85-100 | A | Confident | Excellent delivery |
| 70-84 | B | Moderate | Good, some areas to improve |
| 55-69 | C | Moderate | Acceptable, notable issues |
| 40-54 | D | Uncertain | Poor, significant concerns |
| <40 | F | Uncertain | Critical issues |

### Signal Quality (Reliability) Indicators

| Reliability | Frame Stability | Analysis Mode | Recommendation |
|------------|-----------------|---------------|-----------------|
| ≥75% | ≥65% | HIGH-CONFIDENCE | Use for scoring |
| 50-74% | 40-64% | GUARDED | Use cautiously |
| <50% | <40% | UNCERTAIN | Requires calibration |

---

## FACE LANDMARK REFERENCE MAP

### Key Landmark Indices

```
REGIONS:
    Nose:           [0, 6]
    Lips:           [13, 14, 61, 291]
    Eyes:           [33, 133, 160, 159, 145, 144, 158, 153]
                    [362, 263, 385, 386, 374, 380, 387, 373]
    Eyebrows:       [70, 168, 300]
    Cheeks:         [205, 425]
    Iris:           [468, 473]

ZONES:
    Face Region     Landmarks     Purpose
    ────────────────────────────────────────
    Left Eye        33→159→145    Gaze tracking, blinking
    Right Eye       263→386→374   Gaze tracking, blinking
    Left Eyebrow    70→168        Emotion (surprise, sad)
    Right Eyebrow   168→300       Emotion (surprise, sad)
    Mouth           13,14,61,291  Emotion (happy, sad)
    Cheeks          205,425       Emotion (happy, surprised)
```

---

## FRAME-LEVEL ANALYSIS FLOW

```
┌─────────────────────────────────────────────────────────────┐
│ VIDEO FRAME INPUT (at 8 FPS from ~30 FPS source)           │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┬──────────┬─────────┐
        │                     │          │         │
        ▼                     ▼          ▼         ▼
    EMOTION(0-1)          GAZE(zone)  POSTURE   GESTURE
    - happy               - center    (0-1)     (type)
    - neutral             - left      - slouch  - expressive
    - sad                 - right     - head    - neutral
    - anxious             - down      - level   - nervous
    - surprised           - away      - tilt    - hidden
    - angry                                     
        │                     │          │         │
        └──────────┬──────────┴──────────┴─────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │ TEMPORAL SMOOTHING (5-frame) │
        │ Emotion & Posture windowed   │
        └────────┬─────────────────────┘
                 │
        ┌────────▼──────────────────────┐
        │ FRAME SCORE CALCULATION       │
        │ Frame = 35% eye + 25% emotion │
        │       + 25% posture + 15% gest│
        │ Result: 0-100 pts             │
        └────────┬──────────────────────┘
                 │
        ┌────────▼──────────────────────┐
        │ ACCUMULATION                  │
        │ - Collect in frame_scores[]   │
        │ - Track timestamps            │
        │ - Monitor stability           │
        └─────────────────────────────────┘
```

---

## QUALITY FILTERING DECISION TREE

```
Does session have video data?
├─ NO → Return defaults, "no_data" mode
└─ YES ↓

Can extract face landmarks?
├─ NO (poor lighting) → emotion_score = default
└─ YES ↓

Can detect eye contact?
├─ NO (face turned away) → eye_center = 0%
└─ YES ↓

Can process audio?
├─ NO (silent) → wpm = 0, filler = 0
└─ YES ↓

Calculate signal_quality = reliability metric
├─ ≥75% → "HIGH-CONFIDENCE" analysis
├─ 50-74% → "GUARDED" analysis (warnings issued)
└─ <50% → "UNCERTAIN" analysis (suggest rerecord)
```

---

## EMOTION TRIGGER MATRIX

Which facial features activate each emotion?

```
EMOTION    │ CHEEKS  │ BROWS   │ MOUTH   │ EYES    │ PRIORITY
───────────┼─────────┼─────────┼─────────┼─────────┼──────────
Happy      │ HIGH↑   │ normal  │ UP↑     │ normal  │ Cheeks >> Mouth
Sad        │ normal  │ UP↑     │ DOWN↓   │ tight   │ Mouth > Brows
Anxious    │ normal  │ HIGH↑   │ tight   │ WIDE✕   │ Eyes > Brows
Surprised  │ raised  │ HIGH↑   │ OPEN◯   │ wide    │ Mouth > Brows
Angry      │ normal  │ DOWN↓   │ tight   │ intense │ Brows > Mouth
Neutral    │ relaxed │ relaxed │ closed  │ normal  │ Absence of others
```

---

## COMMON ANALYSIS SCENARIOS

### Scenario 1: High-Confidence Presentation
```
signal_quality: ≥75%
eye_center: ≥60%
posture_score: ≥0.8
voice_score: ≥0.75
wpm: within ideal range
Result: "CONFIDENT" grade A/B
Action: Approve for interview/presentation
```

### Scenario 2: Nervous Speaker
```
gesture_nervous_pct: >35%
eye_center: <40%
emotion_anxious: >0.3
pause_count: 6+
Result: "MODERATE" grade C
Action: Suggest relaxation techniques
```

### Scenario 3: Poor Recording Quality
```
signal_quality: <50%
frame_stability: <40%
emotion: all near 0
eye_gaze: mostly "away"
Result: "UNCERTAIN"
Action: Request re-recording (better lighting/audio)
```

### Scenario 4: Excellent Posture but Monotone Voice
```
posture_score: 0.95
pitch_variation: 8 Hz (< 15 threshold)
voice_score: 0.3
Overall: Good body language, weak voice projection
Action: Voice coaching priority
```

---

## ALGORITHM FAMILY SUMMARY

| Analysis Type | Algorithm | Model | Accuracy | Real-time |
|---------------|-----------|-------|----------|-----------|
| Face Detect | Landmark-based | MediaPipe Mesh | ~99.7% | ✓ |
| Emotion | Geometric features | Custom heuristic | ~80-85% | ✓ |
| Eye Tracking | Iris normalization | MediaPipe Mesh | ~90% | ✓ |
| Blink Detection | Eye Aspect Ratio | State machine | ~95% | ✓ |
| Posture | Body landmarks | MediaPipe Pose | ~85-90% | ✓ |
| Gesture | Hand landmarks + geometry | MediaPipe Hands | ~80-85% | ✓ |
| Speech | ASR | Whisper (base) | ~85-90% | ✓ TV |
| Pitch Tracking | PYIN method | librosa | ~85% | ✗ |
| Energy Analysis | RMS signal | librosa | ~95% | ✗ |
| Coaching Tips | LLM | Gemini 1.5F | Variable | ✗ |

**Legend**: ✓ = Real-time capable, ✗ = Batch processing, TV = Time-variable

---

## CONFIG TUNING GUIDE

To adjust thresholds, modify `config.py`:

```python
# STRICTER (detect more issues)
BLINK_EAR_THRESHOLD = 0.18  # Lower = more sensitive
SLOUCH_Y_THRESHOLD = 0.55   # Lower = stricter posture
LONG_PAUSE_THRESHOLD = 1.5  # Lower = fewer pauses allowed

# RELAXED (more forgiving)
BLINK_EAR_THRESHOLD = 0.25  # Higher = less sensitive
SLOUCH_Y_THRESHOLD = 0.65   # Higher = more slouching tolerated
LONG_PAUSE_THRESHOLD = 2.5  # Higher = more pause tolerance

# CHANGE WPM EXPECTATIONS
IDEAL_WPM_MIN = 100  # Lower minimum
IDEAL_WPM_MAX = 160  # Higher maximum

# REWEIGHT SCORING
WEIGHT_VOICE = 0.20  # Increase voice importance
WEIGHT_EMOTION = 0.10  # Decrease emotion importance
```

---

## DEPENDENCY VERSIONS (as of April 2026)

| Package | Version | Purpose |
|---------|---------|---------|
| mediapipe | ≥0.10.0 | Face/Pose/Hand detection |
| opencv-python | ≥4.9.0 | Video capture & processing |
| openai-whisper | ≥20231117 | Speech recognition |
| librosa | ≥0.10.0 | Audio analysis |
| numpy | ≥1.26.0 | Numerical computing |
| scipy | ≥1.12.0 | Signal processing |
| google-genai | ≥1.0.0 | AI coaching |

---

**Document Type**: Quick Reference & Decision Matrix  
**Generated**: April 13, 2026  
**Use alongside**: TECHNICAL_INVENTORY.md and QUICK_REFERENCE.md
