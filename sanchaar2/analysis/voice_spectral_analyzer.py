"""
Voice Spectral Analysis Module
Generates voice spectrogram and chromagram visualizations inspired by SIH2022.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# Use non-GUI backend
matplotlib.use('Agg')


class VoiceSpectralAnalyzer:
    """Analyze and visualize voice spectral characteristics."""

    @staticmethod
    def compute_spectrogram(
        audio_data: np.ndarray,
        sr: int,
        window: str = 'hann',
        nperseg: int = 2048,
        noverlap: Optional[int] = None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute spectrogram from audio data.
        
        Args:
            audio_data: Audio time series
            sr: Sampling rate
            window: Window function (hann, hamming, etc.)
            nperseg: Window size
            noverlap: Overlap
            
        Returns:
            frequencies, times, spectrogram
        """
        try:
            from scipy import signal as sp_signal

            if noverlap is None:
                noverlap = nperseg // 2

            f, t, Sxx = sp_signal.spectrogram(
                audio_data,
                fs=sr,
                window=window,
                nperseg=nperseg,
                noverlap=noverlap,
            )

            return f, t, Sxx

        except Exception as e:
            print(f"Error computing spectrogram: {e}")
            return np.array([]), np.array([]), np.array([])

    @staticmethod
    def compute_chromagram(
        audio_data: np.ndarray,
        sr: int,
        hop_length: int = 512,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute chromagram (pitch-energy distribution).
        
        Args:
            audio_data: Audio time series
            sr: Sampling rate
            hop_length: Hop length for STFT
            
        Returns:
            chroma matrix (12 x time), times
        """
        try:
            import librosa

            chroma = librosa.feature.chroma_cqt(y=audio_data, sr=sr, hop_length=hop_length)
            times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=hop_length)

            return chroma, times

        except Exception as e:
            print(f"Error computing chromagram: {e}")
            return np.array([]), np.array([])

    @staticmethod
    def visualize_spectrogram(
        audio_path: Path,
        output_path: Optional[Path] = None,
        cmap: str = 'viridis',
    ) -> Path | None:
        """
        Create spectrogram visualization from audio file.
        
        Args:
            audio_path: Path to audio file
            output_path: Path to save figure
            cmap: Colormap name
            
        Returns:
            Path to saved figure or None
        """
        try:
            import librosa

            # Load audio
            y, sr = librosa.load(str(audio_path), sr=None)

            # Compute mel spectrogram
            D = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=512)
            S_db = librosa.power_to_db(D, ref=np.max)

            fig, ax = plt.subplots(figsize=(14, 6), dpi=100)

            img = librosa.display.specshow(
                S_db,
                sr=sr,
                hop_length=512,
                x_axis='time',
                y_axis='mel',
                cmap=cmap,
                ax=ax,
            )

            fig.colorbar(img, ax=ax, label='Power (dB)')
            ax.set_title('Voice Spectrogram - Frequency vs Time', fontsize=14, weight='bold')

            if output_path:
                plt.savefig(output_path, dpi=100, bbox_inches='tight')
                plt.close(fig)
                return output_path

            plt.close(fig)
            return None

        except Exception as e:
            print(f"Error visualizing spectrogram: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None

    @staticmethod
    def visualize_chromagram(
        audio_path: Path,
        output_path: Optional[Path] = None,
        cmap: str = 'jet',
    ) -> Path | None:
        """
        Create chromagram visualization (12 musical notes vs time).
        
        Args:
            audio_path: Path to audio file
            output_path: Path to save figure
            cmap: Colormap name
            
        Returns:
            Path to saved figure or None
        """
        try:
            import librosa

            # Load audio
            y, sr = librosa.load(str(audio_path), sr=None)

            # Compute chromagram
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)

            fig, ax = plt.subplots(figsize=(14, 6), dpi=100)

            img = librosa.display.specshow(
                chroma,
                sr=sr,
                hop_length=512,
                x_axis='time',
                y_axis='chroma',
                cmap=cmap,
                ax=ax,
            )

            fig.colorbar(img, ax=ax, label='Energy')
            ax.set_title('Voice Chromagram - Musical Notes vs Time', fontsize=14, weight='bold')

            # Set chroma labels
            chroma_notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            ax.set_yticks(np.arange(12))
            ax.set_yticklabels(chroma_notes)

            if output_path:
                plt.savefig(output_path, dpi=100, bbox_inches='tight')
                plt.close(fig)
                return output_path

            plt.close(fig)
            return None

        except Exception as e:
            print(f"Error visualizing chromagram: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None

    @staticmethod
    def compute_pitch_contour(
        audio_data: np.ndarray,
        sr: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute pitch contour (fundamental frequency over time).
        
        Args:
            audio_data: Audio time series
            sr: Sampling rate
            
        Returns:
            times, frequencies
        """
        try:
            import librosa

            # Compute constant-Q transform magnitude
            C = librosa.cqt(audio_data, sr=sr)
            fmin = librosa.midi_to_hz(36)  # Note C1
            pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sr, fmin=fmin, fmax=fmin * 24, threshold=0.1)

            # Track pitch
            index = 0
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                pitch_values.append(pitch)

            times = librosa.frames_to_time(np.arange(len(pitch_values)), sr=sr)

            return times, np.array(pitch_values)

        except Exception as e:
            print(f"Error computing pitch contour: {e}")
            return np.array([]), np.array([])

    @staticmethod
    def visualize_pitch_contour(
        audio_path: Path,
        output_path: Optional[Path] = None,
    ) -> Path | None:
        """
        Create pitch contour visualization.
        
        Args:
            audio_path: Path to audio file
            output_path: Path to save figure
            
        Returns:
            Path to saved figure or None
        """
        try:
            import librosa

            # Load audio
            y, sr = librosa.load(str(audio_path), sr=None)

            times, pitches = VoiceSpectralAnalyzer.compute_pitch_contour(y, sr)

            if len(pitches) == 0:
                return None

            fig, ax = plt.subplots(figsize=(12, 5), dpi=100)

            ax.plot(times, pitches, linewidth=2, color='#0984E3')
            ax.fill_between(times, pitches, alpha=0.3, color='#0984E3')

            # Add mean line
            mean_pitch = np.mean(pitches[pitches > 0])
            ax.axhline(mean_pitch, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_pitch:.1f} Hz')

            ax.set_xlabel('Time (seconds)', fontweight='bold')
            ax.set_ylabel('Frequency (Hz)', fontweight='bold')
            ax.set_title('Pitch Contour Over Time', fontsize=14, weight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()

            if output_path:
                plt.savefig(output_path, dpi=100, bbox_inches='tight')
                plt.close(fig)
                return output_path

            plt.close(fig)
            return None

        except Exception as e:
            print(f"Error visualizing pitch contour: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None

    @staticmethod
    def get_spectral_features(
        audio_path: Path,
    ) -> dict[str, float]:
        """
        Extract spectral features from audio.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with spectral features
        """
        try:
            import librosa

            y, sr = librosa.load(str(audio_path), sr=None)

            # Spectral centroids
            S = librosa.feature.melspectrogram(y=y, sr=sr)
            S_db = librosa.power_to_db(S, ref=np.max)
            cent = librosa.feature.spectral_centroid(S=S_db)[0]

            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)[0]

            # MFCC
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

            return {
                'spectral_centroid_mean': float(np.mean(cent)),
                'spectral_centroid_std': float(np.std(cent)),
                'zero_crossing_rate_mean': float(np.mean(zcr)),
                'zero_crossing_rate_std': float(np.std(zcr)),
                'mfcc_mean': float(np.mean(mfcc)),
            }

        except Exception as e:
            print(f"Error extracting spectral features: {e}")
            return {}
