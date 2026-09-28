# Drone-Based Markerless Motion Capture

Dual-drone markerless motion capture for 3D biomechanical analysis of outdoor athlete movement.

Built as a multi-year capstone design project (ENGG 501/502) in partnership with the
**Sport Product Testing (SPT) Group** at Canadian Sport Institute Alberta.

---

## Overview

Traditional marker-based motion capture is accurate but confined to the lab. Markerless
systems exist but require multi-camera arrays around a fixed volume. Wearable IMU systems
capture full sessions but are obtrusive and can shift during activity.

This project develops a **drone-based, markerless** alternative. Two camera-equipped drones
follow an athlete, capture synchronized video, and software reconstructs 3D joint and
segment kinematics — with no markers, no lab, and minimal interference with natural
movement.

Target sports include trail running, skiing, bobsleigh starts, and track and field events.

The system is designed for use in sports science, biomechanics research, and athlete
performance optimization.

---

## System Pipeline

```
     project.yaml + videos + calibration
                    │
                    ▼
             ┌──────────────┐
             │  project/    │  loads config, provides paths, tracks state
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │  video/      │  frames + metadata + synchronization
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │  pose/       │  2D landmarks per camera
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │  processing/ │  filter, fill gaps, reject outliers
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │reconstruction│  calibration + 2D → 3D
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │ kinematics/  │  angles, events, metrics
             └──────┬───────┘
                    │
              ┌─────┴─────┐
              ▼           ▼
     ┌──────────────┐ ┌──────────────┐
     │ validation/  │ │visualization/│
     └──────┬───────┘ └──────┬───────┘
            │                │
            └───────┬────────┘
                    ▼
             ┌──────────────┐
             │  reporting/  │  CSVs, PDF, videos
             └──────────────┘
```

`pipeline/` walks this chain. `gui/` drives `pipeline/`. `project/` provides context.

---

## Repository Structure

```
drone-markerless-motion-capture/
├── src/drone_mocap/
│   ├── __init__.py
│   ├── run.py                  # application entry point
│   │
│   ├── gui/                    # Tkinter windows and panels
│   ├── pipeline/               # orchestration
│   ├── project/                # per-analysis container (config, storage, state)
│   │
│   ├── video/                  # video files, frames, metadata, synchronization
│   ├── pose/                   # 2D landmark estimation
│   ├── processing/             # filtering, gap filling, outlier rejection
│   ├── reconstruction/         # calibration + 3D reconstruction
│   ├── kinematics/             # joint angles, events, metrics
│   │
│   ├── validation/             # accuracy vs. reference data
│   ├── visualization/          # plots, skeletons, trajectories
│   └── reporting/              # CSVs, PDF, diagnostic videos
│
├── tests/                      # pytest suite, mirrors src/
├── docs/                       # architecture, data dictionary, protocols
├── examples/                   # example project folder
└── outputs/                    # generated artifacts (gitignored)
```

Each subsystem exposes a small public API in its `__init__.py`. The GUI never imports
a subsystem directly — it goes through `pipeline/`.

---

## Installation

Requires **Python 3.12+** and [uv](https://docs.astral.sh/uv/).

Install uv package manager, clone into repository, and install dependencies:

```bash
pip install uv      
git clone https://github.com/thejacksonharding/drone-markerless-motion-capture.git
cd drone-markerless-motion-capture
uv sync
```

`uv sync` creates `.venv/`, installs all dependencies, and installs `drone_mocap` in
editable mode. No separate install step.

---

## Running

### Activate virtual environment

```bash
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m drone_mocap.run
```

### Standalone Executable App

Building a self-contained executable app or running pytests requires some extra dependencies:

```bash
uv sync --extra dev
```

Build the self-contained app with:

```bash
pyinstaller drone_app.spec
```

On macOS this produces `dist/drone-mocap.app`. Launch it with:

```bash
open dist/drone-mocap.app
```

For debugging, run the inner binary to see terminal output:

```bash
./dist/drone-mocap.app/Contents/MacOS/drone-mocap
```

On Windows and Linux, `dist/drone-mocap` is a plain executable.
Run with:

```bash
./dist/drone-mocap
```

---

## Testing

```bash
pytest
```

Tests mirror the source layout. Each subsystem has its own test folder under
`tests/`. Tests follow BDD format.

---

## Project Layout at Runtime

A **DroCap project** is a folder. It holds everything needed to reproduce one analysis.

```
TrailRun_001/
├── project.yaml            # what the user asked DroCap to do
├── input/
│   ├── drone_01.mp4
│   └── drone_02.mp4
├── calibration/
│   ├── camera_01.yaml
│   ├── camera_02.yaml
│   └── stereo.yaml
├── processing/             # intermediate state
├── output/
│   ├── motion/
│   ├── visualizations/
│   └── report/
├── validation/
└── manifest.json           # what DroCap actually did
```

`project.yaml` is the source of truth for one analysis: which videos, which cameras,
which calibration, which sync method, which pose model, which filter, which metrics,
whether to validate against a reference, and where results go.

`manifest.json` records what was actually run: software version, git commit, timestamps,
resolved parameters, and completion status. It's how you answer "how did I get these
results?" six months later.

---

## Outputs

For each project run, the system generates:

| Output | Description |
|---|---|
| `angles.csv` | Per-frame joint angles, per side, in degrees |
| `segments.csv` | Per-frame segment orientations |
| `joint_positions.csv` | Per-frame 3D joint centers, in meters |
| `events.csv` | Gait and sport-specific events |
| `manifest.json` | What was actually done, with versions |
| `sync_report.json` | Time offset and QC metrics between views |
| `tracking_qc.json` | Valid frame percentage and dropout statistics |
| `diagnostic_*.mp4` | Annotated video with skeleton overlay |
| `reconstruction_3d.mp4` | 3D view of the triangulated skeleton |
| `summary.pdf` | Plots, scalar metrics, metadata |

When reference MoCap or IMU data is supplied:

| Output | Description |
|---|---|
| `validation_metrics.json` | RMSE, bias, limits of agreement per joint |
| `validation_report.pdf` | Human-readable validation report |

See `docs/OUTPUTS.md` for full details, units, and sign conventions.

---

## Subsystems

| Subsystem | Question it answers | Produces |
|---|---|---|
| `project/` | What analysis am I doing? | Project config, paths, state, manifest |
| `video/` | What footage am I analyzing? | Frames, metadata, sync offset |
| `pose/` | Where are the joints in 2D? | `LandmarkStream` per camera |
| `processing/` | How do I clean the data? | Filtered landmarks |
| `reconstruction/` | Where are the joints in 3D? | `Trajectory3D` |
| `kinematics/` | How is the athlete moving? | Angles, events, metrics |
| `validation/` | How accurate is it? | Validation metrics |
| `visualization/` | How do I see the results? | Plots and rendered video |
| `reporting/` | How do I communicate results? | CSVs, PDF |
| `pipeline/` | In what order do these run? | RunContext |
| `gui/` | How does the user drive it? | Tkinter windows |

---

## Documentation

| Document | Purpose |
|---|---|
| `docs/ARCHITECTURE.md` | System design, subsystem responsibilities, data flow |
| `docs/DATA_DICTIONARY.md` | Every output column, unit, and sign convention |
| `docs/CALIBRATION_PROTOCOL.md` | Rig setup and verification |
| `docs/VALIDATION_PROTOCOL.md` | Comparison against reference MoCap/IMU |
| `docs/OUTPUTS.md` | Full run directory layout and file formats |
| `docs/USER_GUIDE.md` | End-user walkthrough |

---

## Known Limitations

- **Two cameras are required for 3D.** A single drone produces 2D sagittal estimates only.

---

## Team

Capstone design project (ENGG 501/502), University of Calgary.

| Role | Name |
|---|---|
| Student | Jackson Harding |
| Student | _(add)_ |
| Student | _(add)_ |
| Student | _(add)_ |
| Supervisor | _(add)_ |
| Sponsor contact | Dr. Christian Clermont, Sport Product Testing |

---

## Acknowledgments

Developed in partnership with the **Sport Product Testing (SPT) Group** at
[Canadian Sport Institute Alberta](https://www.csialberta.ca/).

Funded in part by a voluntary financial contribution from SPT.

Built on the initial prototype and foundational algorithms developed by the previous
year's capstone team.

---

## License

MIT — see [`LICENSE`](LICENSE).