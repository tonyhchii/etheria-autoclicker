from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QPushButton
)
from models import Step


class EditStepDialog(QDialog):
    def __init__(self, step: Step, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Step")
        self.setMinimumWidth(300)

        self.step = step

        layout = QVBoxLayout(self)

        self.x_input = QSpinBox()
        self.x_input.setRange(0, 3000)
        self.x_input.setValue(step.x)

        self.y_input = QSpinBox()
        self.y_input.setRange(0, 3000)
        self.y_input.setValue(step.y)

        self.radius_input = QSpinBox()
        self.radius_input.setRange(0, 500)
        self.radius_input.setValue(step.radius)

        self.delay_min_input = QDoubleSpinBox()
        self.delay_min_input.setRange(0, 60)
        self.delay_min_input.setValue(step.delay_min)

        self.delay_max_input = QDoubleSpinBox()
        self.delay_max_input.setRange(0, 60)
        self.delay_max_input.setValue(step.delay_max)

        layout.addWidget(QLabel("X:"))
        layout.addWidget(self.x_input)
        layout.addWidget(QLabel("Y:"))
        layout.addWidget(self.y_input)
        layout.addWidget(QLabel("Radius:"))
        layout.addWidget(self.radius_input)
        layout.addWidget(QLabel("Delay Min:"))
        layout.addWidget(self.delay_min_input)
        layout.addWidget(QLabel("Delay Max:"))
        layout.addWidget(self.delay_max_input)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_updated_step(self) -> Step:
        return Step(
            x=self.x_input.value(),
            y=self.y_input.value(),
            radius=self.radius_input.value(),
            delay_min=self.delay_min_input.value(),
            delay_max=self.delay_max_input.value()
        )