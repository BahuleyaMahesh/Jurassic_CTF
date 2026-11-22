# Progressive Hints (2 Hints per Stage)

## Stage 01 — The Excavation
- **Hint 1:** Check `excavation_01.jpg` metadata (`exiftool` or `strings`) and the PNG `tEXt` comment inside `excavation_02.png`.
- **Hint 2:** Extract the least significant bit (`& 1`) of the Red channel only in `excavation_02.png`, packed 8 bits per byte MSB-first.

## Stage 02 — The Dead Frequency
- **Hint 1:** The stage name points to 748 Hz, and the static around 748 Hz has been notched out to hide a faint Morse carrier.
- **Hint 2:** Apply a narrow bandpass filter around 748 Hz (`730–766 Hz`) OR view the spectrogram between 16.5 kHz and 19.8 kHz.

## Stage 03 — The Negative Specimens
- **Hint 1:** Each PNG uses a different pixel transform: invert (`255-x`), extreme dark compression, single RGB channel isolation, and dark gamma.
- **Hint 2:** Invert `specimen_01`, auto-level `specimen_02`, inspect only the Blue channel of `specimen_03`, and apply `gamma=0.25` (or threshold > 12) to `specimen_04`.

## Stage 04 — The Missing Researcher
- **Hint 1:** Decode the Base64 and Hex strings in `staff_records.txt` and inspect the `/Keywords` metadata of `research_log.pdf`.
- **Hint 2:** `research_log.pdf` Page 2 has white-on-white text (`pdftotext` or `strings`), and `experiment_07.pdf` has an embedded attachment (`transmission_protocol.txt`).

## Stage 05 — The Last Transmission
- **Hint 1:** Split `last_transmission.wav` into Left and Right mono tracks; reverse the Left channel in time.
- **Hint 2:** Decode 2200 Hz Morse in the reversed Left channel (`THORNE97`), inspect 14–18.5 kHz spectrogram in the Right channel (`OMEGA748`), and append Stage 02's password.

## Stage 06 — Brackett City
- **Hint 1:** Read `coordinates.dat` for the exact OpenSSL AES-256-CBC PBKDF2 cipher parameters and key formula.
- **Hint 2:** Decrypt `incident_1997.enc` using `THORNE97-OMEGA748-HELIX748`.

## Stage 07 — The Extinction Protocol
- **Hint 1:** Parse the 32-byte header of `extinction_protocol.bin` (`JEXT1997`) to find the payload offset (64) and length; ignore the decoy string.
- **Hint 2:** XOR bytes `[64 : 64+len]` with `38.4420N_109.5120W`, `zlib.decompress`, then decrypt `final_archive.dat` with `CRYO_OMEGA_97:OMEGA-PURGE-2342:VELOCIS-07`.
