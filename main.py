import sys
from transformers import AutoModelForCausalLM, AutoTokenizer
from PySide6.QtCore import QThread, Signal, QTimer, Slot, QSize, QDateTime, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QTextEdit, QVBoxLayout, QLineEdit, QWidget, QHBoxLayout, QMainWindow, QStackedWidget
from PySide6.QtGui import QTextCharFormat, QColor, QFont
from bs4 import BeautifulSoup

def init_model():
    checkpoint = r"E:\PythonProject\rag\Qwen\Qwen2.5-1.5B-Instruct"
    device = "cpu"
    model = AutoModelForCausalLM.from_pretrained(
        checkpoint,
        torch_dtype="auto",
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    return tokenizer, model, device

def llm_response(messages, tokenizer, model, device):
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=512
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return response

class MyThread(QThread):
    finished_signal = Signal(str)

    def __init__(self, message, tokenizer, model, device):
        super().__init__()
        self.message = message
        self.tokenizer = tokenizer
        self.model = model
        self.device = device

    def run(self):
        response = llm_response(self.message, self.tokenizer, self.model, self.device)
        self.finished_signal.emit(response)

class ChatWidget(QWidget):
    def __init__(self, tokenizer, model, device):
        super().__init__()
        self.tokenizer = tokenizer
        self.model = model
        self.device = device
        self.message_id = 0
        self.setup_ui()
        self.setup_chat_styles()
        self.request_button.clicked.connect(self.send_request)
        self.clear_history_button.clicked.connect(self.clear_history)
        self.thinking_timer = QTimer(self)
        self.thinking_timer.timeout.connect(self.update_thinking_label)
        self.thinking_dot_count = 0
        self.history = [
            {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."}
        ]

    def setup_chat_styles(self):
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .chat-container { padding: 10px; }
                .message { margin-bottom: 10px; padding: 5px; }
                .user-message { color: blue; }
                .assistant-message { color: red; }
                .thinking-message { color: red; }
                .timestamp { color: gray; font-size: 8pt; margin-left: 5px; }
            </style>
        </head>
        <body>
            <div id="chat-container"></div>
        </body>
        </html>
        """
        self.chat_area.setHtml(html_template)
        self.soup = BeautifulSoup(html_template, "lxml")
        self.chat_container = self.soup.find(id="chat-container")

    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        main_layout.addWidget(self.chat_area)
        
        input_layout = QHBoxLayout()
        
        self.input_text = QLineEdit(self)
        self.input_text.setPlaceholderText("请输入您的问题")
        input_layout.addWidget(self.input_text)
        
        self.input_text.returnPressed.connect(self.send_request)
        
        self.request_button = QPushButton('发送')
        self.request_button.setFixedWidth(50)
        input_layout.addWidget(self.request_button)
        
        self.clear_history_button = QPushButton('清空历史消息')
        self.clear_history_button.setFixedWidth(100)
        input_layout.addWidget(self.clear_history_button)
        
        main_layout.addLayout(input_layout)
        self.setLayout(main_layout)

    def send_request(self):
        message = self.input_text.text().strip()
        self.history.append({"role": "user", "content": message})

        if not message:
            self.chat_area.append("请输入问题")
            return
        
        self.add_message("User", message)
        self.input_text.clear()
        self.thinking_dot_count = 0
        self.update_thinking_label()
        self.thinking_timer.start(1000)
        self.thread_ = MyThread(self.history, self.tokenizer, self.model, self.device)

        self.thread_.finished_signal.connect(self.thread_finished)
        self.thread_.start()

    def clear_history(self):
        self.history = [
            {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."}
        ]

    def add_message(self, role, message):
        self.message_id += 1
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        message_div = self.soup.new_tag('span', id=f'msg-{self.message_id}', **{'class': 'message'})
        if role == "thinking":
            thinking_div = self.soup.find(id="thinking-message")
            if thinking_div:
                thinking_div.decompose()
                
            message_div['id'] = "thinking-message"
            message_div['class'] = "thinking-message"
            message_div.string = f"Assistant: {message}"
        else:
            content_span = self.soup.new_tag('span')
            content_span['class'] = f"{role.lower()}-message"
            content_span.string = f"{role}: {message}"
            message_div.append(content_span)
            br = self.soup.new_tag('br')
            message_div.append(br)
            time_span = self.soup.new_tag('span', **{'class': 'timestamp'})
            time_span.string = f"({current_time})"
            message_div.append(time_span)
            br = self.soup.new_tag('br')
            message_div.append(br)
            
        self.chat_container.append(message_div)
        self.chat_area.setHtml(str(self.soup))
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )
        
    @Slot()
    def update_thinking_label(self):
        self.thinking_dot_count = (self.thinking_dot_count + 1) % 4
        dots = '.' * self.thinking_dot_count
        self.add_message("thinking", f"正在思考{dots}")

    @Slot(str)
    def thread_finished(self, response):
        self.thinking_timer.stop()
        thinking_div = self.soup.find(id="thinking-message")
        if thinking_div:
            thinking_div.decompose()
        self.add_message("Assistant", response)
        self.history.append({"role": "assistant", "content": response})
        print(self.history)

class MainWindow(QMainWindow):
    def __init__(self, tokenizer, model, device):
        super().__init__()
        self.setWindowTitle("对话系统")
        self.setFixedSize(900, 600)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧边栏
        sidebar = QWidget()
        sidebar.setFixedWidth(100)
        sidebar.setStyleSheet("background-color: #f0f0f0;")
        sidebar_layout = QVBoxLayout(sidebar)
        
        sidebar_layout.addStretch()
        
        knowledge_btn = QPushButton("知识库")
        knowledge_btn.clicked.connect(self.show_knowledge_base)
        sidebar_layout.addWidget(knowledge_btn)
        
        self.right_stack = QStackedWidget()
        
        # 对话区域
        self.chat_widget = ChatWidget(tokenizer, model, device)
        
        # 知识库区域
        self.knowledge_area = QWidget()
        knowledge_layout = QVBoxLayout(self.knowledge_area)
        
        back_btn = QPushButton("返回对话")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.show_chat)
        knowledge_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        knowledge_layout.addStretch()
        
        self.right_stack.addWidget(self.chat_widget)
        self.right_stack.addWidget(self.knowledge_area)
        
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.right_stack)
        
    def show_knowledge_base(self):
        self.right_stack.setCurrentIndex(1)
        
    def show_chat(self):
        self.right_stack.setCurrentIndex(0)

if __name__ == '__main__':
    tokenizer, model, device = init_model()
    app = QApplication(sys.argv)
    window = MainWindow(tokenizer, model, device)
    window.show()
    sys.exit(app.exec())