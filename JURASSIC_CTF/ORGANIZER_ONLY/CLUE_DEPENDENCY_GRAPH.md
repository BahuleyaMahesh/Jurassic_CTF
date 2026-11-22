# Clue Dependency Graph

```text
STAGE 01 (excavation_01.jpg EXIF + excavation_02.png Red-LSB)
  ├── Grid Ref: 38.4420N_109.5120W ──────────► Stage 04, Stage 06 Map, Stage 07 (.bin XOR key)
  ├── Frequency Hint: 748Hz ─────────────────► Stage 02 (carrier notch Morse)
  └── Auth Prefix: AMBER97 ──────────────────► Stage 04 cross-check
        │
        ▼
STAGE 02 (frequency_748.wav: 748Hz Morse + 16.5-19.8kHz spectrogram)
  └── Password: HELIX748 ────────────────────► Stage 05/06 AES key suffix
        │
        ▼
STAGE 03 (specimen_01..04.png: invert, auto-level, Blue ch, gamma)
  ├── Specimen ID: VELOCIS-07 (Code V07-DELTA) ► Stage 04, Stage 07 AES passphrase
  └── Location: VAULT-B3 / SUBLEVEL-4 ───────► Stage 04, Stage 06 Map
        │
        ▼
STAGE 04 (staff_records.txt + research_log.pdf + experiment_07.pdf)
  ├── Lead Researcher: ARIS_THORNE ──────────► Stage 04 Flag, Stage 06/07
  ├── Key Phrase: CRYO_OMEGA_97 ─────────────► Stage 07 AES passphrase
  └── Warning: Reverse Stage 05 Left Channel ► Stage 05
        │
        ▼
STAGE 05 (lab_recording.wav + last_transmission.wav stereo)
  ├── Left (reversed 2200Hz Morse): THORNE97 ─┐
  ├── Right (14-18.5kHz spec)     : OMEGA748 ─┼─► AES Key: THORNE97-OMEGA748-HELIX748
  └── Stage 02 Password           : HELIX748 ─┘       │
                                                      ▼
STAGE 06 (brackett_map.png + coordinates.dat + incident_1997.enc)
  └── Incident Code: OMEGA-PURGE-2342 + Key Rules ────► Stage 07
        │
        ▼
STAGE 07 (extinction_protocol.bin + final_archive.dat)
  ├── XOR(.bin[64:], '38.4420N_109.5120W') -> zlib -> AES formula
  └── OpenSSL AES-256-CBC('CRYO_OMEGA_97:OMEGA-PURGE-2342:VELOCIS-07') -> FINAL FLAG
```
