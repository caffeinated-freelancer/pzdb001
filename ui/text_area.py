from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton


class TextAreaDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Area Dialog")

        # Create layout
        layout = QVBoxLayout()

        # Create text edit widget
        self.text_edit = QTextEdit()

        # Add buttons
        self.button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        self.button_box.addWidget(ok_button)
        self.button_box.addWidget(cancel_button)

        # Connect buttons to actions (replace with your desired actions)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        # Add elements to layout
        layout.addWidget(self.text_edit)
        layout.addLayout(self.button_box)

        # Set layout
        self.setLayout(layout)

    def get_text(self):
        """
        Returns the text entered in the text edit.
        """
        return self.text_edit.toPlainText()