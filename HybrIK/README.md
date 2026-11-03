# Reproducible HybrIK macOS setup

These scripts document the **verified successful** Apple Silicon run of HybrIK on 600 frames of `footage/processed/aidan_walking_85s_10s.mp4` (1280×720, 59.94 fps). CPU inference took 17m28s in the latest run. They are prepared from the terminal log, **not independently executed in this sandbox**.

## Important prerequisites

- Apple Silicon Mac, Python 3.9.21 installed at `~/.pyenv/versions/3.9.21/bin/python`, Git, Xcode Command Line Tools, FFmpeg.
- Place these scripts in the **repository root** under `scripts/`.
- The current **working** modified files must be retained and committed in the repository:
  - `HybrIK/scripts/demo_video.py` (`--device {auto,cuda,mps,cpu}` support)
  - `HybrIK/hybrik/utils/presets/__init__.py` (lazy SMPLX import fix)
  - `HybrIK/hybrik/version.py` (modified by editable install; review diff before deciding whether to commit)
  - `HybrIK/scripts/pytorch3d_cpu_bounds.patch` (patch applied to PyTorch3D CPU rasterizer)
- Preserve `HybrIK/model_files/` with `basicModel_neutral_lbs_10_207_0_v1.0.0.pkl`, `h36m_mean_beta.npy`, `J_regressor_h36m.npy`. These are not downloaded or included here; verify their licenses before sharing.
- This package **does not contain** the above modified HybrIK source files or patch because their contents were not supplied. Copy them from your successful local working checkout, not from the earlier unmodified Git commit.

## Commands (from repository root)

```bash
bash scripts/setup_hybrik_macos.sh
bash scripts/download_models.sh
bash scripts/run_hybrik.sh
bash scripts/verify_results.sh
```

The default run expects the existing 10-second clip at `footage/processed/aidan_walking_85s_10s.mp4`. To generate it from the original 3.3 GB video (if needed):

```bash
mkdir -p footage/processed
ffmpeg -ss 85 -i footage/drone_footage.MP4 -t 10 -c:v libx264 -pix_fmt yuv420p -an footage/processed/aidan_walking_85s_10s.mp4
```

To run another input, provide an **absolute** input path, a new output folder name, and optional device:

```bash
bash scripts/run_hybrik.sh "$PWD/footage/processed/aidan_walking_85s_10s.mp4" res_test cpu
```

The script refuses to overwrite an existing result folder. Ensure sufficient free disk space: HybrIK extracts every frame to PNG and saves rendered images. A prior run failed due to `No space left on device`; subsequent complete run succeeded.

## Confirmed output

`HybrIK/res_aidan_walking_85s_10s/res.pk` had `pred_xyz_29` shape `(600,29,3)` and `pred_xyz_17` shape `(600,17,3)`. Videos: `res_aidan_walking_85s_10s.mp4` and `res_2d_aidan_walking_85s_10s.mp4`.

## Known environment caveats

- `pip check` reported `tb-nightly` missing and HybrIK's declared OpenCV requirement `==4.1.2.30` conflicting with installed `4.8.1.78`. The 600-frame inference still completed. Do not downgrade blindly.
- PyTorch3D was built from commit `75ebeeaea0908c5527e7b1e305fbc7681382db47` (v0.7.8), using clang and the custom patch.
- No need to install `tb-nightly` solely to run the verified demo.
- `pip freeze > hybrik-working-requirements.txt` was executed in the successful run; preserve that file as a supplementary environment snapshot.
- Do not commit `.venv`, pretrained weights, raw footage, model files without checking licenses, or generated frames.
