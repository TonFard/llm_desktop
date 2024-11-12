import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QWidget, 
                              QVBoxLayout, QLabel, QFrame, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent

class Card(QFrame):
    def __init__(self, number, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("background-color: lightblue; border: 1px solid black;")
        self.number = number  # 保存卡片编号
        
        self.delete_button = QPushButton("×", self)
        self.delete_button.setFixedSize(20, 20)
        self.delete_button.setStyleSheet(
            "QPushButton { background-color: red; color: white; border: none; }"
            "QPushButton:hover { background-color: darkred; }"
        )
        
        self.content_label = QLabel(f"Card {number}", self)
        self.content_label.setAlignment(Qt.AlignCenter)
        
    def resizeEvent(self, event):
        self.delete_button.move(
            self.width() - self.delete_button.width(),
            0
        )
        self.content_label.setGeometry(10, 10, self.width() - 20, self.height() - 20)

class CardArea(QWidget):
    def __init__(self, cards_width, cards_height, row, col):
        super().__init__()
        self.cards = []
        self.pages = [[]]
        self.current_page = 0
        self.cards_per_page = row * col
        self.row = row
        self.col = col
        self.cards_height = cards_height
        self.cards_width = cards_width
        self.card_count = 0
        self.setMinimumSize(self.cards_width, self.cards_height)
        
    # 在CardArea类中修改add_card方法：
    def add_card(self):
        self.card_count += 1
        card = Card(self.card_count, self)
        card_width = self.cards_width // self.col
        card_height = self.cards_height // self.row
        card.setFixedSize(card_width - 10, card_height - 10)
        
        current_page_cards = len(self.pages[self.current_page])
        cur_row = current_page_cards // self.col
        cur_col = current_page_cards % self.col
        x_pos = cur_col * card_width + 5
        y_pos = cur_row * card_height + 5
        
        card.move(x_pos, y_pos)
        card.show()
        
        card.delete_button.clicked.connect(lambda: self.confirm_remove_card(card))
        
        self.cards.append(card)
        self.pages[self.current_page].append(card)
        self.recalculate_positions()  # 确保位置正确
        
    def confirm_remove_card(self, card):
        reply = QMessageBox.question(
            self,
            'Confirm Deletion',
            'Are you sure you want to delete this card?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.remove_card(card)
            
    def remove_card(self, card):
        if card in self.cards:
            # 找到要删除的卡片在哪一页
            page_index = None
            for i, page in enumerate(self.pages):
                if card in page:
                    page_index = i
                    break
                    
            if page_index is not None:
                # 从cards和pages中移除卡片
                self.cards.remove(card)
                self.pages[page_index].remove(card)
                card.deleteLater()
                
                # 重新组织页面
                self.reorganize_pages()
                
                # 如果当前页超出范围，切换到最后一页
                if self.current_page >= len(self.pages):
                    self.current_page = max(0, len(self.pages) - 1)
                
                # 重新显示当前页
                self.show_page(self.current_page)

    def reorganize_pages(self):
        # 将所有卡片重新组织到页面中
        all_cards = self.cards.copy()
        self.pages = [[]]
        
        # 按每页最大容量重新分配卡片
        for i, card in enumerate(all_cards):
            page_index = i // self.cards_per_page
            while len(self.pages) <= page_index:
                self.pages.append([])
            self.pages[page_index].append(card)
            
        # 移除空页面
        self.pages = [page for page in self.pages if page]
        
        # 如果没有页面，创建一个空页面
        if not self.pages:
            self.pages = [[]]
            
    def recalculate_positions(self):
        card_width = self.cards_width // self.col
        card_height = self.cards_height // self.row
        
        # 首先隐藏所有卡片
        for card in self.cards:
            card.hide()
            
        # 只显示当前页的卡片，并重新计算位置
        if self.current_page < len(self.pages):
            for i, card in enumerate(self.pages[self.current_page]):
                cur_row = i // self.col
                cur_col = i % self.col
                x_pos = cur_col * card_width + 5
                y_pos = cur_row * card_height + 5
                card.move(x_pos, y_pos)
                card.show()
            
    def hide_all_cards(self):
        for card in self.cards:
            card.hide()
            
    def show_page(self, page_number):
        if 0 <= page_number < len(self.pages):
            self.current_page = page_number
            self.recalculate_positions()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Card Generator")
        self.setFixedSize(1000, 700)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        
        # 创建卡片显示区域 (2x2 格式)
        self.card_area = CardArea(1000, 600, 2, 2)
        
        # 创建底部控制栏
        self.bottom_widget = QWidget()
        self.bottom_layout = QHBoxLayout(self.bottom_widget)
        
        # 创建生成按钮容器（靠右）
        self.generate_container = QWidget()
        self.generate_layout = QHBoxLayout(self.generate_container)
        self.generate_button = QPushButton("Generate Card")
        self.generate_layout.addWidget(self.generate_button)
        self.generate_layout.addStretch()
        
        # 创建页面控制容器（居中）
        self.page_control_container = QWidget()
        self.page_control_layout = QHBoxLayout(self.page_control_container)
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.page_label = QLabel("Page: 1/1")
        
        # 设置按钮大小
        for button in [self.prev_button, self.next_button, self.generate_button]:
            button.setFixedHeight(40)
            button.setMinimumWidth(100)
        
        # 添加页面控制按钮到居中容器
        self.page_control_layout.addStretch()
        self.page_control_layout.addWidget(self.prev_button)
        self.page_control_layout.addWidget(self.page_label)
        self.page_control_layout.addWidget(self.next_button)
        self.page_control_layout.addStretch()
        
        # 将容器添加到底部布局
        self.bottom_layout.addWidget(self.page_control_container)
        self.bottom_layout.addWidget(self.generate_container)
        
        # 连接信号
        self.generate_button.clicked.connect(self.on_generate_clicked)
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)
        
        # 将主要部件添加到布局中
        self.layout.addWidget(self.card_area)
        self.layout.addWidget(self.bottom_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 更新页面按钮状态
        self.update_page_controls()
        
    # 在MainWindow类中修改on_generate_clicked方法：
    def on_generate_clicked(self):
        # 如果当前页面已满，先创建新页面并跳转
        if (len(self.card_area.pages[self.card_area.current_page]) >= 
            self.card_area.cards_per_page):
            self.card_area.pages.append([])
            self.card_area.show_page(len(self.card_area.pages) - 1)
            self.update_page_controls()
        
        # 然后添加新卡片
        self.card_area.add_card()
        self.update_page_controls()
        
    def prev_page(self):
        if self.card_area.current_page > 0:
            self.card_area.show_page(self.card_area.current_page - 1)
            self.update_page_controls()
            
    def next_page(self):
        if self.card_area.current_page < len(self.card_area.pages) - 1:
            self.card_area.show_page(self.card_area.current_page + 1)
            self.update_page_controls()
            
    def update_page_controls(self):
        # 确保至少有一页
        if not self.card_area.pages:
            self.card_area.pages = [[]]
            self.card_area.current_page = 0
            
        current_page = self.card_area.current_page + 1
        total_pages = len(self.card_area.pages)
        self.page_label.setText(f"Page: {current_page}/{total_pages}")
        
        # 更新按钮状态
        self.prev_button.setEnabled(current_page > 1)
        self.next_button.setEnabled(current_page < total_pages)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())