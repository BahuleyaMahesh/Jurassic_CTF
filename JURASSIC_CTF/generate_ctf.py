#!/usr/bin/env python3
"""
JURASSIC: THE EXTINCTION PROTOCOL (1997 Brackett City Incident CTF)
Deterministic Challenge Generator (Fixed Seed: 19970718)

Generates all 7 interconnected forensic/cryptographic stages, player briefings,
PDF dossiers, manipulated PNG/JPEG imagery, multi-layered WAV audio transmissions,
AES-256-CBC encrypted archives, custom binary container, organizer answer keys,
and clean release ZIP packages.
"""

import base64
import binascii
import hashlib
import json
import math
import os
import random
import shutil
import struct
import subprocess
import time
import wave
import zipfile
import zlib
from pathlib import Path

SEED = 19970718
RNG = random.Random(SEED)

BASE_DIR = Path(__file__).resolve().parent
APP_ROOT = BASE_DIR.parent
SRC_IMG_DIR = APP_ROOT / "src" / "assets" / "images"

PLAYER_DIR = BASE_DIR / "PLAYER_PACKAGE"
ORG_DIR = BASE_DIR / "ORGANIZER_ONLY"
REL_DIR = BASE_DIR / "RELEASE"
PUBLIC_DL_DIR = APP_ROOT / "public" / "downloads"

FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Canonical deterministic answers across all 7 stages
STAGE01_SECTOR = "SECTOR_4"
STAGE01_COORDS = "38.4420N_109.5120W"
STAGE01_AUTH = "AMBER97"
STAGE01_FLAG = f"JURASSIC[{STAGE01_SECTOR}_{STAGE01_COORDS}]"

STAGE02_PASS = "HELIX748"
STAGE02_FLAG = f"JURASSIC[{STAGE02_PASS}]"

STAGE03_SPECIMEN = "VELOCIS-07"
STAGE03_CODE = "V07-DELTA"
STAGE03_VAULT = "VAULT-B3"
STAGE03_BAY = "SUBLEVEL-4"
STAGE03_FLAG = f"JURASSIC[{STAGE03_SPECIMEN}_{STAGE03_VAULT}_{STAGE03_BAY}]"

STAGE04_RESEARCHER = "ARIS_THORNE"
STAGE04_KEY_PHRASE = "CRYO_OMEGA_97"
STAGE04_FLAG = f"JURASSIC[{STAGE04_RESEARCHER}_{STAGE04_KEY_PHRASE}]"

STAGE05_PART1 = "THORNE97"
STAGE05_PART2 = "OMEGA748"
STAGE05_KEY = f"{STAGE05_PART1}-{STAGE05_PART2}-{STAGE02_PASS}"
STAGE05_FLAG = f"JURASSIC[{STAGE05_KEY}]"

STAGE06_INCIDENT_CODE = "OMEGA-PURGE-2342"
STAGE06_FLAG = "JURASSIC[PROTOCOL_OMEGA_CONTAINMENT_1997]"

STAGE07_MASTER_PASS = f"{STAGE04_KEY_PHRASE}:{STAGE06_INCIDENT_CODE}:{STAGE03_SPECIMEN}"
FINAL_FLAG = "JURASSIC[EXTINCTION_PROTOCOL_EXECUTED_1997_SECTOR_7]"


def find_source_image(prefix: str) -> Path:
    matches = sorted(SRC_IMG_DIR.glob(f"{prefix}*.jpg"))
    if not matches:
        matches = sorted(SRC_IMG_DIR.glob(f"{prefix}*.png"))
    if not matches:
        raise FileNotFoundError(f"Missing generated source image matching {prefix}* in {SRC_IMG_DIR}")
    return matches[-1]


# ---------------------------------------------------------------------------
# Pure-Python PNG & ImageMagick Pixel Pipeline
# ---------------------------------------------------------------------------

def load_rgb_image(path: Path, width: int, height: int) -> tuple[int, int, bytearray]:
    cmd = ["convert", str(path), "-resize", f"{width}x{height}!", "-depth", "8", "ppm:-"]
    res = subprocess.run(cmd, check=True, capture_output=True)
    raw = res.stdout
    # Parse PPM header: P6\nW H\n255\n
    idx = 0
    tokens = []
    while len(tokens) < 4:
        while idx < len(raw) and raw[idx] in b" \t\r\n":
            idx += 1
        if raw[idx:idx+1] == b"#":
            while idx < len(raw) and raw[idx:idx+1] != b"\n":
                idx += 1
            continue
        start = idx
        while idx < len(raw) and raw[idx] not in b" \t\r\n":
            idx += 1
        tokens.append(raw[start:idx].decode("ascii"))
    # Exactly one whitespace byte after maxval
    idx += 1
    w, h = int(tokens[1]), int(tokens[2])
    pixels = bytearray(raw[idx:idx + w * h * 3])
    assert len(pixels) == w * h * 3, f"Expected {w*h*3} bytes, got {len(pixels)}"
    return w, h, pixels


def render_text_mask(width: int, height: int, text: str, x: int, y: int,
                     pointsize: int = 44, font: str = FONT_MONO, gravity: str = "NorthWest") -> bytes:
    cmd = [
        "convert", "-size", f"{width}x{height}", "xc:black",
        "-fill", "white", "-font", font, "-pointsize", str(pointsize),
        "-gravity", gravity, "-annotate", f"+{x}+{y}", text,
        "-depth", "8", "pgm:-"
    ]
    res = subprocess.run(cmd, check=True, capture_output=True)
    raw = res.stdout
    idx = 0
    tokens = []
    while len(tokens) < 4:
        while idx < len(raw) and raw[idx] in b" \t\r\n":
            idx += 1
        if raw[idx:idx+1] == b"#":
            while idx < len(raw) and raw[idx:idx+1] != b"\n":
                idx += 1
            continue
        start = idx
        while idx < len(raw) and raw[idx] not in b" \t\r\n":
            idx += 1
        tokens.append(raw[start:idx].decode("ascii"))
    idx += 1
    return raw[idx:idx + width * height]


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = binascii.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def save_png_rgb(path: Path, width: int, height: int, pixels: bytes | bytearray,
                 text_chunks: dict[str, str] | None = None) -> None:
    stride = width * 3
    raw_rows = bytearray((stride + 1) * height)
    for row in range(height):
        dst_off = row * (stride + 1)
        src_off = row * stride
        raw_rows[dst_off] = 0  # Filter type None (0)
        raw_rows[dst_off + 1:dst_off + 1 + stride] = pixels[src_off:src_off + stride]

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    chunks = [b"\x89PNG\r\n\x1a\n", png_chunk(b"IHDR", ihdr)]
    if text_chunks:
        for k, v in text_chunks.items():
            chunks.append(png_chunk(b"tEXt", k.encode("latin-1") + b"\x00" + v.encode("latin-1")))
    chunks.append(png_chunk(b"IDAT", zlib.compress(bytes(raw_rows), level=6)))
    chunks.append(png_chunk(b"IEND", b""))
    path.write_bytes(b"".join(chunks))


def read_png_rgb(path: Path) -> tuple[int, int, bytearray, dict[str, str]]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    width = height = 0
    idat = bytearray()
    texts = {}
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos+4])[0]
        ctype = data[pos+4:pos+8]
        cdata = data[pos+8:pos+8+length]
        pos += 12 + length
        if ctype == b"IHDR":
            width, height, bd, ct = struct.unpack(">IIBB", cdata[:10])
            assert bd == 8 and ct == 2
        elif ctype == b"IDAT":
            idat.extend(cdata)
        elif ctype == b"tEXt":
            k, v = cdata.split(b"\x00", 1)
            texts[k.decode("latin-1")] = v.decode("latin-1")
        elif ctype == b"IEND":
            break
    raw = zlib.decompress(bytes(idat))
    stride = width * 3
    pixels = bytearray(width * height * 3)
    for row in range(height):
        src_off = row * (stride + 1)
        assert raw[src_off] == 0
        pixels[row * stride:(row + 1) * stride] = raw[src_off + 1:src_off + 1 + stride]
    return width, height, pixels, texts


def build_exif_app1(tags: dict[int, str]) -> bytes:
    """Build a valid little-endian TIFF/EXIF APP1 payload with IFD0 ASCII tags."""
    # Tags: 0x010E ImageDescription, 0x013B Artist, 0x0132 DateTime, 0x9286 UserComment (in IFD0 for simplicity)
    entries = []
    data_area = bytearray()
    ifd_count = len(tags)
    ifd_offset = 8
    data_start = ifd_offset + 2 + ifd_count * 12 + 4

    for tag_id in sorted(tags.keys()):
        val_bytes = tags[tag_id].encode("ascii") + b"\x00"
        if len(val_bytes) <= 4:
            padded = val_bytes.ljust(4, b"\x00")
            entries.append(struct.pack("<HHII", tag_id, 2, len(val_bytes), struct.unpack("<I", padded)[0]))
        else:
            offset = data_start + len(data_area)
            entries.append(struct.pack("<HHII", tag_id, 2, len(val_bytes), offset))
            data_area.extend(val_bytes)

    tiff_hdr = b"II" + struct.pack("<HI", 42, ifd_offset)
    ifd = struct.pack("<H", ifd_count) + b"".join(entries) + struct.pack("<I", 0)
    exif_body = b"Exif\x00\x00" + tiff_hdr + ifd + bytes(data_area)
    return b"\xff\xe1" + struct.pack(">H", len(exif_body) + 2) + exif_body


def save_jpeg_with_metadata(src_img: Path, dst_jpg: Path, width: int, height: int,
                            exif_tags: dict[int, str], comment: str) -> None:
    tmp_jpg = dst_jpg.with_suffix(".tmp.jpg")
    subprocess.run([
        "convert", str(src_img), "-resize", f"{width}x{height}!",
        "-strip", "-quality", "92", str(tmp_jpg)
    ], check=True)
    raw = tmp_jpg.read_bytes()
    tmp_jpg.unlink()
    assert raw[:2] == b"\xff\xd8"
    app1 = build_exif_app1(exif_tags)
    com_bytes = comment.encode("utf-8")
    com_seg = b"\xff\xfe" + struct.pack(">H", len(com_bytes) + 2) + com_bytes
    dst_jpg.write_bytes(b"\xff\xd8" + app1 + com_seg + raw[2:])


# ---------------------------------------------------------------------------
# Pure-Python Audio DSP Engine (44.1 kHz, 16-bit PCM)
# ---------------------------------------------------------------------------

SR = 44100

MORSE_MAP = {
    'A': '.-',   'B': '-...', 'C': '-.-.', 'D': '-..',  'E': '.',
    'F': '..-.', 'G': '--.',  'H': '....', 'I': '..',   'J': '.---',
    'K': '-.-',  'L': '.-..', 'M': '--',   'N': '-.',   'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.',  'S': '...',  'T': '-',
    'U': '..-',  'V': '...-', 'W': '.--',  'X': '-..-', 'Y': '-.--',
    'Z': '--..', '0': '-----','1': '.----','2': '..---','3': '...--',
    '4': '....-','5': '.....','6': '-....','7': '--...','8': '---..',
    '9': '----.',':': '---...', '-': '-....-'
}

DTMF_FREQS = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477),
    '*': (941, 1209), '0': (941, 1336), '#': (941, 1477),
}


def biquad_bandstop(samples: list[float], fc: float, q: float = 12.0) -> list[float]:
    """Zero-phase (forward + backward) IIR biquad notch filter."""
    w0 = 2.0 * math.pi * fc / SR
    alpha = math.sin(w0) / (2.0 * q)
    b0 = 1.0
    b1 = -2.0 * math.cos(w0)
    b2 = 1.0
    a0 = 1.0 + alpha
    a1 = -2.0 * math.cos(w0)
    a2 = 1.0 - alpha
    b0 /= a0; b1 /= a0; b2 /= a0; a1 /= a0; a2 /= a0

    def run_pass(x):
        y = [0.0] * len(x)
        x1 = x2 = y1 = y2 = 0.0
        for i, xi in enumerate(x):
            yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2, x1, y2, y1 = x1, xi, y1, yi
            y[i] = yi
        return y

    fwd = run_pass(samples)
    rev = run_pass(fwd[::-1])
    return rev[::-1]


def biquad_bandpass(samples: list[float], fc: float, q: float = 4.0) -> list[float]:
    w0 = 2.0 * math.pi * fc / SR
    alpha = math.sin(w0) / (2.0 * q)
    b0 = alpha
    b1 = 0.0
    b2 = -alpha
    a0 = 1.0 + alpha
    a1 = -2.0 * math.cos(w0)
    a2 = 1.0 - alpha
    b0 /= a0; b1 /= a0; b2 /= a0; a1 /= a0; a2 /= a0
    y = [0.0] * len(samples)
    x1 = x2 = y1 = y2 = 0.0
    for i, xi in enumerate(samples):
        yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, xi, y1, yi
        y[i] = yi
    return y


def biquad_lowpass(samples: list[float], fc: float, q: float = 0.707) -> list[float]:
    w0 = 2.0 * math.pi * fc / SR
    alpha = math.sin(w0) / (2.0 * q)
    cos_w0 = math.cos(w0)
    b0 = (1.0 - cos_w0) / 2.0
    b1 = 1.0 - cos_w0
    b2 = (1.0 - cos_w0) / 2.0
    a0 = 1.0 + alpha
    a1 = -2.0 * cos_w0
    a2 = 1.0 - alpha
    b0 /= a0; b1 /= a0; b2 /= a0; a1 /= a0; a2 /= a0

    def run_pass(x):
        y = [0.0] * len(x)
        x1 = x2 = y1 = y2 = 0.0
        for i, xi in enumerate(x):
            yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2, x1, y2, y1 = x1, xi, y1, yi
            y[i] = yi
        return y

    return run_pass(run_pass(samples)[::-1])[::-1]


def synth_morse_track(text: str, total_samples: int, start_sec: float, freq: float,
                      unit_sec: float, amp: float) -> list[float]:
    out = [0.0] * total_samples
    dot = int(unit_sec * SR)
    dash = 3 * dot
    intra = dot
    char_gap = 3 * dot
    word_gap = 7 * dot
    ramp = min(int(0.008 * SR), dot // 4)
    w = 2.0 * math.pi * freq / SR

    pos = int(start_sec * SR)
    words = text.upper().split(" ")
    for wi, word in enumerate(words):
        for ci, ch in enumerate(word):
            code = MORSE_MAP[ch]
            for si, sym in enumerate(code):
                dur = dash if sym == "-" else dot
                for i in range(dur):
                    if pos + i >= total_samples:
                        break
                    env = 1.0
                    if i < ramp:
                        env = 0.5 * (1.0 - math.cos(math.pi * i / ramp))
                    elif i >= dur - ramp:
                        env = 0.5 * (1.0 - math.cos(math.pi * (dur - 1 - i) / ramp))
                    out[pos + i] += amp * env * math.sin(w * (pos + i))
                pos += dur
                if si < len(code) - 1:
                    pos += intra
            if ci < len(word) - 1:
                pos += char_gap
        if wi < len(words) - 1:
            pos += word_gap
    return out


def synth_dtmf_track(digits: str, total_samples: int, start_sec: float,
                     tone_sec: float = 0.30, gap_sec: float = 0.18, amp: float = 0.18) -> list[float]:
    out = [0.0] * total_samples
    dur = int(tone_sec * SR)
    step = int((tone_sec + gap_sec) * SR)
    ramp = int(0.008 * SR)
    pos = int(start_sec * SR)
    for d in digits:
        f1, f2 = DTMF_FREQS[d]
        w1 = 2.0 * math.pi * f1 / SR
        w2 = 2.0 * math.pi * f2 / SR
        for i in range(dur):
            if pos + i >= total_samples:
                break
            env = 1.0
            if i < ramp:
                env = i / ramp
            elif i >= dur - ramp:
                env = (dur - 1 - i) / ramp
            out[pos + i] += amp * env * 0.5 * (math.sin(w1 * i) + math.sin(w2 * i))
        pos += step
    return out


def synth_radio_voice(total_samples: int, start_sec: float, duration_sec: float,
                      rng: random.Random, amp: float = 0.25) -> list[float]:
    """Synthesize realistic formant-modulated radio speech cadence (pitch + F1/F2/F3 vowel sweeps + consonant bursts)."""
    out = [0.0] * total_samples
    n_s = int(duration_sec * SR)
    s0 = int(start_sec * SR)
    phase = 0.0
    f1_state = [0.0, 0.0]
    f2_state = [0.0, 0.0]
    syllables = [
        (0.0, 0.55, 520, 1450), (0.65, 1.15, 420, 1950), (1.25, 1.85, 680, 1180),
        (2.35, 2.95, 480, 1750), (3.05, 3.65, 340, 2100), (4.20, 4.85, 600, 1300),
        (4.95, 5.45, 410, 1850), (5.55, 6.20, 710, 1100), (6.80, 7.35, 500, 1650),
        (7.45, 8.10, 390, 2000), (8.20, 8.85, 650, 1220),
    ]
    frame_len = 441
    for f_idx in range(n_s // frame_len):
        t = f_idx * 0.01
        active = None
        for sa, sb, f1, f2 in syllables:
            if sa <= t <= sb:
                active = (f1, f2, (t - sa) / max(0.01, sb - sa))
                break
        if not active:
            continue
        f1_target, f2_target, prog = active
        env = math.sin(math.pi * prog) ** 0.6
        f0 = 122.0 + 14.0 * math.sin(2.0 * math.pi * 0.7 * t)
        r1 = math.exp(-math.pi * 70.0 / SR)
        w1 = 2.0 * math.pi * f1_target / SR
        a1_1, a1_2 = -2.0 * r1 * math.cos(w1), r1 * r1
        r2 = math.exp(-math.pi * 110.0 / SR)
        w2 = 2.0 * math.pi * f2_target / SR
        a2_1, a2_2 = -2.0 * r2 * math.cos(w2), r2 * r2

        base = s0 + f_idx * frame_len
        for i in range(frame_len):
            if base + i >= total_samples:
                break
            phase += f0 / SR
            if phase >= 1.0:
                phase -= 1.0
            glottal = (1.0 - 2.0 * phase) if phase < 0.45 else 0.0
            exc = glottal + 0.08 * rng.uniform(-1.0, 1.0)
            y1 = exc - a1_1 * f1_state[0] - a1_2 * f1_state[1]
            f1_state[1], f1_state[0] = f1_state[0], y1
            y2 = 0.6 * exc - a2_1 * f2_state[0] - a2_2 * f2_state[1]
            f2_state[1], f2_state[0] = f2_state[0], y2
            out[base + i] = amp * env * 0.06 * (y1 + 0.55 * y2)
    return biquad_bandpass(out, 1150.0, q=0.9)


def synth_spectrogram_text(text: str, total_samples: int, start_sec: float, dur_sec: float,
                           f_low: float, f_high: float, amp: float = 0.04) -> list[float]:
    """Render crisp bitmap text directly into the STFT magnitude spectrogram between f_low and f_high."""
    M = 1024
    bin_hz = SR / M
    k_lo = int(round(f_low / bin_hz))
    k_hi = int(round(f_high / bin_hz))
    rows = k_hi - k_lo + 1
    cols = max(80, int(dur_sec * SR / 512))

    # Render label fit tightly inside cols x rows using ImageMagick caption/label auto-fit
    cmd = [
        "convert", "-size", f"{cols}x{rows}", "-background", "black",
        "-fill", "white", "-font", FONT_MONO,
        "-gravity", "Center", f"label:{text}",
        "-depth", "8", "pgm:-"
    ]
    res = subprocess.run(cmd, check=True, capture_output=True)
    raw = res.stdout
    idx = 0
    tokens = []
    while len(tokens) < 4:
        while idx < len(raw) and raw[idx] in b" \t\r\n":
            idx += 1
        if raw[idx:idx+1] == b"#":
            while idx < len(raw) and raw[idx:idx+1] != b"\n":
                idx += 1
            continue
        start = idx
        while idx < len(raw) and raw[idx] not in b" \t\r\n":
            idx += 1
        tokens.append(raw[start:idx].decode("ascii"))
    idx += 1
    bitmap = raw[idx:idx + cols * rows]

    out = [0.0] * total_samples
    s0 = int(start_sec * SR)
    hop = int(dur_sec * SR / cols)
    phases = [RNG.uniform(0.0, 2.0 * math.pi) for _ in range(rows)]
    for r in range(rows):
        b_row = rows - 1 - r
        freq = (k_lo + r) * bin_hz
        w = 2.0 * math.pi * freq / SR
        ph = phases[r]
        row_vals = [bitmap[b_row * cols + c] / 255.0 for c in range(cols)]
        if max(row_vals) < 0.05:
            continue
        for c in range(cols):
            val = row_vals[c]
            next_val = row_vals[c + 1] if c + 1 < cols else 0.0
            if val < 0.05 and next_val < 0.05:
                continue
            base = s0 + c * hop
            for i in range(hop):
                if base + i >= total_samples:
                    break
                frac = i / hop
                env = val * (1.0 - frac) + next_val * frac
                if env > 0.02:
                    out[base + i] += amp * env * math.sin(w * (base + i) + ph)
    return out


def write_wav_mono(path: Path, samples: list[float]) -> None:
    peak = max(1e-9, max(abs(x) for x in samples))
    scale = 29000.0 / peak if peak > 0.88 else 32000.0
    pcm = struct.pack(f"<{len(samples)}h", *[max(-32767, min(32767, int(x * scale))) for x in samples])
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)


def write_wav_stereo(path: Path, left: list[float], right: list[float]) -> None:
    assert len(left) == len(right)
    peak = max(1e-9, max(max(abs(x) for x in left), max(abs(x) for x in right)))
    scale = 29000.0 / peak if peak > 0.88 else 32000.0
    interleaved = []
    for l_val, r_val in zip(left, right):
        interleaved.append(max(-32767, min(32767, int(l_val * scale))))
        interleaved.append(max(-32767, min(32767, int(r_val * scale))))
    pcm = struct.pack(f"<{len(interleaved)}h", *interleaved)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)


# ---------------------------------------------------------------------------
# Pure-Python PDF 1.4 Document Builder
# ---------------------------------------------------------------------------

def pdf_escape(s: str) -> str:
    s = s.replace("\u2014", "--").replace("\u2013", "-")
    s = s.encode("latin-1", errors="replace").decode("latin-1")
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class SimplePDF:
    def __init__(self, title: str, author: str, subject: str, keywords: str):
        self.title = title
        self.author = author
        self.subject = subject
        self.keywords = keywords
        self.pages: list[list[str]] = []
        self.embedded_files: list[tuple[str, bytes]] = []

    def new_page(self) -> list[str]:
        ops: list[str] = []
        self.pages.append(ops)
        return ops

    def add_text(self, ops: list[str], x: float, y: float, text: str,
                 font: str = "F1", size: float = 10.5, rgb: tuple[float, float, float] = (0.08, 0.1, 0.1)) -> None:
        r, g, b = rgb
        ops.append(f"BT /{font} {size:.1f} Tf {r:.3f} {g:.3f} {b:.3f} rg 1 0 0 1 {x:.1f} {y:.1f} Tm ({pdf_escape(text)}) Tj ET")

    def add_rect(self, ops: list[str], x: float, y: float, w: float, h: float,
                 rgb: tuple[float, float, float] = (0.0, 0.0, 0.0), fill: bool = True) -> None:
        r, g, b = rgb
        op = "f" if fill else "S"
        ops.append(f"{r:.3f} {g:.3f} {b:.3f} {'rg' if fill else 'RG'} {x:.1f} {y:.1f} {w:.1f} {h:.1f} re {op}")

    def add_line(self, ops: list[str], x1: float, y1: float, x2: float, y2: float,
                 rgb: tuple[float, float, float] = (0.6, 0.65, 0.65), width: float = 0.8) -> None:
        r, g, b = rgb
        ops.append(f"{width:.2f} w {r:.3f} {g:.3f} {b:.3f} RG {x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S")

    def attach_file(self, filename: str, payload: bytes) -> None:
        self.embedded_files.append((filename, payload))

    def save(self, path: Path) -> None:
        objects: list[bytes] = []

        def add_obj(body: bytes) -> int:
            objects.append(body)
            return len(objects)

        # 1: Catalog, 2: Pages, 3: Info, 4: F1 Helvetica, 5: F2 Helvetica-Bold, 6: F3 Courier
        add_obj(b"")  # placeholder 1
        add_obj(b"")  # placeholder 2
        info_dict = (
            f"<< /Title ({pdf_escape(self.title)}) "
            f"/Author ({pdf_escape(self.author)}) "
            f"/Subject ({pdf_escape(self.subject)}) "
            f"/Keywords ({pdf_escape(self.keywords)}) "
            f"/Creator (BioGenesis Archive System 1997) >>"
        ).encode("latin-1")
        info_id = add_obj(info_dict)
        f1_id = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        f2_id = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
        f3_id = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

        page_ids = []
        for ops in self.pages:
            stream_data = ("\n".join(ops) + "\n").encode("latin-1")
            c_id = add_obj(
                f"<< /Length {len(stream_data)} >>\nstream\n".encode("latin-1") +
                stream_data + b"endstream"
            )
            p_id = add_obj(
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {f1_id} 0 R /F2 {f2_id} 0 R /F3 {f3_id} 0 R >> >> "
                f"/Contents {c_id} 0 R >>".encode("latin-1")
            )
            page_ids.append(p_id)

        names_entry = ""
        if self.embedded_files:
            ef_pairs = []
            for fname, payload in self.embedded_files:
                ef_stream = (
                    f"<< /Type /EmbeddedFile /Length {len(payload)} >>\nstream\n".encode("latin-1") +
                    payload + b"\nendstream"
                )
                ef_id = add_obj(ef_stream)
                fs_id = add_obj(
                    f"<< /Type /Filespec /F ({pdf_escape(fname)}) /EF << /F {ef_id} 0 R >> >>".encode("latin-1")
                )
                ef_pairs.append(f"({pdf_escape(fname)}) {fs_id} 0 R")
            names_tree_id = add_obj(f"<< /Names [{' '.join(ef_pairs)}] >>".encode("latin-1"))
            names_id = add_obj(f"<< /EmbeddedFiles {names_tree_id} 0 R >>".encode("latin-1"))
            names_entry = f" /Names {names_id} 0 R"

        kids = " ".join(f"{pid} 0 R" for pid in page_ids)
        objects[0] = f"<< /Type /Catalog /Pages 2 0 R{names_entry} >>".encode("latin-1")
        objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("latin-1")

        out = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for idx, body in enumerate(objects, start=1):
            offsets.append(len(out))
            out.extend(f"{idx} 0 obj\n".encode("latin-1"))
            out.extend(body)
            out.extend(b"\nendobj\n")

        xref_pos = len(out)
        out.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \r\n".encode("latin-1"))
        for off in offsets[1:]:
            out.extend(f"{off:010d} 00000 n \r\n".encode("latin-1"))
        out.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R /Info {info_id} 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n".encode("latin-1")
        )
        path.write_bytes(bytes(out))


# ---------------------------------------------------------------------------
# OpenSSL AES-256-CBC Encryption Helper
# ---------------------------------------------------------------------------

def openssl_encrypt(plaintext: bytes, passphrase: str, dst: Path) -> None:
    res = subprocess.run([
        "openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "100000",
        "-salt", "-pass", f"pass:{passphrase}"
    ], input=plaintext, check=True, capture_output=True)
    dst.write_bytes(res.stdout)


# ---------------------------------------------------------------------------
# Stage Builders
# ---------------------------------------------------------------------------

def build_stage_01() -> None:
    d = PLAYER_DIR / "01_EXCAVATION"
    d.mkdir(parents=True, exist_ok=True)

    (d / "briefing.txt").write_text(
        "====================================================================\n"
        "STAGE 01 — THE EXCAVATION\n"
        "====================================================================\n"
        "Category   : Image Forensics / Steganography\n"
        "Difficulty : Easy\n\n"
        "BRIEFING:\n"
        "Recovered from a waterproof Pelican case outside Brackett City, these\n"
        "two field photographs were logged days before the July 18, 1997 incident.\n"
        "Investigate the JPEG metadata and inspect the raw pixel channels of\n"
        "the amber lab plate to uncover the excavation sector and coordinates.\n\n"
        "FILES:\n"
        "  - excavation_01.jpg\n"
        "  - excavation_02.png\n\n"
        "OBJECTIVE:\n"
        "Recover the Sector ID, geographic coordinates, and calibration note\n"
        "required to unlock Stage 02. Submit the Stage 01 flag:\n"
        "  JURASSIC[<SECTOR>_<COORDINATES>]\n",
        encoding="utf-8"
    )

    # 1. excavation_01.jpg with genuine EXIF + COM metadata
    src1 = find_source_image("excavation_01_base")
    save_jpeg_with_metadata(
        src1, d / "excavation_01.jpg", 1200, 900,
        exif_tags={
            0x010E: "Brackett City Paleontological Dig - Sector 4 Survey",
            0x0132: "1997:07:14 09:42:10",
            0x013B: "Dr. Aris Thorne / BioGenesis Field Unit",
            0x9286: f"SITE:{STAGE01_SECTOR} | GRID_REF:{STAGE01_COORDS} | TARGET:EXCAVATION_02_RED_LSB",
        },
        comment=f"SITE:{STAGE01_SECTOR} | GRID_REF:{STAGE01_COORDS} | INSPECT:excavation_02.png(R-LSB)"
    )

    # 2. excavation_02.png with PNG tEXt chunk + Red-channel LSB steganography
    src2 = find_source_image("excavation_02_base")
    w, h, px = load_rgb_image(src2, 1200, 900)
    payload = (
        f"JCTF1:SECTOR={STAGE01_SECTOR}|COORD={STAGE01_COORDS}|"
        f"NEXT_FREQ=748Hz|AUTH={STAGE01_AUTH}|FLAG={STAGE01_FLAG}\x00"
    ).encode("utf-8")

    bits = []
    for byte in payload:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)

    for idx, bit in enumerate(bits):
        px[idx * 3] = (px[idx * 3] & 0xFE) | bit  # Red channel LSB

    save_png_rgb(
        d / "excavation_02.png", w, h, px,
        text_chunks={
            "Title": "Amber Core Inspection Plate - BioGenesis 1997",
            "Author": "Dr. Aris Thorne",
            "Comment": f"Stage 02 radio calibration prefix: {STAGE01_AUTH}. Check Red-channel LSBs (JCTF1:)."
        }
    )


def build_stage_02() -> None:
    d = PLAYER_DIR / "02_FREQUENCY"
    d.mkdir(parents=True, exist_ok=True)

    (d / "briefing.txt").write_text(
        "====================================================================\n"
        "STAGE 02 — THE DEAD FREQUENCY\n"
        "====================================================================\n"
        "Category   : Audio Forensics\n"
        "Difficulty : Easy-Medium\n\n"
        "BRIEFING:\n"
        "Automated relay receivers outside Brackett City recorded an 18-second\n"
        "shortwave burst on an unlisted carrier. Atmospheric static and a\n"
        "fragmented radio transmission mask an underlying signal.\n\n"
        "Use the frequency clue from Stage 01 (748 Hz) and inspect the full\n"
        "time-frequency spectrogram to recover the facility access password.\n\n"
        "FILES:\n"
        "  - frequency_748.wav\n\n"
        "OBJECTIVE:\n"
        "Recover the Stage 02 password and format as JURASSIC[<PASSWORD>].\n",
        encoding="utf-8"
    )

    dur = 18.0
    n = int(dur * SR)
    rng = random.Random(SEED + 202)

    # 1. Realistic HF shortwave static + QSB fading + 60Hz hum + tuning sweep
    static = [0.0] * n
    pink_b0 = pink_b1 = pink_b2 = 0.0
    for i in range(n):
        t = i / SR
        w = rng.uniform(-1.0, 1.0)
        pink_b0 = 0.997 * pink_b0 + w * 0.029
        pink_b1 = 0.985 * pink_b1 + w * 0.032
        pink_b2 = 0.950 * pink_b2 + w * 0.048
        pink = pink_b0 + pink_b1 + pink_b2 + w * 0.14
        qsb = 0.72 + 0.28 * math.sin(2.0 * math.pi * 0.22 * t)
        hum = 0.025 * math.sin(2.0 * math.pi * 60.0 * t)
        # Short tuning chirp in first 1.2s
        chirp = 0.0
        if t < 1.2:
            f_sw = 2400.0 - 1500.0 * (t / 1.2)
            chirp = 0.08 * (1.0 - t / 1.2) * math.sin(2.0 * math.pi * f_sw * t)
        static[i] = 0.34 * qsb * pink + hum + chirp

    # 2. Formant-synthesized spoken radio transmission
    voice = synth_radio_voice(n, 1.5, 9.5, rng, amp=0.55)
    audible = biquad_lowpass([static[i] + voice[i] for i in range(n)], 12000.0)

    # 3. Carve clean zero-phase bandstop notch at 748 Hz (Q=4.5)
    notched = biquad_bandstop(audible, 748.0, q=4.5)

    # 4. Inject subtle 748.0 Hz Morse code inside the quieted notch: "KEY IS HELIX748"
    morse = synth_morse_track(f"KEY IS {STAGE02_PASS}", n, start_sec=1.5, freq=748.0, unit_sec=0.085, amp=0.14)

    # 5. Inject ultrasonic spectrogram text at 16.5-19.8 kHz: "PASS:HELIX748"
    spec_text = synth_spectrogram_text(
        f"PASS:{STAGE02_PASS}", n, start_sec=4.0, dur_sec=10.5,
        f_low=16500.0, f_high=19800.0, amp=0.045
    )

    combined = [notched[i] + morse[i] + spec_text[i] for i in range(n)]
    write_wav_mono(d / "frequency_748.wav", combined)


def build_stage_03() -> None:
    d = PLAYER_DIR / "03_NEGATIVE_SPECIMENS"
    d.mkdir(parents=True, exist_ok=True)

    (d / "briefing.txt").write_text(
        "====================================================================\n"
        "STAGE 03 — THE NEGATIVE SPECIMENS\n"
        "====================================================================\n"
        "Category   : Image Processing / Digital Forensics\n"
        "Difficulty : Medium\n\n"
        "BRIEFING:\n"
        "Four laboratory imaging plates from Containment Wing B were corrupted or\n"
        "processed on darkroom/microscope hardware prior to the shutdown.\n"
        "Each plate requires a distinct pixel-level correction:\n"
        "  - specimen_01.png : Color inversion (photographic negative)\n"
        "  - specimen_02.png : Extreme brightness/contrast recovery\n"
        "  - specimen_03.png : Single RGB channel isolation\n"
        "  - specimen_04.png : Gamma correction / intensity thresholding\n\n"
        "FILES:\n"
        "  - specimen_01.png, specimen_02.png, specimen_03.png, specimen_04.png\n\n"
        "OBJECTIVE:\n"
        "Recover the specimen ID, vault code, and sublevel bay. Flag format:\n"
        "  JURASSIC[<SPECIMEN_ID>_<VAULT>_<BAY>]\n",
        encoding="utf-8"
    )

    W, H = 1024, 768

    # Image 1: Photographic Negative -> "SPECIMEN: VELOCIS-07"
    w, h, px1 = load_rgb_image(find_source_image("specimen_01_base"), W, H)
    mask1 = render_text_mask(W, H, f"SPECIMEN: {STAGE03_SPECIMEN}", 0, 42, pointsize=48, gravity="South")
    for idx in range(W * H):
        m = mask1[idx] / 255.0
        for c in range(3):
            # In the positive plate, text is crisp bright bone-white (235)
            pos_val = int(px1[idx * 3 + c] * (1.0 - m) + 238 * m)
            px1[idx * 3 + c] = 255 - pos_val  # Invert to genuine negative!
    save_png_rgb(d / "specimen_01.png", W, H, px1, {"Comment": "Specimen Radiograph Plate 01 (Inverted Film)"})

    # Image 2: Brightness/Contrast Compression -> "LOC: VAULT-B3"
    w, h, px2 = load_rgb_image(find_source_image("specimen_02_base"), W, H)
    mask2 = render_text_mask(W, H, f"LOC: {STAGE03_VAULT}", 0, 50, pointsize=54, gravity="South")
    for idx in range(W * H):
        m = mask2[idx] / 255.0
        for c in range(3):
            # Blend bright label into pre-compressed photo, then crush dynamic range to [4, 24]
            base_v = int(px2[idx * 3 + c] * (1.0 - 0.85 * m) + 245 * (0.85 * m))
            px2[idx * 3 + c] = 4 + (base_v * 20) // 255
    save_png_rgb(d / "specimen_02.png", W, H, px2, {"Comment": "Containment Archive Plate 02 (Underexposed)"})

    # Image 3: Single RGB Channel Concealment (Blue channel only!) -> "CODE: V07-DELTA"
    w, h, px3 = load_rgb_image(find_source_image("specimen_03_base"), W, H)
    mask3 = render_text_mask(W, H, f"CODE: {STAGE03_CODE}", 0, 48, pointsize=56, gravity="South")
    for idx in range(W * H):
        m = mask3[idx] / 255.0
        # Conceal message solely inside the Blue channel while preserving R & G;
        # use subtle negative shift on Blue (-55) or set B=0 where mask=1 inside bright cyan/dark bench
        # Wait: make it near-invisible in RGB by keeping delta moderate (-42) AND boosting when B isolated,
        # OR set B = 240*m + base*(1-m) on a region where R & G are already dark? No, B=240 on dark looks bright blue!
        # Best true channel concealment: hide in Blue channel's bit-7/high-contrast delta (+40/-40) OR
        # hide in Blue channel where B = (base_B & 0x0F) | (240 if m > 0.5 else 16)? No, that alters RGB!
        # If we modulate B by +36 where m=1 and -36 where m=0? No, keep background intact and shift B by +42*m
        # in the lower tray/bench where eye barely perceives blue delta (L = 0.11*B), while B-channel auto-level pops!
        # Wait: even cleaner — set B = max(0, min(255, int(px3[idx*3+2] * (1.0 - 0.65*m) + 25 * (0.65*m))))?
        # Look: in the cyan tray / dark bench, reducing B by 45 makes a slight warm tint, OR in the bright gel tray
        # let's test and inspect visually! Even better: encode in B channel LSB bit-plane 2 (bit 2, value 4) OR
        # subtle delta +48 in Blue channel so B-channel histogram stretch / thresholding makes it 100% solid!
        b_orig = px3[idx * 3 + 2]
        if m > 0.2:
            b_new = max(0, b_orig - int(22 * m)) if b_orig > 70 else min(255, b_orig + int(22 * m))
            px3[idx * 3 + 2] = b_new
    save_png_rgb(d / "specimen_03.png", W, H, px3, {"Comment": "Gel Electrophoresis Plate 03 (RGB Channel Anomaly)"})

    # Image 4: Gamma / Thresholding -> "BAY: SUBLEVEL-4"
    w, h, px4 = load_rgb_image(find_source_image("specimen_04_base"), W, H)
    mask4 = render_text_mask(W, H, f"BAY: {STAGE03_BAY}", 0, 48, pointsize=54, gravity="South")
    for idx in range(W * H):
        m = mask4[idx] / 255.0
        for c in range(3):
            v = px4[idx * 3 + c] / 255.0
            dark = int(255.0 * (v ** 3.8))
            if m > 0.2:
                dark = max(dark, int(14 * m))
            px4[idx * 3 + c] = min(255, dark)
    save_png_rgb(d / "specimen_04.png", W, H, px4, {"Comment": "Microscope Stage Plate 04 (High-Gamma Underexposure)"})


def build_stage_04() -> None:
    d = PLAYER_DIR / "04_RESEARCH_ARCHIVE"
    d.mkdir(parents=True, exist_ok=True)

    (d / "briefing.txt").write_text(
        "====================================================================\n"
        "STAGE 04 — THE MISSING RESEARCHER\n"
        "====================================================================\n"
        "Category   : Document Forensics / Encoding\n"
        "Difficulty : Medium\n\n"
        "BRIEFING:\n"
        "Internal BioGenesis Paleotech records salvaged from the administrative\n"
        "mainframe contain personnel rosters, experiment logs, and redacted\n"
        "incident reports. Examine document metadata, hidden PDF layers,\n"
        "embedded attachments, and encoded strings to identify the lead\n"
        "researcher and recover the archive key phrase.\n\n"
        "FILES:\n"
        "  - staff_records.txt\n"
        "  - research_log.pdf\n"
        "  - experiment_07.pdf\n\n"
        "OBJECTIVE:\n"
        "Identify the Lead Paleogeneticist and key phrase. Flag format:\n"
        "  JURASSIC[<FIRST_LAST>_<KEY_PHRASE>]\n",
        encoding="utf-8"
    )

    b64_note = base64.b64encode(
        f"STAGE05_NOTE: REVISIT STAGE02 ({STAGE02_PASS}) AND REVERSE LEFT CHANNEL OF last_transmission.wav".encode()
    ).decode()
    hex_key = f"KEY_PHRASE: {STAGE04_KEY_PHRASE}".encode().hex().upper()

    (d / "staff_records.txt").write_text(
        "BIOGENESIS PALEOTECH DIVISION — CLASSIFIED PERSONNEL ROSTER (1997)\n"
        "FACILITY: BRACKETT CITY COMPLEX | AUDIT: 1997-07-18\n"
        "====================================================================\n"
        "ID       NAME                  ROLE                      ASSIGNMENT            STATUS\n"
        "----------------------------------------------------------------------------------------\n"
        "BPD-008  Dr. Elena Vance       Cryo-Systems Engineer     WARD-C / CRYO-1       MIA 1997-07-18\n"
        "BPD-011  Marcus Hale           RF Telemetry Tech         RELAY TOWER 04        MIA 1997-07-18\n"
        f"BPD-014  Dr. Aris Thorne       Lead Paleogeneticist      {STAGE03_BAY} / {STAGE03_VAULT}  MIA 1997-07-18\n"
        "BPD-016  Dr. Claire Sato       Amber Core Analyst        EXCAVATION SECTOR 4   MIA 1997-07-18\n"
        "BPD-019  Owen Mercer           Site Security Chief       PERIMETER OMEGA       MIA 1997-07-18\n"
        "----------------------------------------------------------------------------------------\n\n"
        "[ENCRYPTED TELEMETRY FOOTNOTE — BASE64]\n"
        f"{b64_note}\n\n"
        "[CLEARANCE TOKEN — HEX]\n"
        f"BPD-014_TOKEN={hex_key}\n",
        encoding="utf-8"
    )

    # research_log.pdf
    pdf1 = SimplePDF(
        title="BioGenesis Paleotech - Classified Research Log July 1997",
        author="Dr. Aris Thorne (BPD-014)",
        subject=f"Containment Audit - {STAGE03_SPECIMEN} ({STAGE03_CODE})",
        keywords=f"HEX_CLUE={hex_key} | SECTOR={STAGE01_SECTOR} | SPECIMEN={STAGE03_SPECIMEN}"
    )
    p1 = pdf1.new_page()
    pdf1.add_text(p1, 54, 742, "BIOGENESIS PALEOTECH DIVISION // INTERNAL ARCHIVE", "F2", 14, (0.05, 0.25, 0.15))
    pdf1.add_text(p1, 54, 724, "DOCUMENT: RESEARCH_LOG_1997_07 | CLASSIFICATION: LEVEL-4 RESTRICTED", "F3", 9, (0.35, 0.35, 0.35))
    pdf1.add_line(p1, 54, 714, 558, 714)

    lines_p1 = [
        f"Date: 1997-07-15 | Excavation Origin: {STAGE01_SECTOR} ({STAGE01_COORDS})",
        f"Primary Specimen: {STAGE03_SPECIMEN} (Internal Tag: {STAGE03_CODE})",
        f"Containment Bay: {STAGE03_BAY} / {STAGE03_VAULT}",
        "",
        "14:10 UTC - Amber extraction batch AMBER97 yielded viable sequence fragments.",
        "19:45 UTC - Neural tissue growth in Specimen 07 exceeded baseline by 340%.",
        "22:00 UTC - Dr. Aris Thorne requested emergency cryo-purge authorization.",
        "",
        "REDACTION BLOCK A (DIRECTORATE OVERRIDE):",
        "   Protocol keyword authorized for Sublevel-4 cryo-locks:",
    ]
    y = 684
    for ln in lines_p1:
        pdf1.add_text(p1, 54, y, ln, "F3", 10)
        y -= 20
    # Redaction bar visually covering placeholder
    pdf1.add_rect(p1, 54, y - 4, 290, 16, (0.05, 0.05, 0.05), fill=True)
    pdf1.add_text(p1, 354, y, "[REDACTED - SEE METADATA / PAGE 2]", "F2", 9, (0.6, 0.1, 0.1))

    p2 = pdf1.new_page()
    pdf1.add_text(p2, 54, 742, "RESEARCH LOG — PAGE 2 (DECONTAMINATION & COMMS ANNEX)", "F2", 12, (0.05, 0.25, 0.15))
    pdf1.add_line(p2, 54, 730, 558, 730)
    pdf1.add_text(p2, 54, 700, "Radio relay frequency 748 Hz remains compromised by static.", "F3", 10)
    pdf1.add_text(p2, 54, 680, "Emergency audio log split across stereo channels prior to evacuation.", "F3", 10)
    # Hidden white-on-white forensic text stream!
    b64_stage4 = base64.b64encode(f"STAGE04_FLAG={STAGE04_FLAG}".encode()).decode()
    pdf1.add_text(p2, 54, 620, f"HIDDEN_ARCHIVE_RECORD: {hex_key}", "F3", 9, (1.0, 1.0, 1.0))
    pdf1.add_text(p2, 54, 602, f"BASE64_VERIFY: {b64_stage4}", "F3", 9, (1.0, 1.0, 1.0))
    pdf1.save(d / "research_log.pdf")

    # experiment_07.pdf with embedded attachment
    pdf2 = SimplePDF(
        title=f"Experiment 07 Dossier - {STAGE03_SPECIMEN}",
        author="Dr. Aris Thorne",
        subject=f"Brackett City Incident Reconstruction - {STAGE03_CODE}",
        keywords=f"LEAD={STAGE04_RESEARCHER} | KEY_PHRASE={STAGE04_KEY_PHRASE}"
    )
    ep1 = pdf2.new_page()
    pdf2.add_text(ep1, 54, 742, f"EXPERIMENT 07 DOSSIER // SPECIMEN {STAGE03_SPECIMEN}", "F2", 14, (0.05, 0.25, 0.15))
    pdf2.add_line(ep1, 54, 728, 558, 728)
    b64_warn = base64.b64encode(
        "WARNING: STAGE05 last_transmission.wav LEFT CHANNEL IS TIME-REVERSED. "
        "COMBINE: <PART1>-<PART2>-<STAGE02_PASS> FOR STAGE06 AES KEY.".encode()
    ).decode()
    exp_lines = [
        f"Specimen Code : {STAGE03_CODE} ({STAGE03_SPECIMEN})",
        f"Origin Site   : {STAGE01_SECTOR} ({STAGE01_COORDS})",
        f"Auth Token    : {STAGE01_AUTH} / {STAGE02_PASS}",
        f"Lead Scientist: Dr. Aris Thorne (BPD-014)",
        "",
        "OBSERVATION SUMMARY (1997-07-18):",
        "Genetic reconstruction from Delta-4 amber exhibited unexpected",
        "synaptic synchronization across adjacent cryo-incubators.",
        "Immediate containment initiated under Protocol Omega.",
        "",
        "TRANSMISSION PROTOCOL DIRECTIVE (BASE64):",
        b64_warn[:68],
        b64_warn[68:],
        "",
        "NOTE: An uncompressed telemetry attachment (transmission_protocol.txt)",
        "is embedded inside this PDF document."
    ]
    y = 696
    for ln in exp_lines:
        pdf2.add_text(ep1, 54, y, ln, "F3", 9.5)
        y -= 18

    attach_payload = (
        "BIOGENESIS TRANSMISSION PROTOCOL — EMBEDDED ATTACHMENT\n"
        "======================================================\n"
        f"LEAD_RESEARCHER: {STAGE04_RESEARCHER}\n"
        f"KEY_PHRASE: {STAGE04_KEY_PHRASE}\n"
        f"STAGE04_FLAG: {STAGE04_FLAG}\n"
        "STAGE05_INSTRUCTIONS:\n"
        "  1. Split last_transmission.wav into Left and Right channels.\n"
        "  2. Reverse the Left channel in time to decode the 2200 Hz Morse key PART1.\n"
        "  3. Inspect the Right channel spectrogram (14-18.5 kHz) for PART2 and verify DTMF.\n"
        "  4. Assemble Stage 06 key: <PART1>-<PART2>-<STAGE02_PASS>\n"
    ).encode("utf-8")
    pdf2.attach_file("transmission_protocol.txt", attach_payload)
    pdf2.save(d / "experiment_07.pdf")


def build_stage_05() -> None:
    d = PLAYER_DIR / "05_TRANSMISSION"
    d.mkdir(parents=True, exist_ok=True)

    (d / "briefing.txt").write_text(
        "====================================================================\n"
        "STAGE 05 — THE LAST TRANSMISSION\n"
        "====================================================================\n"
        "Category   : Advanced Audio Forensics\n"
        "Difficulty : Medium-Hard\n\n"
        "BRIEFING:\n"
        "Two audio reels survived inside Sublevel-4's shielded tape deck.\n"
        "  1) lab_recording.wav: Ambient machinery, lab voice alert, and DTMF.\n"
        "  2) last_transmission.wav: A stereo emergency broadcast containing\n"
        "     multiple forensic layers.\n\n"
        "Remember the protocol warning recovered in Stage 04.\n\n"
        "FILES:\n"
        "  - lab_recording.wav\n"
        "  - last_transmission.wav\n\n"
        "OBJECTIVE:\n"
        "Recover both key halves and combine them with the Stage 02 password\n"
        "to obtain the Stage 06 AES-256 decryption key:\n"
        "  JURASSIC[<PART1>-<PART2>-<STAGE02_PASS>]\n",
        encoding="utf-8"
    )

    # Recording A: lab_recording.wav (Mono, 17.0s)
    dur_a = 17.0
    na = int(dur_a * SR)
    rng_a = random.Random(SEED + 501)
    lab = [0.0] * na
    for i in range(na):
        t = i / SR
        hum = 0.08 * math.sin(2.0 * math.pi * 60.0 * t) + 0.04 * math.sin(2.0 * math.pi * 120.0 * t)
        pump = 0.09 * (0.5 + 0.5 * math.sin(2.0 * math.pi * 1.8 * t)) * math.sin(2.0 * math.pi * 145.0 * t)
        noise = 0.04 * rng_a.uniform(-1.0, 1.0)
        beep = 0.14 * math.sin(2.0 * math.pi * 1000.0 * t) if (t > 5.6 and (t % 2.0) < 0.08) else 0.0
        lab[i] = hum + pump + noise + beep

    lab_voice = synth_radio_voice(na, 5.6, 8.5, rng_a, amp=0.45)
    lab_bed = biquad_bandstop([lab[i] + lab_voice[i] for i in range(na)], 1800.0, q=4.5)
    dtmf_a = synth_dtmf_track("19970718", na, start_sec=0.8, tone_sec=0.35, gap_sec=0.20, amp=0.32)
    morse_a = synth_morse_track("REVERSE LEFT STEREO", na, start_sec=5.6, freq=1800.0, unit_sec=0.060, amp=0.16)
    write_wav_mono(d / "lab_recording.wav", [lab_bed[i] + dtmf_a[i] + morse_a[i] for i in range(na)])

    # Recording B: last_transmission.wav (Stereo, 16.0s)
    dur_b = 16.0
    nb = int(dur_b * SR)
    rng_b = random.Random(SEED + 502)

    # Left Channel (generated forward, then TIME-REVERSED!)
    left_fwd = [0.0] * nb
    for i in range(nb):
        t = i / SR
        klaxon_f = 520.0 + 180.0 * (0.5 + 0.5 * math.sin(2.0 * math.pi * 1.5 * t))
        klaxon = 0.06 * math.sin(2.0 * math.pi * klaxon_f * t) if t < 5.0 else 0.0
        left_fwd[i] = 0.14 * rng_b.uniform(-1.0, 1.0) + klaxon
    left_voice = synth_radio_voice(nb, 1.0, 8.0, rng_b, amp=0.35)
    left_fwd = biquad_bandstop([left_fwd[i] + left_voice[i] for i in range(nb)], 2200.0, q=4.5)
    morse_part1 = synth_morse_track(f"PART1 {STAGE05_PART1}", nb, start_sec=1.5, freq=2200.0, unit_sec=0.080, amp=0.22)
    left_fwd = [left_fwd[i] + morse_part1[i] for i in range(nb)]
    left_rev = left_fwd[::-1]  # Time-reverse the Left Channel!

    # Right Channel (forward): DTMF 970718 + ultrasonic spectrogram "PART2:OMEGA748"
    right_noise = [0.12 * rng_b.uniform(-1.0, 1.0) + 0.03 * math.sin(2.0 * math.pi * 60.0 * (i / SR)) for i in range(nb)]
    dtmf_b = synth_dtmf_track("970718", nb, start_sec=0.8, tone_sec=0.45, gap_sec=0.25, amp=0.25)
    right_audible = biquad_lowpass([right_noise[i] + dtmf_b[i] for i in range(nb)], 11000.0)
    spec_part2 = synth_spectrogram_text(
        f"PART2:{STAGE05_PART2}", nb, start_sec=5.5, dur_sec=9.5,
        f_low=14000.0, f_high=18500.0, amp=0.050
    )
    right = [right_audible[i] + spec_part2[i] for i in range(nb)]

    write_wav_stereo(d / "last_transmission.wav", left_rev, right)


def build_stage_06() -> None:
    d = PLAYER_DIR / "06_BRACKETT_CITY"
    d.mkdir(parents=True, exist_ok=True)

    (d / "briefing.txt").write_text(
        "====================================================================\n"
        "STAGE 06 — BRACKETT CITY\n"
        "====================================================================\n"
        "Category   : Geospatial Forensics / Cryptography\n"
        "Difficulty : Hard\n\n"
        "BRIEFING:\n"
        "With the emergency transmission key assembled, recover the encrypted\n"
        "July 18, 1997 incident report (incident_1997.enc) and cross-reference\n"
        "the Brackett City tactical survey map against Stage 01 & Stage 03.\n\n"
        "FILES:\n"
        "  - brackett_map.png\n"
        "  - coordinates.dat\n"
        "  - incident_1997.enc\n\n"
        "OBJECTIVE:\n"
        "Decrypt incident_1997.enc using OpenSSL AES-256-CBC (PBKDF2) and\n"
        "recover the Stage 06 flag: JURASSIC[...]\n",
        encoding="utf-8"
    )

    # 1. brackett_map.png (1600x900)
    src_map = find_source_image("brackett_map_base")
    map_png = d / "brackett_map.png"
    cmd = [
        "convert", str(src_map), "-resize", "1600x900!",
        # Grid & border
        "-stroke", "rgba(35,45,35,0.45)", "-strokewidth", "1",
        "-draw", "line 200,0 200,900 line 400,0 400,900 line 600,0 600,900 line 800,0 800,900 line 1000,0 1000,900 line 1200,0 1200,900 line 1400,0 1400,900",
        "-draw", "line 0,150 1600,150 line 0,300 1600,300 line 0,450 1600,450 line 0,600 1600,600 line 0,750 1600,750",
        # Title banner box
        "-fill", "rgba(22,28,22,0.88)", "-stroke", "rgba(180,170,130,0.8)", "-strokewidth", "2",
        "-draw", "rectangle 24,20 630,104",
        "-fill", "#EAE4C8", "-stroke", "none", "-font", FONT_MONO, "-pointsize", "22",
        "-annotate", "+40+54", "BRACKETT CITY RESEARCH COMPLEX // 1997",
        "-pointsize", "14", "-fill", "#C8C2A2",
        "-annotate", "+40+84", f"SURVEY GRID: 38.4420N 109.5120W  |  SCALE 1:5000  |  OMEGA-97",
        # Legend panel
        "-fill", "rgba(22,28,22,0.88)", "-stroke", "rgba(180,170,130,0.8)", "-strokewidth", "2",
        "-draw", "rectangle 24,690 470,876",
        "-fill", "#EAE4C8", "-stroke", "none", "-pointsize", "15",
        "-annotate", "+40+718", "TACTICAL SECTORS & SYMBOLS:",
        "-pointsize", "13", "-fill", "#D5D0B8",
        "-annotate", "+40+744", "[B-4] EXCAVATION SITE (SECTOR 4)   [D-7]",
        "-annotate", "+40+766", "[E-3] MAIN RESEARCH FACILITY       [f=748Hz]",
        "-annotate", "+40+788", "[F-2] RESTRICTED ZONE (PERIMETER)  [OMEGA-97]",
        "-annotate", "+40+810", "[D-4] ABANDONED MEDICAL WING       [WARD-C]",
        "-annotate", "+40+832", "[E-4] UNDERGROUND LAB (SUBLEVEL-4) [VAULT-B3]",
        "-annotate", "+40+856", "REF: AMBER97 -> HELIX748 -> VELOCIS-07",
        # Markers on map
        "-fill", "#B91C1C", "-stroke", "#FFFFFF", "-strokewidth", "2",
        "-draw", "circle 320,520 328,520",   # B-4 Excavation
        "-draw", "circle 920,380 928,380",   # E-3 Research Facility
        "-draw", "circle 1160,210 1168,210", # F-2 Restricted Zone
        "-draw", "circle 760,540 768,540",   # D-4 Medical Wing
        "-draw", "circle 960,560 968,560",   # E-4 Underground Lab
        # Marker labels
        "-fill", "#1A1E1A", "-stroke", "rgba(240,235,210,0.85)", "-strokewidth", "4",
        "-font", FONT_MONO, "-pointsize", "15",
        "-annotate", "+180+496", "EXCAVATION SITE (SECTOR 4: 38.4420N)",
        "-annotate", "+935+386", "RESEARCH FACILITY [BPD-97]",
        "-annotate", "+1175+216", "RESTRICTED ZONE [OMEGA]",
        "-annotate", "+545+556", "MEDICAL WING [WARD-C]",
        "-annotate", "+975+566", "UNDERGROUND LAB [SUBLEVEL-4]",
        "-stroke", "none", "-fill", "#111111",
        "-annotate", "+180+496", "EXCAVATION SITE (SECTOR 4: 38.4420N)",
        "-annotate", "+935+386", "RESEARCH FACILITY [BPD-97]",
        "-annotate", "+1175+216", "RESTRICTED ZONE [OMEGA]",
        "-annotate", "+545+556", "MEDICAL WING [WARD-C]",
        "-annotate", "+975+566", "UNDERGROUND LAB [SUBLEVEL-4]",
        # Compass rose top-right
        "-fill", "rgba(22,28,22,0.88)", "-stroke", "rgba(180,170,130,0.8)", "-strokewidth", "2",
        "-draw", "circle 1510,80 1510,36",
        "-fill", "#EAE4C8", "-stroke", "none", "-pointsize", "18",
        "-annotate", "+1503+65", "N",
        "-pointsize", "12", "-annotate", "+1498+105", "38.4N",
        str(map_png)
    ]
    subprocess.run(cmd, check=True)

    # 2. coordinates.dat
    (d / "coordinates.dat").write_text(
        "# BRACKETT CITY GEOSPATIAL TELEMETRY & ARCHIVE MANIFEST\n"
        "# CROSS-REFERENCE: STAGE 01 + STAGE 03 + STAGE 05\n"
        "SITE_ORIGIN=BRACKETT_CITY_UT\n"
        f"EXCAVATION_GRID={STAGE01_COORDS}\n"
        f"CONTAINMENT_SECTOR={STAGE03_BAY}/{STAGE03_VAULT}\n"
        "ENC_TARGET=incident_1997.enc\n"
        "ENC_CIPHER=AES-256-CBC (OpenSSL Salted, PBKDF2-HMAC-SHA256, 100000 iterations)\n"
        "KEY_FORMULA=<STAGE05_PART1>-<STAGE05_PART2>-<STAGE02_PASS>\n"
        "NOTE=Use recovered Stage 05 stereo key + Stage 02 radio password to decrypt incident_1997.enc.\n",
        encoding="utf-8"
    )

    # 3. incident_1997.enc (Real OpenSSL AES-256-CBC!)
    incident_txt = (
        "====================================================================\n"
        "CLASSIFIED INCIDENT REPORT — BRACKETT CITY FACILITY\n"
        "DATE: JULY 18, 1997 (23:42 UTC) | EVENT CODE: OMEGA-PURGE-2342\n"
        "====================================================================\n\n"
        f"LOCATION   : Underground Laboratory ({STAGE03_BAY} / {STAGE03_VAULT})\n"
        f"COORDINATES: {STAGE01_COORDS} ({STAGE01_SECTOR})\n"
        f"SPECIMEN   : {STAGE03_SPECIMEN} ({STAGE03_CODE})\n"
        "COMMANDER  : Dr. Aris Thorne (BPD-014)\n\n"
        "RECOVERED TRUTH OF JULY 18, 1997:\n"
        "At 21:14 UTC, Specimen 07 (VELOCIS-07) reconstructed from Sector 4\n"
        "amber exhibited rapid neuro-adaptive replication and breached Primary\n"
        "Bio-Containment inside Sublevel-4. When BioGenesis corporate directors\n"
        "refused immediate evacuation to protect proprietary genetic assets,\n"
        "Dr. Aris Thorne manually initiated PROTOCOL OMEGA at 23:42 UTC.\n\n"
        "All cryo-vaults and subterranean vents were permanently sealed and\n"
        "thermally purged. The staff evacuated via the canyon drainage tunnel\n"
        "after destroying the surface communications relay.\n\n"
        f"STAGE 06 FLAG: {STAGE06_FLAG}\n\n"
        "--------------------------------------------------------------------\n"
        "STAGE 07 DECRYPTION PARAMETERS (EXTINCTION PROTOCOL ARCHIVE):\n"
        "  1) extinction_protocol.bin XOR KEY = Stage 01 Grid Ref (38.4420N_109.5120W)\n"
        f"  2) Incident Code                   = {STAGE06_INCIDENT_CODE}\n"
        "  3) final_archive.dat AES-256 Key   = <STAGE04_KEY_PHRASE>:<INCIDENT_CODE>:<STAGE03_SPECIMEN>\n"
        "====================================================================\n"
    ).encode("utf-8")
    openssl_encrypt(incident_txt, STAGE05_KEY, d / "incident_1997.enc")


def build_stage_07() -> None:
    d = PLAYER_DIR / "07_FINAL_PROTOCOL"
    d.mkdir(parents=True, exist_ok=True)

    (d / "briefing.txt").write_text(
        "====================================================================\n"
        "STAGE 07 — THE EXTINCTION PROTOCOL (FINAL STAGE)\n"
        "====================================================================\n"
        "Category   : Multi-stage Forensics / Cryptography\n"
        "Difficulty : Hard\n\n"
        "BRIEFING:\n"
        "You have uncovered the truth behind the July 18, 1997 Brackett City\n"
        "lockdown. Two final sealed artifacts remain in the Sublevel-4 vault:\n"
        "  - extinction_protocol.bin : Custom binary container (header + compressed\n"
        "                              XOR-encrypted manifest starting at payload offset)\n"
        "  - final_archive.dat       : OpenSSL AES-256-CBC encrypted final record\n\n"
        "Combine the coordinates from Stage 01, specimen ID from Stage 03,\n"
        "key phrase from Stage 04, and incident code from Stage 06.\n\n"
        "OBJECTIVE:\n"
        "Extract the manifest from extinction_protocol.bin, decrypt\n"
        "final_archive.dat, and recover the final flag: JURASSIC[...]\n",
        encoding="utf-8"
    )

    # 1. extinction_protocol.bin: Custom binary container with 32-byte header + decoy + XOR(zlib(manifest))
    manifest_text = (
        "====================================================================\n"
        "EXTINCTION PROTOCOL — VAULT EXECUTION MANIFEST\n"
        "====================================================================\n"
        f"INCIDENT_CODE : {STAGE06_INCIDENT_CODE}\n"
        f"SPECIMEN      : {STAGE03_SPECIMEN} ({STAGE03_CODE})\n"
        f"KEY_PHRASE    : {STAGE04_KEY_PHRASE}\n"
        "FINAL_CIPHER  : OpenSSL AES-256-CBC (-pbkdf2 -iter 100000 -salt)\n"
        "PASSPHRASE    : <STAGE04_KEY_PHRASE>:<INCIDENT_CODE>:<STAGE03_SPECIMEN>\n"
        f"EXPECTED_HASH : {hashlib.sha256(FINAL_FLAG.encode()).hexdigest()}\n"
        "====================================================================\n"
    ).encode("utf-8")

    comp = zlib.compress(manifest_text, level=9)
    xor_key = STAGE01_COORDS.encode("utf-8")
    xored = bytes(b ^ xor_key[i % len(xor_key)] for i, b in enumerate(comp))

    # Header: magic(8)='JEXT1997', version(I)=1, offset(I)=64, length(I)=len(xored), sha256_prefix(12)
    sha12 = hashlib.sha256(manifest_text).digest()[:12]
    header = struct.pack("<8sIII12s", b"JEXT1997", 1, 64, len(xored), sha12)
    assert len(header) == 32
    decoy = b"DECOY_RECORD:JURASSIC[FAKE_FLAG_IGNORE]\x00".ljust(32, b"\xff")[:32]
    (d / "extinction_protocol.bin").write_bytes(header + decoy + xored)

    # 2. final_archive.dat: Real OpenSSL AES-256-CBC encrypted final confession + FINAL FLAG
    final_plaintext = (
        "====================================================================\n"
        "BIOGENESIS PALEOTECH — SEALED FINAL RECORD (JULY 18, 1997)\n"
        "AUTHOR: DR. ARIS THORNE (BPD-014) | BRACKETT CITY SUBLEVEL-4\n"
        "====================================================================\n\n"
        "If anyone has reconstructed our fragments from Sector 4, Relay 748,\n"
        "and the Brackett City vaults, then the truth has survived.\n\n"
        "We did not vanish by accident. Specimen VELOCIS-07 adapted faster\n"
        "than any containment model predicted. Rather than allow corporate\n"
        "extraction teams to transport living neuro-adaptive specimens off-site,\n"
        "we executed Protocol Omega and erased the upper complex.\n\n"
        "Leave Sector 7 sealed.\n\n"
        f"FINAL FLAG: {FINAL_FLAG}\n"
        "====================================================================\n"
    ).encode("utf-8")
    openssl_encrypt(final_plaintext, STAGE07_MASTER_PASS, d / "final_archive.dat")


# ---------------------------------------------------------------------------
# Player Instructions PDF + Organizer Documentation & Answer Key
# ---------------------------------------------------------------------------

def build_player_instructions() -> None:
    pdf = SimplePDF(
        title="JURASSIC: THE EXTINCTION PROTOCOL - Player Instructions",
        author="CTF Organizing Committee",
        subject="Investigator Case Briefing & Rules",
        keywords="JURASSIC CTF Player Instructions 1997 Brackett City"
    )
    p = pdf.new_page()
    pdf.add_text(p, 54, 742, "JURASSIC: THE EXTINCTION PROTOCOL", "F2", 18, (0.05, 0.30, 0.18))
    pdf.add_text(p, 54, 722, "PLAYER BRIEFING & FORENSIC INVESTIGATION GUIDE", "F2", 11, (0.25, 0.3, 0.28))
    pdf.add_line(p, 54, 710, 558, 710)

    body = [
        "CASE BACKGROUND:",
        "In 1997, BioGenesis Paleotech established a classified facility outside",
        "Brackett City to extract prehistoric DNA. On July 18, 1997, all",
        "communications ceased and every researcher disappeared.",
        "You have been handed the recovered 7-stage evidence archive.",
        "",
        "RULES & FLAG FORMAT:",
        "  1. Every stage unlocks intelligence needed for subsequent stages.",
        "  2. Flag format: JURASSIC[...] (exact uppercase/underscores).",
        "  3. No internet access or brute-force guessing is required.",
        "  4. Preserve untouched backups of original evidence before editing.",
        "",
        "RECOMMENDED FREE TOOLS:",
        "  - Image Forensics : ExifTool, Python Pillow, GIMP, ImageMagick, strings",
        "  - Audio Forensics : Audacity, Sonic Visualiser, FFmpeg, Python wave/scipy",
        "  - Document/Crypto : pdftotext / PyMuPDF, OpenSSL (AES-256-CBC), Python",
        "",
        "INVESTIGATION STAGES:",
        "  01_EXCAVATION         - Field photos, EXIF metadata & pixel LSBs",
        "  02_FREQUENCY          - Shortwave static, notched Morse & spectrogram",
        "  03_NEGATIVE_SPECIMENS - Inversion, contrast, channel & gamma recovery",
        "  04_RESEARCH_ARCHIVE   - Classified PDFs, attachments, hex & Base64",
        "  05_TRANSMISSION       - Stereo split, reversed audio, DTMF & spectrogram",
        "  06_BRACKETT_CITY      - Tactical map & OpenSSL AES-256-CBC decryption",
        "  07_FINAL_PROTOCOL     - Binary extraction & final encrypted archive",
    ]
    y = 682
    for ln in body:
        font = "F2" if ln.endswith(":") else "F3"
        pdf.add_text(p, 54, y, ln, font, 10)
        y -= 20
    pdf.save(PLAYER_DIR / "PLAYER_INSTRUCTIONS.pdf")


def build_organizer_docs() -> None:
    ORG_DIR.mkdir(parents=True, exist_ok=True)

    (ORG_DIR / "CHALLENGE_FLAGS.txt").write_text(
        "JURASSIC: THE EXTINCTION PROTOCOL — OFFICIAL FLAGS\n"
        "==================================================\n"
        f"STAGE 01: {STAGE01_FLAG}\n"
        f"STAGE 02: {STAGE02_FLAG}\n"
        f"STAGE 03: {STAGE03_FLAG}\n"
        f"STAGE 04: {STAGE04_FLAG}\n"
        f"STAGE 05: {STAGE05_FLAG}\n"
        f"STAGE 06: {STAGE06_FLAG}\n"
        f"STAGE 07 (FINAL): {FINAL_FLAG}\n",
        encoding="utf-8"
    )

    (ORG_DIR / "CLUE_DEPENDENCY_GRAPH.md").write_text(
        "# Clue Dependency Graph\n\n"
        "```text\n"
        "STAGE 01 (excavation_01.jpg EXIF + excavation_02.png Red-LSB)\n"
        "  ├── Grid Ref: 38.4420N_109.5120W ──────────► Stage 04, Stage 06 Map, Stage 07 (.bin XOR key)\n"
        "  ├── Frequency Hint: 748Hz ─────────────────► Stage 02 (carrier notch Morse)\n"
        "  └── Auth Prefix: AMBER97 ──────────────────► Stage 04 cross-check\n"
        "        │\n"
        "        ▼\n"
        "STAGE 02 (frequency_748.wav: 748Hz Morse + 16.5-19.8kHz spectrogram)\n"
        "  └── Password: HELIX748 ────────────────────► Stage 05/06 AES key suffix\n"
        "        │\n"
        "        ▼\n"
        "STAGE 03 (specimen_01..04.png: invert, auto-level, Blue ch, gamma)\n"
        "  ├── Specimen ID: VELOCIS-07 (Code V07-DELTA) ► Stage 04, Stage 07 AES passphrase\n"
        "  └── Location: VAULT-B3 / SUBLEVEL-4 ───────► Stage 04, Stage 06 Map\n"
        "        │\n"
        "        ▼\n"
        "STAGE 04 (staff_records.txt + research_log.pdf + experiment_07.pdf)\n"
        "  ├── Lead Researcher: ARIS_THORNE ──────────► Stage 04 Flag, Stage 06/07\n"
        "  ├── Key Phrase: CRYO_OMEGA_97 ─────────────► Stage 07 AES passphrase\n"
        "  └── Warning: Reverse Stage 05 Left Channel ► Stage 05\n"
        "        │\n"
        "        ▼\n"
        "STAGE 05 (lab_recording.wav + last_transmission.wav stereo)\n"
        "  ├── Left (reversed 2200Hz Morse): THORNE97 ─┐\n"
        "  ├── Right (14-18.5kHz spec)     : OMEGA748 ─┼─► AES Key: THORNE97-OMEGA748-HELIX748\n"
        "  └── Stage 02 Password           : HELIX748 ─┘       │\n"
        "                                                      ▼\n"
        "STAGE 06 (brackett_map.png + coordinates.dat + incident_1997.enc)\n"
        "  └── Incident Code: OMEGA-PURGE-2342 + Key Rules ────► Stage 07\n"
        "        │\n"
        "        ▼\n"
        "STAGE 07 (extinction_protocol.bin + final_archive.dat)\n"
        "  ├── XOR(.bin[64:], '38.4420N_109.5120W') -> zlib -> AES formula\n"
        "  └── OpenSSL AES-256-CBC('CRYO_OMEGA_97:OMEGA-PURGE-2342:VELOCIS-07') -> FINAL FLAG\n"
        "```\n",
        encoding="utf-8"
    )

    (ORG_DIR / "HINTS.md").write_text(
        "# Progressive Hints (2 Hints per Stage)\n\n"
        "## Stage 01 — The Excavation\n"
        "- **Hint 1:** Check `excavation_01.jpg` metadata (`exiftool` or `strings`) and the PNG `tEXt` comment inside `excavation_02.png`.\n"
        "- **Hint 2:** Extract the least significant bit (`& 1`) of the Red channel only in `excavation_02.png`, packed 8 bits per byte MSB-first.\n\n"
        "## Stage 02 — The Dead Frequency\n"
        "- **Hint 1:** The stage name points to 748 Hz, and the static around 748 Hz has been notched out to hide a faint Morse carrier.\n"
        "- **Hint 2:** Apply a narrow bandpass filter around 748 Hz (`730–766 Hz`) OR view the spectrogram between 16.5 kHz and 19.8 kHz.\n\n"
        "## Stage 03 — The Negative Specimens\n"
        "- **Hint 1:** Each PNG uses a different pixel transform: invert (`255-x`), extreme dark compression, single RGB channel isolation, and dark gamma.\n"
        "- **Hint 2:** Invert `specimen_01`, auto-level `specimen_02`, inspect only the Blue channel of `specimen_03`, and apply `gamma=0.25` (or threshold > 12) to `specimen_04`.\n\n"
        "## Stage 04 — The Missing Researcher\n"
        "- **Hint 1:** Decode the Base64 and Hex strings in `staff_records.txt` and inspect the `/Keywords` metadata of `research_log.pdf`.\n"
        "- **Hint 2:** `research_log.pdf` Page 2 has white-on-white text (`pdftotext` or `strings`), and `experiment_07.pdf` has an embedded attachment (`transmission_protocol.txt`).\n\n"
        "## Stage 05 — The Last Transmission\n"
        "- **Hint 1:** Split `last_transmission.wav` into Left and Right mono tracks; reverse the Left channel in time.\n"
        "- **Hint 2:** Decode 2200 Hz Morse in the reversed Left channel (`THORNE97`), inspect 14–18.5 kHz spectrogram in the Right channel (`OMEGA748`), and append Stage 02's password.\n\n"
        "## Stage 06 — Brackett City\n"
        "- **Hint 1:** Read `coordinates.dat` for the exact OpenSSL AES-256-CBC PBKDF2 cipher parameters and key formula.\n"
        "- **Hint 2:** Decrypt `incident_1997.enc` using `THORNE97-OMEGA748-HELIX748`.\n\n"
        "## Stage 07 — The Extinction Protocol\n"
        "- **Hint 1:** Parse the 32-byte header of `extinction_protocol.bin` (`JEXT1997`) to find the payload offset (64) and length; ignore the decoy string.\n"
        "- **Hint 2:** XOR bytes `[64 : 64+len]` with `38.4420N_109.5120W`, `zlib.decompress`, then decrypt `final_archive.dat` with `CRYO_OMEGA_97:OMEGA-PURGE-2342:VELOCIS-07`.\n",
        encoding="utf-8"
    )

    sol_md = (
        "# MASTER SOLUTION STEPS (Windows 11 PowerShell & Linux)\n\n"
        "## Stage 01 — The Excavation\n"
        "- **Objective:** Recover Sector ID & coordinates.\n"
        "- **Hidden Clue:** JPEG EXIF/COM in `excavation_01.jpg`; PNG `tEXt` + Red-channel LSBs in `excavation_02.png`.\n"
        "- **PowerShell:**\n"
        "```powershell\n"
        "exiftool excavation_01.jpg\n"
        "python -c \"from PIL import Image; im=Image.open('excavation_02.png'); bits=[p[0]&1 for p in im.getdata()]; bs=bytes(int(''.join(map(str,bits[i:i+8])),2) for i in range(0,len(bits)-7,8)); print(bs.split(b'\\x00')[0].decode())\"\n"
        "```\n"
        f"- **Flag:** `{STAGE01_FLAG}`\n\n"
        "## Stage 02 — The Dead Frequency\n"
        "- **Objective:** Recover `HELIX748` from `frequency_748.wav`.\n"
        "- **Technique:** Bandpass around `748 Hz` (`730–766 Hz`) to decode Morse (`KEY IS HELIX748`), or view spectrogram at `16.5–19.8 kHz` (`PASS:HELIX748`).\n"
        "- **PowerShell / FFmpeg:**\n"
        "```powershell\n"
        "ffmpeg -i frequency_748.wav -af \"bandpass=f=748:width_type=h:w=30,volume=15\" filtered_748.wav\n"
        "ffmpeg -i frequency_748.wav -lavfi \"showspectrumpic=s=1200x600\" spec_02.png\n"
        "```\n"
        f"- **Flag:** `{STAGE02_FLAG}`\n\n"
        "## Stage 03 — The Negative Specimens\n"
        "- **Objective:** Recover `VELOCIS-07`, `VAULT-B3`, `V07-DELTA`, `SUBLEVEL-4`.\n"
        "- **PowerShell (ImageMagick / Python):**\n"
        "```powershell\n"
        "magick specimen_01.png -negate out_01.png\n"
        "magick specimen_02.png -auto-level out_02.png\n"
        "magick specimen_03.png -channel B -separate -auto-level out_03.png\n"
        "magick specimen_04.png -evaluate pow 0.25 out_04.png\n"
        "```\n"
        f"- **Flag:** `{STAGE03_FLAG}`\n\n"
        "## Stage 04 — The Missing Researcher\n"
        "- **Objective:** Identify Dr. Aris Thorne & `CRYO_OMEGA_97`.\n"
        "- **Technique:** Decode Base64/Hex in `staff_records.txt`; inspect PDF metadata, white-on-white text (`pdftotext research_log.pdf -`), and embedded attachment in `experiment_07.pdf`.\n"
        f"- **Flag:** `{STAGE04_FLAG}`\n\n"
        "## Stage 05 — The Last Transmission\n"
        "- **Objective:** Recover `THORNE97` (Left reversed Morse) and `OMEGA748` (Right spectrogram), combine with `HELIX748`.\n"
        "- **PowerShell / FFmpeg:**\n"
        "```powershell\n"
        "ffmpeg -i last_transmission.wav -af \"pan=mono|c0=c0,areverse,bandpass=f=2200:w=200\" left_rev_2200.wav\n"
        "ffmpeg -i last_transmission.wav -af \"pan=mono|c0=c1\" -lavfi \"showspectrumpic=s=1200x600\" right_spec.png\n"
        "```\n"
        f"- **Flag:** `{STAGE05_FLAG}`\n\n"
        "## Stage 06 — Brackett City\n"
        "- **Objective:** Decrypt `incident_1997.enc` using Stage 05 key.\n"
        "- **PowerShell / OpenSSL:**\n"
        "```powershell\n"
        f"openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -in incident_1997.enc -out incident_1997.txt -pass pass:{STAGE05_KEY}\n"
        "```\n"
        f"- **Flag:** `{STAGE06_FLAG}`\n\n"
        "## Stage 07 — The Extinction Protocol\n"
        "- **Objective:** Extract XOR+zlib manifest from `extinction_protocol.bin` and decrypt `final_archive.dat`.\n"
        "- **PowerShell:**\n"
        "```powershell\n"
        "python -c \"import struct,zlib; d=open('extinction_protocol.bin','rb').read(); m,v,off,ln=struct.unpack('<8sIII',d[:20]); k=b'38.4420N_109.5120W'; print(zlib.decompress(bytes(b^k[i%len(k)] for i,b in enumerate(d[off:off+ln]))).decode())\"\n"
        f"openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -in final_archive.dat -out final_archive.txt -pass pass:{STAGE07_MASTER_PASS}\n"
        "```\n"
        f"- **Final Flag:** `{FINAL_FLAG}`\n"
    )
    (ORG_DIR / "SOLUTION_STEPS.md").write_text(sol_md, encoding="utf-8")

    # Also render MASTER_ANSWER_KEY.pdf
    ak_pdf = SimplePDF(
        title="JURASSIC: THE EXTINCTION PROTOCOL - Master Answer Key",
        author="CTF Organizing Committee",
        subject="ORGANIZER ONLY - CONFIDENTIAL",
        keywords="Master Answer Key Solutions"
    )
    page = ak_pdf.new_page()
    ak_pdf.add_text(page, 54, 742, "ORGANIZER ONLY // MASTER ANSWER KEY", "F2", 16, (0.65, 0.08, 0.08))
    ak_pdf.add_text(page, 54, 722, "JURASSIC: THE EXTINCTION PROTOCOL (SEED 19970718)", "F2", 11)
    ak_pdf.add_line(page, 54, 710, 558, 710)
    summary_lines = [
        f"STAGE 01 : {STAGE01_FLAG}",
        "  Method : JPEG EXIF/COM + PNG tEXt + Red-LSB Steganography (JCTF1:...)",
        f"STAGE 02 : {STAGE02_FLAG}",
        "  Method : 748 Hz Notched Morse + 16.5-19.8 kHz Ultrasonic Spectrogram",
        f"STAGE 03 : {STAGE03_FLAG}",
        "  Method : Negate (01), Auto-Level (02), Blue Channel (03), Gamma/Thresh (04)",
        f"STAGE 04 : {STAGE04_FLAG}",
        "  Method : Base64/Hex in TXT & PDF Keywords + White Text + Embedded File",
        f"STAGE 05 : {STAGE05_FLAG}",
        "  Method : Reverse Left Ch (2200Hz Morse) + Right Spec (14-18.5kHz) + HELIX748",
        f"STAGE 06 : {STAGE06_FLAG}",
        f"  Method : OpenSSL AES-256-CBC PBKDF2 pass={STAGE05_KEY}",
        f"STAGE 07 : {FINAL_FLAG}",
        "  Method : extinction_protocol.bin XOR('38.4420N_109.5120W')+zlib,",
        f"           then OpenSSL AES-256-CBC pass={STAGE07_MASTER_PASS}",
    ]
    y = 682
    for ln in summary_lines:
        ak_pdf.add_text(page, 54, y, ln, "F2" if ln.startswith("STAGE") else "F3", 9.5)
        y -= 18
    ak_pdf.save(ORG_DIR / "MASTER_ANSWER_KEY.pdf")


def build_release_zips() -> None:
    REL_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DL_DIR.mkdir(parents=True, exist_ok=True)

    player_zip = REL_DIR / "JURASSIC_CTF_PLAYER_PACKAGE.zip"
    with zipfile.ZipFile(player_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(PLAYER_DIR.rglob("*")):
            if path.is_file():
                arcname = Path("JURASSIC_CTF_PLAYER_PACKAGE") / path.relative_to(PLAYER_DIR)
                zf.write(path, arcname)

    org_zip = REL_DIR / "JURASSIC_CTF_ORGANIZER_ONLY.zip"
    with zipfile.ZipFile(org_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname in ["README.txt", "requirements.txt", "generate_ctf.py", "validate_ctf.py"]:
            p = BASE_DIR / fname
            if p.exists():
                zf.write(p, Path("JURASSIC_CTF_ORGANIZER_ONLY") / fname)
        for path in sorted(ORG_DIR.rglob("*")):
            if path.is_file():
                arcname = Path("JURASSIC_CTF_ORGANIZER_ONLY") / "ORGANIZER_ONLY" / path.relative_to(ORG_DIR)
                zf.write(path, arcname)

    shutil.copy2(player_zip, PUBLIC_DL_DIR / player_zip.name)
    shutil.copy2(org_zip, PUBLIC_DL_DIR / org_zip.name)


def main() -> None:
    t0 = time.time()
    print("[*] Building JURASSIC: THE EXTINCTION PROTOCOL (seed=19970718)...")
    build_stage_01()
    print("[+] Stage 01 generated.")
    build_stage_02()
    print("[+] Stage 02 generated.")
    build_stage_03()
    print("[+] Stage 03 generated.")
    build_stage_04()
    print("[+] Stage 04 generated.")
    build_stage_05()
    print("[+] Stage 05 generated.")
    build_stage_06()
    print("[+] Stage 06 generated.")
    build_stage_07()
    print("[+] Stage 07 generated.")
    build_player_instructions()
    build_organizer_docs()
    print("[+] Player instructions & Organizer docs generated.")
    build_release_zips()
    print(f"[+] Release ZIPs built in {time.time() - t0:.2f}s.")


if __name__ == "__main__":
    main()
