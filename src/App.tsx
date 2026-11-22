import { useState } from 'react';
import { Download, FileArchive, ShieldCheck, Layers, ArrowRight } from 'lucide-react';

interface StageSpec {
  id: string;
  number: string;
  title: string;
  category: string;
  difficulty: string;
  files: string[];
  techniques: string;
  outputSummary: string;
  dependsOn: string;
}

const STAGES: StageSpec[] = [
  {
    id: '01',
    number: '01',
    title: 'The Excavation',
    category: 'Image Forensics / Steganography',
    difficulty: 'Easy',
    files: ['excavation_01.jpg', 'excavation_02.png', 'briefing.txt'],
    techniques: 'JPEG EXIF IFD0/COM inspection, PNG tEXt metadata parsing, Red-channel LSB extraction.',
    outputSummary: 'Sector identifier, geographic coordinates, and calibration prefix for Stage 02.',
    dependsOn: 'Entry stage',
  },
  {
    id: '02',
    number: '02',
    title: 'The Dead Frequency',
    category: 'Audio Forensics',
    difficulty: 'Easy-Medium',
    files: ['frequency_748.wav', 'briefing.txt'],
    techniques: 'Bandpass filtering around 748 Hz, Morse envelope decoding, and 16.5-19.8 kHz ultrasonic spectrogram analysis.',
    outputSummary: 'Facility access password required in downstream multi-part key assembly.',
    dependsOn: 'Stage 01 frequency & prefix clue',
  },
  {
    id: '03',
    number: '03',
    title: 'The Negative Specimens',
    category: 'Image Processing / Digital Forensics',
    difficulty: 'Medium',
    files: ['specimen_01.png', 'specimen_02.png', 'specimen_03.png', 'specimen_04.png', 'briefing.txt'],
    techniques: 'Color inversion, dynamic range auto-leveling, Blue RGB channel isolation, and gamma correction (0.25).',
    outputSummary: 'Specimen designation, containment vault code, and sublevel bay identifier.',
    dependsOn: 'Cross-referenced in Stage 04 & Stage 07',
  },
  {
    id: '04',
    number: '04',
    title: 'The Missing Researcher',
    category: 'Document Forensics / Encoding',
    difficulty: 'Medium',
    files: ['staff_records.txt', 'research_log.pdf', 'experiment_07.pdf', 'briefing.txt'],
    techniques: 'Base64/Hex decoding, PDF Info metadata, white-on-white stream extraction, and embedded PDF file recovery.',
    outputSummary: 'Lead researcher identity, archive key phrase, and stereo-reversal directive for Stage 05.',
    dependsOn: 'Stage 01, Stage 02, Stage 03 references',
  },
  {
    id: '05',
    number: '05',
    title: 'The Last Transmission',
    category: 'Advanced Audio Forensics',
    difficulty: 'Medium-Hard',
    files: ['lab_recording.wav', 'last_transmission.wav', 'briefing.txt'],
    techniques: 'Goertzel DTMF decoding, stereo split, time-reversal of Left channel (2200 Hz Morse), and 14-18.5 kHz Right-channel spectrogram.',
    outputSummary: 'Composite AES-256-CBC decryption key combining Stage 05 parts with Stage 02 password.',
    dependsOn: 'Stage 02 password + Stage 04 reversal note',
  },
  {
    id: '06',
    number: '06',
    title: 'Brackett City',
    category: 'Geospatial Forensics / Cryptography',
    difficulty: 'Hard',
    files: ['brackett_map.png', 'coordinates.dat', 'incident_1997.enc', 'briefing.txt'],
    techniques: 'Tactical map sector correlation and OpenSSL AES-256-CBC PBKDF2 decryption (100,000 iterations).',
    outputSummary: 'Classified July 18, 1997 incident report, incident code, and Stage 07 key derivation rules.',
    dependsOn: 'Stage 01, Stage 03, Stage 05 key',
  },
  {
    id: '07',
    number: '07',
    title: 'The Extinction Protocol',
    category: 'Multi-stage Forensics / Cryptography',
    difficulty: 'Hard',
    files: ['extinction_protocol.bin', 'final_archive.dat', 'briefing.txt'],
    techniques: 'Custom binary header parsing (JEXT1997), repeating-key XOR decryption, zlib decompression, and AES-256-CBC master unlock.',
    outputSummary: 'Final classified confession and competition flag in JURASSIC[...] format.',
    dependsOn: 'Stage 01, Stage 03, Stage 04, Stage 06',
  },
];

const VALIDATION_ITEMS = [
  { check: 'Stage 01a — JPEG EXIF & COM metadata', method: 'TIFF IFD0 + APP1/COM byte parse', status: 'Verified' },
  { check: 'Stage 01b — PNG Red-channel LSB steganography', method: 'Bitwise LSB extraction & tEXt audit', status: 'Verified' },
  { check: 'Stage 02 — 748 Hz Morse & 16.5-19.8 kHz spectrogram', method: 'Goertzel envelope + ultrasonic ratio >100x', status: 'Verified' },
  { check: 'Stage 03 — Four pixel-forensic specimen plates', method: 'Invert, range stretch, B-channel & gamma checks', status: 'Verified' },
  { check: 'Stage 04 — PDF streams, metadata & attachment', method: 'Ghostscript render + embedded file verify', status: 'Verified' },
  { check: 'Stage 05 — Stereo split, DTMF, reversed Morse & spec', method: 'Goertzel DTMF + time-reversed 2200 Hz Morse', status: 'Verified' },
  { check: 'Stage 06 — OpenSSL AES-256-CBC incident report', method: 'PBKDF2 SHA-256 (100k iter) decryption', status: 'Verified' },
  { check: 'Stage 07 — Binary XOR+zlib & final AES-256 archive', method: 'Header unpack + SHA-256 prefix + AES decrypt', status: 'Verified' },
  { check: 'Release isolation — Player ZIP security scan', method: 'Zero organizer files or final flag leaks', status: 'Clean' },
];

export default function App() {
  const [selectedStageId, setSelectedStageId] = useState<string>('01');
  const activeStage = STAGES.find((s) => s.id === selectedStageId) ?? STAGES[0];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Strict 3-Zone Top Bar */}
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-8 px-6 py-4">
          <a
            href="#overview"
            className="text-lg font-bold tracking-tight text-slate-900 whitespace-nowrap shrink-0"
          >
            Jurassic Archive
          </a>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
            <a href="#overview" className="hover:text-slate-900 transition-colors whitespace-nowrap shrink-0">
              Overview
            </a>
            <a href="#downloads" className="hover:text-slate-900 transition-colors whitespace-nowrap shrink-0">
              Downloads
            </a>
            <a href="#stages" className="hover:text-slate-900 transition-colors whitespace-nowrap shrink-0">
              Stages
            </a>
            <a href="#validation" className="hover:text-slate-900 transition-colors whitespace-nowrap shrink-0">
              Validation
            </a>
          </nav>

          <div className="flex items-center shrink-0">
            <a
              href="/downloads/JURASSIC_CTF_PLAYER_PACKAGE.zip"
              download="JURASSIC_CTF_PLAYER_PACKAGE.zip"
              className="inline-flex items-center gap-2 rounded-lg bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 transition-colors whitespace-nowrap shrink-0"
            >
              <Download className="h-3.5 w-3.5" aria-hidden="true" />
              Download Player ZIP
            </a>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-12 space-y-16">
        {/* Hero Overview */}
        <section id="overview" className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-stretch">
          <div className="lg:col-span-7 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-slate-500">
                <span>Brackett City Archive</span>
                <span aria-hidden="true">·</span>
                <span>July 18, 1997</span>
                <span aria-hidden="true">·</span>
                <span>Flag Format: JURASSIC[...]</span>
              </div>
              <h1 className="text-4xl font-bold tracking-tight text-slate-900 leading-tight text-balance">
                JURASSIC: The Extinction Protocol
              </h1>
              <p className="text-base text-slate-600 leading-relaxed max-w-2xl">
                A complete 7-stage digital forensics, steganography, audio signal processing, and
                cryptography competition set in the abandoned 1997 BioGenesis Paleotech complex
                outside Brackett City. Every stage embeds deterministic, tool-verifiable evidence
                across photographs, 44.1 kHz WAV recordings, PDFs, binaries, and OpenSSL AES-256-CBC
                archives.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="text-xs text-slate-500">Challenge Stages</div>
                <div className="mt-1 text-2xl font-mono font-semibold tabular-nums text-slate-900">07</div>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="text-xs text-slate-500">Audio Sample Rate</div>
                <div className="mt-1 text-2xl font-mono font-semibold tabular-nums text-slate-900">
                  44.1<span className="ml-1 text-xs font-normal text-slate-500">kHz</span>
                </div>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="text-xs text-slate-500">Cipher Standard</div>
                <div className="mt-1 text-2xl font-mono font-semibold tabular-nums text-slate-900">
                  256<span className="ml-1 text-xs font-normal text-slate-500">bit AES</span>
                </div>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="text-xs text-slate-500">Deterministic Seed</div>
                <div className="mt-1 text-xl font-mono font-semibold tabular-nums text-slate-900">19970718</div>
              </div>
            </div>
          </div>

          {/* Direct Download Panel */}
          <div id="downloads" className="lg:col-span-5 rounded-lg border border-slate-200 bg-white p-6 flex flex-col justify-between space-y-6">
            <div className="space-y-2">
              <h2 className="text-lg font-semibold text-slate-900">Competition Release Packages</h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                Distribute only the Player Package to competitors. Keep the Organizer Package strictly
                separate for competition administration and automated validation.
              </p>
            </div>

            <div className="space-y-4">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Player Challenge Package</div>
                    <div className="mt-0.5 text-xs font-mono text-slate-500">
                      JURASSIC_CTF_PLAYER_PACKAGE.zip · Stages 01–07 + Instructions PDF
                    </div>
                  </div>
                  <FileArchive className="h-5 w-5 text-teal-700 shrink-0" aria-hidden="true" />
                </div>
                <a
                  href="/downloads/JURASSIC_CTF_PLAYER_PACKAGE.zip"
                  download="JURASSIC_CTF_PLAYER_PACKAGE.zip"
                  className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-800 transition-colors whitespace-nowrap"
                >
                  <Download className="h-4 w-4" aria-hidden="true" />
                  Download Player ZIP
                </a>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Organizer Answer Key & Scripts</div>
                    <div className="mt-0.5 text-xs font-mono text-slate-500">
                      JURASSIC_CTF_ORGANIZER_ONLY.zip · Key, Hints, Generator & Validator
                    </div>
                  </div>
                  <ShieldCheck className="h-5 w-5 text-slate-700 shrink-0" aria-hidden="true" />
                </div>
                <a
                  href="/downloads/JURASSIC_CTF_ORGANIZER_ONLY.zip"
                  download="JURASSIC_CTF_ORGANIZER_ONLY.zip"
                  className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-900 hover:bg-slate-100 transition-colors whitespace-nowrap"
                >
                  <Download className="h-4 w-4" aria-hidden="true" />
                  Download Organizer ZIP
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Interactive 7-Stage Forensics Explorer */}
        <section id="stages" className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-slate-200 pb-4">
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                Seven-Stage Investigation Pipeline
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Select any stage to inspect its forensic artifacts, techniques, and cross-stage dependencies.
              </p>
            </div>
            <div className="text-xs font-mono text-slate-500">
              Expected Solve Duration: 45–90 Minutes
            </div>
          </div>

          {/* Interactive Filter Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 rounded-lg bg-slate-100 p-1.5 border border-slate-200">
            {STAGES.map((stage) => {
              const active = stage.id === selectedStageId;
              return (
                <button
                  key={stage.id}
                  type="button"
                  onClick={() => setSelectedStageId(stage.id)}
                  className={`px-3 py-2 text-xs font-medium rounded-md transition-colors whitespace-nowrap shrink-0 cursor-pointer ${
                    active
                      ? 'bg-white text-slate-900 border border-slate-200'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Stage {stage.number}
                </button>
              );
            })}
          </div>

          {/* Active Stage Detail Card */}
          <div className="rounded-lg border border-slate-200 bg-white p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-7 space-y-4">
              <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-slate-500">
                <span>Stage {activeStage.number}</span>
                <span aria-hidden="true">·</span>
                <span>{activeStage.category}</span>
                <span aria-hidden="true">·</span>
                <span>Difficulty: {activeStage.difficulty}</span>
              </div>
              <h3 className="text-2xl font-bold text-slate-900">{activeStage.title}</h3>
              <p className="text-sm text-slate-700 leading-relaxed">{activeStage.techniques}</p>
              <div className="pt-2 space-y-1.5 text-sm">
                <div className="font-semibold text-slate-900">Recovered Output</div>
                <div className="text-slate-600">{activeStage.outputSummary}</div>
              </div>
              <div className="pt-1 flex items-center gap-2 text-xs font-mono text-teal-800">
                <ArrowRight className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                <span>Dependency: {activeStage.dependsOn}</span>
              </div>
            </div>

            <div className="lg:col-span-5 rounded-lg bg-slate-50 border border-slate-200 p-5 space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                <Layers className="h-3.5 w-3.5" aria-hidden="true" />
                <span>Player Artifacts</span>
              </div>
              <ul className="space-y-2">
                {activeStage.files.map((fname) => (
                  <li
                    key={fname}
                    className="flex items-center justify-between border-b border-slate-200 last:border-b-0 pb-2 last:pb-0 text-sm font-mono text-slate-800"
                  >
                    <span>{fname}</span>
                    <span className="text-xs text-slate-500">Included in ZIP</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* Automated Validation Matrix */}
        <section id="validation" className="space-y-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              Automated Forensic Verification
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Every stage in the release archive is independently solved and audited by validate_ctf.py.
            </p>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-xs font-semibold text-slate-600">
                  <th className="px-4 py-3">Verification Check</th>
                  <th className="px-4 py-3">Forensic Extraction Method</th>
                  <th className="px-4 py-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-sm">
                {VALIDATION_ITEMS.map((item) => (
                  <tr key={item.check} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-slate-900">{item.check}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-600">{item.method}</td>
                    <td className="px-4 py-3 text-right font-mono text-xs font-semibold text-teal-700">
                      {item.status}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white mt-16">
        <div className="mx-auto flex max-w-6xl flex-col sm:flex-row items-center justify-between gap-4 px-6 py-6 text-xs text-slate-500">
          <span>JURASSIC: The Extinction Protocol · Deterministic Forensic Archive</span>
          <div className="flex items-center gap-6">
            <a href="/downloads/JURASSIC_CTF_PLAYER_PACKAGE.zip" download className="hover:text-slate-900">
              Player ZIP
            </a>
            <a href="/downloads/JURASSIC_CTF_ORGANIZER_ONLY.zip" download className="hover:text-slate-900">
              Organizer ZIP
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
