import sys
import datetime
from tzlocal import get_localzone_name
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, QRect, QPointF, QEasingCurve

# --- Цветовая палитра ---
LIME_GREEN = QColor("#ADFF2F")  # Яркий лайм
DARK_BACKGROUND = QColor("#121212")
BORDER_COLOR = QColor("#333333")
MAIN_TEXT_COLOR = LIME_GREEN
TIME_COLOR = QColor("#FFFFFF")

class ElectricLineWidget(QWidget):
    """Виджет для рисования декоративных линий с анимированной искрой."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._spark_position = 0.0  # Позиция искры от 0.0 до 1.0

        # Анимация для движения искры
        self.animation = QPropertyAnimation(self, b'spark_position')
        self.animation.setDuration(3000) # 3 секунды на один проход
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setLoopCount(-1) # Бесконечный цикл
        self.animation.start()

    # Свойство для анимации
    @pyqtProperty(float)
    def spark_position(self):
        return self._spark_position

    @spark_position.setter
    def spark_position(self, value):
        self._spark_position = value
        self.update()  # Перерисовать виджет при изменении позиции

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(LIME_GREEN, 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        # Рисуем декоративные линии
        w, h = self.width(), self.height()
        path_points = [
            QPointF(w * 0.1, h * 0.9),
            QPointF(w * 0.2, h * 0.2),
            QPointF(w * 0.8, h * 0.2),
            QPointF(w * 0.9, h * 0.9)
        ]
        painter.drawPolyline(path_points)
        
        # Рисуем искру
        spark_point = self.calculate_spark_point(path_points)
        spark_color = LIME_GREEN.lighter(150)
        painter.setBrush(QBrush(spark_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(spark_point, 5, 5)

    def calculate_spark_point(self, points):
        """Вычисляет координаты искры вдоль ломаной линии."""
        total_length = 0
        lengths = []
        for i in range(len(points) - 1):
            length = (points[i+1] - points[i]).toPoint().manhattanLength()
            lengths.append(length)
            total_length += length
        
        if total_length == 0:
            return points[0]

        target_length = self._spark_position * total_length
        current_length = 0
        for i in range(len(points) - 1):
            segment_length = lengths[i]
            if current_length + segment_length >= target_length:
                ratio = (target_length - current_length) / segment_length
                start, end = points[i], points[i+1]
                return start + (end - start) * ratio
            current_length += segment_length
        return points[-1]


class CustomProgressBar(QWidget):
    """Современный кастомный прогресс-бар."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0 # 0 to 100
        self.setFixedSize(300, 15)

    def setProgress(self, value):
        self._progress = max(0, min(100, value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Фон
        rect = self.rect()
        painter.setBrush(QBrush(DARK_BACKGROUND))
        painter.setPen(QPen(BORDER_COLOR, 1))
        painter.drawRoundedRect(rect, 7, 7)

        # Полоса прогресса
        if self._progress > 0:
            progress_width = int(self._progress / 100.0 * self.width())
            progress_rect = QRect(0, 0, progress_width, self.height())
            painter.setBrush(QBrush(LIME_GREEN))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(progress_rect, 7, 7)

class TimeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Current Time")
        self.setFixedSize(500, 350)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {DARK_BACKGROUND.name()};
            }}
        """)
        
        # --- Виджеты ---
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Декорации
        self.lines = ElectricLineWidget(self.central_widget)
        self.lines.setGeometry(0, 0, 500, 350)

        # Кнопка
        self.time_button = QPushButton("Который час?", self.central_widget)
        self.time_button.setGeometry(150, 100, 200, 80)
        self.time_button.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.time_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {MAIN_TEXT_COLOR.name()};
                border: 2px solid {LIME_GREEN.name()};
                border-radius: 40px;
            }}
            QPushButton:hover {{
                background-color: {LIME_GREEN.name()};
                color: {DARK_BACKGROUND.name()};
            }}
            QPushButton:pressed {{
                background-color: {LIME_GREEN.darker(120).name()};
            }}
        """)

        # Прогресс-бар
        self.progress_bar = CustomProgressBar(self.central_widget)
        self.progress_bar.setGeometry(100, 200, 300, 15)
        self.progress_bar.hide()
        
        self.progress_timer = QTimer(self)
        self.progress_value = 0

        # Метки для времени и часового пояса
        self.time_label = QLabel("", self.central_widget)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Consolas", 48, QFont.Weight.Bold))
        self.time_label.setGeometry(0, 100, 500, 80)
        self.time_label.setStyleSheet(f"color: {TIME_COLOR.name()}; background: transparent;")
        
        self.timezone_label = QLabel("", self.central_widget)
        self.timezone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timezone_label.setFont(QFont("Segoe UI", 14))
        self.timezone_label.setGeometry(0, 180, 500, 40)
        self.timezone_label.setStyleSheet(f"color: {LIME_GREEN.name()}; background: transparent;")

        # --- Анимации для появления текста ---
        self.time_anim = QPropertyAnimation(self.time_label, b"windowOpacity")
        self.tz_anim = QPropertyAnimation(self.timezone_label, b"windowOpacity")
        
        # --- Подключения ---
        self.time_button.clicked.connect(self.start_time_request)
        self.progress_timer.timeout.connect(self.update_progress)
        
        self.hide_time_labels(instant=True)

    def start_time_request(self):
        """Запускает процесс отображения времени."""
        self.time_button.hide()
        self.hide_time_labels(instant=True)
        
        self.progress_value = 0
        self.progress_bar.setProgress(0)
        self.progress_bar.show()
        
        # Прогресс-бар будет обновляться каждые 70 мс в течение 7 секунд
        self.progress_timer.start(70) 

    def update_progress(self):
        """Обновляет значение прогресс-бара."""
        self.progress_value += 1
        self.progress_bar.setProgress(self.progress_value)
        if self.progress_value >= 100:
            self.progress_timer.stop()
            self.progress_bar.hide()
            self.show_time()

    def show_time(self):
        """Отображает время с анимацией."""
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        timezone_name = get_localzone_name()
        
        self.time_label.setText(current_time)
        self.timezone_label.setText(timezone_name)

        # Настраиваем и запускаем анимацию проявления
        for anim in [self.time_anim, self.tz_anim]:
            anim.setDuration(1500) # 1.5 секунды
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            anim.start()
        
        self.time_label.show()
        self.timezone_label.show()
        
        # Показать кнопку снова через некоторое время
        QTimer.singleShot(2000, self.time_button.show)

    def hide_time_labels(self, instant=False):
        """Скрывает метки с временем."""
        if instant:
            self.time_label.hide()
            self.timezone_label.hide()
        else:
            # Здесь можно было бы сделать анимацию исчезновения
            self.time_label.hide()
            self.timezone_label.hide()
            
if __name__ == '__main__':
    # Убедитесь, что установлены необходимые библиотеки:
    # pip install PyQt6 tzlocal
    app = QApplication(sys.argv)
    window = TimeApp()
    window.show()
    sys.exit(app.exec())
