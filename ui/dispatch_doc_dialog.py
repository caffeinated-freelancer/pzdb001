from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextEdit

from version import __version__


class DispatchDocDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f'分班演算法說明 {__version__}')

        self.resize(720, 600)

        # Create layout and widgets
        layout = QVBoxLayout()

        text_edit = QTextEdit()
        font = QFont('Microsoft YaHei', 12)
        text_edit.setFont(font)
        text_edit.setReadOnly(True)  # Optional: Make text non-editable
        text_edit.setHtml(f'''
<h3>分班演算法說明</h3>
<ol>
<li>新班學長最優先排入各負責班級。</li>
<li>介紹人是學長的新舊學員分班至介紹人的班級。</li>
<li>介紹人跟被介紹人形成一個<font color="blue">介紹關係環</font>時, 做成一個分班群組 <font color="red">[關係環群組]</font>, 
暫時不分配班級, 待後續分配。<small>(關係環的所有性別﹑班別均相同）</small></li>
<li>介紹人跟被介紹人沒有形成環, 而形成<font color="blue">介紹關係鏈</font>, 當介紹關係鏈的<font color="green">領頭介紹人</font>
被分班確定的同時, 介紹關係鏈的所有其它學員一起分進到同一班。<small>(關係鏈的所有性別﹑班別均相同</small>）</li>
<li>升班意願調查中, 學長剛好也是新班學長, 且學員沒有介紹人的所有學員, 分班至學長的班級。</li>
<li>升班意願調查中, 同一學長的學員做成一個群組 <font color="brown">[同班群組]</font>, 待分班。(盡可能 <small>但不一定</small> 分在同一班)</li>
<li><font color="red">[關係環群組]</font> <font color="brown">[同班群組]</font> 混在一起分班, 從人數最多的群組開始分到名額剩最多的班級組別, 人數太多塞不下時, 
<font color="brown">[同班群組]</font> 的組有可能被拆成兩到多組, 但<font color="red">[關係環群組]</font> 
則保持不拆以保證分配到同一班級。<font color="red">[關係環群組]</font>分配的班級的人數有可能超過平均。</li>
</ol>
<p><b>註1</b>: 上述中, 說明 4 <font color="blue">介紹關係環</font>的這些學員的分班是伴隨在 5,7 的過程中, 
如果<font color="green">領頭介紹人</font>被排進時, 一起進到同一班。
<font color="blue">介紹關係環</font>分到的班級有可能造成該班的人數特別多。</p>
<p><B>註2</b>: 禪修班意願調查因有介紹人的關係, 在分班有較高的優先權。學員同時在意願調查跟升班調查均有記錄時, 
會以分配<font color="red">跟介紹人同班為優先</font>, 而不會分到原學長的新班。</p>
<p><b>註3</b>: 非本期學員也可以當介紹人(如果資料庫中找到姓名相符), 但非學員若為介紹人時, 不會做為分班參考。
<font color="red">兩位新學員形成介紹關係環或關係鏈時, 不會分到同一班</font>,
最好的做法是找<font color="brown">一位同性別且意願班級相同的學員做為兩位新學員的介紹人</font>。</p>
        ''')
        button = QPushButton("關閉")
        button.setFixedHeight(55)
        button.setFont(font)

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
