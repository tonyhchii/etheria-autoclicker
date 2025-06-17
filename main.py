import sys
import random
import pywinctl
import math
import ctypes
import pyautogui
import time
import keyboard
import threading
from typing import List

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QHBoxLayout, QLabel,
    QInputDialog, QStackedWidget, QMessageBox, QListWidgetItem, QDialog, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QPainter
from models import Config, Step
from step_item_widget import StepItemWidget
from edit_step_dialog import EditStepDialog

import json
import os

CONFIG_FILE = "configs.json"

class OverlayControlPanel(QWidget):
    def __init__(self, on_close_callback):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(on_close_callback)
        layout.addWidget(close_btn)

        self.setStyleSheet("background-color: rgba(30, 30, 30, 180); color: white; border-radius: 4px;")

class TransparentOverlay(QWidget):
    positionClicked = pyqtSignal(int, int) 
    def __init__(self, x, y, width, height, config: Config):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(x, y, width, height)
        self.config = config
        self.active_for_step = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(QColor(0, 255, 0, 100))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())


        painter.setBrush(Qt.NoBrush)
        step_pen = QPen(QColor(0, 0, 0, 200))  # green
        step_pen.setWidth(2)
        painter.setPen(step_pen)
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)
        
        if hasattr(self, "config") and self.config:
            for i, step in enumerate(self.config.steps):
                local_x = step.x - self.x()
                local_y = step.y - self.y()
                radius = step.radius

                rect = QRect(local_x - radius, local_y - radius, radius * 2, radius * 2)
                painter.drawEllipse(rect)
                painter.drawText(QRect(local_x - 10, local_y - 10, 20, 20), Qt.AlignCenter, str(i + 1))

    def mousePressEvent(self, event):
        if self.active_for_step and event.button() == Qt.LeftButton:
            self.active_for_step = False  # deactivate after first use
            self.positionClicked.emit(event.x(), event.y())


class AutoClickerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Clicker Config")
        self.resize(400, 600)

        self.configs: List[Config] = []
        self.current_config: Config = None
        self.selected_step_index: int = -1
        self.repeat = 1

        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        self.config_list = QListWidget()

        self.window_selector_layout = QHBoxLayout()
        self.window_selector_label = QLabel("Attach to Window:")
        self.window_selector = QComboBox()
        self.window_selector_refresh_btn = QPushButton("⟳")
        self.window_selector.setMaximumWidth(200)
        self.selected_window = None
        self.stop_flag = False
        self.overlay = QWidget()

        self.show_overlay_btn = QPushButton("Show Overlay")
        self.window_selector_layout.addWidget(self.show_overlay_btn)
        self.show_overlay_btn.clicked.connect(self.show_overlay)

        self.window_selector_layout.addWidget(self.window_selector_label)
        self.window_selector_layout.addWidget(self.window_selector)
        self.window_selector_layout.addWidget(self.window_selector_refresh_btn)
        self.main_layout.addLayout(self.window_selector_layout)


        self.populate_window_list()
        self.window_selector_refresh_btn.clicked.connect(self.populate_window_list)

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self.init_config_screen()
        self.init_step_editor_screen()

        self.load_configs()
        self.config_list.addItems([config.name for config in self.configs])

    def init_config_screen(self):
        """Screen to select a config"""
        self.config_screen = QWidget()
        layout = QVBoxLayout(self.config_screen)

        self.config_list = QListWidget()
        self.add_config_btn = QPushButton("Add Config")
        self.add_config_btn.clicked.connect(self.add_config)

        layout.addWidget(QLabel("Configs"))
        layout.addWidget(self.config_list)
        layout.addWidget(self.add_config_btn)

        self.stack.addWidget(self.config_screen)

        self.config_list.itemClicked.connect(self.enter_step_editor)


    def populate_window_list(self):
        self.window_selector.clear()
        titles = [title for title in pywinctl.getAllTitles() if title.strip()]
        if not titles:
            self.window_selector.addItem("No windows found")
        else:
            self.window_selector.addItems(titles)

    def add_config(self):
        name, ok = QInputDialog.getText(self, "Add Config", "Enter config name:")
        if ok and name.strip():
            name = name.strip()
            # Check for duplicates
            if any(cfg.name == name for cfg in self.configs):
                QMessageBox.warning(self, "Duplicate", f"A config named '{name}' already exists.")
                return  
            new_config = Config(name=name)
            self.configs.append(new_config)
            self.config_list.addItem(name)

    def init_step_editor_screen(self):
        """Screen to edit steps of a config"""
        self.step_screen = QWidget()
        layout = QVBoxLayout(self.step_screen)

        self.step_header = QLabel("[Config Name]")
        self.back_btn = QPushButton("Back to Configs")
        layout.addWidget(self.step_header)
        layout.addWidget(self.back_btn)

        self.step_list = QListWidget()
        layout.addWidget(self.step_list)

        self.add_step_btn = QPushButton("Add Step")
        layout.addWidget(self.add_step_btn)
        self.add_step_btn.clicked.connect(self.add_step)

        self.repeat_label = QLabel("Repeat:")
        self.repeat_input = QSpinBox()
        self.repeat_input.setMinimum(1)
        self.repeat_input.setMaximum(999)  # Arbitrary upper limit
        self.repeat_input.setValue(self.repeat)  # Default
        self.repeat_input.valueChanged.connect(self.update_repeat_value)
        layout.addWidget(self.repeat_input)

        self.start_steps_btn = QPushButton("Start")
        layout.addWidget(self.start_steps_btn)
        self.start_steps_btn.clicked.connect(self.start_steps)

        self.stack.addWidget(self.step_screen)
        self.back_btn.clicked.connect(self.back_to_config_list)
    
    def show_overlay(self):
        selected_title = self.window_selector.currentText()
        matches = pywinctl.getWindowsWithTitle(selected_title)
        self.selected_window = matches[0]

        if not matches:
            QMessageBox.warning(self, "Not Found", "Target window not found.")
            return

        target = matches[0]
        x, y = target.left, target.top
        w, h = target.width, target.height

        self.overlay = TransparentOverlay(x, y, w, h, self.current_config)
        self.overlay.show()

        self.overlay_controls = OverlayControlPanel(self.close_overlay)
        self.overlay_controls.setParent(None)  # make it a separate floating window
        self.overlay_controls.move(x + w + 20, y - 20)
        self.overlay_controls.show()


    def close_overlay(self):
        if hasattr(self, "overlay"):
            self.overlay.hide()
        if hasattr(self, "overlay_controls"):
            self.overlay_controls.hide()

    def enter_step_editor(self, item):
        """Switch to step editor screen for selected config"""
        config_name = item.text()
        for config in self.configs:
            if config.name == config_name:
                self.current_config = config
                break

        self.step_header.setText(f"{self.current_config.name}")
        self.refresh_step_list()
        self.stack.setCurrentWidget(self.step_screen)

    def back_to_config_list(self):
        self.stack.setCurrentWidget(self.config_screen)

    def add_step(self):
        if not hasattr(self, "overlay") or not self.overlay.isVisible():
            QMessageBox.warning(self, "Overlay Missing", "Overlay must be active to add steps.")
            return

        self.overlay.active_for_step = True
        self.overlay.positionClicked.connect(self.handle_overlay_click_for_step)

    def handle_overlay_click_for_step(self, x, y):
        abs_x = self.overlay.x() + x
        abs_y = self.overlay.y() + y

        new_step = Step(x=abs_x, y=abs_y, radius=20, delay_min=0.5, delay_max=1.5)
        self.current_config.steps.append(new_step)
        self.refresh_step_list()
        self.overlay.repaint()

        self.overlay.positionClicked.disconnect(self.handle_overlay_click_for_step)

    def delete_step(self, index):
        if 0 <= index < len(self.current_config.steps):
            del self.current_config.steps[index]
            self.refresh_step_list()
            self.overlay.repaint()

    def edit_step(self, index):
        step = self.current_config.steps[index]
        dialog = EditStepDialog(step, self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_config.steps[index] = dialog.get_updated_step()
            self.refresh_step_list()
            self.overlay.repaint()


    def refresh_step_list(self):
        """Update the step list display"""
        self.step_list.clear()
        for i, step in enumerate(self.current_config.steps):
            item_widget = StepItemWidget(
                i, step,
                move_up_callback=self.move_step_up,
                move_down_callback=self.move_step_down,
                delete_callback=self.delete_step,
                edit_callback=self.edit_step
            )
            list_item = QListWidgetItem(self.step_list)
            list_item.setSizeHint(item_widget.sizeHint())
            self.step_list.addItem(list_item)
            self.step_list.setItemWidget(list_item, item_widget)

    def move_step_up(self, index):
        if index > 0:
            self.current_config.steps[index - 1], self.current_config.steps[index] = \
                self.current_config.steps[index], self.current_config.steps[index - 1]
            self.refresh_step_list()
            self.overlay.repaint()

    def move_step_down(self, index):
        if index < len(self.current_config.steps) - 1:
            self.current_config.steps[index + 1], self.current_config.steps[index] = \
                self.current_config.steps[index], self.current_config.steps[index + 1]
            self.refresh_step_list()
            self.overlay.repaint()

    def update_repeat_value(self, value):
        self.repeat = value

    def closeEvent(self, event):
        self.save_configs()
        event.accept()

    def save_configs(self):
        data = [config.to_dict() for config in self.configs]
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load_configs(self):
        if not os.path.exists(CONFIG_FILE):
            return
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            self.configs = [Config.from_dict(cfg_data) for cfg_data in data]

    def start_steps(self):
        if self.selected_window:
            self.stop_flag = False
            self.close_overlay()

            threading.Thread(target=self.listen_for_exit_key, daemon=True).start()
            for _ in range(self.repeat):
                for i, step in enumerate(self.current_config.steps):
                    if self.stop_flag:
                        self.stop_flag = False
                        break
                    self.click_client(step)
                time.sleep(1)
            print("end")
        else:
            QMessageBox.warning(self, "No Window", "Select a window")

    def click_client(self, step):
        if self.selected_window:
            self.selected_window.activate()
            time.sleep(1)
            x, y = self.random_point_in_circle(step.x, step.y, step.radius)
            print(step.name)
            click(x,y, random.uniform(.05,.1))
            delay = random.uniform(step.delay_min, step.delay_max)
            time.sleep(delay)

    def random_point_in_circle(self, cx, cy, radius):
        r = radius * math.sqrt(random.random())  # uniform distribution
        theta = random.uniform(0, 2 * math.pi)
        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)
        return int(x), int(y)
    
    def listen_for_exit_key(self):
    # Runs in a background thread
        while True:
            if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
                print("Stop key pressed!")
                self.stop_flag = True
                break

PUL = ctypes.POINTER(ctypes.c_ulong)

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]
    
def click(x, y, hold_time=0.02):
    ctypes.windll.user32.SetCursorPos(x, y)

    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))  # Mouse down
    command = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

    time.sleep(hold_time) 

    ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))  # Mouse up
    command = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoClickerGUI()
    window.show()
    sys.exit(app.exec_())
