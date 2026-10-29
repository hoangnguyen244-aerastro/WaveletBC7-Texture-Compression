"""WaveletBC7 Research Studio: local PySide6 experiment interface."""
from __future__ import annotations
import csv
import json
import sys
import traceback
from pathlib import Path
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
 QHBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QComboBox,
 QTableWidget, QTableWidgetItem, QMessageBox, QSplitter, QScrollArea)
from src.wavelet_bc7.research import Configuration, Method, run
from src.wavelet_bc7.analysis import analyze
from scripts.generate_report import generate

ROOT = Path(__file__).resolve().parents[1]

class Worker(QObject):
    finished = Signal(str)
    failed = Signal(str)
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
    def execute(self):
        try:
            result = run(self.cfg)
            analyze(result)
            generate(result.parent)
            self.finished.emit(str(result.parent))
        except Exception:
            self.failed.emit(traceback.format_exc())

def image_pixmap(path, error_against=None):
    with Image.open(path) as img:
        rgb = np.array(img.convert("RGB"), dtype=np.uint8)
    if error_against is not None:
        with Image.open(error_against) as img:
            original = np.array(img.convert("RGB"), dtype=np.uint8)
        if original.shape != rgb.shape:
            raise ValueError("Images have different sizes")
        diff = np.abs(original.astype(np.int16) - rgb.astype(np.int16))
        strength = np.clip(diff.mean(axis=2) * 8, 0, 255).astype(np.uint8)
        rgb = np.stack([strength, np.zeros_like(strength), 255-strength], axis=2)
    h,w,_ = rgb.shape
    return QPixmap.fromImage(QImage(rgb.tobytes(),w,h,3*w,QImage.Format.Format_RGB888).copy())

class Studio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WaveletBC7 Research Studio — Pilot & Parameter Sweep")
        self.resize(1250,850)
        self.thread = None
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        controls = QHBoxLayout()
        layout.addLayout(controls)
        self.manifest = QLineEdit(str(ROOT/"datasets"/"manifest.csv"))
        self.exe = QLineEdit(str(ROOT/"tools"/"texconv.exe"))
        self.output = QLineEdit(str(ROOT/"results"/"experiments"/"gui_sweep_001"))
        self.strengths = QLineEdit("0.25, 0.5, 1, 2, 4, 6, 8")
        self.split = QComboBox()
        self.split.addItems(["pilot","train","validation","test"])
        for label,edit in [("Manifest",self.manifest),("texconv",self.exe),("Output",self.output)]:
            line=QHBoxLayout()
            line.addWidget(QLabel(label))
            line.addWidget(edit)
            browse=QPushButton("Browse")
            browse.clicked.connect(lambda checked=False,e=edit,d=label:self.browse(e,d))
            line.addWidget(browse)
            layout.addLayout(line)
        controls.addWidget(QLabel("Split:"))
        controls.addWidget(self.split)
        controls.addWidget(QLabel("Strength sweep:"))
        controls.addWidget(self.strengths)
        self.run_button=QPushButton("Run Sweep")
        self.run_button.clicked.connect(self.start)
        controls.addWidget(self.run_button)
        self.status=QLabel("Ready. Outputs are never overwritten.")
        layout.addWidget(self.status)
        buttons=QHBoxLayout()
        layout.addLayout(buttons)
        open_button=QPushButton("Open Existing Results")
        open_button.clicked.connect(self.open_existing)
        buttons.addWidget(open_button)
        report_button=QPushButton("Generate Report")
        report_button.clicked.connect(self.report)
        buttons.addWidget(report_button)
        self.table=QTableWidget()
        layout.addWidget(self.table,2)
        layout.addWidget(QLabel("Visual comparison: select a result row (original / preprocessed / decoded / amplified error)"))
        self.images=QHBoxLayout()
        layout.addLayout(self.images,2)
        self.preview=[]
        for name in ["Original","Preprocessed","Decoded","Error (×8)"]:
            column=QVBoxLayout()
            column.addWidget(QLabel(name))
            pic=QLabel()
            pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pic.setMinimumSize(150,130)
            pic.setStyleSheet("background:#202733; border:1px solid #475569;")
            column.addWidget(pic)
            self.images.addLayout(column)
            self.preview.append(pic)
        self.table.itemSelectionChanged.connect(self.show_images)
        self.root=None
        self.records=[]
    def browse(self,edit,kind):
        if kind=="Output":
            value=QFileDialog.getExistingDirectory(self,"Select output parent directory")
            if value: edit.setText(str(Path(value)/"new_sweep"))
        else:
            value,_=QFileDialog.getOpenFileName(self,"Choose file",str(ROOT))
            if value: edit.setText(value)
    def methods(self):
        values=[float(s.strip()) for s in self.strengths.text().split(",") if s.strip()]
        if not values or any(not np.isfinite(x) or x<0 for x in values):
            raise ValueError("Strengths must be finite nonnegative numbers")
        values=sorted(set(values))
        methods=[Method("baseline","identity",0.)]
        for v in values:
            label=format(v,"g").replace(".","p")
            if v==0: continue
            methods.extend([Method(f"fixed_{label}","fixed",v),
                            Method(f"adaptive_{label}","adaptive",v)])
        return tuple(methods)
    def start(self):
        try:
            cfg=Configuration(dataset_manifest=self.manifest.text(),
                output_directory=self.output.text(),
                texconv_executable=self.exe.text(),
                backend="cpu",split=self.split.currentText(),methods=self.methods())
        except Exception as exc:
            QMessageBox.warning(self,"Configuration error",str(exc))
            return
        self.run_button.setEnabled(False)
        self.status.setText("Running experiments on background worker...")
        self.thread=QThread()
        self.worker=Worker(cfg)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.execute)
        self.worker.finished.connect(self.completed)
        self.worker.failed.connect(self.failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda:self.run_button.setEnabled(True))
        self.thread.start()
    def completed(self,path):
        self.status.setText("Completed: "+path)
        self.load(Path(path))
    def failed(self,msg):
        self.status.setText("Experiment failed: see error message")
        QMessageBox.critical(self,"Experiment error",msg[-8000:])
    def open_existing(self):
        d=QFileDialog.getExistingDirectory(self,"Select experiment results")
        if d: self.load(Path(d))
    def report(self):
        root=self.root
        if root is None:
            QMessageBox.information(self,"No results","Open an experiment first.")
            return
        try:
            generate(root)
            QMessageBox.information(self,"Report","Saved report.md and figures/ under "+str(root))
        except Exception as exc:
            QMessageBox.critical(self,"Report failed",str(exc))
    def load(self,path):
        csvpath=path/"raw_results.csv"
        try:
            with csvpath.open(encoding="utf-8",newline="") as stream:
                rows=list(csv.DictReader(stream))
            if not rows: raise ValueError("Empty results file")
            fields=list(rows[0])
            self.records=rows
            self.root=path
            self.table.setRowCount(len(rows))
            self.table.setColumnCount(len(fields))
            self.table.setHorizontalHeaderLabels(fields)
            for i,r in enumerate(rows):
                for j,key in enumerate(fields):
                    self.table.setItem(i,j,QTableWidgetItem(str(r[key])))
            self.status.setText(f"Loaded {len(rows)} runs from {path}")
        except Exception as exc:
            QMessageBox.critical(self,"Read error",str(exc))
    def show_images(self):
        if not self.records or self.root is None: return
        index=self.table.currentRow()
        if index<0 or index>=len(self.records): return
        r=self.records[index]
        with Path(self.manifest.text()).open(newline="",encoding="utf-8-sig") as f:
            candidates={x["image_id"]:x for x in csv.DictReader(f)}
        source=(Path(self.manifest.text()).parent/candidates[r["image_id"]]["path"]).resolve()
        tag=f"{r['image_id']}_{r['method']}"
        folder=self.root/"artifacts"/tag
        paths=[source,folder/"preprocessed.png",folder/"decoded.png",folder/"decoded.png"]
        try:
            for i,(label,path) in enumerate(zip(self.preview,paths)):
                pix=image_pixmap(path,source if i==3 else None)
                label.setPixmap(pix.scaled(280,240,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        except Exception as exc:
            self.status.setText("Preview error: "+str(exc))

def main():
    app=QApplication(sys.argv)
    window=Studio()
    window.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
