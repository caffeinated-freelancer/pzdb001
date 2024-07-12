from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextEdit

from version import __version__


class DispatchDocDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f'分班演算法說明 {__version__}')

        self.resize(600, 600)

        # Create layout and widgets
        layout = QVBoxLayout()

        text_edit = QTextEdit()
        font = QFont('Microsoft YaHei', 12)
        text_edit.setFont(font)
        text_edit.setReadOnly(True)  # Optional: Make text non-editable
        text_edit.setHtml(f'''
<h3>分班演算法說明</h3>
<ol>
<li>學長的部份優先排入。</li>
<li>排入介紹人剛好也是學長的學員的, 新舊生都可以。</li>
<li>介紹人跟被介紹人形成 loop 的, 做成一個分班群組 <font color="red">[type 1 群組]</font>, 暫時不配班級。</li>
<li>介紹人跟被介紹人沒有形成 loop 的, 也做一個分班群組, 但有一個領頭的介紹人, 暫不分發, 但這群人會跟著領頭介紹人被分班時, 一起分進到同一班。</li>
<li>排入升班意願調查中, 學長剛好也是新班學長的學員。</li>
<li>升班意願調查中, 同一學長的學員做成一個群組<font color="red">[type 2 群組]</font>, 待分班。</li>
<li><font color="red">[type 1 群組][type 2 群組]</font> 混在一起分班, 從人數最多的開始分到最少人的班級組別, 人數太多塞不下時, 
<font color="red">[type 2 群組]</font> 的組有可能被拆, 但<font color="red">[type 1 群組]</font> 則不拆, 會讓人數超過平均。</li>
</ol>
<p>
註1: 這裡沒有說明 4 的部份這些學員的分班, 基本是是伴隨在 5,7 的過程中, 如果領頭介紹人被排進時, 一起進到同一班,
但這樣部份沒有先進群組計算人數, 所以有機會分出來的各組的人數差異會超過 1 人。
</p>
<p>
註2: 禪修班意願調查因有介紹人的關係, 在分班有較高的優先權。學員同時在意願調查跟升班調查均有記錄時, 會以分配跟介紹人同班為優先,
因此有可能不會分到原學長的新班。所以, 想更換班級的舊生可以透過登錄在禪修班意願調查中分配到介紹人的班級。
</p>
<p>
註3: 非本期學員可以當介紹人(如果資料庫有資料), 但非學員若為介紹人時, 不會做為分班參考。
兩個非學員有雖有介紹關係, 但不會分到同一班，所以要找一個學長或學員當介紹人, 這樣就可以讓這三個人分到同一班。
</p>
        ''')
        button = QPushButton("Close")

        # Add widgets to layout and set layout
        # layout.addWidget(label)
        layout.addWidget(text_edit)
        layout.addWidget(button)
        self.setLayout(layout)

        # Connect button click to slot (method)
        button.clicked.connect(self.close)

    # def __init__(self):
    #     super().__init__(parent=None)
    #     self.setWindowTitle("分班演算法說明")
    #     dialogLayout = QVBoxLayout()
    #     formLayout = QFormLayout()
    #     formLayout.addRow("Name:", QLineEdit())
    #     formLayout.addRow("Age:", QLineEdit())
    #     formLayout.addRow("Job:", QLineEdit())
    #     formLayout.addRow("Hobbies:", QLineEdit())
    #     dialogLayout.addLayout(formLayout)
    #     buttons = QDialogButtonBox()
    #     buttons.setStandardButtons(
    #         QDialogButtonBox.StandardButton.Cancel
    #         | QDialogButtonBox.StandardButton.Ok
    #     )
    #     dialogLayout.addWidget(buttons)
    #     self.setLayout(dialogLayout)
