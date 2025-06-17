import sys
import random
import pywinctl
from typing import List

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QHBoxLayout, QLabel,
    QInputDialog, QStackedWidget, QMessageBox, QListWidgetItem, QDialog, QComboBox
)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QPainter
from models import Config, Step
from step_item_widget import StepItemWidget
from edit_step_dialog import EditStepDialog

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
    def __init__(self, x, y, width, height):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # click-through
        self.setGeometry(x, y, width, height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 255, 0, 100))  # semi-transparent green
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())


class AutoClickerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Clicker Config")
        self.resize(500, 600)

        self.configs: List[Config] = []
        self.current_config: Config = None
        self.selected_step_index: int = -1

        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        self.config_list = QListWidget()

        self.window_selector_layout = QHBoxLayout()
        self.window_selector_label = QLabel("Attach to Window:")
        self.window_selector = QComboBox()
        self.window_selector_refresh_btn = QPushButton("⟳")

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

        self.stack.addWidget(self.step_screen)
        self.back_btn.clicked.connect(self.back_to_config_list)
    
    def show_overlay(self):
        selected_title = self.window_selector.currentText()
        matches = pywinctl.getWindowsWithTitle(selected_title)

        if not matches:
            QMessageBox.warning(self, "Not Found", "Target window not found.")
            return

        target = matches[0]
        x, y = target.left, target.top
        w, h = target.width, target.height

        self.overlay = TransparentOverlay(x, y, w, h)
        self.overlay.show()

        if not hasattr(self, "overlay_controls"):
            self.overlay_controls = OverlayControlPanel(self.close_overlay)

        self.overlay_controls.move(x + w - 40, y + 10)  # top-right corner of overlay
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
        new_step = Step(x=100, y=100, radius=20, delay_min=0.5, delay_max=1.5)
        self.current_config.steps.append(new_step)
        self.refresh_step_list()

    def delete_step(self, index):
        if 0 <= index < len(self.current_config.steps):
            del self.current_config.steps[index]
            self.refresh_step_list()
    def edit_step(self, index):
        step = self.current_config.steps[index]
        dialog = EditStepDialog(step, self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_config.steps[index] = dialog.get_updated_step()
            self.refresh_step_list()


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

    def move_step_down(self, index):
        if index < len(self.current_config.steps) - 1:
            self.current_config.steps[index + 1], self.current_config.steps[index] = \
                self.current_config.steps[index], self.current_config.steps[index + 1]
            self.refresh_step_list()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoClickerGUI()
    window.show()
    sys.exit(app.exec_())
