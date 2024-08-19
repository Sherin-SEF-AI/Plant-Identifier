import sys
import requests
import base64
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QTextEdit, 
                             QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QProgressBar, QComboBox,
                             QTabWidget, QLineEdit, QGridLayout, QSpinBox, QCheckBox)
from PyQt5.QtGui import QPixmap, QIcon, QFont, QTextCharFormat, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class GeminiAPIThread(QThread):
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, image_path, api_key, prompt, model="gemini-pro-vision"):
        super().__init__()
        self.image_path = image_path
        self.api_key = api_key
        self.prompt = prompt
        self.model = model

    def run(self):
        try:
            with open(self.image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": self.prompt},
                            {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
                        ]
                    }
                ]
            }
            headers = {
                'Content-Type': 'application/json'
            }
            api_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.api_key}'

            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            self.result_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))

class EnhancedPlantIdentifierApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Enhanced Plant Identifier App')
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon('plant_icon.png'))  # Make sure to have this icon file
        self.setStyleSheet("""
            QMainWindow, QTabWidget::pane {
                background-color: #f0f8ff;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLabel, QTextEdit, QLineEdit {
                font-size: 14px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #e1e1e1;
                border: 1px solid #c4c4c4;
                border-bottom-color: #C2C7CB;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 8ex;
                padding: 2px;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background-color: #4CAF50;
                color: white;
            }
        """)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_identifier_tab(), "Plant Identifier")
        self.tab_widget.addTab(self.create_care_guide_tab(), "Care Guide")
        self.tab_widget.addTab(self.create_disease_detector_tab(), "Disease Detector")

        main_layout.addWidget(self.tab_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def create_identifier_tab(self):
        tab = QWidget()
        layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Left side (Image upload and display)
        self.image_label = QLabel('Upload an image of a plant')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #aaa; border-radius: 5px; padding: 10px;")
        left_layout.addWidget(self.image_label)

        upload_button = QPushButton('Upload Image')
        upload_button.clicked.connect(self.upload_image)
        left_layout.addWidget(upload_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        # Right side (Results and options)
        self.result_text = QTextEdit('Plant information will appear here...')
        self.result_text.setReadOnly(True)
        right_layout.addWidget(self.result_text)

        self.language_combo = QComboBox()
        self.language_combo.addItems(['English', 'Spanish', 'French', 'German'])
        self.language_combo.currentIndexChanged.connect(self.translate_result)
        right_layout.addWidget(self.language_combo)

        save_button = QPushButton('Save Results')
        save_button.clicked.connect(self.save_results)
        right_layout.addWidget(save_button)

        layout.addLayout(left_layout, 1)
        layout.addLayout(right_layout, 1)
        tab.setLayout(layout)
        return tab

    def create_care_guide_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Plant Name:"))
        self.plant_name_input = QLineEdit()
        input_layout.addWidget(self.plant_name_input)
        generate_button = QPushButton("Generate Care Guide")
        generate_button.clicked.connect(self.generate_care_guide)
        input_layout.addWidget(generate_button)

        layout.addLayout(input_layout)

        self.care_guide_text = QTextEdit()
        self.care_guide_text.setReadOnly(True)
        layout.addWidget(self.care_guide_text)

        tab.setLayout(layout)
        return tab

    def create_disease_detector_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        upload_layout = QHBoxLayout()
        self.disease_image_label = QLabel('Upload an image of the plant')
        self.disease_image_label.setAlignment(Qt.AlignCenter)
        self.disease_image_label.setStyleSheet("border: 2px dashed #aaa; border-radius: 5px; padding: 10px;")
        upload_layout.addWidget(self.disease_image_label)

        upload_disease_button = QPushButton('Upload Image')
        upload_disease_button.clicked.connect(self.upload_disease_image)
        upload_layout.addWidget(upload_disease_button)

        layout.addLayout(upload_layout)

        detect_button = QPushButton("Detect Disease")
        detect_button.clicked.connect(self.detect_disease)
        layout.addWidget(detect_button)

        self.disease_result_text = QTextEdit()
        self.disease_result_text.setReadOnly(True)
        layout.addWidget(self.disease_result_text)

        tab.setLayout(layout)
        return tab

    def upload_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open Image File', '', 'Images (*.png *.jpg *.jpeg)')
        if file_name:
            pixmap = QPixmap(file_name)
            scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.identify_plant(file_name)

    def upload_disease_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open Image File', '', 'Images (*.png *.jpg *.jpeg)')
        if file_name:
            pixmap = QPixmap(file_name)
            scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.disease_image_label.setPixmap(scaled_pixmap)
            self.disease_image_path = file_name

    def identify_plant(self, image_path):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        api_key = 'AIzaSyB9SHxq8lN2wn-YNDL2urjbZycOqK8YnmI'  # Your API key
        prompt = "Identify this plant and provide detailed information about it, including its scientific name, common names, care instructions, and any interesting facts."
        self.thread = GeminiAPIThread(image_path, api_key, prompt)
        self.thread.result_signal.connect(self.display_plant_result)
        self.thread.error_signal.connect(self.display_error)
        self.thread.finished.connect(lambda: self.progress_bar.setVisible(False))
        self.thread.start()

    def display_plant_result(self, result):
        if 'candidates' in result and result['candidates']:
            plant_info = result['candidates'][0]['content']['parts'][0]['text']
            self.result_text.setPlainText(plant_info)
        else:
            self.result_text.setPlainText("No information found. Try another image.")

    def display_error(self, error):
        QMessageBox.critical(self, "Error", f"API request failed: {error}")
        self.result_text.setPlainText("Failed to process the request.")

    def translate_result(self):
        # Here you would implement the translation logic
        # For demonstration, we'll just add a prefix
        language = self.language_combo.currentText()
        current_text = self.result_text.toPlainText()
        self.result_text.setPlainText(f"[Translated to {language}]\n\n{current_text}")

    def save_results(self):
        file_name, _ = QFileDialog.getSaveFileName(self, 'Save Results', '', 'Text Files (*.txt)')
        if file_name:
            with open(file_name, 'w') as file:
                file.write(self.result_text.toPlainText())
            QMessageBox.information(self, "Success", "Results saved successfully!")

    def generate_care_guide(self):
        plant_name = self.plant_name_input.text()
        if not plant_name:
            QMessageBox.warning(self, "Input Required", "Please enter a plant name.")
            return

        api_key = ''  # Your API key
        prompt = f"Generate a detailed care guide for {plant_name}, including watering needs, sunlight requirements, soil type, fertilization, and common issues."
        self.thread = GeminiAPIThread(None, api_key, prompt, model="gemini-1.5-flash-latest")
        self.thread.result_signal.connect(self.display_care_guide)
        self.thread.error_signal.connect(self.display_error)
        self.thread.start()

    def display_care_guide(self, result):
        if 'candidates' in result and result['candidates']:
            care_guide = result['candidates'][0]['content']['parts'][0]['text']
            self.care_guide_text.setPlainText(care_guide)
        else:
            self.care_guide_text.setPlainText("Failed to generate care guide. Please try again.")

    def detect_disease(self):
        if not hasattr(self, 'disease_image_path'):
            QMessageBox.warning(self, "Image Required", "Please upload an image first.")
            return

        api_key = ''  # Your API key
        prompt = "Analyze this plant image and identify any visible diseases or pests. Provide a detailed description of the issue, potential causes, and recommended treatments."
        self.thread = GeminiAPIThread(self.disease_image_path, api_key, prompt)
        self.thread.result_signal.connect(self.display_disease_result)
        self.thread.error_signal.connect(self.display_error)
        self.thread.start()

    def display_disease_result(self, result):
        if 'candidates' in result and result['candidates']:
            disease_info = result['candidates'][0]['content']['parts'][0]['text']
            self.disease_result_text.setPlainText(disease_info)
        else:
            self.disease_result_text.setPlainText("No disease information found. Try another image.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EnhancedPlantIdentifierApp()
    window.show()
    sys.exit(app.exec_())
