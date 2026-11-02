from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QSlider, QComboBox,
                             QRadioButton, QButtonGroup, QFrame, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class FeedbackDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("游戏体验反馈")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        title = QLabel("📝 游戏体验反馈")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        frame_section = QFrame()
        frame_section.setObjectName("feedbackSection")
        frame_layout = QVBoxLayout(frame_section)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        frame_layout.setSpacing(12)
        
        frame_label = QLabel("画面流畅度")
        frame_label.setObjectName("questionLabel")
        frame_layout.addWidget(frame_label)
        
        self.frame_rating = QSlider(Qt.Orientation.Horizontal)
        self.frame_rating.setRange(1, 5)
        self.frame_rating.setValue(3)
        self.frame_rating.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.frame_rating.setTickInterval(1)
        frame_layout.addWidget(self.frame_rating)
        
        frame_desc = QHBoxLayout()
        labels = ["很卡顿", "卡顿", "一般", "流畅", "非常流畅"]
        for i, label in enumerate(labels):
            lbl = QLabel(label)
            lbl.setObjectName("ratingLabel")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            frame_desc.addWidget(lbl)
        frame_layout.addLayout(frame_desc)
        
        layout.addWidget(frame_section)
        
        sound_section = QFrame()
        sound_section.setObjectName("feedbackSection")
        sound_layout = QVBoxLayout(sound_section)
        sound_layout.setContentsMargins(16, 16, 16, 16)
        sound_layout.setSpacing(12)
        
        sound_label = QLabel("声音质量")
        sound_label.setObjectName("questionLabel")
        sound_layout.addWidget(sound_label)
        
        sound_options = QHBoxLayout()
        self.sound_group = QButtonGroup(self)
        
        sound_choices = [
            ("正常", "normal"),
            ("轻微卡顿", "minor"),
            ("严重卡顿", "severe"),
            ("没有声音", "none"),
        ]
        
        for i, (text, value) in enumerate(sound_choices):
            radio = QRadioButton(text)
            radio.setObjectName("radioOption")
            self.sound_group.addButton(radio, i)
            sound_options.addWidget(radio)
            if i == 0:
                radio.setChecked(True)
        
        sound_layout.addLayout(sound_options)
        layout.addWidget(sound_section)
        
        issue_section = QFrame()
        issue_section.setObjectName("feedbackSection")
        issue_layout = QVBoxLayout(issue_section)
        issue_layout.setContentsMargins(16, 16, 16, 16)
        issue_layout.setSpacing(12)
        
        issue_label = QLabel("遇到的问题 (可多选)")
        issue_label.setObjectName("questionLabel")
        issue_layout.addWidget(issue_label)
        
        issues_grid = QVBoxLayout()
        self.issue_checks = []
        issues = [
            "画面掉帧/卡顿",
            "声音卡顿/爆音",
            "游戏闪退",
            "加载缓慢",
            "温度过高/风扇噪音大",
            "网络延迟高",
        ]
        
        for issue in issues:
            cb = QCheckBox(issue)
            cb.setObjectName("issueCheck")
            self.issue_checks.append(cb)
            issues_grid.addWidget(cb)
        
        issue_layout.addLayout(issues_grid)
        layout.addWidget(issue_section)
        
        desc_section = QFrame()
        desc_section.setObjectName("feedbackSection")
        desc_layout = QVBoxLayout(desc_section)
        desc_layout.setContentsMargins(16, 16, 16, 16)
        desc_layout.setSpacing(12)
        
        desc_label = QLabel("详细描述 (可选)")
        desc_label.setObjectName("questionLabel")
        desc_layout.addWidget(desc_label)
        
        self.desc_text = QTextEdit()
        self.desc_text.setPlaceholderText("请描述您遇到的具体情况，例如在什么场景下出现问题，持续多久等...")
        self.desc_text.setObjectName("feedbackText")
        self.desc_text.setMaximumHeight(100)
        desc_layout.addWidget(self.desc_text)
        
        layout.addWidget(desc_section)
        
        action_section = QFrame()
        action_section.setObjectName("feedbackSection")
        action_layout = QVBoxLayout(action_section)
        action_layout.setContentsMargins(16, 16, 16, 16)
        action_layout.setSpacing(12)
        
        action_label = QLabel("希望我们做什么？")
        action_label.setObjectName("questionLabel")
        action_layout.addWidget(action_label)
        
        self.action_combo = QComboBox()
        self.action_combo.setObjectName("actionCombo")
        self.action_combo.addItems([
            "自动优化画质",
            "优先保证帧率",
            "优先保证画质",
            "降低CPU占用",
            "降低GPU温度",
            "优化声音设置",
        ])
        action_layout.addWidget(self.action_combo)
        
        layout.addWidget(action_section)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        
        submit_btn = QPushButton("提交反馈并优化")
        submit_btn.setObjectName("submitButton")
        submit_btn.clicked.connect(self.accept)
        btn_row.addWidget(submit_btn)
        
        layout.addLayout(btn_row)
    
    def setup_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
            }
            
            #dialogTitle {
                font-size: 20px;
                font-weight: bold;
                color: #f1f5f9;
                padding-bottom: 8px;
            }
            
            #feedbackSection {
                background-color: #1e293b;
                border-radius: 10px;
                border: 1px solid #334155;
            }
            
            #questionLabel {
                font-size: 14px;
                font-weight: bold;
                color: #e2e8f0;
            }
            
            #ratingLabel {
                font-size: 11px;
                color: #94a3b8;
            }
            
            QSlider::groove:horizontal {
                height: 8px;
                background: #334155;
                border-radius: 4px;
            }
            
            QSlider::sub-page:horizontal {
                background: #3b82f6;
                border-radius: 4px;
            }
            
            QSlider::handle:horizontal {
                background: #3b82f6;
                border: 2px solid #60a5fa;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            
            QRadioButton {
                color: #94a3b8;
                font-size: 13px;
                spacing: 6px;
            }
            
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #475569;
                background: #0f172a;
            }
            
            QRadioButton::indicator:checked {
                border-color: #3b82f6;
                background: #3b82f6;
            }
            
            QCheckBox {
                color: #94a3b8;
                font-size: 13px;
                spacing: 8px;
                padding: 4px 0;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #475569;
                background: #0f172a;
            }
            
            QCheckBox::indicator:checked {
                border-color: #3b82f6;
                background: #3b82f6;
            }
            
            QTextEdit, QComboBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
                padding: 8px;
                font-size: 13px;
            }
            
            QComboBox:hover {
                border-color: #475569;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #94a3b8;
            }
            
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #e2e8f0;
                selection-background-color: #3b82f6;
                padding: 4px;
            }
            
            #cancelButton {
                background-color: #334155;
                color: #e2e8f0;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
            }
            
            #cancelButton:hover {
                background-color: #475569;
            }
            
            #submitButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #6366f1);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            
            #submitButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #4f46e5);
            }
        """)
    
    def get_feedback(self):
        selected_issues = []
        for cb in self.issue_checks:
            if cb.isChecked():
                selected_issues.append(cb.text())
        
        sound_button = self.sound_group.checkedButton()
        sound_status = sound_button.text() if sound_button else "正常"
        
        return {
            "frame_rating": self.frame_rating.value(),
            "sound_status": sound_status,
            "issues": selected_issues,
            "description": self.desc_text.toPlainText(),
            "action": self.action_combo.currentText(),
        }
