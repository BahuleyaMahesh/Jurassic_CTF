# MASTER SOLUTION STEPS (Windows 11 PowerShell & Linux)

## Stage 01 — The Excavation
- **Objective:** Recover Sector ID & coordinates.
- **Hidden Clue:** JPEG EXIF/COM in `excavation_01.jpg`; PNG `tEXt` + Red-channel LSBs in `excavation_02.png`.
- **PowerShell:**
```powershell
exiftool excavation_01.jpg
python -c "from PIL import Image; im=Image.open('excavation_02.png'); bits=[p[0]&1 for p in im.getdata()]; bs=bytes(int(''.join(map(str,bits[i:i+8])),2) for i in range(0,len(bits)-7,8)); print(bs.split(b'\x00')[0].decode())"
```
- **Flag:** `JURASSIC[SECTOR_4_38.4420N_109.5120W]`

## Stage 02 — The Dead Frequency
- **Objective:** Recover `HELIX748` from `frequency_748.wav`.
- **Technique:** Bandpass around `748 Hz` (`730–766 Hz`) to decode Morse (`KEY IS HELIX748`), or view spectrogram at `16.5–19.8 kHz` (`PASS:HELIX748`).
- **PowerShell / FFmpeg:**
```powershell
ffmpeg -i frequency_748.wav -af "bandpass=f=748:width_type=h:w=30,volume=15" filtered_748.wav
ffmpeg -i frequency_748.wav -lavfi "showspectrumpic=s=1200x600" spec_02.png
```
- **Flag:** `JURASSIC[HELIX748]`

## Stage 03 — The Negative Specimens
- **Objective:** Recover `VELOCIS-07`, `VAULT-B3`, `V07-DELTA`, `SUBLEVEL-4`.
- **PowerShell (ImageMagick / Python):**
```powershell
magick specimen_01.png -negate out_01.png
magick specimen_02.png -auto-level out_02.png
magick specimen_03.png -channel B -separate -auto-level out_03.png
magick specimen_04.png -evaluate pow 0.25 out_04.png
```
- **Flag:** `JURASSIC[VELOCIS-07_VAULT-B3_SUBLEVEL-4]`

## Stage 04 — The Missing Researcher
- **Objective:** Identify Dr. Aris Thorne & `CRYO_OMEGA_97`.
- **Technique:** Decode Base64/Hex in `staff_records.txt`; inspect PDF metadata, white-on-white text (`pdftotext research_log.pdf -`), and embedded attachment in `experiment_07.pdf`.
- **Flag:** `JURASSIC[ARIS_THORNE_CRYO_OMEGA_97]`

## Stage 05 — The Last Transmission
- **Objective:** Recover `THORNE97` (Left reversed Morse) and `OMEGA748` (Right spectrogram), combine with `HELIX748`.
- **PowerShell / FFmpeg:**
```powershell
ffmpeg -i last_transmission.wav -af "pan=mono|c0=c0,areverse,bandpass=f=2200:w=200" left_rev_2200.wav
ffmpeg -i last_transmission.wav -af "pan=mono|c0=c1" -lavfi "showspectrumpic=s=1200x600" right_spec.png
```
- **Flag:** `JURASSIC[THORNE97-OMEGA748-HELIX748]`

## Stage 06 — Brackett City
- **Objective:** Decrypt `incident_1997.enc` using Stage 05 key.
- **PowerShell / OpenSSL:**
```powershell
openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -in incident_1997.enc -out incident_1997.txt -pass pass:THORNE97-OMEGA748-HELIX748
```
- **Flag:** `JURASSIC[PROTOCOL_OMEGA_CONTAINMENT_1997]`

## Stage 07 — The Extinction Protocol
- **Objective:** Extract XOR+zlib manifest from `extinction_protocol.bin` and decrypt `final_archive.dat`.
- **PowerShell:**
```powershell
python -c "import struct,zlib; d=open('extinction_protocol.bin','rb').read(); m,v,off,ln=struct.unpack('<8sIII',d[:20]); k=b'38.4420N_109.5120W'; print(zlib.decompress(bytes(b^k[i%len(k)] for i,b in enumerate(d[off:off+ln]))).decode())"
openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -in final_archive.dat -out final_archive.txt -pass pass:CRYO_OMEGA_97:OMEGA-PURGE-2342:VELOCIS-07
```
- **Final Flag:** `JURASSIC[EXTINCTION_PROTOCOL_EXECUTED_1997_SECTOR_7]`
