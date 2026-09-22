# Drone MoCap

Dual-drone markerless motion capture system for 3D biomechanical analysis.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/thejacksonharding/drone-markerless-motion-capture.git
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Activate the virtual environment

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

---

## Usage

Run the application:

```bash
python -m drone_mocap
```

---

## Development

Install new dependencies:

```bash
uv add <package>
```

Run tests:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check .
```