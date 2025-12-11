from typing import Optional
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QApplication, QHBoxLayout, QSpinBox, QDoubleSpinBox, QMessageBox
from PySide6.QtCore import Qt, QTimer
import win32api
import win32con
import sys

class Clicker(QWidget):
    def __init__(self) -> None:
        """
        初始化Click类实例
        
        Returns:
            None: 无返回值
        """
        super().__init__()
        self.count: int = 50  # 默认点击次数
        self.click_interval: float = 0.1  # 默认点击间隔时间(秒)
        self.click_x: int = 900  # 默认点击位置X坐标
        self.click_y: int = 450  # 默认点击位置Y坐标
        self.is_selecting_position: bool = False  # 是否正在选择点击位置
        self._click_in_progress: bool = False # 是否正在点击中
        self.selection_timer: Optional[QTimer] = None  # 选择点击位置定时器
        self.init_ui()

    def init_ui(self) -> None:
        """
        初始化用户界面
        
        Returns:
            None: 无返回值
        """
        self.setWindowTitle("点击器")
        self.setFixedSize(300,150)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        layout = QVBoxLayout()

        # 点击次数输入控件
        count_layout = QHBoxLayout()
        count_label = QLabel("点击次数：")
        self.count_input = QSpinBox()
        self.count_input.setMinimum(1)
        self.count_input.setMaximum(1000000)
        self.count_input.setValue(self.count)
        self.count_input.valueChanged.connect(self.update_counter)
        
        count_layout.addWidget(count_label)
        count_layout.addWidget(self.count_input)
        
        # 点击间隔时间输入控件
        interval_layout = QHBoxLayout()
        interval_label = QLabel("间隔时间(秒)：")
        self.interval_input = QDoubleSpinBox()
        self.interval_input.setMinimum(0.01)
        self.interval_input.setMaximum(10.0)
        self.interval_input.setSingleStep(0.1)
        self.interval_input.setValue(self.click_interval)
        self.interval_input.valueChanged.connect(self.update_interval)
        
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_input)
        
        # 点击位置选择控件
        position_layout = QHBoxLayout()
        position_label = QLabel("点击位置：")
        self.position_label_display = QLabel(f"x: {self.click_x}, y: {self.click_y}")
        self.select_position_btn = QPushButton("选择位置")
        self.select_position_btn.clicked.connect(self.start_position_selection)
        
        position_layout.addWidget(position_label)
        position_layout.addWidget(self.position_label_display)
        position_layout.addStretch(1)
        position_layout.addWidget(self.select_position_btn)
        
        # 提示信息区域
        info_layout = QHBoxLayout()
        self.number_label = QLabel(f"剩余点击次数：{str(self.count)}")
        self.position_label = QLabel(f"当前坐标：x: {self.click_x}, y: {self.click_y}")

        info_layout.addWidget(self.number_label)
        info_layout.addWidget(self.position_label)

        # 开始按钮
        self.start_btn = QPushButton("开始")
        self.start_btn.clicked.connect(self.start_clicking)

        layout.addLayout(count_layout)
        layout.addLayout(interval_layout)
        layout.addLayout(position_layout)
        layout.addLayout(info_layout)
        layout.addStretch(1)    
        layout.addWidget(self.start_btn)

        self.setLayout(layout)

        # 坐标更新定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.get_position)
        self.timer.start(100)
        
        # 自动点击定时器
        self.click_timer = QTimer(self)
        self.click_timer.timeout.connect(self.auto_click)

        # 右键检测定时器
        self.stop_timer = QTimer(self)
        self.stop_timer.timeout.connect(self.check_stop_right_click)

        # 位置选择定时器
        self.selection_timer = QTimer(self)
        self.selection_timer.timeout.connect(self.check_mouse_click)

    def update_counter(self, value: int) -> None:
        """
        更新计数器显示的剩余点击次数
        
        Args:
            value (int): 要设置的新计数值
            
        Returns:
            None: 无返回值
        """
        self.count = value
        self.number_label.setText(f"剩余点击次数：{str(self.count)}")
            
    def update_interval(self, value: float) -> None:
        """
        更新点击间隔时间
        
        Args:
            value (float): 新的点击间隔时间（秒）
            
        Returns:
            None: 无返回值
        """
        self.click_interval = value
        
    def start_position_selection(self) -> None:
        """
        开始选择点击位置
        
        Returns:
            None: 无返回值
        """
        self.is_selecting_position = True
        self.select_position_btn.setText("点击任意位置")
        self.select_position_btn.setStyleSheet("background-color: red; color: white;")
        # 启动定时器来监听鼠标点击
        if self.selection_timer is None or not self.selection_timer.isActive():
            self.selection_timer.start(50)

    def check_mouse_click(self) -> None:
        """
        检查鼠标点击状态并获取点击位置坐标
        
        Returns:
            None: 无返回值
        """
        # 检查鼠标左键是否被点击
        if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
            # 获取当前鼠标位置
            x, y = win32api.GetCursorPos()
            self.click_x = x
            self.click_y = y
            self.position_label_display.setText(f"x: {self.click_x}, y: {self.click_y}")
            
            # 停止选择过程
            self.is_selecting_position = False
            if self.selection_timer is not None and self.selection_timer.isActive():
                self.selection_timer.stop()
            self.select_position_btn.setText("选择位置")
            self.select_position_btn.setStyleSheet("")
            
    def start_clicking(self) -> None:
        """
        开始或停止自动点击过程
        
        Returns:
            None: 无返回值
        """
        if self.click_timer.isActive():
            # 如果已经在点击，则停止
            self.click_timer.stop()
            if self.stop_timer.isActive():
                self.stop_timer.stop()
            self.start_btn.setText("开始")
            self.count_input.setEnabled(True)
            self.interval_input.setEnabled(True)
            self.select_position_btn.setEnabled(True)
        else:
            # 开始自动点击
            self.count = self.count_input.value()
            self.number_label.setText(f"剩余点击次数：{str(self.count)}")
            self.count_input.setEnabled(False)
            self.interval_input.setEnabled(False)
            self.select_position_btn.setEnabled(False)
            self.start_btn.setText("停止")

            # 根据设定的时间间隔点击（使用毫秒）
            self.click_timer.start(int(self.click_interval * 1000))
            # 开始时启动右键检测
            self.stop_timer.start(50)

    def auto_click(self) -> None:
        """
        执行自动点击操作
        
        Returns:
            None: 无返回值
        """
        # 防止重入：如果已有点击进行中，跳过本次触发
        if self.count <= 0:
            self._finish_clicking()
            return

        if self._click_in_progress:
            return

        # 开始一次点击动作，按下 -> 延迟释放 -> 更新计数
        self._click_in_progress = True
        win32api.SetCursorPos((self.click_x, self.click_y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, self.click_x, self.click_y, 0, 0)
        QTimer.singleShot(50, self._release_and_update)

    def _release_and_update(self) -> None:
        """
        释放鼠标按键并更新点击计数
        
        Returns:
            None: 无返回值
        """
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, self.click_x, self.click_y, 0, 0)
        self.count -= 1
        self.number_label.setText(f"剩余点击次数：{str(self.count)}")
        self._click_in_progress = False
        if self.count <= 0:
            self._finish_clicking()

    def _finish_clicking(self) -> None:
        """
        完成点击任务并恢复UI状态
        
        Returns:
            None: 无返回值
        """
        if self.click_timer.isActive():
            self.click_timer.stop()
        if hasattr(self, 'stop_timer') and self.stop_timer.isActive():
            self.stop_timer.stop()
        self.start_btn.setText("开始")
        self.count_input.setEnabled(True)
        self.interval_input.setEnabled(True)
        self.select_position_btn.setEnabled(True)

    def check_stop_right_click(self) -> None:
        """
        检测右键按下以停止自动点击

        Returns:
            None
        """
        # 如果检测到右键按下，停止自动点击
        if win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000:
            self._finish_clicking()

    def get_position(self) -> None:
        """
        获取并更新当前鼠标位置信息
        
        Returns:
            None: 无返回值
        """
        x, y = win32api.GetCursorPos()

        # 仅当位置变更时更新标签以减少 GUI 重绘
        current_text = self.position_label.text()
        new_text = f"当前坐标：x: {x}, y: {y}"
        if current_text != new_text:
            self.position_label.setText(new_text)


def main():
    """程序入口点"""
    app: QApplication = QApplication([])
    app.setStyle("Fusion")
    click: Clicker = Clicker()
    click.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
