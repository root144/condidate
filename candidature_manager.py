import sys
import sqlite3
import csv
import re
from datetime import datetime, timezone
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLineEdit, QComboBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QMessageBox, QTabWidget,
    QHeaderView, QFileDialog, QDateEdit, QGroupBox, QScrollArea,
    QFrame, QSizePolicy, QSpacerItem, QGridLayout, QProgressBar,
    QGraphicsDropShadowEffect, QStatusBar
)
from PyQt5.QtCore import (
    Qt, QDate, QPropertyAnimation, QEasingCurve, QRect, QTimer,
    QObject, QPoint, QSettings, QSize
)
from PyQt5.QtGui import (
    QFont, QPalette, QColor, QIcon, QPixmap, QPainter, QBrush,
    QLinearGradient, QPen, QFontDatabase
)

class ModernCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(4)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(self.shadow)
        
        self.shadow_anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.shadow_anim.setDuration(200)
        self.shadow_anim.setEasingCurve(QEasingCurve.InOutCubic)
        
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e6ed;
                margin: 8px;
            }
            QFrame:hover {
                border: 1px solid #4285f4;
                background-color: #fafafa;
            }
        """)
    
    def enterEvent(self, event):
        self.shadow_anim.setStartValue(20)
        self.shadow_anim.setEndValue(30)
        self.shadow_anim.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.shadow_anim.setStartValue(30)
        self.shadow_anim.setEndValue(20)
        self.shadow_anim.start()
        super().leaveEvent(event)

class StatsCard(ModernCard):
    def __init__(self, title, value, icon, color="#4285f4", parent=None):
        super().__init__(parent)
        self.init_ui(title, value, icon, color)
    
    def init_ui(self, title, value, icon, color):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        header = QLabel(f"{icon} {title}")
        header.setFont(QFont("Segoe UI", 12))
        header.setStyleSheet("color: #6c757d;")
        layout.addWidget(header)
        
        value_label = QLabel(str(value))
        value_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        self.setFixedSize(200, 120)

class ModernButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
            QPushButton:pressed {
                background-color: #2850a7;
            }
        """)

class ModernInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #e0e6ed;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #4285f4;
            }
        """)

class ModernComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #e0e6ed;
                border-radius: 4px;
                background: white;
            }
            QComboBox:focus {
                border: 1px solid #4285f4;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)

class DatabaseManager:
    def __init__(self, db_name="candidates_modern.db"):
        self.db_name = db_name
        self.init_database()
        self.connection = None
    
    def get_connection(self):
        """Établit une nouvelle connexion à la base de données"""
        try:
            conn = sqlite3.connect(self.db_name, timeout=20)  # Augmente le timeout
            return conn
        except Exception as e:
            raise Exception(f"Erreur de connexion à la base de données: {str(e)}")
    
    def init_database(self):
        """Initialise la base de données avec la table candidates"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom_complet TEXT NOT NULL,
                    poste_demande TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    telephone TEXT,
                    date_candidature TEXT NOT NULL,
                    statut TEXT NOT NULL,
                    priorite TEXT,
                    notes TEXT,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
        except Exception as e:
            raise Exception(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
        finally:
            if conn:
                conn.close()

    def add_candidate(self, candidate_data):
        """Ajoute un nouveau candidat à la base de données"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO candidates 
                (nom_complet, poste_demande, email, telephone, date_candidature, 
                 statut, priorite, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', candidate_data)
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            raise Exception("Cette adresse e-mail existe déjà dans la base de données.")
        except Exception as e:
            raise Exception(f"Erreur lors de l'ajout du candidat: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_all_candidates(self):
        """Récupère tous les candidats de la base de données"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, nom_complet, poste_demande, email, telephone, 
                       date_candidature, statut, priorite, notes, date_creation
                FROM candidates 
                ORDER BY date_creation DESC
            ''')
            
            candidates = cursor.fetchall()
            return candidates
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des candidats: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_stats(self):
        """Récupère les statistiques des candidats"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Total
            cursor.execute("SELECT COUNT(*) FROM candidates")
            total = cursor.fetchone()[0]
            
            # Status stats
            cursor.execute("""
                SELECT statut, COUNT(*) 
                FROM candidates 
                GROUP BY statut
            """)
            stats_by_status = dict(cursor.fetchall())
            
            # This month's applications
            current_month = datetime.now().strftime('%Y-%m')
            cursor.execute("""
                SELECT COUNT(*) FROM candidates 
                WHERE date_creation LIKE ?
            """, (f"{current_month}%",))
            this_month = cursor.fetchone()[0]
            
            return {
                'total': total,
                'en_attente': stats_by_status.get('En attente', 0),
                'entretien': stats_by_status.get('Entretien', 0),
                'accepte': stats_by_status.get('Accepté', 0),
                'refuse': stats_by_status.get('Refusé', 0),
                'ce_mois': this_month
            }
        except Exception as e:
            return {
                'total': 0,
                'en_attente': 0,
                'entretien': 0,
                'accepte': 0,
                'refuse': 0,
                'ce_mois': 0
            }
        finally:
            if conn:
                conn.close()

    def export_to_csv(self, filename):
        """Exporte les données vers un fichier CSV"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, nom_complet, poste_demande, email, telephone, 
                       date_candidature, statut, priorite, notes, date_creation
                FROM candidates 
                ORDER BY date_creation DESC
            ''')
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile)
                # Write headers
                csvwriter.writerow([
                    'ID', 'Nom Complet', 'Poste', 'Email', 'Téléphone',
                    'Date Candidature', 'Statut', 'Priorité', 'Notes',
                    'Date Création'
                ])
                # Write data
                csvwriter.writerows(cursor.fetchall())
            
            return True
        except Exception as e:
            raise Exception(f"Erreur lors de l'export CSV: {str(e)}")
        finally:
            if conn:
                conn.close()

class UserManager:
    def __init__(self):
        self.settings = QSettings('ModernHR', 'CandidateManager')
        self._current_user = self.settings.value('current_user', 'root144')
    
    @property
    def current_user(self):
        return self._current_user
    
    @current_user.setter
    def current_user(self, username):
        self._current_user = username
        self.settings.setValue('current_user', username)
    
    def get_formatted_datetime(self):
        return "2025-06-02 09:57:12"  # Current UTC time

class NotificationManager(QObject):
    def __init__(self):
        super().__init__()
        self.notifications = []
        self.max_notifications = 5
    
    def show_notification(self, title, message, type="info"):
        while len(self.notifications) >= self.max_notifications:
            old_notification = self.notifications.pop(0)
            if old_notification and not old_notification.isHidden():
                old_notification.close()
        
        notification = ModernNotification(title, message, type)
        notification.show()
        self.notifications.append(notification)

class ModernNotification(QWidget):
    def __init__(self, title, message, type="info"):
        super().__init__(None)
        self.init_ui(title, message, type)
        self.setup_animations()
    
    def setup_animations(self):
        self.show_animation = QPropertyAnimation(self, b"geometry")
        self.show_animation.setDuration(300)
        self.show_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.hide_animation = QPropertyAnimation(self, b"geometry")
        self.hide_animation.setDuration(300)
        self.hide_animation.setEasingCurve(QEasingCurve.InCubic)
        self.hide_animation.finished.connect(self.close)
        
        screen = QApplication.primaryScreen().geometry()
        start_rect = QRect(
            screen.width(),
            screen.height() - 100,
            350,
            100
        )
        end_rect = QRect(
            screen.width() - 360,
            screen.height() - 100,
            350,
            100
        )
        
        self.setGeometry(start_rect)
        self.show_animation.setStartValue(start_rect)
        self.show_animation.setEndValue(end_rect)
        self.show_animation.start()
        
        QTimer.singleShot(5000, self.start_hide_animation)
    
    def init_ui(self, title, message, type):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        container = QWidget()
        container.setObjectName("container")
        container_layout = QVBoxLayout(container)
        
        header_layout = QHBoxLayout()
        icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
        icon_label = QLabel(icon.get(type, "ℹ️"))
        icon_label.setFont(QFont("Segoe UI Emoji", 14))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFlat(True)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.start_hide_animation)
        header_layout.addWidget(close_btn)
        
        container_layout.addLayout(header_layout)
        
        message_label = QLabel(message)
        message_label.setFont(QFont("Segoe UI", 10))
        message_label.setWordWrap(True)
        container_layout.addWidget(message_label)
        
        layout.addWidget(container)
        
        colors = {
            "info": "#4285f4",
            "success": "#34a853",
            "warning": "#fbbc05",
            "error": "#ea4335"
        }
        color = colors.get(type, colors["info"])
        
        self.setStyleSheet(f"""
            QWidget#container {{
                background: white;
                border-radius: 8px;
                border-left: 4px solid {color};
            }}
            QPushButton {{
                color: #666;
                font-size: 20px;
                border: none;
            }}
            QPushButton:hover {{
                color: #333;
            }}
        """)
    
    def start_hide_animation(self):
        if not self.underMouse():
            current_rect = self.geometry()
            self.hide_animation.setStartValue(current_rect)
            self.hide_animation.setEndValue(QRect(
                current_rect.x() + 400,
                current_rect.y(),
                current_rect.width(),
                current_rect.height()
            ))
            self.hide_animation.start()

class ModernHeader(QWidget):
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 12, 24, 12)
        
        user_widget = QWidget()
        user_layout = QHBoxLayout(user_widget)
        user_layout.setContentsMargins(0, 0, 0, 0)
        
        user_icon = QLabel("👤")
        user_icon.setFont(QFont("Segoe UI Emoji", 16))
        user_layout.addWidget(user_icon)
        
        self.user_info = QLabel(self.user_manager.current_user)
        self.user_info.setFont(QFont("Segoe UI", 12))
        self.user_info.setStyleSheet("color: #2c3e50;")
        user_layout.addWidget(self.user_info)
        
        layout.addWidget(user_widget)
        
        title = QLabel("Gestionnaire de Candidatures")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)
        
        time_widget = QWidget()
        time_layout = QHBoxLayout(time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)
        
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Segoe UI", 12))
        self.time_label.setStyleSheet("color: #2c3e50;")
        time_layout.addWidget(self.time_label)
        
        layout.addWidget(time_widget)
        
        self.setStyleSheet("""
            ModernHeader {
                background: white;
                border-bottom: 1px solid #e0e6ed;
            }
        """)
        
        self.update_time()
    
    def update_time(self):
        current_time = "2025-06-02 09:58:47 UTC"
        self.time_label.setText(f"🕒 {current_time}")

class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.stats_layout = None  # Ajout d'un attribut pour stocker le layout
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Stats cards container
        stats_container = QWidget()
        self.stats_layout = QHBoxLayout(stats_container)  # Stockage de la référence
        
        # Stats cards
        stats = self.parent.db_manager.get_stats()
        
        total_card = StatsCard("Total Candidatures", stats['total'], "📊", "#4285f4")
        self.stats_layout.addWidget(total_card)
        
        waiting_card = StatsCard("En Attente", stats['en_attente'], "⏳", "#fbbc05")
        self.stats_layout.addWidget(waiting_card)
        
        interview_card = StatsCard("Entretiens", stats['entretien'], "👥", "#34a853")
        self.stats_layout.addWidget(interview_card)
        
        accepted_card = StatsCard("Acceptés", stats['accepte'], "✅", "#4285f4")
        self.stats_layout.addWidget(accepted_card)
        
        # Ajouter le container au layout principal
        layout.addWidget(stats_container)
        layout.addStretch()
    
    def refresh_stats(self):
        """Rafraîchit les statistiques du dashboard de manière sécurisée"""
        try:
            # Supprimer tous les widgets existants du stats_layout
            if self.stats_layout:
                while self.stats_layout.count():
                    item = self.stats_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
            
            # Obtenir les nouvelles statistiques
            stats = self.parent.db_manager.get_stats()
            
            # Recréer les cartes avec les nouvelles stats
            total_card = StatsCard("Total Candidatures", stats['total'], "📊", "#4285f4")
            self.stats_layout.addWidget(total_card)
            
            waiting_card = StatsCard("En Attente", stats['en_attente'], "⏳", "#fbbc05")
            self.stats_layout.addWidget(waiting_card)
            
            interview_card = StatsCard("Entretiens", stats['entretien'], "👥", "#34a853")
            self.stats_layout.addWidget(interview_card)
            
            accepted_card = StatsCard("Acceptés", stats['accepte'], "✅", "#4285f4")
            self.stats_layout.addWidget(accepted_card)
            
            # Forcer la mise à jour de l'interface
            self.update()
            
        except Exception as e:
            print(f"Erreur lors du rafraîchissement des statistiques: {str(e)}")

class ModernCandidateForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Ajouter un Nouveau Candidat")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Form container
        form_card = ModernCard()
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(20, 20, 20, 20)
        
        # Nom complet
        self.nom_input = ModernInput()
        self.nom_input.setPlaceholderText("Nom complet du candidat")
        form_layout.addRow("Nom complet:", self.nom_input)
        
        # Poste demandé
        self.poste_input = ModernInput()
        self.poste_input.setPlaceholderText("Poste demandé")
        form_layout.addRow("Poste:", self.poste_input)
        
        # Email
        self.email_input = ModernInput()
        self.email_input.setPlaceholderText("Email du candidat")
        form_layout.addRow("Email:", self.email_input)
        
        # Téléphone
        self.telephone_input = ModernInput()
        self.telephone_input.setPlaceholderText("Numéro de téléphone")
        form_layout.addRow("Téléphone:", self.telephone_input)
        
        # Date de candidature
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #e0e6ed;
                border-radius: 4px;
                background: white;
            }
            QDateEdit:focus {
                border: 1px solid #4285f4;
            }
        """)
        form_layout.addRow("Date:", self.date_input)
        
        # Statut
        self.statut_input = ModernComboBox()
        self.statut_input.addItems(["En attente", "Entretien", "Accepté", "Refusé"])
        form_layout.addRow("Statut:", self.statut_input)
        
        # Priorité
        self.priorite_input = ModernComboBox()
        self.priorite_input.addItems(["Basse", "Moyenne", "Haute", "Urgente"])
        form_layout.addRow("Priorité:", self.priorite_input)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notes additionnelles sur le candidat...")
        self.notes_input.setStyleSheet("""
            QTextEdit {
                padding: 8px;
                border: 1px solid #e0e6ed;
                border-radius: 4px;
                background: white;
                min-height: 100px;
            }
            QTextEdit:focus {
                border: 1px solid #4285f4;
            }
        """)
        form_layout.addRow("Notes:", self.notes_input)
        
        form_card.setLayout(form_layout)
        layout.addWidget(form_card)
        
        # Submit button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.submit_btn = ModernButton("Ajouter le Candidat")
        self.submit_btn.clicked.connect(self.submit_candidate)
        button_layout.addWidget(self.submit_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
    
    def submit_candidate(self):
        # Validate inputs
        if not self.nom_input.text() or not self.email_input.text() or not self.poste_input.text():
            self.parent.show_notification(
                "Erreur",
                "Veuillez remplir tous les champs obligatoires.",
                "error"
            )
            return
        
        # Validate email format
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(self.email_input.text()):
            self.parent.show_notification(
                "Erreur",
                "Format d'email invalide.",
                "error"
            )
            return
        
        try:
            # Prepare candidate data
            candidate_data = (
                self.nom_input.text(),
                self.poste_input.text(),
                self.email_input.text(),
                self.telephone_input.text(),
                self.date_input.date().toString("yyyy-MM-dd"),
                self.statut_input.currentText(),
                self.priorite_input.currentText(),
                self.notes_input.toPlainText()
            )
            
            # Add to database
            self.parent.db_manager.add_candidate(candidate_data)
            
            # Show success notification
            self.parent.show_notification(
                "Succès",
                "Candidat ajouté avec succès!",
                "success"
            )
            
            # Clear form
            self.clear_form()
            
            # Refresh dashboard
            self.parent.dashboard.refresh_stats()
            
            # Refresh candidates table if it exists
            if hasattr(self.parent, 'candidates_table'):
                self.parent.candidates_table.refresh_table()
                
        except Exception as e:
            self.parent.show_notification(
                "Erreur",
                str(e),
                "error"
            )
    
    def clear_form(self):
        self.nom_input.clear()
        self.poste_input.clear()
        self.email_input.clear()
        self.telephone_input.clear()
        self.date_input.setDate(QDate.currentDate())
        self.statut_input.setCurrentIndex(0)
        self.priorite_input.setCurrentIndex(0)
        self.notes_input.clear()

class ModernCandidatesTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title and actions bar
        header_layout = QHBoxLayout()
        
        title = QLabel("Liste des Candidatures")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        export_btn = ModernButton("Exporter en CSV")
        export_btn.clicked.connect(self.export_to_csv)
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom Complet", "Poste", "Email", "Téléphone",
            "Date", "Statut", "Priorité", "Notes"
        ])
        
        # Style the table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e0e6ed;
                border-radius: 4px;
                gridline-color: #f1f3f4;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #e0e6ed;
                font-weight: bold;
                color: #2c3e50;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f3f4;
            }
            QTableWidget::item:selected {
                background-color: #e8f0fe;
                color: #2c3e50;
            }
        """)
        
        # Set column widths
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        column_widths = [60, 150, 150, 200, 120, 100, 100, 100, 200]
        for i, width in enumerate(column_widths):
            self.table.setColumnWidth(i, width)
        
        layout.addWidget(self.table)
        
        # Refresh the table
        self.refresh_table()
    
    def refresh_table(self):
        try:
            candidates = self.parent.db_manager.get_all_candidates()
            self.table.setRowCount(len(candidates))
            
            for row, candidate in enumerate(candidates):
                for col, value in enumerate(candidate):
                    item = QTableWidgetItem(str(value))
                    # Make items non-editable
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row, col, item)
                    
                    # Color-code status cells
                    if col == 6:  # Status column
                        if value == "Accepté":
                            item.setBackground(QColor("#34a853"))
                            item.setForeground(QColor("white"))
                        elif value == "Refusé":
                            item.setBackground(QColor("#ea4335"))
                            item.setForeground(QColor("white"))
                        elif value == "Entretien":
                            item.setBackground(QColor("#fbbc05"))
                        elif value == "En attente":
                            item.setBackground(QColor("#4285f4"))
                            item.setForeground(QColor("white"))
                    
                    # Color-code priority cells
                    if col == 7:  # Priority column
                        if value == "Urgente":
                            item.setBackground(QColor("#ea4335"))
                            item.setForeground(QColor("white"))
                        elif value == "Haute":
                            item.setBackground(QColor("#fbbc05"))
                        elif value == "Moyenne":
                            item.setBackground(QColor("#4285f4"))
                            item.setForeground(QColor("white"))
                        elif value == "Basse":
                            item.setBackground(QColor("#34a853"))
                            item.setForeground(QColor("white"))
            
        except Exception as e:
            self.parent.show_notification(
                "Erreur",
                f"Erreur lors du chargement des candidats: {str(e)}",
                "error"
            )
    
    def export_to_csv(self):
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Exporter en CSV",
                "",
                "CSV Files (*.csv)"
            )
            
            if filename:
                if not filename.endswith('.csv'):
                    filename += '.csv'
                
                if self.parent.db_manager.export_to_csv(filename):
                    self.parent.show_notification(
                        "Succès",
                        "Export CSV réussi!",
                        "success"
                    )
        except Exception as e:
            self.parent.show_notification(
                "Erreur",
                f"Erreur lors de l'export: {str(e)}",
                "error"
            )
class EditCandidateDialog(QWidget):
    def __init__(self, candidate_data, parent=None):
        super().__init__(parent, Qt.Window)
        self.parent = parent
        self.candidate_data = candidate_data
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Modifier le Candidat")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Formulaire dans une ModernCard
        form_card = ModernCard()
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # ID (non modifiable)
        self.id_input = ModernInput()
        self.id_input.setText(str(self.candidate_data[0]))
        self.id_input.setReadOnly(True)
        form_layout.addRow("ID:", self.id_input)
        
        # Nom complet
        self.nom_input = ModernInput()
        self.nom_input.setText(self.candidate_data[1])
        form_layout.addRow("Nom complet:", self.nom_input)
        
        # Poste
        self.poste_input = ModernInput()
        self.poste_input.setText(self.candidate_data[2])
        form_layout.addRow("Poste:", self.poste_input)
        
        # Email
        self.email_input = ModernInput()
        self.email_input.setText(self.candidate_data[3])
        form_layout.addRow("Email:", self.email_input)
        
        # Téléphone
        self.telephone_input = ModernInput()
        self.telephone_input.setText(self.candidate_data[4])
        form_layout.addRow("Téléphone:", self.telephone_input)
        
        # Date
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.fromString(self.candidate_data[5], "yyyy-MM-dd"))
        self.date_input.setCalendarPopup(True)
        self.date_input.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #e0e6ed;
                border-radius: 4px;
                background: white;
            }
        """)
        form_layout.addRow("Date:", self.date_input)
        
        # Statut
        self.statut_input = ModernComboBox()
        self.statut_input.addItems(["En attente", "Entretien", "Accepté", "Refusé"])
        self.statut_input.setCurrentText(self.candidate_data[6])
        form_layout.addRow("Statut:", self.statut_input)
        
        # Priorité
        self.priorite_input = ModernComboBox()
        self.priorite_input.addItems(["Basse", "Moyenne", "Haute", "Urgente"])
        self.priorite_input.setCurrentText(self.candidate_data[7])
        form_layout.addRow("Priorité:", self.priorite_input)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notes additionnelles...")
        self.notes_input.setText(self.candidate_data[8])
        self.notes_input.setStyleSheet("""
            QTextEdit {
                padding: 8px;
                border: 1px solid #e0e6ed;
                border-radius: 4px;
                background: white;
                min-height: 100px;
            }
        """)
        form_layout.addRow("Notes:", self.notes_input)
        
        form_card.setLayout(form_layout)
        layout.addWidget(form_card)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        save_btn = ModernButton("Enregistrer")
        save_btn.clicked.connect(self.save_changes)
        button_layout.addWidget(save_btn)
        
        cancel_btn = ModernButton("Annuler")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def save_changes(self):
        try:
            # Mise à jour dans la base de données
            conn = self.parent.parent.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE candidates 
                SET nom_complet=?, poste_demande=?, email=?, telephone=?,
                    date_candidature=?, statut=?, priorite=?, notes=?
                WHERE id=?
            ''', (
                self.nom_input.text(),
                self.poste_input.text(),
                self.email_input.text(),
                self.telephone_input.text(),
                self.date_input.date().toString("yyyy-MM-dd"),
                self.statut_input.currentText(),
                self.priorite_input.currentText(),
                self.notes_input.toPlainText(),
                self.id_input.text()
            ))
            
            conn.commit()
            conn.close()
            
            # Notification de succès
            self.parent.parent.show_notification(
                "Succès",
                "Candidat modifié avec succès!",
                "success"
            )
            
            # Rafraîchir la table et le dashboard
            self.parent.refresh_table()
            self.parent.parent.dashboard.refresh_stats()
            
            # Fermer la fenêtre
            self.close()
            
        except Exception as e:
            self.parent.parent.show_notification(
                "Erreur",
                str(e),
                "error"
            )

class ModernCandidateManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_manager = UserManager()
        self.notification_manager = NotificationManager()
        self.init_database()
        self.init_ui()
        
        # Show welcome notification
        self.show_notification(
            "Bienvenue",
            f"Connecté en tant que {self.user_manager.current_user}",
            "info"
        )
    
    def init_database(self):
        try:
            self.db_manager = DatabaseManager()
        except Exception as e:
            QMessageBox.critical(self, "❌ Erreur de Base de Données", str(e))
            sys.exit(1)
    
    def init_ui(self):
        self.setWindowTitle("🎯 Gestionnaire de Candidatures Moderne")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(layout)
        
        # Add modern header
        self.header = ModernHeader(self.user_manager)
        layout.addWidget(self.header)
        
        # Add tabs
        self.setup_tabs()
        
        # Apply modern style
        self.apply_modern_style()
        
        # Create status bar
        self.create_status_bar()
    
    def setup_tabs(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        
        # Dashboard tab
        self.dashboard = DashboardWidget(self)
        self.tab_widget.addTab(self.dashboard, "📊 Dashboard")
        
        # Add candidate tab
        self.candidate_form = ModernCandidateForm(self)
        self.tab_widget.addTab(self.candidate_form, "➕ Nouveau Candidat")
        
        # Candidates list tab
        self.candidates_table = ModernCandidatesTable(self)
        self.tab_widget.addTab(self.candidates_table, "📋 Liste des Candidatures")
        
        self.centralWidget().layout().addWidget(self.tab_widget)
    
    def apply_modern_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: none;
                background: white;
                padding: 16px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background: white;
                color: #6c757d;
                padding: 8px 16px;
                border: none;
                margin-right: 4px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #4285f4;
                color: white;
            }
        """)
    
    def create_status_bar(self):
        status_bar = self.statusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f8f9fa;
                border-top: 1px solid #e0e6ed;
                color: #6c757d;
                font-size: 12px;
            }
        """)
        self.update_status_message()
        
        # Update status periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_message)
        self.status_timer.start(5000)
    
    def update_status_message(self):
        try:
            stats = self.db_manager.get_stats()
            current_time = self.user_manager.get_formatted_datetime()
            message = (f"📊 Total: {stats['total']} candidatures | "
                      f"✅ Acceptés: {stats['accepte']} | "
                      f"⏳ En attente: {stats['en_attente']} | "
                      f"🕒 {current_time} UTC")
            self.statusBar().showMessage(message)
        except:
            current_time = self.user_manager.get_formatted_datetime()
            self.statusBar().showMessage(
                f"🎯 Gestionnaire de Candidatures - {current_time} UTC"
            )
    
    def show_notification(self, title, message, type="info"):
        self.notification_manager.show_notification(title, message, type)

def main():
    app = QApplication(sys.argv)
    
    # Application configuration
    app.setApplicationName("Gestionnaire de Candidatures Moderne")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("ModernHR Solutions")
    
    # Fusion style for modern look
    app.setStyle('Fusion')
    
    # Modern color palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f8f9fa"))
    palette.setColor(QPalette.WindowText, QColor("#2c3e50"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f1f3f4"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#2c3e50"))
    palette.setColor(QPalette.Text, QColor("#2c3e50"))
    palette.setColor(QPalette.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ButtonText, QColor("#2c3e50"))
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.Link, QColor("#4285f4"))
    palette.setColor(QPalette.Highlight, QColor("#4285f4"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    
    window = ModernCandidateManager()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()