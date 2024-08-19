import sys
import requests
import base64
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QTextEdit, 
    QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QProgressBar, QComboBox,
    QTabWidget, QLineEdit, QGridLayout, QSpinBox, QCheckBox, QCalendarWidget,
    QListWidget, QDialog, QDialogButtonBox
)
from PyQt5.QtGui import QPixmap, QIcon, QFont, QTextCharFormat, QColor, QPainter
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate, QTimer
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from datetime import datetime, timedelta

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
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": self.prompt}
                        ]
                    }
                ]
            }
            
            if self.image_path:
                with open(self.image_path, 'rb') as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
                payload["contents"][0]["parts"].append({"inline_data": {"mime_type": "image/jpeg", "data": image_data}})

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

class PlantCareApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Comprehensive Plant Care Application')
        self.setGeometry(100, 100, 1300, 800)
        self.setWindowIcon(QIcon('plant_icon.png'))
        self.load_stylesheet()

        self.plant_database = {}  # Initialize plant_database
        self.load_plant_database()  # Load plant database before UI setup

        self.init_ui()

    def load_stylesheet(self):
        style = """
        QMainWindow, QTabWidget::pane {
            background-color: #E8F5E9;
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
            background-color: #C8E6C9;
            border: 1px solid #A5D6A7;
            border-bottom-color: #C8E6C9;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            min-width: 8ex;
            padding: 2px;
        }
        QTabBar::tab:selected, QTabBar::tab:hover {
            background-color: #4CAF50;
            color: white;
        }
        QTextEdit, QListWidget {
            background-color: #FFFFFF;
            border: 1px solid #A5D6A7;
            border-radius: 5px;
        }
        QProgressBar {
            border: 2px solid #4CAF50;
            border-radius: 5px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
        }
        """
        self.setStyleSheet(style)

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_identifier_tab(), "Plant Identifier")
        self.tab_widget.addTab(self.create_care_guide_tab(), "Care Guide")
        self.tab_widget.addTab(self.create_disease_detector_tab(), "Disease Detector")
        self.tab_widget.addTab(self.create_plant_tracker_tab(), "Plant Tracker")
        self.tab_widget.addTab(self.create_watering_schedule_tab(), "Watering Schedule")
        self.tab_widget.addTab(self.create_growth_tracker_tab(), "Growth Tracker")

        main_layout.addWidget(self.tab_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def create_identifier_tab(self):
        tab = QWidget()
        layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.image_label = QLabel('Upload an image of a plant')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #4CAF50; border-radius: 5px; padding: 10px;")
        left_layout.addWidget(self.image_label)

        upload_button = QPushButton('Upload Image')
        upload_button.clicked.connect(self.upload_image)
        left_layout.addWidget(upload_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

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

        add_to_tracker_button = QPushButton('Add to Plant Tracker')
        add_to_tracker_button.clicked.connect(self.add_to_plant_tracker)
        right_layout.addWidget(add_to_tracker_button)

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

        save_care_guide_button = QPushButton("Save Care Guide")
        save_care_guide_button.clicked.connect(self.save_care_guide)
        layout.addWidget(save_care_guide_button)

        tab.setLayout(layout)
        return tab

    def create_disease_detector_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        upload_layout = QHBoxLayout()
        self.disease_image_label = QLabel('Upload an image of the plant')
        self.disease_image_label.setAlignment(Qt.AlignCenter)
        self.disease_image_label.setStyleSheet("border: 2px dashed #4CAF50; border-radius: 5px; padding: 10px;")
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

        save_disease_info_button = QPushButton("Save Disease Information")
        save_disease_info_button.clicked.connect(self.save_disease_info)
        layout.addWidget(save_disease_info_button)

        tab.setLayout(layout)
        return tab

    def create_plant_tracker_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.plant_list = QListWidget()
        self.plant_list.itemClicked.connect(self.show_plant_details)
        layout.addWidget(self.plant_list)

        button_layout = QHBoxLayout()
        add_plant_button = QPushButton("Add Plant")
        add_plant_button.clicked.connect(self.add_plant_dialog)
        button_layout.addWidget(add_plant_button)

        remove_plant_button = QPushButton("Remove Plant")
        remove_plant_button.clicked.connect(self.remove_plant)
        button_layout.addWidget(remove_plant_button)

        layout.addLayout(button_layout)

        self.plant_details_text = QTextEdit()
        self.plant_details_text.setReadOnly(True)
        layout.addWidget(self.plant_details_text)

        tab.setLayout(layout)
        return tab

    def create_watering_schedule_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.update_watering_info)
        layout.addWidget(self.calendar)

        self.watering_info = QTextEdit()
        self.watering_info.setReadOnly(True)
        layout.addWidget(self.watering_info)

        button_layout = QHBoxLayout()
        add_watering_event = QPushButton("Add Watering Event")
        add_watering_event.clicked.connect(self.add_watering_event)
        button_layout.addWidget(add_watering_event)

        generate_schedule = QPushButton("Generate Watering Schedule")
        generate_schedule.clicked.connect(self.generate_watering_schedule)
        button_layout.addWidget(generate_schedule)

        layout.addLayout(button_layout)

        tab.setLayout(layout)
        return tab

    def create_growth_tracker_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        chart_layout = QHBoxLayout()
        self.growth_chart = QChart()
        self.growth_chart.setTitle("Plant Growth Tracker")
        self.chart_view = QChartView(self.growth_chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        chart_layout.addWidget(self.chart_view)

        layout.addLayout(chart_layout)

        input_layout = QHBoxLayout()
        self.plant_select_growth = QComboBox()
        self.plant_select_growth.addItems(self.plant_database.keys())
        input_layout.addWidget(self.plant_select_growth)

        self.growth_value = QSpinBox()
        self.growth_value.setRange(0, 1000)
        self.growth_value.setSuffix(" cm")
        input_layout.addWidget(self.growth_value)

        add_growth_data = QPushButton("Add Growth Data")
        add_growth_data.clicked.connect(self.add_growth_data)
        input_layout.addWidget(add_growth_data)

        layout.addLayout(input_layout)

        tab.setLayout(layout)
        return tab

    def upload_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open Image File', '', 'Images (*.png *.jpg *.jpeg)')
        if file_name:
            pixmap = QPixmap(file_name)
            scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.identify_plant(file_name)

    def identify_plant(self, image_path):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        api_key = 'AIzaSyB9SHxq8lN2wn-YNDL2urjbZycOqK8YnmI'  # Replace with your actual API key
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
        current_text = self.result_text.toPlainText()
        language = self.language_combo.currentText()
        
        api_key = 'AIzaSyB9SHxq8lN2wn-YNDL2urjbZycOqK8YnmI'  # Replace with your actual API key
        prompt = f"Translate the following text to {language}:\n\n{current_text}"
        
        self.thread = GeminiAPIThread(None, api_key, prompt, model="gemini-1.5-flash-latest")
        self.thread.result_signal.connect(self.display_translated_result)
        self.thread.error_signal.connect(self.display_error)
        self.thread.start()

    def display_translated_result(self, result):
        if 'candidates' in result and result['candidates']:
            translated_text = result['candidates'][0]['content']['parts'][0]['text']
            self.result_text.setPlainText(translated_text)
        else:
            QMessageBox.warning(self, "Translation Error", "Failed to translate the text. Please try again.")

    def save_results(self):
        file_name, _ = QFileDialog.getSaveFileName(self, 'Save Results', '', 'Text Files (*.txt)')
        if file_name:
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(self.result_text.toPlainText())
            QMessageBox.information(self, "Success", "Results saved successfully!")

    def add_to_plant_tracker(self):
        plant_info = self.result_text.toPlainText()
        if plant_info:
            plant_name, ok = QInputDialog.getText(self, "Add to Plant Tracker", "Enter a name for this plant:")
            if ok and plant_name:
                self.plant_database[plant_name] = {"info": plant_info, "watering_schedule": [], "growth_data": []}
                self.update_plant_tracker_ui()
                self.save_plant_database()

    def generate_care_guide(self):
        plant_name = self.plant_name_input.text()
        if not plant_name:
            QMessageBox.warning(self, "Input Required", "Please enter a plant name.")
            return

        api_key = 'Your-API-Key-Here'  # Replace with your actual API key
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

    def save_care_guide(self):
        file_name, _ = QFileDialog.getSaveFileName(self, 'Save Care Guide', '', 'Text Files (*.txt)')
        if file_name:
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(self.care_guide_text.toPlainText())
            QMessageBox.information(self, "Success", "Care guide saved successfully!")

    def upload_disease_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open Image File', '', 'Images (*.png *.jpg *.jpeg)')
        if file_name:
            pixmap = QPixmap(file_name)
            scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.disease_image_label.setPixmap(scaled_pixmap)
            self.disease_image_path = file_name

    def detect_disease(self):
        if not hasattr(self, 'disease_image_path'):
            QMessageBox.warning(self, "Image Required", "Please upload an image first.")
            return

        api_key = 'Your-API-Key-Here'  # Replace with your actual API key
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

    def save_disease_info(self):
        file_name, _ = QFileDialog.getSaveFileName(self, 'Save Disease Information', '', 'Text Files (*.txt)')
        if file_name:
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(self.disease_result_text.toPlainText())
            QMessageBox.information(self, "Success", "Disease information saved successfully!")

    def update_plant_tracker_ui(self):
        self.plant_list.clear()
        self.plant_list.addItems(self.plant_database.keys())
        self.plant_select_growth.clear()
        self.plant_select_growth.addItems(self.plant_database.keys())

    def show_plant_details(self, item):
        plant_name = item.text()
        plant_info = self.plant_database[plant_name]['info']
        self.plant_details_text.setPlainText(plant_info)

    def add_plant_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Plant")
        layout = QVBoxLayout()

        name_input = QLineEdit()
        layout.addWidget(QLabel("Plant Name:"))
        layout.addWidget(name_input)

        info_input = QTextEdit()
        layout.addWidget(QLabel("Plant Information:"))
        layout.addWidget(info_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec_():
            plant_name = name_input.text()
            plant_info = info_input.toPlainText()
            if plant_name and plant_info:
                self.plant_database[plant_name] = {"info": plant_info, "watering_schedule": [], "growth_data": []}
                self.update_plant_tracker_ui()
                self.save_plant_database()

    def remove_plant(self):
        current_item = self.plant_list.currentItem()
        if current_item:
            plant_name = current_item.text()
            reply = QMessageBox.question(self, 'Remove Plant', f"Are you sure you want to remove {plant_name}?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self.plant_database[plant_name]
                self.update_plant_tracker_ui()
                self.save_plant_database()

    def update_watering_info(self):
        selected_date = self.calendar.selectedDate()
        watering_info = "Watering schedule for selected date:\n\n"
        for plant, data in self.plant_database.items():
            if any(event['date'] == selected_date.toString(Qt.ISODate) for event in data['watering_schedule']):
                watering_info += f"{plant}: Water today\n"
        self.watering_info.setPlainText(watering_info)

    def add_watering_event(self):
        plant_name, ok = QInputDialog.getItem(self, "Select Plant", "Choose a plant:", self.plant_database.keys(), 0, False)
        if ok and plant_name:
            selected_date = self.calendar.selectedDate()
            self.plant_database[plant_name]['watering_schedule'].append({
                'date': selected_date.toString(Qt.ISODate),
                'watered': True
            })
            self.update_watering_info()
            self.save_plant_database()

    def generate_watering_schedule(self):
        for plant, data in self.plant_database.items():
            # This is a simple schedule generator. You might want to make this more sophisticated.
            today = QDate.currentDate()
            for i in range(30):  # Generate schedule for next 30 days
                if i % 3 == 0:  # Water every 3 days
                    data['watering_schedule'].append({
                        'date': today.addDays(i).toString(Qt.ISODate),
                        'watered': False
                    })
        self.update_watering_info()
        self.save_plant_database()

    def add_growth_data(self):
        plant_name = self.plant_select_growth.currentText()
        growth_value = self.growth_value.value()
        if plant_name and growth_value > 0:
            self.plant_database[plant_name]['growth_data'].append({
                'date': QDate.currentDate().toString(Qt.ISODate),
                'height': growth_value
            })
            self.update_growth_chart(plant_name)
            self.save_plant_database()

    def update_growth_chart(self, plant_name):
        self.growth_chart.removeAllSeries()
        series = QLineSeries()
        
        for data_point in self.plant_database[plant_name]['growth_data']:
            date = QDate.fromString(data_point['date'], Qt.ISODate)
            series.append(date.toJulianDay(), data_point['height'])

        self.growth_chart.addSeries(series)
        self.growth_chart.createDefaultAxes()
        self.growth_chart.axes(Qt.Horizontal)[0].setFormat("dd/MM/yyyy")
        self.growth_chart.setTitle(f"Growth Chart for {plant_name}")

    def load_plant_database(self):
        if os.path.exists('plant_database.json'):
            with open('plant_database.json', 'r') as file:
                self.plant_database = json.load(file)
            self.update_plant_tracker_ui()

    def save_plant_database(self):
        with open('plant_database.json', 'w') as file:
            json.dump(self.plant_database, file)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlantCareApp()
    window.show()
    sys.exit(app.exec_())

