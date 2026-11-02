import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QGroupBox, QGridLayout, QProgressBar,
    QFileDialog, QSplitter
)
from PyQt6.QtGui import QAction, QPixmap, QImage
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# ==============================================================================
# 1. BACKGROUND WORKER (Mocks the Pipeline)
# ==============================================================================
class PipelineWorker(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    results_ready = pyqtSignal(dict)

    def run(self):
        # This simulates the pipeline processing
        steps = [
            "Loading videos...",
            "Running RTMPose (2D Estimation)...",
            "Extracting ChArUco calibration...",
            "Running Linear Triangulation...",
            "Calculating Kinematics...",
            "Generating Report..."
        ]
        
        for i, step in enumerate(steps):
            self.status_updated.emit(step)
            time.sleep(0.8) # Fake processing time
            self.progress_updated.emit(int(((i + 1) / len(steps)) * 100))

        # Send dummy 3D data back to the GUI
        dummy_results = {
            "joints_3d": np.random.rand(3, 15) * 1000, # 3 rows (x,y,z), 15 joints
            "mae": 14.2,
            "frames": 1500,
            "status": "Success"
        }
        self.results_ready.emit(dummy_results)


# ==============================================================================
# 2. CUSTOM PANELS
# ==============================================================================
class VideoPanel(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        layout = QVBoxLayout(self)
        
        self.video_label = QLabel("No Video Loaded")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #1e1e1e; color: #888; border: 1px solid #333;")
        self.video_label.setMinimumSize(400, 300)
        
        layout.addWidget(self.video_label)

    def display_dummy_image(self, text):
        # Creates a dummy image with text so we can see the panel working
        img = QImage(640, 480, QImage.Format.Format_RGB32)
        img.fill(Qt.GlobalColor.black)
        
        # We just set text for now since generating pixels is messy for a mockup
        self.video_label.setText(f"📷 {text}\n(Dummy Video Feed)")
        self.video_label.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-size: 20px;")


class PlotPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("3D Reconstruction", parent)
        layout = QVBoxLayout(self)
        
        # Setup Matplotlib Figure
        self.fig = plt.Figure(figsize=(5, 4), dpi=100)
        self.fig.patch.set_facecolor('#2b2b2b') # Dark theme for plot
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        
        self.update_plot(None)

    def update_plot(self, joints_3d):
        self.ax.clear()
        
        # Style the 3D plot
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.zaxis.label.set_color('white')
        self.ax.title.set_color('white')
        
        if joints_3d is not None:
            x, y, z = joints_3d
            self.ax.scatter(x, y, z, c='#00ff00', marker='o', s=50, label='Joints')
            self.ax.set_title("Live 3D Skeleton")
        else:
            self.ax.set_title("Waiting for Pipeline...")

        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.set_zlabel("Z (mm)")
        
        self.canvas.draw()


class MetricsPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Metrics & Logs", parent)
        layout = QVBoxLayout(self)
        
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        self.metrics_text.setStyleSheet("background-color: #1e1e1e; color: #ccc; font-family: monospace;")
        
        layout.addWidget(QLabel("System Log:"))
        layout.addWidget(self.metrics_text)
        
    def log(self, message, level="INFO"):
        color = "#00ff00" if level == "INFO" else "#ff0000"
        self.metrics_text.append(f"<span style='color:{color}'>[{level}]</span> {message}")
        
    def update_metrics(self, results):
        self.log(f"Joint MAE: {results['mae']} mm")
        self.log(f"Frames Processed: {results['frames']}")
        self.log("Pipeline finished successfully.")


# ==============================================================================
# 3. MAIN WINDOW (Layout & Glue)
# ==============================================================================
class DroCapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DroCap 2.0 - Markerless Motion Capture")
        self.resize(1400, 900)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; }
            QGroupBox { 
                color: white; 
                border: 1px solid #555; 
                border-radius: 5px; 
                margin-top: 10px; 
                font-weight: bold;
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; }
            QPushButton { 
                background-color: #444; color: white; border: 1px solid #555; 
                padding: 8px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #555; }
            QPushButton:disabled { background-color: #333; color: #777; }
            QLabel { color: white; }
        """)

        # --- Create Menu Bar ---
        self.create_menus()

        # --- Main Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Top Section: Control Panel (Load, Run, Progress Bar)
        top_control_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("📂 Load Project")
        self.btn_load.clicked.connect(self.mock_load_project)
        
        self.btn_run = QPushButton("▶ Run Pipeline")
        self.btn_run.clicked.connect(self.run_pipeline)
        self.btn_run.setEnabled(False) # Disabled until project loaded
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #555; border-radius: 5px; text-align: center; color: white; } QProgressBar::chunk { background-color: #00aa00; }")
        
        top_control_layout.addWidget(self.btn_load)
        top_control_layout.addWidget(self.btn_run)
        top_control_layout.addWidget(self.progress_bar, stretch=1)
        
        main_layout.addLayout(top_control_layout)

        # 2. Main Grid: Videos on top, 3D Plot & Metrics on bottom
        grid_layout = QGridLayout()
        
        # Top Row: Two Video Panels
        self.video1_panel = VideoPanel("Camera 1 (Left / iPhone 1)")
        self.video2_panel = VideoPanel("Camera 2 (Right / iPhone 2)")
        grid_layout.addWidget(self.video1_panel, 0, 0)
        grid_layout.addWidget(self.video2_panel, 0, 1)

        # Bottom Row: 3D Plot and Metrics
        self.plot_panel = PlotPanel()
        self.metrics_panel = MetricsPanel()
        
        # Splitter lets the user resize the 3D plot vs the metrics
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.plot_panel)
        splitter.addWidget(self.metrics_panel)
        splitter.setSizes([600, 400])
        
        grid_layout.addWidget(splitter, 1, 0, 1, 2) # Span both columns

        main_layout.addLayout(grid_layout)
        
        # Set row/column stretching so videos take up good space
        grid_layout.setRowStretch(0, 3)
        grid_layout.setRowStretch(1, 2)

    def create_menus(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        
        action_open = QAction("Open Project...", self)
        action_open.triggered.connect(self.mock_load_project)
        file_menu.addAction(action_open)
        
        action_exit = QAction("Exit", self)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)
        
        # Help Menu
        help_menu = menubar.addMenu("Help")
        action_about = QAction("About DroCap 2.0", self)
        help_menu.addAction(action_about)

    def mock_load_project(self):
        self.metrics_panel.log("Opening file dialog...")
        
        # Simulate loading a project
        self.metrics_panel.log("Project 'TrailRun_001' loaded.")
        self.metrics_panel.log("Found: drone_01.mp4, drone_02.mp4, calibration.yaml")
        
        self.video1_panel.display_dummy_image("Camera 1: Raw Feed")
        self.video2_panel.display_dummy_image("Camera 2: Raw Feed")
        
        self.btn_run.setEnabled(True)
        self.progress_bar.setValue(0)

    def run_pipeline(self):
        self.metrics_panel.log("Starting pipeline worker thread...")
        self.btn_run.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Setup the worker thread
        self.worker = PipelineWorker()
        self.worker.status_updated.connect(self.metrics_panel.log)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.results_ready.connect(self.on_pipeline_complete)
        
        self.worker.start()

    def on_pipeline_complete(self, results):
        self.metrics_panel.update_metrics(results)
        self.metrics_panel.log("Updating 3D plot with results.")
        
        # Update the plot with the dummy 3D coordinates
        self.plot_panel.update_plot(results["joints_3d"])
        
        self.btn_run.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = DroCapApp()
    window.show()
    sys.exit(app.exec())