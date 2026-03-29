"""
ARTHA AI — Video Engine
Generates short MP4 market summary videos using MoviePy.
Gracefully degrades if MoviePy or ffmpeg is unavailable.
"""

import os
import numpy as np
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("assets/generated_videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _try_moviepy_import():
    """Safely import MoviePy components."""
    try:
        from moviepy.editor import (
            VideoClip, TextClip, ColorClip,
            CompositeVideoClip, concatenate_videoclips,
            ImageClip
        )
        return True, {
            "VideoClip": VideoClip,
            "TextClip": TextClip,
            "ColorClip": ColorClip,
            "CompositeVideoClip": CompositeVideoClip,
            "concatenate": concatenate_videoclips,
            "ImageClip": ImageClip,
        }
    except Exception:
        return False, {}


def generate_price_chart_frame(t, close_series, width=1280, height=720):
    """Generate a single frame of an animated price chart."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from io import BytesIO
        from PIL import Image

        progress = min(1.0, t / 5.0)
        n_points = max(2, int(len(close_series) * progress))
        data = close_series[-n_points:]

        fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#161b22")

        x = np.arange(len(data))
        ax.plot(x, data.values, color="#00d4ff", linewidth=2.5)
        ax.fill_between(x, data.values, alpha=0.15, color="#00d4ff")

        ax.spines["bottom"].set_color("#21262d")
        ax.spines["left"].set_color("#21262d")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(colors="#e6edf3", labelsize=10)
        ax.xaxis.label.set_color("#e6edf3")
        ax.yaxis.label.set_color("#e6edf3")
        ax.grid(color="#21262d", linestyle="--", linewidth=0.5)

        plt.tight_layout(pad=0.5)
        buf = BytesIO()
        plt.savefig(buf, format="png", facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        img = Image.open(buf).convert("RGB")
        return np.array(img)

    except Exception:
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :, 2] = 30
        return frame


def generate_summary_video(
    symbol: str,
    signal: str,
    confidence: int,
    rsi: float,
    trend: str,
    close: float,
    close_series=None,
    duration: int = 8,
) -> dict:
    """
    Generate a short MP4 market summary video.
    Returns dict: {success, filepath, message}
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"artha_{symbol.replace('.NS', '')}_{timestamp}.mp4"
    filepath = OUTPUT_DIR / filename

    available, moviepy = _try_moviepy_import()

    if not available:
        return _fallback_video_report(symbol, signal, confidence, rsi, trend, close, filepath)

    try:
        return _generate_with_moviepy(
            moviepy, symbol, signal, confidence, rsi, trend, close,
            close_series, duration, filepath
        )
    except Exception as e:
        return _fallback_video_report(symbol, signal, confidence, rsi, trend, close, filepath, error=str(e))


def _generate_with_moviepy(moviepy, symbol, signal, confidence, rsi, trend, close, close_series, duration, filepath):
    """Inner function that uses MoviePy."""
    ColorClip = moviepy["ColorClip"]
    TextClip = moviepy["TextClip"]
    CompositeVideoClip = moviepy["CompositeVideoClip"]

    W, H = 1280, 720

    # Background
    bg = ColorClip(size=(W, H), color=(14, 17, 23), duration=duration)

    clips = [bg]

    def make_text(text, fontsize, color, pos, start=0, end=None):
        try:
            tc = TextClip(
                text, fontsize=fontsize, color=color,
                font="DejaVu-Sans-Bold", method="caption",
                size=(W - 100, None), align="West",
            )
            tc = tc.set_position(pos).set_start(start)
            if end:
                tc = tc.set_end(end)
            else:
                tc = tc.set_duration(duration - start)
            return tc
        except Exception:
            return None

    signal_color_map = {
        "STRONG_BUY": "lime",
        "BUY": "lime",
        "WATCH": "yellow",
        "HOLD": "white",
        "CAUTION": "orange",
        "AVOID": "red",
    }
    sig_color = signal_color_map.get(signal, "white")

    # Title
    t1 = make_text(f"ARTHA AI  |  NSE Market Intelligence", 32, "#00d4ff", ("center", 30), start=0.2)
    t2 = make_text(f"{symbol.replace('.NS', '')}", 72, "white", ("center", 100), start=0.5)
    t3 = make_text(f"CMP: ₹{close:.2f}", 40, "#aaaaaa", ("center", 185), start=0.8)
    t4 = make_text(f"SIGNAL: {signal}", 56, sig_color, ("center", 270), start=1.2)
    t5 = make_text(f"Confidence: {confidence}%   |   RSI: {rsi:.1f}   |   Trend: {trend}", 32, "#cccccc", ("center", 360), start=1.6)
    t6 = make_text(f"Powered by ARTHA AI  —  For Educational Purposes Only", 20, "#555555", ("center", H - 50), start=2.0)

    for t in [t1, t2, t3, t4, t5, t6]:
        if t is not None:
            clips.append(t)

    final = CompositeVideoClip(clips, size=(W, H))
    final = final.set_duration(duration)
    final.write_videofile(
        str(filepath),
        fps=24,
        codec="libx264",
        audio=False,
        verbose=False,
        logger=None,
    )

    return {
        "success": True,
        "filepath": str(filepath),
        "filename": filepath.name,
        "message": f"Video generated: {filepath.name}",
    }


def _fallback_video_report(symbol, signal, confidence, rsi, trend, close, filepath, error=None):
    """
    When MoviePy/ffmpeg is not available, generate a text summary file
    and inform the user gracefully.
    """
    txt_path = str(filepath).replace(".mp4", "_summary.txt")
    summary = f"""
ARTHA AI — Market Summary Report
=================================
Generated: {datetime.now().strftime('%d %b %Y, %H:%M IST')}

Stock   : {symbol}
CMP     : ₹{close:.2f}
Signal  : {signal}
Confidence: {confidence}%
RSI     : {rsi:.1f}
Trend   : {trend}

Note: Video generation requires MoviePy + FFmpeg.
      Install with: pip install moviepy && brew install ffmpeg (macOS)
      or: apt-get install ffmpeg (Linux)

This text summary was generated as a fallback.
"""
    try:
        with open(txt_path, "w") as f:
            f.write(summary)
    except Exception:
        pass

    return {
        "success": False,
        "filepath": txt_path,
        "filename": os.path.basename(txt_path),
        "message": (
            "📄 Video engine requires FFmpeg. A text summary was saved instead. "
            "Install FFmpeg to enable video generation."
        ),
        "error": error,
        "fallback_text": summary,
    }
