from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QStackedWidget,
                             QProgressBar, QGridLayout, QMessageBox, QFileDialog,
                             QDialog, QTextEdit, QSlider, QComboBox, QListWidget,
                             QListWidgetItem, QAbstractItemView, QTableWidget,
                             QTableWidgetItem, QHeaderView, QCheckBox, QSpinBox,
                             QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon, QColor, QBrush
import sys
import os
import time

from core.system_info import SystemInfo
from core.system_optimizer import SystemOptimizer
from core.system_cleaner import SystemCleaner
from core.startup_service_manager import StartupManager, ServiceManager
from core.process_manager import ProcessManager
from core.performance_monitor import PerformanceMonitor
from core.game_launcher import GameLauncher
from core.game_settings import GameSettings
from core.auto_tuner import AutoTuner, OptimizationLevel
from gui.settings_page import SettingsPage


class BenchmarkThread(QThread):
    finished = pyqtSignal(dict, bool)
    
    def __init__(self, optimizer, before_data=None):
        super().__init__()
        self.optimizer = optimizer
        self.before_data = before_data
    
    def run(self):
        results = self.optimizer.run_benchmark()
        is_after = self.before_data is not None
        self.finished.emit(results, is_after)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("系统性能调优助手")
        self.setMinimumSize(1100, 750)
        self.resize(1300, 850)
        
        self.system_info = SystemInfo()
        self.system_optimizer = SystemOptimizer()
        self.system_cleaner = SystemCleaner()
        self.startup_manager = StartupManager()
        self.service_manager = ServiceManager()
        self.process_manager = ProcessManager()
        self.perf_monitor = PerformanceMonitor()
        self.game_launcher = GameLauncher()
        self.game_settings = GameSettings()
        self.auto_tuner = AutoTuner(self.perf_monitor, self.system_optimizer, self.game_settings)
        
        self.game_shortcut = None
        self.is_optimizing = False
        self._benchmark_before = None
        self._benchmark_after = None
        
        self.setup_ui()
        self.setup_style()
        self.setup_timer()
        self.update_dashboard()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        sidebar = self.create_sidebar()
        sidebar.setFixedWidth(240)
        main_layout.addWidget(sidebar)
        
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        self.dashboard_page = self.create_dashboard_page()
        self.optimize_page = self.create_optimize_page()
        self.cleaner_page = self.create_cleaner_page()
        self.process_page = self.create_process_page()
        self.monitor_page = self.create_monitor_page()
        self.game_mode_page = self.create_game_mode_page()
        self.settings_page_widget = SettingsPage()
        
        self.content_stack.addWidget(self.dashboard_page)
        self.content_stack.addWidget(self.optimize_page)
        self.content_stack.addWidget(self.cleaner_page)
        self.content_stack.addWidget(self.process_page)
        self.content_stack.addWidget(self.monitor_page)
        self.content_stack.addWidget(self.game_mode_page)
        self.content_stack.addWidget(self.settings_page_widget)
        
        self.content_stack.setCurrentIndex(0)
    
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(6)
        
        logo_label = QLabel("⚡ 系统调优助手")
        logo_label.setObjectName("logo")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        
        sub_label = QLabel("System Performance Tuner")
        sub_label.setObjectName("subLogo")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub_label)
        
        layout.addSpacing(16)
        
        nav_items = [
            ("📊 仪表盘", 0),
            ("🚀 一键优化", 1),
            ("🧹 清理加速", 2),
            ("⚙️ 进程管理", 3),
            ("📈 性能监控", 4),
            ("🎮 游戏模式", 5),
            ("🔧 设置", 6),
        ]
        
        self.nav_buttons = []
        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=index: self.switch_page(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        self.nav_buttons[0].setChecked(True)
        
        layout.addStretch()
        
        self.health_label = QLabel("● 系统健康")
        self.health_label.setObjectName("statusLabel")
        self.health_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.health_label)
        
        return sidebar
    
    def create_dashboard_page(self):
        page = QWidget()
        page.setObjectName("contentPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        header_row = QHBoxLayout()
        title = QLabel("系统概览")
        title.setObjectName("pageTitle")
        header_row.addWidget(title)
        header_row.addStretch()
        
        self.score_label = QLabel("系统评分: -- 分")
        self.score_label.setObjectName("scoreDisplay")
        header_row.addWidget(self.score_label)
        
        layout.addLayout(header_row)
        
        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)
        
        self.cpu_card = self.create_stat_card("CPU", "--%", "cpu")
        self.mem_card = self.create_stat_card("内存", "--GB", "memory")
        self.disk_card = self.create_stat_card("磁盘", "--%", "disk")
        self.network_card = self.create_stat_card("网络", "-- Mbps", "network")
        
        cards_layout.addWidget(self.cpu_card, 0, 0)
        cards_layout.addWidget(self.mem_card, 0, 1)
        cards_layout.addWidget(self.disk_card, 1, 0)
        cards_layout.addWidget(self.network_card, 1, 1)
        
        layout.addLayout(cards_layout)
        
        health_section = QFrame()
        health_section.setObjectName("healthSection")
        health_layout = QVBoxLayout(health_section)
        health_layout.setContentsMargins(24, 20, 24, 20)
        health_layout.setSpacing(16)
        
        health_header = QHBoxLayout()
        health_title = QLabel("系统健康状态")
        health_title.setObjectName("sectionTitle")
        health_header.addWidget(health_title)
        health_header.addStretch()
        
        self.health_status = QLabel("检测中...")
        self.health_status.setObjectName("healthStatus")
        health_header.addWidget(self.health_status)
        
        health_layout.addLayout(health_header)
        
        self.health_desc = QLabel("")
        self.health_desc.setObjectName("healthDesc")
        health_layout.addWidget(self.health_desc)
        
        self.health_bar = QProgressBar()
        self.health_bar.setObjectName("healthBar")
        self.health_bar.setTextVisible(False)
        self.health_bar.setRange(0, 100)
        self.health_bar.setValue(0)
        health_layout.addWidget(self.health_bar)
        
        action_row = QHBoxLayout()
        
        self.quick_optimize_btn = QPushButton("🚀 一键优化")
        self.quick_optimize_btn.setObjectName("primaryButton")
        self.quick_optimize_btn.setMinimumHeight(48)
        self.quick_optimize_btn.clicked.connect(self.quick_optimize)
        action_row.addWidget(self.quick_optimize_btn)
        
        self.quick_clean_btn = QPushButton("🧹 一键清理")
        self.quick_clean_btn.setObjectName("secondaryButton")
        self.quick_clean_btn.setMinimumHeight(48)
        self.quick_clean_btn.clicked.connect(lambda: self.switch_page(2))
        action_row.addWidget(self.quick_clean_btn)
        
        health_layout.addLayout(action_row)
        
        layout.addWidget(health_section)
        
        info_section = QFrame()
        info_section.setObjectName("infoSection")
        info_layout = QVBoxLayout(info_section)
        info_layout.setContentsMargins(20, 16, 20, 16)
        info_layout.setSpacing(12)
        
        info_title = QLabel("系统信息")
        info_title.setObjectName("sectionTitle")
        info_layout.addWidget(info_title)
        
        info_grid = QGridLayout()
        info_grid.setSpacing(8)
        
        self.cpu_name_label = QLabel("CPU: 检测中...")
        self.cpu_name_label.setObjectName("infoItem")
        info_grid.addWidget(self.cpu_name_label, 0, 0)
        
        self.gpu_name_label = QLabel("GPU: 检测中...")
        self.gpu_name_label.setObjectName("infoItem")
        info_grid.addWidget(self.gpu_name_label, 0, 1)
        
        self.os_label = QLabel("系统: 检测中...")
        self.os_label.setObjectName("infoItem")
        info_grid.addWidget(self.os_label, 1, 0)
        
        self.disk_total_label = QLabel("磁盘: 检测中...")
        self.disk_total_label.setObjectName("infoItem")
        info_grid.addWidget(self.disk_total_label, 1, 1)
        
        info_layout.addLayout(info_grid)
        
        layout.addWidget(info_section)
        
        compare_section = QFrame()
        compare_section.setObjectName("infoSection")
        compare_layout = QVBoxLayout(compare_section)
        compare_layout.setContentsMargins(20, 16, 20, 16)
        compare_layout.setSpacing(16)
        
        compare_header = QHBoxLayout()
        compare_title = QLabel("性能对比测试")
        compare_title.setObjectName("sectionTitle")
        compare_header.addWidget(compare_title)
        compare_header.addStretch()
        
        self.benchmark_btn = QPushButton("开始测试")
        self.benchmark_btn.setObjectName("secondaryButton")
        self.benchmark_btn.clicked.connect(self.run_benchmark_test)
        compare_header.addWidget(self.benchmark_btn)
        
        compare_layout.addLayout(compare_header)
        
        self.benchmark_status = QLabel("点击开始测试，对比优化前后的性能差异")
        self.benchmark_status.setObjectName("healthDesc")
        compare_layout.addWidget(self.benchmark_status)
        
        bench_grid = QGridLayout()
        bench_grid.setSpacing(12)
        
        bench_labels = ["CPU计算", "内存读写", "磁盘IO", "综合评分"]
        bench_keys = ["cpu_score", "memory_score", "disk_score", "total_score"]
        
        for i, (label, key) in enumerate(zip(bench_labels, bench_keys)):
            name_lbl = QLabel(label)
            name_lbl.setObjectName("cardTitle")
            bench_grid.addWidget(name_lbl, i, 0)
            
            before_lbl = QLabel("--")
            before_lbl.setObjectName("benchBefore")
            before_lbl.setStyleSheet("color: #f59e0b; font-size: 16px; font-weight: bold;")
            bench_grid.addWidget(before_lbl, i, 1)
            setattr(self, f"bench_{key}_before", before_lbl)
            
            arrow_lbl = QLabel("→")
            arrow_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            arrow_lbl.setStyleSheet("color: #64748b; font-size: 16px;")
            bench_grid.addWidget(arrow_lbl, i, 2)
            
            after_lbl = QLabel("--")
            after_lbl.setObjectName("benchAfter")
            after_lbl.setStyleSheet("color: #22c55e; font-size: 16px; font-weight: bold;")
            bench_grid.addWidget(after_lbl, i, 3)
            setattr(self, f"bench_{key}_after", after_lbl)
            
            imp_lbl = QLabel("--")
            imp_lbl.setObjectName("benchImp")
            imp_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            imp_lbl.setStyleSheet("color: #60a5fa; font-size: 14px; font-weight: 600;")
            bench_grid.addWidget(imp_lbl, i, 4)
            setattr(self, f"bench_{key}_imp", imp_lbl)
        
        bench_grid.setColumnStretch(0, 2)
        bench_grid.setColumnStretch(1, 2)
        bench_grid.setColumnStretch(2, 1)
        bench_grid.setColumnStretch(3, 2)
        bench_grid.setColumnStretch(4, 2)
        
        compare_layout.addLayout(bench_grid)
        
        layout.addWidget(compare_section)
        
        layout.addStretch()
        
        return page
    
    def create_stat_card(self, title, value, card_type):
        card = QFrame()
        card.setObjectName("statCard")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("cardValue")
        layout.addWidget(value_label)
        
        bar = QProgressBar()
        bar.setObjectName("statBar")
        bar.setTextVisible(False)
        bar.setRange(0, 100)
        bar.setValue(0)
        layout.addWidget(bar)
        
        setattr(self, f"{card_type}_value_label", value_label)
        setattr(self, f"{card_type}_bar", bar)
        
        return card
    
    def create_optimize_page(self):
        page = QWidget()
        page.setObjectName("contentPage")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("一键优化")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        mode_section = QFrame()
        mode_section.setObjectName("modeSection")
        mode_layout = QVBoxLayout(mode_section)
        mode_layout.setContentsMargins(20, 20, 20, 20)
        mode_layout.setSpacing(16)
        
        mode_title = QLabel("优化模式")
        mode_title.setObjectName("sectionTitle")
        mode_layout.addWidget(mode_title)
        
        mode_row = QHBoxLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.setObjectName("modeCombo")
        self.mode_combo.addItems([
            "均衡模式 - 兼顾性能与稳定",
            "性能模式 - 释放全部性能",
            "极致模式 - 极限性能释放"
        ])
        self.mode_combo.setMinimumWidth(300)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        
        mode_layout.addLayout(mode_row)
        
        mode_desc = QLabel("选择适合的优化模式，程序会自动应用对应的系统优化方案")
        mode_desc.setObjectName("modeDesc")
        mode_layout.addWidget(mode_desc)
        
        layout.addWidget(mode_section)
        
        opt_list_section = QFrame()
        opt_list_section.setObjectName("optListSection")
        opt_list_layout = QVBoxLayout(opt_list_section)
        opt_list_layout.setContentsMargins(20, 16, 20, 16)
        opt_list_layout.setSpacing(12)
        
        opt_title = QLabel("优化项")
        opt_title.setObjectName("sectionTitle")
        opt_list_layout.addWidget(opt_title)
        
        self.opt_table = QTableWidget()
        self.opt_table.setObjectName("optTable")
        self.opt_table.setColumnCount(4)
        self.opt_table.setHorizontalHeaderLabels(["优化项", "分类", "影响", "状态"])
        self.opt_table.verticalHeader().setVisible(False)
        self.opt_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.opt_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.opt_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.opt_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.opt_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.opt_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.opt_table.setColumnWidth(1, 100)
        self.opt_table.setColumnWidth(2, 80)
        self.opt_table.setColumnWidth(3, 100)
        self.opt_table.setMinimumHeight(300)
        
        opt_list_layout.addWidget(self.opt_table)
        
        layout.addWidget(opt_list_section)
        
        btn_row = QHBoxLayout()
        
        self.optimize_all_btn = QPushButton("🚀 一键全部优化")
        self.optimize_all_btn.setObjectName("primaryButton")
        self.optimize_all_btn.setMinimumHeight(52)
        self.optimize_all_btn.clicked.connect(self.apply_all_optimizations)
        btn_row.addWidget(self.optimize_all_btn)
        
        self.restore_btn = QPushButton("↩️ 恢复默认设置")
        self.restore_btn.setObjectName("secondaryButton")
        self.restore_btn.setMinimumHeight(52)
        self.restore_btn.clicked.connect(self.restore_optimizations)
        btn_row.addWidget(self.restore_btn)
        
        layout.addLayout(btn_row)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        self._populate_opt_table()
        
        return page
    
    def _populate_opt_table(self):
        opts = self.system_optimizer.get_all_optimizations()
        self.opt_table.setRowCount(len(opts))
        
        category_names = {
            "power": "电源管理",
            "visual": "视觉效果",
            "performance": "性能优化",
            "startup": "启动优化",
            "memory": "内存优化",
            "network": "网络优化",
            "system": "系统设置",
            "services": "服务优化"
        }
        
        for row, opt in enumerate(opts):
            name_item = QTableWidgetItem(opt["name"])
            name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            name_item.setCheckState(Qt.CheckState.Checked)
            
            cat_item = QTableWidgetItem(category_names.get(opt["category"], opt["category"]))
            cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            impact_item = QTableWidgetItem(opt["impact"])
            impact_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            status_item = QTableWidgetItem("未优化")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QBrush(QColor("#94a3b8")))
            
            self.opt_table.setItem(row, 0, name_item)
            self.opt_table.setItem(row, 1, cat_item)
            self.opt_table.setItem(row, 2, impact_item)
            self.opt_table.setItem(row, 3, status_item)
    
    def create_cleaner_page(self):
        page = QWidget()
        page.setObjectName("contentPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("清理加速")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        clean_section = QFrame()
        clean_section.setObjectName("cleanSection")
        clean_layout = QVBoxLayout(clean_section)
        clean_layout.setContentsMargins(20, 20, 20, 20)
        clean_layout.setSpacing(16)
        
        clean_header = QHBoxLayout()
        clean_title = QLabel("垃圾文件清理")
        clean_title.setObjectName("sectionTitle")
        clean_header.addWidget(clean_title)
        clean_header.addStretch()
        
        self.scan_btn = QPushButton("🔍 扫描")
        self.scan_btn.setObjectName("secondaryButton")
        self.scan_btn.clicked.connect(self.scan_cleanup)
        clean_header.addWidget(self.scan_btn)
        
        self.clean_btn = QPushButton("🧹 一键清理")
        self.clean_btn.setObjectName("primaryButton")
        self.clean_btn.clicked.connect(self.clean_all)
        clean_header.addWidget(self.clean_btn)
        
        clean_layout.addLayout(clean_header)
        
        self.clean_result_label = QLabel("点击扫描开始检测可清理的垃圾文件")
        self.clean_result_label.setObjectName("cleanResult")
        clean_layout.addWidget(self.clean_result_label)
        
        self.clean_table = QTableWidget()
        self.clean_table.setObjectName("cleanTable")
        self.clean_table.setColumnCount(4)
        self.clean_table.setHorizontalHeaderLabels(["项目", "文件数", "大小", "安全"])
        self.clean_table.verticalHeader().setVisible(False)
        self.clean_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clean_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.clean_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.clean_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.clean_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.clean_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.clean_table.setColumnWidth(1, 100)
        self.clean_table.setColumnWidth(2, 120)
        self.clean_table.setColumnWidth(3, 80)
        self.clean_table.setMinimumHeight(250)
        
        clean_layout.addWidget(self.clean_table)
        
        layout.addWidget(clean_section)
        
        startup_section = QFrame()
        startup_section.setObjectName("startupSection")
        startup_layout = QVBoxLayout(startup_section)
        startup_layout.setContentsMargins(20, 20, 20, 20)
        startup_layout.setSpacing(12)
        
        startup_header = QHBoxLayout()
        startup_title = QLabel("启动项管理")
        startup_title.setObjectName("sectionTitle")
        startup_header.addWidget(startup_title)
        startup_header.addStretch()
        
        self.refresh_startup_btn = QPushButton("🔄 刷新")
        self.refresh_startup_btn.setObjectName("secondaryButton")
        self.refresh_startup_btn.clicked.connect(self.refresh_startup_items)
        startup_header.addWidget(self.refresh_startup_btn)
        
        startup_layout.addLayout(startup_header)
        
        self.startup_table = QTableWidget()
        self.startup_table.setObjectName("startupTable")
        self.startup_table.setColumnCount(4)
        self.startup_table.setHorizontalHeaderLabels(["名称", "位置", "影响", "操作"])
        self.startup_table.verticalHeader().setVisible(False)
        self.startup_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.startup_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.startup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.startup_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.startup_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.startup_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.startup_table.setColumnWidth(1, 140)
        self.startup_table.setColumnWidth(2, 80)
        self.startup_table.setColumnWidth(3, 100)
        self.startup_table.setMinimumHeight(200)
        
        startup_layout.addWidget(self.startup_table)
        
        layout.addWidget(startup_section)
        
        layout.addStretch()
        
        self.refresh_startup_items()
        
        return page
    
    def create_process_page(self):
        page = QWidget()
        page.setObjectName("contentPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("进程管理")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        summary_section = QFrame()
        summary_section.setObjectName("summarySection")
        summary_layout = QHBoxLayout(summary_section)
        summary_layout.setContentsMargins(20, 16, 20, 16)
        summary_layout.setSpacing(40)
        
        self.proc_count_label = QLabel("进程数: --")
        self.proc_count_label.setObjectName("summaryItem")
        summary_layout.addWidget(self.proc_count_label)
        
        self.proc_cpu_label = QLabel("CPU: --%")
        self.proc_cpu_label.setObjectName("summaryItem")
        summary_layout.addWidget(self.proc_cpu_label)
        
        self.proc_mem_label = QLabel("内存: --%")
        self.proc_mem_label.setObjectName("summaryItem")
        summary_layout.addWidget(self.proc_mem_label)
        
        summary_layout.addStretch()
        
        self.kill_process_btn = QPushButton("结束进程")
        self.kill_process_btn.setObjectName("dangerButton")
        self.kill_process_btn.clicked.connect(self.kill_selected_process)
        summary_layout.addWidget(self.kill_process_btn)
        
        layout.addWidget(summary_section)
        
        self.process_table = QTableWidget()
        self.process_table.setObjectName("processTable")
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels(["进程名", "PID", "CPU %", "内存", "状态", "用户"])
        self.process_table.verticalHeader().setVisible(False)
        self.process_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.process_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.process_table.setSortingEnabled(True)
        self.process_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.process_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.process_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.process_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.process_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.process_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.process_table.setColumnWidth(1, 70)
        self.process_table.setColumnWidth(2, 80)
        self.process_table.setColumnWidth(3, 100)
        self.process_table.setColumnWidth(4, 80)
        self.process_table.setColumnWidth(5, 140)
        
        layout.addWidget(self.process_table)
        
        return page
    
    def create_monitor_page(self):
        page = QWidget()
        page.setObjectName("contentPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("性能监控")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        fps_section = QFrame()
        fps_section.setObjectName("fpsSection")
        fps_layout = QVBoxLayout(fps_section)
        fps_layout.setContentsMargins(20, 20, 20, 20)
        fps_layout.setSpacing(16)
        
        fps_header = QHBoxLayout()
        fps_title = QLabel("实时性能")
        fps_title.setObjectName("sectionTitle")
        fps_header.addWidget(fps_title)
        fps_header.addStretch()
        
        self.fps_value = QLabel("0")
        self.fps_value.setObjectName("fpsValue")
        fps_header.addWidget(self.fps_value)
        
        fps_unit = QLabel("FPS")
        fps_unit.setObjectName("fpsUnit")
        fps_unit.setAlignment(Qt.AlignmentFlag.AlignBottom)
        fps_header.addWidget(fps_unit)
        
        fps_layout.addLayout(fps_header)
        
        fps_details = QHBoxLayout()
        self.fps_min = QLabel("最低: 0")
        self.fps_min.setObjectName("fpsDetail")
        fps_details.addWidget(self.fps_min)
        
        self.fps_avg = QLabel("平均: 0")
        self.fps_avg.setObjectName("fpsDetail")
        fps_details.addWidget(self.fps_avg)
        
        self.fps_max = QLabel("最高: 0")
        self.fps_max.setObjectName("fpsDetail")
        fps_details.addWidget(self.fps_max)
        
        self.fps_grade = QLabel("等级: -")
        self.fps_grade.setObjectName("fpsGrade")
        fps_details.addStretch()
        fps_details.addWidget(self.fps_grade)
        
        fps_layout.addLayout(fps_details)
        
        layout.addWidget(fps_section)
        
        stats_grid = QGridLayout()
        stats_grid.setSpacing(16)
        
        self.mon_cpu = self.create_monitor_card("CPU 使用率", "cpu_mon")
        self.mon_memory = self.create_monitor_card("内存使用", "mem_mon")
        self.mon_disk = self.create_monitor_card("磁盘活动", "disk_mon")
        self.mon_net = self.create_monitor_card("网络速度", "net_mon")
        
        stats_grid.addWidget(self.mon_cpu, 0, 0)
        stats_grid.addWidget(self.mon_memory, 0, 1)
        stats_grid.addWidget(self.mon_disk, 1, 0)
        stats_grid.addWidget(self.mon_net, 1, 1)
        
        layout.addLayout(stats_grid)
        
        layout.addStretch()
        
        return page
    
    def create_monitor_card(self, title, key):
        card = QFrame()
        card.setObjectName("monitorCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        
        title_label = QLabel(title)
        title_label.setObjectName("monitorTitle")
        layout.addWidget(title_label)
        
        value_label = QLabel("0%")
        value_label.setObjectName("monitorValue")
        layout.addWidget(value_label)
        
        bar = QProgressBar()
        bar.setObjectName("monitorBar")
        bar.setTextVisible(False)
        bar.setRange(0, 100)
        bar.setValue(0)
        layout.addWidget(bar)
        
        setattr(self, f"{key}_value", value_label)
        setattr(self, f"{key}_bar", bar)
        
        return card
    
    def create_game_mode_page(self):
        page = QWidget()
        page.setObjectName("contentPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title_row = QHBoxLayout()
        title = QLabel("游戏模式")
        title.setObjectName("pageTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        
        self.game_mode_toggle = QPushButton("🎮 开启游戏模式")
        self.game_mode_toggle.setObjectName("primaryButton")
        self.game_mode_toggle.clicked.connect(self.toggle_game_mode)
        title_row.addWidget(self.game_mode_toggle)
        
        layout.addLayout(title_row)
        
        game_note = QLabel("💡 游戏模式是系统调优的特色附加功能")
        game_note.setObjectName("gameNote")
        game_note.setStyleSheet("color: #60a5fa; font-size: 13px; font-weight: 600;")
        layout.addWidget(game_note)
        
        game_desc = QLabel(
            "通过系统级调优释放电脑性能潜力，游戏流畅度提升是系统性能优化的直观体现。\n"
            "游戏模式会在系统极致优化的基础上，进一步优先分配资源给游戏程序，包括：\n"
            "• 切换到卓越性能电源计划\n"
            "• 提升游戏进程优先级\n"
            "• 关闭不必要的后台服务和视觉效果\n"
            "• 实时动态调整，平衡画质与流畅度"
        )
        game_desc.setObjectName("gameDesc")
        game_desc.setWordWrap(True)
        layout.addWidget(game_desc)
        
        game_section = QFrame()
        game_section.setObjectName("gameSection")
        game_layout = QVBoxLayout(game_section)
        game_layout.setContentsMargins(20, 20, 20, 20)
        game_layout.setSpacing(16)
        
        game_header = QHBoxLayout()
        game_title = QLabel("游戏启动")
        game_title.setObjectName("sectionTitle")
        game_header.addWidget(game_title)
        game_header.addStretch()
        
        select_btn = QPushButton("选择快捷方式")
        select_btn.setObjectName("secondaryButton")
        select_btn.clicked.connect(self.select_shortcut)
        game_header.addWidget(select_btn)
        
        game_layout.addLayout(game_header)
        
        self.game_path_label = QLabel("尚未选择游戏快捷方式")
        self.game_path_label.setObjectName("gamePathLabel")
        self.game_path_label.setWordWrap(True)
        game_layout.addWidget(self.game_path_label)
        
        self.launch_game_btn = QPushButton("🚀 启动游戏 + 游戏模式")
        self.launch_game_btn.setObjectName("primaryButton")
        self.launch_game_btn.setMinimumHeight(50)
        self.launch_game_btn.clicked.connect(self.start_game_mode)
        game_layout.addWidget(self.launch_game_btn)
        
        layout.addWidget(game_section)
        
        auto_tune_section = QFrame()
        auto_tune_section.setObjectName("autoTuneSection")
        auto_layout = QVBoxLayout(auto_tune_section)
        auto_layout.setContentsMargins(20, 20, 20, 20)
        auto_layout.setSpacing(12)
        
        auto_header = QHBoxLayout()
        auto_title = QLabel("自动调优")
        auto_title.setObjectName("sectionTitle")
        auto_header.addWidget(auto_title)
        auto_header.addStretch()
        
        self.auto_tune_btn = QPushButton("启动自动调优")
        self.auto_tune_btn.setObjectName("secondaryButton")
        self.auto_tune_btn.clicked.connect(self.toggle_auto_tune)
        auto_header.addWidget(self.auto_tune_btn)
        auto_layout.addLayout(auto_header)
        
        self.auto_level = QLabel("当前画质等级: -")
        self.auto_level.setObjectName("autoLevel")
        auto_layout.addWidget(self.auto_level)
        
        self.auto_status = QLabel("状态: 未启动")
        self.auto_status.setObjectName("autoStatus")
        auto_layout.addWidget(self.auto_status)
        
        rec_header = QLabel("💡 优化建议")
        rec_header.setObjectName("sectionTitle")
        auto_layout.addWidget(rec_header)
        
        self.recommendations = QTextEdit()
        self.recommendations.setObjectName("recommendations")
        self.recommendations.setReadOnly(True)
        self.recommendations.setMaximumHeight(100)
        auto_layout.addWidget(self.recommendations)
        
        layout.addWidget(auto_tune_section)
        
        layout.addStretch()
        
        return page
    
    def setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f172a;
            }
            
            #sidebar {
                background-color: #1e293b;
                border-right: 1px solid #334155;
            }
            
            #logo {
                font-size: 18px;
                font-weight: bold;
                color: #e2e8f0;
                padding-top: 8px;
            }
            
            #subLogo {
                font-size: 11px;
                color: #64748b;
                letter-spacing: 1px;
            }
            
            #navButton {
                text-align: left;
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                background: transparent;
                color: #94a3b8;
                font-size: 14px;
            }
            
            #navButton:hover {
                background-color: #334155;
                color: #e2e8f0;
            }
            
            #navButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(59, 130, 246, 0.2), stop:1 rgba(139, 92, 246, 0.2));
                color: #60a5fa;
                border-left: 3px solid #3b82f6;
                border-radius: 0 8px 8px 0;
            }
            
            #statusLabel {
                color: #22c55e;
                font-size: 12px;
                padding: 8px;
            }
            
            #contentPage {
                background-color: #0f172a;
            }
            
            #pageTitle {
                font-size: 24px;
                font-weight: bold;
                color: #f1f5f9;
            }
            
            #scoreDisplay {
                font-size: 16px;
                font-weight: bold;
                color: #fbbf24;
                padding: 8px 16px;
                background: rgba(251, 191, 36, 0.1);
                border-radius: 8px;
                border: 1px solid rgba(251, 191, 36, 0.2);
            }
            
            #sectionTitle {
                font-size: 16px;
                font-weight: bold;
                color: #e2e8f0;
            }
            
            #statCard {
                background-color: #1e293b;
                border-radius: 12px;
                border: 1px solid #334155;
            }
            
            #cardTitle {
                font-size: 14px;
                color: #94a3b8;
            }
            
            #cardValue {
                font-size: 28px;
                font-weight: bold;
                color: #f1f5f9;
            }
            
            #statBar {
                height: 6px;
                border-radius: 3px;
                background-color: #334155;
            }
            
            #statBar::chunk {
                border-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #6366f1);
            }
            
            #healthSection, #infoSection, #modeSection, #cleanSection,
            #startupSection, #gameSection, #autoTuneSection, #fpsSection,
            #optListSection, #summarySection {
                background-color: #1e293b;
                border-radius: 12px;
                border: 1px solid #334155;
            }
            
            #healthStatus {
                font-size: 18px;
                font-weight: bold;
                color: #fbbf24;
            }
            
            #healthDesc {
                font-size: 13px;
                color: #94a3b8;
            }
            
            #healthBar {
                height: 8px;
                border-radius: 4px;
                background-color: #334155;
            }
            
            #healthBar::chunk {
                border-radius: 4px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #22c55e, stop:1 #84cc16);
            }
            
            #infoItem {
                font-size: 13px;
                color: #94a3b8;
            }
            
            #primaryButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #6366f1);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
                padding: 10px 20px;
            }
            
            #primaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #4f46e5);
            }
            
            #secondaryButton {
                background-color: #334155;
                color: #e2e8f0;
                border: 1px solid #475569;
                border-radius: 10px;
                font-size: 14px;
                padding: 10px 20px;
            }
            
            #secondaryButton:hover {
                background-color: #475569;
            }
            
            #dangerButton {
                background-color: rgba(239, 68, 68, 0.2);
                color: #fca5a5;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 10px;
                font-size: 14px;
                padding: 8px 16px;
            }
            
            #dangerButton:hover {
                background-color: rgba(239, 68, 68, 0.3);
            }
            
            #modeCombo {
                background-color: #0f172a;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 10px 14px;
                color: #e2e8f0;
                font-size: 14px;
            }
            
            #modeCombo:hover {
                border-color: #64748b;
            }
            
            #modeCombo QAbstractItemView {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #e2e8f0;
                padding: 4px;
                selection-background-color: #3b82f6;
            }
            
            #modeDesc {
                color: #94a3b8;
                font-size: 13px;
            }
            
            QTableWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 13px;
                gridline-color: #1e293b;
            }
            
            QTableWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #1e293b;
            }
            
            QTableWidget::item:selected {
                background-color: rgba(59, 130, 246, 0.2);
                color: #60a5fa;
            }
            
            QHeaderView::section {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 10px 12px;
                border: none;
                border-bottom: 1px solid #334155;
                font-weight: 600;
                font-size: 12px;
            }
            
            #cleanResult {
                color: #94a3b8;
                font-size: 13px;
            }
            
            #summaryItem {
                color: #e2e8f0;
                font-size: 14px;
                font-weight: 600;
            }
            
            #gamePathLabel {
                color: #94a3b8;
                font-size: 13px;
                padding: 8px 0;
            }
            
            #gameDesc {
                color: #94a3b8;
                font-size: 14px;
                padding-bottom: 8px;
            }
            
            #fpsValue {
                font-size: 48px;
                font-weight: bold;
                color: #22c55e;
            }
            
            #fpsUnit {
                color: #64748b;
                font-size: 14px;
                padding-bottom: 8px;
            }
            
            #fpsDetail {
                color: #94a3b8;
                font-size: 13px;
            }
            
            #fpsGrade {
                color: #fbbf24;
                font-size: 14px;
                font-weight: bold;
            }
            
            #monitorCard {
                background-color: #1e293b;
                border-radius: 10px;
                border: 1px solid #334155;
            }
            
            #monitorTitle {
                font-size: 13px;
                color: #94a3b8;
            }
            
            #monitorValue {
                font-size: 22px;
                font-weight: bold;
                color: #f1f5f9;
            }
            
            #monitorBar {
                height: 5px;
                border-radius: 3px;
                background-color: #334155;
            }
            
            #monitorBar::chunk {
                border-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #22c55e, stop:1 #84cc16);
            }
            
            #autoLevel, #autoStatus {
                color: #94a3b8;
                font-size: 13px;
            }
            
            #recommendations {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 13px;
                padding: 8px;
            }
            
            QProgressBar {
                text-align: center;
            }
            
            QScrollBar:vertical {
                background: #1e293b;
                width: 8px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical {
                background: #475569;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #64748b;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            
            QScrollArea {
                background-color: #0f172a;
                border: none;
            }
            
            QScrollArea QWidget {
                background-color: #0f172a;
            }
            
            #settingsScroll {
                background-color: #0f172a;
            }
            
            #settingsContent {
                background-color: #0f172a;
            }
            
            #settingsSection {
                background-color: #1e293b;
                border-radius: 12px;
                border: 1px solid #334155;
            }
            
            #settingCheck {
                spacing: 8px;
            }
            
            #settingCheck::indicator {
                width: 18px;
                height: 18px;
                border-radius: 5px;
                border: 2px solid #475569;
                background-color: #0f172a;
            }
            
            #settingCheck::indicator:checked {
                background-color: #3b82f6;
                border-color: #3b82f6;
            }
            
            #settingCheck::indicator:hover {
                border-color: #60a5fa;
            }
            
            #aboutValue {
                color: #60a5fa;
                font-weight: 600;
            }
            
            #qualityDescLeft, #qualityDescRight {
                color: #64748b;
                font-size: 12px;
            }
            
            QSlider::groove:horizontal {
                height: 6px;
                background: #334155;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
                background: #3b82f6;
            }
            
            QSlider::handle:horizontal:hover {
                background: #60a5fa;
            }
            
            QSlider::sub-page:horizontal {
                background: #3b82f6;
                border-radius: 3px;
            }
            
            QSpinBox {
                background-color: #0f172a;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 6px 10px;
                color: #e2e8f0;
                font-size: 14px;
            }
            
            QSpinBox:hover {
                border-color: #64748b;
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                background-color: #1e293b;
                border: none;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #334155;
            }
        """)
    
    def setup_timer(self):
        self.dashboard_timer = QTimer()
        self.dashboard_timer.timeout.connect(self.update_dashboard)
        self.dashboard_timer.start(2000)
        
        self.process_timer = QTimer()
        self.process_timer.timeout.connect(self.update_process_list)
        self.process_timer.start(3000)
        
        self.perf_timer = QTimer()
        self.perf_timer.timeout.connect(self.update_perf_monitor)
        self.perf_timer.start(1000)
        
        self.perf_monitor.start()
    
    def update_dashboard(self):
        self.system_info.refresh()
        
        cpu = self.system_info.cpu_info
        mem = self.system_info.memory_info
        gpu = self.system_info.gpu_info[0] if self.system_info.gpu_info else {}
        os_info = self.system_info.os_info
        
        self.cpu_value_label.setText(f"{cpu['load_percent']:.0f}%")
        self.cpu_bar.setValue(int(cpu["load_percent"]))
        
        self.memory_value_label.setText(f"{mem['used']:.1f}/{mem['total']:.1f}GB")
        self.memory_bar.setValue(int(mem["percent"]))
        
        disks = self.system_info.disk_info
        if disks:
            sys_disk = disks[0]
            self.disk_value_label.setText(f"{sys_disk['percent']:.0f}%")
            self.disk_bar.setValue(int(sys_disk["percent"]))
            self.disk_total_label.setText(f"磁盘: {sys_disk['total']:.0f}GB 总容量")
        
        self.network_value_label.setText("0 Mbps")
        self.network_bar.setValue(0)
        
        score = self.system_optimizer.get_system_score()
        health, color, desc = self.system_optimizer.get_system_health()
        
        self.score_label.setText(f"系统评分: {score} 分")
        self.health_status.setText(health)
        self.health_status.setStyleSheet(f"color: #{self._get_color_hex(color)};")
        self.health_desc.setText(desc)
        self.health_bar.setValue(score)
        
        self.cpu_name_label.setText(f"CPU: {cpu['name'][:40]}")
        gpu_name = gpu.get("name", "未知") if gpu else "未知"
        self.gpu_name_label.setText(f"GPU: {gpu_name[:40]}")
        self.os_label.setText(f"系统: {os_info['system']} {os_info['release']}")
    
    def _get_color_hex(self, color_name):
        colors = {
            "green": "22c55e",
            "yellow": "f59e0b",
            "orange": "f97316",
            "red": "ef4444"
        }
        return colors.get(color_name, "fbbf24")
    
    def update_process_list(self):
        if self.content_stack.currentIndex() != 3:
            return
        
        procs = self.process_manager.get_top_cpu_processes(50)
        
        self.process_table.setRowCount(len(procs))
        
        for row, proc in enumerate(procs):
            name_item = QTableWidgetItem(proc["name"] or "未知")
            pid_item = QTableWidgetItem(str(proc["pid"]))
            pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cpu_item = QTableWidgetItem(f"{proc['cpu_percent']:.1f}")
            cpu_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            mem_str = self.process_manager.format_bytes(proc["memory_rss"])
            mem_item = QTableWidgetItem(mem_str)
            mem_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item = QTableWidgetItem(proc["status"] or "-")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            user_item = QTableWidgetItem(proc["username"].split("\\")[-1] if proc["username"] else "-")
            
            self.process_table.setItem(row, 0, name_item)
            self.process_table.setItem(row, 1, pid_item)
            self.process_table.setItem(row, 2, cpu_item)
            self.process_table.setItem(row, 3, mem_item)
            self.process_table.setItem(row, 4, status_item)
            self.process_table.setItem(row, 5, user_item)
        
        summary = self.process_manager.get_system_resource_summary()
        self.proc_count_label.setText(f"进程数: {summary['process_count']}")
        self.proc_cpu_label.setText(f"CPU: {summary['cpu_percent']:.1f}%")
        self.proc_mem_label.setText(f"内存: {summary['memory_percent']:.1f}%")
    
    def update_perf_monitor(self):
        stats = self.perf_monitor.get_stats()
        
        self.fps_value.setText(f"{stats['fps']:.0f}")
        self.fps_min.setText(f"最低: {stats['fps_min']:.0f}")
        self.fps_avg.setText(f"平均: {stats['fps_avg']:.0f}")
        self.fps_max.setText(f"最高: {stats['fps_max']:.0f}")
        
        grade, _ = self.perf_monitor.get_performance_grade()
        self.fps_grade.setText(f"等级: {grade}")
        
        self.cpu_mon_value.setText(f"{stats['cpu']:.1f}%")
        self.cpu_mon_bar.setValue(int(stats['cpu']))
        
        mem_percent = self.system_info.memory_info["percent"]
        self.mem_mon_value.setText(f"{mem_percent:.1f}%")
        self.mem_mon_bar.setValue(int(mem_percent))
        
        gpu_load = self.system_info.gpu_info[0].get("load", 0) if self.system_info.gpu_info else 0
        gpu_load_val = gpu_load * 100 if gpu_load <= 1 else gpu_load
        self.disk_mon_value.setText(f"{gpu_load_val:.0f}%")
        self.disk_mon_bar.setValue(int(gpu_load_val))
        
        current_level = self.auto_tuner.get_current_level()
        level_names = {
            OptimizationLevel.MINIMUM: "最低",
            OptimizationLevel.LOW: "低",
            OptimizationLevel.MEDIUM: "中",
            OptimizationLevel.HIGH: "高",
            OptimizationLevel.ULTRA: "极致"
        }
        self.auto_level.setText(f"当前画质等级: {level_names.get(current_level, '未知')}")
        
        recs = self.auto_tuner.get_recommendation()
        self.recommendations.setPlainText("\n".join(recs) if recs else "暂无建议")
    
    def run_benchmark_test(self):
        self.benchmark_btn.setEnabled(False)
        self.benchmark_btn.setText("测试中...")
        self.benchmark_status.setText("正在运行性能测试，请稍候...")
        
        self.benchmark_thread = BenchmarkThread(self.system_optimizer, self._benchmark_before)
        self.benchmark_thread.finished.connect(self._on_benchmark_done)
        self.benchmark_thread.start()
    
    def _on_benchmark_done(self, results, is_after):
        keys = ["cpu_score", "memory_score", "disk_score", "total_score"]
        
        if not is_after:
            self._benchmark_before = results
            for key in keys:
                lbl = getattr(self, f"bench_{key}_before", None)
                if lbl:
                    lbl.setText(str(results.get(key, 0)))
            self.benchmark_status.setText("基准测试完成！建议先一键优化，再点击测试查看优化后效果")
            self.benchmark_btn.setText("测试优化后")
            self.benchmark_btn.setEnabled(True)
        else:
            self._benchmark_after = results
            for key in keys:
                lbl = getattr(self, f"bench_{key}_after", None)
                if lbl:
                    lbl.setText(str(results.get(key, 0)))
            
            comparison = self.system_optimizer.compare_benchmarks(
                self._benchmark_before, self._benchmark_after
            )
            for key in keys:
                imp_lbl = getattr(self, f"bench_{key}_imp", None)
                if imp_lbl:
                    imp = comparison.get(f"{key}_improvement", 0)
                    sign = "+" if imp > 0 else ""
                    imp_lbl.setText(f"{sign}{imp}%")
            
            total_imp = comparison.get("total_score_improvement", 0)
            if total_imp > 0:
                self.benchmark_status.setText(f"测试完成！综合性能提升 {total_imp:.1f}%，优化效果显著")
            elif total_imp < 0:
                self.benchmark_status.setText("测试完成。性能略有波动，属于正常范围")
            else:
                self.benchmark_status.setText("测试完成。性能基本持平")
            
            self.benchmark_btn.setText("重新测试")
            self.benchmark_btn.setEnabled(True)
    
    def switch_page(self, index):
        self.content_stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
    
    def quick_optimize(self):
        mode = self.mode_combo.currentIndex() if hasattr(self, 'mode_combo') else 0
        mode_names = ["balanced", "performance", "extreme"]
        self.apply_optimizations(mode_names[mode])
    
    def apply_all_optimizations(self):
        mode_idx = self.mode_combo.currentIndex()
        mode_names = ["balanced", "performance", "extreme"]
        self.apply_optimizations(mode_names[mode_idx])
    
    def apply_optimizations(self, mode):
        self.health_label.setText("● 优化中...")
        
        results = self.system_optimizer.apply_all_optimizations(mode)
        
        for row in range(self.opt_table.rowCount()):
            name_item = self.opt_table.item(row, 0)
            if name_item.checkState() == Qt.CheckState.Checked:
                opt_key = None
                opts = self.system_optimizer.get_all_optimizations()
                for opt in opts:
                    if opt["name"] == name_item.text():
                        opt_key = opt["key"]
                        break
                
                if opt_key and opt_key in self.system_optimizer.applied_optimizations:
                    status_item = self.opt_table.item(row, 3)
                    status_item.setText("已优化")
                    status_item.setForeground(QBrush(QColor("#22c55e")))
        
        self.health_label.setText("● 优化完成")
        
        applied = self.system_optimizer.get_applied_count()
        QMessageBox.information(self, "优化完成", f"已成功应用 {applied} 项优化！\n\n系统性能已得到提升。")
    
    def restore_optimizations(self):
        reply = QMessageBox.question(
            self,
            "确认恢复",
            "确定要恢复所有系统设置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.system_optimizer.restore_all()
            
            for row in range(self.opt_table.rowCount()):
                status_item = self.opt_table.item(row, 3)
                status_item.setText("未优化")
                status_item.setForeground(QBrush(QColor("#94a3b8")))
            
            self.health_label.setText("● 已恢复")
            QMessageBox.information(self, "已恢复", "系统设置已恢复默认！")
    
    def scan_cleanup(self):
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("扫描中...")
        
        targets = self.system_cleaner.get_cleanup_targets()
        results, total_size, total_files = self.system_cleaner.scan_all(targets)
        
        self.clean_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            name_item = QTableWidgetItem(result["name"])
            name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            name_item.setCheckState(Qt.CheckState.Checked if result["safe"] else Qt.CheckState.Unchecked)
            
            count_item = QTableWidgetItem(str(result["file_count"]))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            size_item = QTableWidgetItem(self.system_cleaner.format_size(result["size"]))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            safe_item = QTableWidgetItem("安全" if result["safe"] else "谨慎")
            safe_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            safe_item.setForeground(QBrush(QColor("#22c55e" if result["safe"] else "#f59e0b")))
            
            self.clean_table.setItem(row, 0, name_item)
            self.clean_table.setItem(row, 1, count_item)
            self.clean_table.setItem(row, 2, size_item)
            self.clean_table.setItem(row, 3, safe_item)
        
        self.clean_result_label.setText(
            f"扫描完成！共发现 {total_files} 个垃圾文件，可释放 {self.system_cleaner.format_size(total_size)} 空间"
        )
        
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🔍 重新扫描")
    
    def clean_all(self):
        if self.clean_table.rowCount() == 0:
            QMessageBox.information(self, "提示", "请先扫描垃圾文件！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认清理",
            "确定要清理选中的垃圾文件吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            targets_to_clean = []
            targets = self.system_cleaner.get_cleanup_targets()
            
            for row in range(self.clean_table.rowCount()):
                name_item = self.clean_table.item(row, 0)
                if name_item.checkState() == Qt.CheckState.Checked:
                    for target in targets:
                        if target["name"] == name_item.text():
                            targets_to_clean.append(target)
                            break
            
            results, total_cleaned, total_files = self.system_cleaner.clean_all(targets_to_clean)
            
            self.clean_result_label.setText(
                f"清理完成！共清理 {total_files} 个文件，释放 {self.system_cleaner.format_size(total_cleaned)} 空间"
            )
            
            QMessageBox.information(
                self,
                "清理完成",
                f"成功清理 {total_files} 个文件！\n\n释放空间: {self.system_cleaner.format_size(total_cleaned)}"
            )
    
    def refresh_startup_items(self):
        items = self.startup_manager.get_startup_items()
        
        self.startup_table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            name_item = QTableWidgetItem(item.name)
            loc_item = QTableWidgetItem(item.location)
            loc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            impact_item = QTableWidgetItem(item.impact)
            impact_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            action_item = QTableWidgetItem("禁用")
            action_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            action_item.setForeground(QBrush(QColor("#f97316")))
            
            self.startup_table.setItem(row, 0, name_item)
            self.startup_table.setItem(row, 1, loc_item)
            self.startup_table.setItem(row, 2, impact_item)
            self.startup_table.setItem(row, 3, action_item)
    
    def kill_selected_process(self):
        current_row = self.process_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个进程！")
            return
        
        pid_item = self.process_table.item(current_row, 1)
        name_item = self.process_table.item(current_row, 0)
        
        if not pid_item:
            return
        
        pid = int(pid_item.text())
        name = name_item.text()
        
        reply = QMessageBox.question(
            self,
            "确认结束进程",
            f"确定要结束进程 \"{name}\" (PID: {pid}) 吗？\n\n这可能导致未保存的数据丢失。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.process_manager.kill_process(pid)
            if success:
                QMessageBox.information(self, "成功", f"进程 {name} 已结束。")
            else:
                QMessageBox.warning(self, "失败", f"无法结束进程: {msg}")
    
    def toggle_game_mode(self):
        if self.is_optimizing:
            self.system_optimizer.restore_all()
            self.is_optimizing = False
            self.game_mode_toggle.setText("🎮 开启游戏模式")
            self.health_label.setText("● 就绪")
        else:
            self.system_optimizer.apply_all_optimizations("extreme")
            self.is_optimizing = True
            self.game_mode_toggle.setText("⏹️ 关闭游戏模式")
            self.health_label.setText("● 游戏模式")
            
            QMessageBox.information(self, "游戏模式", "游戏模式已开启！\n\n系统已切换到极致性能模式。")
    
    def select_shortcut(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择游戏快捷方式",
            os.path.expandvars(r"%USERPROFILE%\Desktop"),
            "快捷方式 (*.lnk);;可执行文件 (*.exe);;所有文件 (*.*)"
        )
        
        if file_path:
            self.game_shortcut = file_path
            
            if file_path.endswith('.lnk'):
                info = self.game_launcher.parse_shortcut(file_path)
                if info:
                    self.game_path_label.setText(
                        f"目标: {info['target']}\n"
                        f"工作目录: {info['work_dir']}"
                    )
            else:
                self.game_path_label.setText(f"已选择: {file_path}")
    
    def start_game_mode(self):
        if not self.game_shortcut:
            QMessageBox.warning(self, "提示", "请先选择游戏快捷方式！")
            return
        
        self.system_optimizer.apply_all_optimizations("extreme")
        self.is_optimizing = True
        self.game_mode_toggle.setText("⏹️ 关闭游戏模式")
        
        if self.game_shortcut.endswith('.lnk'):
            success, msg = self.game_launcher.launch_from_shortcut(self.game_shortcut)
        else:
            success, msg = self.game_launcher.launch_game(self.game_shortcut)
        
        if success:
            pid = self.game_launcher.get_game_pid()
            if pid:
                self.system_optimizer.set_process_high_priority(pid)
            
            self.auto_tuner.start()
            self.auto_status.setText("状态: 自动调优运行中")
            self.auto_tune_btn.setText("停止停止")
            
            QMessageBox.information(self, "成功", f"游戏已启动！\n\n{msg}\n\n游戏模式已开启，自动调优运行中。")
        else:
            QMessageBox.warning(self, "提示", f"游戏启动提示: {msg}\n\n游戏模式仍会保持开启。")
    
    def toggle_auto_tune(self):
        if self.auto_tuner.running:
            self.auto_tuner.stop()
            self.auto_tune_btn.setText("启动自动调优")
            self.auto_status.setText("状态: 已停止")
        else:
            self.auto_tuner.start()
            self.auto_tune_btn.setText("停止自动调优")
            self.auto_status.setText("状态: 自动调优运行中")
    
    def closeEvent(self, event):
        if self.is_optimizing:
            reply = QMessageBox.question(
                self,
                "确认退出",
                "检测到优化正在运行，是否恢复系统设置后退出？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.auto_tuner.stop()
                self.perf_monitor.stop()
                self.system_optimizer.restore_all()
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                self.auto_tuner.stop()
                self.perf_monitor.stop()
                event.accept()
            else:
                event.ignore()
        else:
            self.perf_monitor.stop()
            event.accept()
