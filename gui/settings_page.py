from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QSlider, QComboBox, QCheckBox,
                             QSpinBox, QPushButton, QScrollArea)
from PyQt6.QtCore import Qt


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("contentPage")
        self.setup_ui()
    
    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("settingsScroll")
        
        content = QWidget()
        content.setObjectName("settingsContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("设置")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        general_section = self.create_section("常规设置")
        general_layout = general_section.layout()
        
        startup_row = QHBoxLayout()
        startup_label = QLabel("开机自启")
        startup_check = QCheckBox()
        startup_check.setObjectName("settingCheck")
        startup_row.addWidget(startup_label)
        startup_row.addStretch()
        startup_row.addWidget(startup_check)
        general_layout.addLayout(startup_row)
        
        minimize_row = QHBoxLayout()
        minimize_label = QLabel("启动后最小化")
        minimize_check = QCheckBox()
        minimize_check.setObjectName("settingCheck")
        minimize_row.addWidget(minimize_label)
        minimize_row.addStretch()
        minimize_row.addWidget(minimize_check)
        general_layout.addLayout(minimize_row)
        
        tray_row = QHBoxLayout()
        tray_label = QLabel("关闭时最小化到托盘")
        tray_check = QCheckBox()
        tray_check.setChecked(True)
        tray_check.setObjectName("settingCheck")
        tray_row.addWidget(tray_label)
        tray_row.addStretch()
        tray_row.addWidget(tray_check)
        general_layout.addLayout(tray_row)
        
        layout.addWidget(general_section)
        
        perf_section = self.create_section("性能调优设置")
        perf_layout = perf_section.layout()
        
        target_row = QHBoxLayout()
        target_label = QLabel("目标帧率 (FPS)")
        self.target_fps_combo = QComboBox()
        self.target_fps_combo.addItems(["30", "60", "90", "120", "144", "240", "不限制"])
        self.target_fps_combo.setCurrentText("60")
        self.target_fps_combo.setMinimumWidth(120)
        target_row.addWidget(target_label)
        target_row.addStretch()
        target_row.addWidget(self.target_fps_combo)
        perf_layout.addLayout(target_row)
        
        min_row = QHBoxLayout()
        min_label = QLabel("最低帧率阈值")
        self.min_fps_spin = QSpinBox()
        self.min_fps_spin.setRange(15, 120)
        self.min_fps_spin.setValue(45)
        self.min_fps_spin.setSuffix(" FPS")
        self.min_fps_spin.setMinimumWidth(120)
        min_row.addWidget(min_label)
        min_row.addStretch()
        min_row.addWidget(self.min_fps_spin)
        perf_layout.addLayout(min_row)
        
        interval_row = QHBoxLayout()
        interval_label = QLabel("调优检测间隔")
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["5 秒", "10 秒", "15 秒", "30 秒", "60 秒"])
        self.interval_combo.setCurrentText("10 秒")
        self.interval_combo.setMinimumWidth(120)
        interval_row.addWidget(interval_label)
        interval_row.addStretch()
        interval_row.addWidget(self.interval_combo)
        perf_layout.addLayout(interval_row)
        
        aggressive_row = QHBoxLayout()
        aggressive_label = QLabel("调优强度")
        self.aggressive_combo = QComboBox()
        self.aggressive_combo.addItems(["保守", "平衡", "激进"])
        self.aggressive_combo.setCurrentText("平衡")
        self.aggressive_combo.setMinimumWidth(120)
        aggressive_row.addWidget(aggressive_label)
        aggressive_row.addStretch()
        aggressive_row.addWidget(self.aggressive_combo)
        perf_layout.addLayout(aggressive_row)
        
        auto_apply_row = QHBoxLayout()
        auto_apply_label = QLabel("自动应用调优")
        auto_apply_check = QCheckBox()
        auto_apply_check.setChecked(True)
        auto_apply_check.setObjectName("settingCheck")
        auto_apply_row.addWidget(auto_apply_label)
        auto_apply_row.addStretch()
        auto_apply_row.addWidget(auto_apply_check)
        perf_layout.addLayout(auto_apply_row)
        
        layout.addWidget(perf_section)
        
        quality_section = self.create_section("画质优先级")
        quality_layout = quality_section.layout()
        
        quality_row = QHBoxLayout()
        quality_label = QLabel("画质倾向")
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(50)
        self.quality_slider.setMinimumWidth(200)
        quality_row.addWidget(quality_label)
        quality_row.addSpacing(20)
        quality_row.addWidget(self.quality_slider, 1)
        quality_layout.addLayout(quality_row)
        
        quality_desc = QHBoxLayout()
        left_desc = QLabel("性能优先")
        left_desc.setObjectName("qualityDescLeft")
        right_desc = QLabel("画质优先")
        right_desc.setObjectName("qualityDescRight")
        right_desc.setAlignment(Qt.AlignmentFlag.AlignRight)
        quality_desc.addWidget(left_desc)
        quality_desc.addStretch()
        quality_desc.addWidget(right_desc)
        quality_layout.addLayout(quality_desc)
        
        layout.addWidget(quality_section)
        
        sys_section = self.create_section("系统优化选项")
        sys_layout = sys_section.layout()
        
        sys_options = [
            "优化电源计划",
            "关闭视觉效果",
            "提升进程优先级",
            "启用游戏模式",
            "优化网络设置",
            "清理内存",
            "关闭Windows Defender实时保护",
        ]
        
        for i, option in enumerate(sys_options):
            row = QHBoxLayout()
            label = QLabel(option)
            check = QCheckBox()
            check.setChecked(True)
            check.setObjectName("settingCheck")
            row.addWidget(label)
            row.addStretch()
            row.addWidget(check)
            sys_layout.addLayout(row)
            
            if i < len(sys_options) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setObjectName("divider")
                sys_layout.addWidget(line)
        
        layout.addWidget(sys_section)
        
        about_section = self.create_section("关于")
        about_layout = about_section.layout()
        
        version_row = QHBoxLayout()
        version_label = QLabel("版本")
        version_value = QLabel("v1.0.0")
        version_value.setObjectName("aboutValue")
        version_row.addWidget(version_label)
        version_row.addStretch()
        version_row.addWidget(version_value)
        about_layout.addLayout(version_row)
        
        layout.addWidget(about_section)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        reset_btn = QPushButton("恢复默认设置")
        reset_btn.setObjectName("secondaryButton")
        btn_row.addWidget(reset_btn)
        
        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("primaryButton")
        btn_row.addWidget(save_btn)
        
        layout.addLayout(btn_row)
        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def create_section(self, title):
        section = QFrame()
        section.setObjectName("settingsSection")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)
        
        return section
    
    def setup_style(self):
        pass
