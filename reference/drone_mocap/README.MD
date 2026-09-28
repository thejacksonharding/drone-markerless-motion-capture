
## Installation

Requires **Python 3.12+** and [uv](https://docs.astral.sh/uv/).

For the previous group's project we have to install dependencies separately for the CLI and Desktop app. I have updated it to use uv instead of poetry.

Install dependencies for CLI:

```bash
cd drone-markerless-motion-capture/reference/drone_mocap
uv sync
```

Run CLI:

```bash
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd src
python -m drone_mocap.cli
```

Install dependencies for Desktop app:

```bash
deactivate
cd drone-markerless-motion-capture/reference/drone_mocap/drocap_desktop/
uv sync
```

Run CLI:

```bash
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python main.py
```