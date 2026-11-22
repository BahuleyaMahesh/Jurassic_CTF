================================================================================
JURASSIC: THE EXTINCTION PROTOCOL (1997 BRACKETT CITY INCIDENT CTF)
================================================================================

OVERVIEW
--------
In 1997, BioGenesis Paleotech established a classified prehistoric genetics
research complex outside Brackett City. On July 18, 1997, all communications
ceased and every researcher vanished.

This repository contains the complete generator, automated forensic validation
suite, player distribution package, and organizer materials.

DIRECTORY STRUCTURE
-------------------
- README.txt            This file
- requirements.txt      Recommended Python libraries
- generate_ctf.py       Deterministic CTF generator (seed = 19970718)
- validate_ctf.py       End-to-end automated forensic solver & validator
- PLAYER_PACKAGE/       Player-facing challenge directories (Stages 01-07)
- ORGANIZER_ONLY/       Answer key, hints, dependency graph, validation report
- RELEASE/              Packaged ZIP archives for distribution

QUICK START (REPRODUCE & VALIDATE)
----------------------------------
1. Generate all challenge assets, answer key, and release ZIPs:
     python3 generate_ctf.py

2. Run automated forensic verification against all 7 stages:
     python3 validate_ctf.py

REQUIREMENTS
------------
- Python 3.10+
- Standard CLI utilities (ImageMagick `convert`, `ffmpeg`, `openssl`) or the
  Python packages listed in requirements.txt.

SECURITY NOTICE
---------------
NEVER distribute ORGANIZER_ONLY/ or RELEASE/JURASSIC_CTF_ORGANIZER_ONLY.zip to
competition participants. Only distribute RELEASE/JURASSIC_CTF_PLAYER_PACKAGE.zip.
