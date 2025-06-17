from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QStyle
from PyQt5.QtCore import Qt
from typing import Callable
from models import Step

class StepItemWidget(QWidget):
    def __init__(
        self,
        step_index: int,
        step: Step,
        move_up_callback: Callable[[int], None],
        move_down_callback: Callable[[int], None],
        delete_callback: Callable[[int], None],
        edit_callback: Callable[[int], None]      
    ):
        super().__init__()
        self.step_index = step_index

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)

        step_label = QLabel(
            f"{step_index+1} {step.name}: x={step.x}, y={step.y}, r={step.radius}, "
            f"delay=({step.delay_min}-{step.delay_max})"
        )
        layout.addWidget(step_label)

        btn_up = QPushButton()
        btn_up.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        btn_up.setFixedSize(30, 30)
        btn_up.clicked.connect(lambda: move_up_callback(step_index))
        layout.addWidget(btn_up)

        btn_down = QPushButton()
        btn_down.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        btn_down.setFixedSize(30, 30)
        btn_down.clicked.connect(lambda: move_down_callback(step_index))
        layout.addWidget(btn_down)

        btn_edit = QPushButton()
        btn_edit.setIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        btn_edit.setFixedSize(30, 30)
        btn_edit.clicked.connect(lambda: edit_callback(step_index))
        layout.addWidget(btn_edit)

        btn_delete = QPushButton()
        btn_delete.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        btn_delete.setFixedSize(30, 30)
        btn_delete.clicked.connect(lambda: delete_callback(step_index))
        layout.addWidget(btn_delete)

        layout.addStretch()
