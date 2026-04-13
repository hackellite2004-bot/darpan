"""
Visualization Engine for Darpan
Generates matplotlib charts for emotions, gaze, voice metrics, and trends.
Inspired by SIH2022 project's visualization approach.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Optional

import matplotlib.pyplot as plt
import matplotlib
from matplotlib.figure import Figure
import numpy as np

# Use non-GUI backend for file generation
matplotlib.use('Agg')


class VisualizationEngine:
    """Generate matplotlib visualizations for session analysis."""

    EMOTION_COLORS = {
        'angry': '#FF6B6B',
        'disgusted': '#74B9FF',
        'fearful': '#FDCB6E',
        'happy': '#00B894',
        'neutral': '#A29BFE',
        'sad': '#0984E3',
        'surprised': '#FF7675',
    }

    FIGURE_DPI = 100
    FIGURE_SIZE_SMALL = (8, 6)
    FIGURE_SIZE_MEDIUM = (10, 6)
    FIGURE_SIZE_LARGE = (14, 8)

    @staticmethod
    def create_emotion_distribution_chart(
        emotions: dict[str, float],
        output_path: Optional[Path] = None,
    ) -> Path | None:
        """
        Create a pie chart showing emotion distribution percentages.
        
        Args:
            emotions: Dict with emotion names and percentages
            output_path: Path to save the figure
            
        Returns:
            Path to saved figure or None if creation failed
        """
        try:
            fig, ax = plt.subplots(
                figsize=VisualizationEngine.FIGURE_SIZE_SMALL,
                dpi=VisualizationEngine.FIGURE_DPI,
            )

            # Filter emotions with >0% occurrence and normalize to percentages.
            filtered_emotions = {k: float(v) for k, v in emotions.items() if float(v) > 0}
            if not filtered_emotions:
                plt.close(fig)
                return None

            total = sum(filtered_emotions.values())
            if total > 0:
                filtered_emotions = {k: (v / total) * 100.0 for k, v in filtered_emotions.items()}

            labels = [f"{k.capitalize()}\n({v:.1f}%)" for k, v in filtered_emotions.items()]
            colors = [VisualizationEngine.EMOTION_COLORS.get(k, '#999999') for k in filtered_emotions.keys()]
            values = list(filtered_emotions.values())

            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                colors=colors,
                autopct='%1.1f%%',
                startangle=90,
                wedgeprops={'linewidth': 1.0, 'edgecolor': 'white'},
                textprops={'fontsize': 9, 'weight': 'bold'},
            )

            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(8)
                autotext.set_weight('bold')

            ax.set_title('Emotion Distribution', fontsize=14, weight='bold', pad=20)

            if output_path:
                plt.savefig(output_path, dpi=VisualizationEngine.FIGURE_DPI, bbox_inches='tight')
                plt.close(fig)
                return output_path

            plt.close(fig)
            return None

        except Exception as e:
            print(f"Error creating emotion chart: {e}")
            plt.close(fig)
            return None

    @staticmethod
    def create_eye_gaze_chart(
        gaze_data: dict[str, float],
        output_path: Optional[Path] = None,
    ) -> Path | None:
        """
        Create a bar chart showing eye gaze distribution.
        
        Args:
            gaze_data: Dict with gaze directions and percentages
            output_path: Path to save the figure
            
        Returns:
            Path to saved figure or None
        """
        try:
            fig, ax = plt.subplots(
                figsize=VisualizationEngine.FIGURE_SIZE_SMALL,
                dpi=VisualizationEngine.FIGURE_DPI,
            )

            directions = list(gaze_data.keys())
            percentages = list(gaze_data.values())
            colors = ['#00B894', '#FF6B6B', '#74B9FF', '#FDCB6E']

            bars = ax.bar(directions, percentages, color=colors[:len(directions)], alpha=0.8, edgecolor='black', linewidth=1.5)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{height:.1f}%',
                    ha='center',
                    va='bottom',
                    fontweight='bold',
                    fontsize=10,
                )

            ax.set_ylabel('% of Time', fontsize=11, weight='bold')
            ax.set_title('Eye Gaze Analysis', fontsize=14, weight='bold', pad=20)
            ax.set_ylim(0, max(percentages) * 1.15 if percentages else 100)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            if output_path:
                plt.savefig(output_path, dpi=VisualizationEngine.FIGURE_DPI, bbox_inches='tight')
                plt.close(fig)
                return output_path

            plt.close(fig)
            return None

        except Exception as e:
            print(f"Error creating gaze chart: {e}")
            plt.close(fig)
            return None

    @staticmethod
    def create_speech_metrics_chart(
        wpm: float,
        fillers: int,
        pauses: int,
        output_path: Optional[Path] = None,
    ) -> Path | None:
        """
        Create a multi-panel chart showing speech metrics.
        
        Args:
            wpm: Words per minute
            fillers: Number of filler words
            pauses: Number of long pauses
            output_path: Path to save the figure
            
        Returns:
            Path to saved figure or None
        """
        try:
            fig, axes = plt.subplots(1, 3, figsize=(14, 4), dpi=VisualizationEngine.FIGURE_DPI)

            # WPM gauge
            wpm_optimal = 150  # Optimal WPM
            colors_wpm = ['#FF6B6B' if wpm < 120 else '#FDCB6E' if wpm < 140 else '#00B894' if wpm <= 160 else '#FDCB6E' if wpm < 180 else '#FF6B6B']
            axes[0].barh(['WPM'], [wpm], color=colors_wpm, height=0.4)
            axes[0].axvline(wpm_optimal, color='green', linestyle='--', linewidth=2, label='Optimal (150)')
            axes[0].set_xlim(0, max(200, wpm * 1.2))
            axes[0].set_xlabel('Words Per Minute', fontweight='bold')
            axes[0].set_title(f'Speech Speed\n{wpm} WPM', fontweight='bold')
            axes[0].legend(loc='lower right')
            axes[0].grid(axis='x', alpha=0.3)

            # Filler words
            axes[1].barh(['Fillers'], [fillers], color='#FF7675', height=0.4)
            axes[1].set_xlabel('Count', fontweight='bold')
            axes[1].set_title(f'Filler Words\n{fillers} detected', fontweight='bold')
            axes[1].grid(axis='x', alpha=0.3)

            # Pauses
            axes[2].barh(['Long Pauses'], [pauses], color='#74B9FF', height=0.4)
            axes[2].set_xlabel('Count', fontweight='bold')
            axes[2].set_title(f'Long Pauses (>2s)\n{pauses} detected', fontweight='bold')
            axes[2].grid(axis='x', alpha=0.3)

            fig.suptitle('Speech Analysis Metrics', fontsize=14, weight='bold', y=1.02)
            plt.tight_layout()

            if output_path:
                plt.savefig(output_path, dpi=VisualizationEngine.FIGURE_DPI, bbox_inches='tight')
                plt.close(fig)
                return output_path

            plt.close(fig)
            return None

        except Exception as e:
            print(f"Error creating speech metrics chart: {e}")
            plt.close(fig)
            return None

    @staticmethod
    def create_voice_spectrogram(
        audio_path: Path,
        output_path: Optional[Path] = None,
    ) -> Path | None:
        """
        Create a spectrogram visualization from audio file.
        
        Args:
            audio_path: Path to audio file
            output_path: Path to save the figure
            
        Returns:
            Path to saved figure or None
        """
        try:
            import librosa

            # Load audio
            y, sr = librosa.load(str(audio_path), sr=None)

            # Compute spectrogram
            D = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=512, n_mels=128)
            S_db = librosa.power_to_db(D, ref=np.max)

            fig, ax = plt.subplots(figsize=VisualizationEngine.FIGURE_SIZE_LARGE, dpi=VisualizationEngine.FIGURE_DPI)

            img = librosa.display.specshow(
                S_db,
                sr=sr,
                hop_length=512,
                x_axis='time',
                y_axis='mel',
                cmap='viridis',
                ax=ax,
            )

            ax.set_title('Voice Spectrogram', fontsize=14, weight='bold')
            fig.colorbar(img, ax=ax, label='Power (dB)')

            if output_path:
                plt.savefig(output_path, dpi=VisualizationEngine.FIGURE_DPI, bbox_inches='tight')
                plt.close(fig)
                return output_path

            plt.close(fig)
            return None

        except Exception as e:
            print(f"Error creating spectrogram: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None

    @staticmethod
    def create_confidence_trend_chart(
        scores: list[float],
        timestamps: Optional[list[float]] = None,
        output_path: Optional[Path] = None,
    ) -> Path | None:
        """
        Create a line chart showing confidence score trend over frames.
        
        Args:
            scores: List of frame-wise scores
            timestamps: Optional list of timestamps
            output_path: Path to save the figure
            
        Returns:
            Path to saved figure or None
        """
        try:
            if not scores:
                return None

            fig, ax = plt.subplots(figsize=VisualizationEngine.FIGURE_SIZE_MEDIUM, dpi=VisualizationEngine.FIGURE_DPI)

            if timestamps is None:
                x_values = list(range(len(scores)))
                x_label = 'Frame Number'
            else:
                x_values = timestamps
                x_label = 'Time (seconds)'

            # Plot score trend
            ax.plot(x_values, scores, linewidth=2, color='#0984E3', marker='o', markersize=4, alpha=0.7)

            # Add average line
            avg_score = np.mean(scores)
            ax.axhline(avg_score, color='red', linestyle='--', linewidth=2, label=f'Average: {avg_score:.1f}')
            ax.fill_between(x_values, scores, avg_score, alpha=0.2, color='#0984E3')

            ax.set_xlabel(x_label, fontweight='bold')
            ax.set_ylabel('Confidence Score', fontweight='bold')
            ax.set_title('Confidence Trend Over Time', fontsize=14, weight='bold')
            ax.set_ylim(0, 100)
            ax.grid(True, alpha=0.3)
            ax.legend()

            if output_path:
                plt.savefig(output_path, dpi=VisualizationEngine.FIGURE_DPI, bbox_inches='tight')
                plt.close(fig)
                return output_path

            plt.close(fig)
            return None

        except Exception as e:
            print(f"Error creating trend chart: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None

    @staticmethod
    def create_performance_radar_chart(
        metrics: dict[str, float],
        output_path: Optional[Path] = None,
    ) -> Path | None:
        """
        Create a radar chart showing overall performance metrics.
        
        Args:
            metrics: Dict of metric names and values (0-100 scale)
            output_path: Path to save the figure
            
        Returns:
            Path to saved figure or None
        """
        try:
            if not metrics:
                return None

            categories = list(metrics.keys())
            values = list(metrics.values())
            values += values[:1]  # Complete the circle

            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            angles += angles[:1]

            fig, ax = plt.subplots(figsize=(8, 8), dpi=VisualizationEngine.FIGURE_DPI, subplot_kw=dict(projection='polar'))

            ax.plot(angles, values, 'o-', linewidth=2, color='#0984E3')
            ax.fill(angles, values, alpha=0.25, color='#0984E3')

            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, fontsize=10)
            ax.set_ylim(0, 100)
            ax.set_yticks([20, 40, 60, 80, 100])
            ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=8)
            ax.grid(True, linestyle='--', alpha=0.5)

            ax.set_title('Performance Radar', fontsize=14, weight='bold', pad=20)

            if output_path:
                plt.savefig(output_path, dpi=VisualizationEngine.FIGURE_DPI, bbox_inches='tight')
                plt.close(fig)
                return output_path

            plt.close(fig)
            return None

        except Exception as e:
            print(f"Error creating radar chart: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None

    @staticmethod
    def create_multi_session_comparison(
        sessions: list[dict[str, Any]],
        metric_key: str,
        output_path: Optional[Path] = None,
    ) -> Path | None:
        """
        Create a line chart comparing a metric across multiple sessions.
        
        Args:
            sessions: List of session dicts with metrics
            metric_key: Key of metric to compare
            output_path: Path to save the figure
            
        Returns:
            Path to saved figure or None
        """
        try:
            if not sessions or len(sessions) < 2:
                return None

            fig, ax = plt.subplots(figsize=VisualizationEngine.FIGURE_SIZE_MEDIUM, dpi=VisualizationEngine.FIGURE_DPI)

            x_values = list(range(len(sessions)))
            y_values = [s.get(metric_key, 0) for s in sessions]

            ax.plot(x_values, y_values, marker='o', linewidth=2, markersize=8, color='#00B894')
            ax.fill_between(x_values, y_values, alpha=0.2, color='#00B894')

            # Add trend line
            z = np.polyfit(x_values, y_values, 2)
            p = np.poly1d(z)
            ax.plot(x_values, p(x_values), '--', linewidth=2, color='red', label='Trend', alpha=0.7)

            ax.set_xlabel('Session Number', fontweight='bold')
            ax.set_ylabel(f'{metric_key.replace("_", " ").title()}', fontweight='bold')
            ax.set_title(f'{metric_key.replace("_", " ").title()} Trend', fontsize=14, weight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.set_xticks(x_values)

            if output_path:
                plt.savefig(output_path, dpi=VisualizationEngine.FIGURE_DPI, bbox_inches='tight')
                plt.close(fig)
                return output_path

            plt.close(fig)
            return None

        except Exception as e:
            print(f"Error creating comparison chart: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None
