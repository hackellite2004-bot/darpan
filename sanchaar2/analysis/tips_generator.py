"""
Contextual Tips and Suggestions Generator
Provides personalized AI-powered advice based on session metrics.
Inspired by SIH2022 project's contextual feedback system.
"""

from __future__ import annotations

from typing import Any


class TipsGenerator:
    """Generate contextual tips based on session metrics."""

    @staticmethod
    def generate_wpm_tips(wpm: float) -> str:
        """Generate WPM-based suggestions."""
        base_tip = f"\n📌 **Words Per Minute Analysis** ({wpm:.0f} WPM)\n"

        if wpm < 120:
            return (
                base_tip
                + """
Your speaking speed is slower than average. Consider:
• Gradual speed increase while maintaining clarity
• Practice with shadowing technique (repeating audio)
• Ensure your thoughts are organized before speaking
• Check if you're pausing too frequently

**Optimal Range**: 140-160 WPM for presentations
**Your Status**: 🐢 **TOO SLOW**
                """
            )
        elif wpm < 140:
            return (
                base_tip
                + """
You're close to optimal speed! Small improvements can help:
• Try maintaining consistent pace throughout
• Reduce filler words ("um", "like", "uh")
• Practice with a metronome or pacing exercises
• Record yourself and analyze for patterns

**Optimal Range**: 140-160 WPM for presentations
**Your Status**: ↗ **SLIGHTLY BELOW OPTIMAL**
                """
            )
        elif wpm <= 160:
            return (
                base_tip
                + """
Excellent! Your speed is in the optimal range. Maintain this by:
• Keep structured pauses at punctuation marks
• Vary pace based on content importance
• Balance speed with proper pronunciation
• Adjust pace based on audience feedback

**Optimal Range**: 140-160 WPM for presentations
**Your Status**: ✓ **OPTIMAL**
                """
            )
        elif wpm < 180:
            return (
                base_tip
                + """
You're slightly above optimal. Consider:
• Intentional pauses for emphasis and comprehension
• Slow down on complex topics
• Use strategic silence for audience engagement
• Practice pacing exercises to find consistency

**Optimal Range**: 140-160 WPM for presentations
**Your Status**: ↖ **SLIGHTLY ABOVE OPTIMAL**
                """
            )
        else:
            return (
                base_tip
                + """
Your speed is quite fast. Listeners may struggle. Try:
• Conscious slowing, especially on technical content
• Adding deliberate pauses for emphasis
• Practicing with audio feedback
• Breaking sentences into smaller units
• Recording and comparing with optimal-speed speakers

**Optimal Range**: 140-160 WPM for presentations
**Your Status**: 🚀 **TOO FAST**
                """
            )

    @staticmethod
    def generate_emotion_tips(emotions: dict[str, float]) -> str:
        """Generate emotion-based suggestions."""
        tips = "\n📌 **Emotion Analysis & Suggestions**\n"

        # Find dominant emotions
        happy = emotions.get('happy', 0)
        neutral = emotions.get('neutral', 0)
        sad = emotions.get('sad', 0)
        anxious = emotions.get('anxious', 0)
        surprised = emotions.get('surprised', 0)

        suggestions = []

        if happy > 30:
            suggestions.append(
                "😊 **High Happiness**: Great enthusiasm! Maintain this energy but ensure it matches content tone."
            )

        if neutral > 60:
            suggestions.append(
                "😐 **High Neutrality**: Show more emotional connection. Vary facial expressions and engage with content."
            )

        if sad > 15:
            suggestions.append(
                "😢 **Notable Sadness**: Ensure content isn't misaligned with mood. Check for engagement issues."
            )

        if anxious > 20:
            suggestions.append(
                "😰 **Visible Anxiety**: Deep breaths before speaking. Practice stress-reduction techniques. Your confidence will improve with rehearsal."
            )

        if surprised > 10:
            suggestions.append(
                "😲 **Surprise Detected**: Show natural reactions but maintain composure. Practice responses to potential questions."
            )

        if not suggestions:
            suggestions.append("😊 Your emotions are well-balanced. Great job maintaining composure!")

        return tips + "\n".join(suggestions)

    @staticmethod
    def generate_eye_contact_tips(eye_center_pct: float, eye_away_pct: float, blink_count: int) -> str:
        """Generate eye contact and gaze suggestions."""
        tips = f"\n📌 **Eye Contact & Gaze Analysis**\n"

        suggestions = []

        if eye_center_pct > 60:
            suggestions.append(
                f"✓ **{eye_center_pct:.0f}% Center Gaze**: Excellent eye contact! You're maintaining audience engagement effectively."
            )
        elif eye_center_pct > 40:
            suggestions.append(
                f"→ **{eye_center_pct:.0f}% Center Gaze**: Good eye contact. Try to maintain 60%+ focus on audience."
            )
        else:
            suggestions.append(
                f"⚠ **{eye_center_pct:.0f}% Center Gaze**: Limited eye contact. Practice looking directly at your audience/camera more frequently."
            )

        if eye_away_pct > 30:
            suggestions.append(
                f"→ Looking away {eye_away_pct:.0f}% of the time. Minimize distractions and maintain steady gaze."
            )

        if blink_count > 100:
            suggestions.append(
                f"→ **{blink_count} blinks detected**: Possibly stress indicator. Try relaxation techniques like slow, deep breathing."
            )
        elif blink_count < 30:
            suggestions.append(
                f"✓ **{blink_count} blinks detected**: Normal blink rate. Good control over your physiology."
            )

        return tips + "\n".join(suggestions)

    @staticmethod
    def generate_posture_tips(posture_score: float, slouch_pct: float) -> str:
        """Generate posture and gesture suggestions."""
        tips = f"\n📌 **Posture & Body Language**\n"

        if posture_score > 70:
            suggestions = [f"✓ **{posture_score:.0f}% Good Posture**: Excellent! You're projecting confidence and professionalism."]
        elif posture_score > 50:
            suggestions = [f"→ **{posture_score:.0f}% Adequate Posture**: Try to stand/sit more upright. Better posture improves confidence perception."]
        else:
            suggestions = [f"⚠ **{posture_score:.0f}% Poor Posture**: Focus on sitting/standing straight. This significantly impacts how your message is received."]

        if slouch_pct > 20:
            suggestions.append(
                f"→ **{slouch_pct:.0f}% Slouching**: Be conscious of your posture. Regular posture checks during practice will help."
            )
        else:
            suggestions.append(f"✓ **{slouch_pct:.0f}% Slouching**: Good posture control maintained throughout.")

        return tips + "\n".join(suggestions)

    @staticmethod
    def generate_voice_tips(voice_score: float, pitch_variation: float, is_monotone: bool) -> str:
        """Generate voice and tone suggestions."""
        tips = f"\n📌 **Voice Characteristics**\n"

        suggestions = []

        if voice_score > 70:
            suggestions.append("✓ **Good Voice Quality**: Your voice is clear and well-modulated. Maintain this!")
        elif voice_score > 50:
            suggestions.append("→ **Moderate Voice Quality**: Work on clarity and projection. Speak more deliberately.")
        else:
            suggestions.append("⚠ **Low Voice Quality**: Focus on articulation, projection, and pacing.")

        if is_monotone:
            suggestions.append(
                "→ **Monotonic Delivery Detected**: Add pitch variation by emphasizing key words and varying sentence intonation."
            )
        elif pitch_variation < 0.3:
            suggestions.append(
                "→ **Low Pitch Variation**: Try varying your pitch to add interest. Practice emphasizing different words."
            )
        else:
            suggestions.append(f"✓ **Good Pitch Variation**: Your voice has natural variation ({pitch_variation:.2f}). Keep it engaging!")

        return tips + "\n".join(suggestions)

    @staticmethod
    def generate_filler_words_tips(filler_words: dict[str, int], total_fillers: int) -> str:
        """Generate filler words reduction suggestions."""
        tips = f"\n📌 **Filler Words Analysis** ({total_fillers} total)\n"

        if total_fillers == 0:
            return tips + "✓ **No filler words detected**: Excellent verbal discipline!"

        suggestions = []

        if total_fillers < 5:
            suggestions.append(f"✓ **Low fillers detected ({total_fillers})**: Great control! Your speech is clean and professional.")
        elif total_fillers < 15:
            suggestions.append(f"→ **Moderate fillers ({total_fillers})**: Try pausing instead of saying 'um', 'uh', or 'like'.")
        else:
            suggestions.append(f"⚠ **High fillers ({total_fillers})**: Focus on reducing these. Pause, breathe, and collect thoughts instead.")

        # Top filler words
        if filler_words:
            top_fillers = sorted(filler_words.items(), key=lambda x: x[1], reverse=True)[:3]
            filler_list = ", ".join([f'"{word}"({count})' for word, count in top_fillers])
            suggestions.append(f"→ Top fillers: {filler_list}. Be mindful of these during practice.")

        return tips + "\n".join(suggestions)

    @staticmethod
    def generate_overall_tips(metrics: dict[str, Any]) -> str:
        """Generate comprehensive overall suggestions."""
        tips = "\n🎯 **OVERALL RECOMMENDATIONS**\n"

        score = metrics.get('overall_score', 0)
        grade = metrics.get('grade', '-')

        if grade in ['A', 'B']:
            intro = f"🎉 Excellent presentation ({score:.0f}/100)! You've demonstrated strong communication skills. Here's how to maintain and improve:"
        elif grade == 'C':
            intro = f"Good effort ({score:.0f}/100)! With some focused practice on these areas, you can significantly improve:"
        else:
            intro = f"This is a learning opportunity ({score:.0f}/100). Focus on these key areas for improvement:"

        recommendations = [intro]

        # Prioritize top 3 issues
        issues = []

        if metrics.get('wpm', 0) < 120 or metrics.get('wpm', 0) > 180:
            issues.append(("Speech Speed", "Adjust WPM to 140-160 range", 1))

        if metrics.get('eye_center_pct', 0) < 50:
            issues.append(("Eye Contact", "Increase direct gaze to 60%+", 2))

        if metrics.get('posture_score', 0) < 60:
            issues.append(("Posture", "Improve body alignment", 3))

        if metrics.get('filler_count', 0) > 15:
            issues.append(("Filler Words", "Reduce to under 10 count", 4))

        if metrics.get('is_monotone'):
            issues.append(("Voice Variation", "Add pitch variation", 5))

        if metrics.get('emotion_anxious', 0) > 20:
            issues.append(("Anxiety", "Release tension through breathing", 6))

        # Top 3
        top_issues = sorted(issues, key=lambda x: x[2])[:3]
        for idx, (area, action, _) in enumerate(top_issues, 1):
            recommendations.append(f"{idx}. **{area}**: {action}")

        # Action plan
        recommendations.append(
            "\n📋 **Action Plan**: Practice focusing on these one at a time. Record yourself, review, and measure improvement in your next session."
        )

        return "\n".join(recommendations)

    @staticmethod
    def get_all_tips(metrics: dict[str, Any]) -> str:
        """Generate all contextual tips for a session."""
        all_tips = "=" * 60 + "\n"
        all_tips += "📊 COMPREHENSIVE FEEDBACK REPORT\n"
        all_tips += "=" * 60 + "\n"

        # WPM tips
        all_tips += TipsGenerator.generate_wpm_tips(metrics.get('wpm', 0))
        all_tips += "\n"

        # Emotion tips
        emotions = {
            'happy': metrics.get('emotion_happy', 0),
            'neutral': metrics.get('emotion_neutral', 0),
            'sad': metrics.get('emotion_sad', 0),
            'anxious': metrics.get('emotion_anxious', 0),
            'surprised': metrics.get('emotion_surprised', 0),
        }
        all_tips += TipsGenerator.generate_emotion_tips(emotions)
        all_tips += "\n"

        # Eye contact tips
        all_tips += TipsGenerator.generate_eye_contact_tips(
            metrics.get('eye_center_pct', 0),
            metrics.get('eye_away_pct', 0),
            metrics.get('blink_count', 0),
        )
        all_tips += "\n"

        # Posture tips
        all_tips += TipsGenerator.generate_posture_tips(
            metrics.get('posture_score', 0),
            metrics.get('slouch_pct', 0),
        )
        all_tips += "\n"

        # Voice tips
        all_tips += TipsGenerator.generate_voice_tips(
            metrics.get('voice_score', 0),
            metrics.get('pitch_variation', 0),
            metrics.get('is_monotone', False),
        )
        all_tips += "\n"

        # Filler words tips
        filler_words = metrics.get('filler_words', {})
        all_tips += TipsGenerator.generate_filler_words_tips(
            filler_words,
            metrics.get('filler_count', 0),
        )
        all_tips += "\n"

        # Overall tips
        all_tips += TipsGenerator.generate_overall_tips(metrics)
        all_tips += "\n" + "=" * 60 + "\n"

        return all_tips
