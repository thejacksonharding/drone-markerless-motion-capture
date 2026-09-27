import tkinter as tk
from tkinter import ttk


class CaptureApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Drone MoCap — Capture")
        self.geometry("480x320")
        self.resizable(False, False)
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Drone MoCap",
            font=("TkDefaultFont", 16, "bold"),
        ).pack(anchor="w")

        ttk.Separator(frame).pack(fill="x", pady=12)

        # Status rows
        self._status_row(frame, "Camera A", "Not connected")
        self._status_row(frame, "Camera B", "Not connected")
        self._status_row(frame, "Sync", "Not calibrated")
        self._status_row(frame, "Calibration", "Not loaded")

        ttk.Separator(frame).pack(fill="x", pady=12)

        # Controls
        controls = ttk.Frame(frame)
        controls.pack(fill="x")

        self.start_btn = ttk.Button(
            controls, text="Start Recording", command=self._on_start
        )
        self.start_btn.pack(side="left")

        self.stop_btn = ttk.Button(
            controls, text="Stop", command=self._on_stop, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(8, 0))

        # Status bar
        self.status = ttk.Label(frame, text="Ready", foreground="gray")
        self.status.pack(anchor="w", pady=(16, 0))

    def _status_row(self, parent: ttk.Frame, label: str, value: str) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=f"{label}:", width=14).pack(side="left")
        ttk.Label(row, text=value, foreground="gray").pack(side="left")

    def _on_start(self) -> None:
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status.config(text="Recording...", foreground="green")

    def _on_stop(self) -> None:
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status.config(text="Ready", foreground="gray")


