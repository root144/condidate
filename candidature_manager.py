import sys
import sqlite3
import re
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLineEdit, QComboBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QMessageBox, QTabWidget,
    QHeaderView, QFileDialog, QDateEdit, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QColor

DB_NAME = "candidates_modern.db"

from PyQt5.QtWidgets import QStyledItemDelegate, QComboBox

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(self.items)
        return combo

    def setEditorData(self, editor, index):
        value = index.data()
        idx = editor.findText(value)
        if idx >= 0:
            editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText())
        
class DatabaseManager:
    def __init__(self):
        self.init_database()

    def connect(self):
        return sqlite3.connect(DB_NAME)

    def init_database(self):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute('''
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
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            
    # ... autres méthodes ...
           
    def search_candidates(self, filters):
        query = "SELECT * FROM candidates WHERE 1=1"
        params = []
        if filters.get("nom_complet"):
            query += " AND nom_complet LIKE ?"
            params.append(f"%{filters['nom_complet']}%")
        if filters.get("poste_demande"):
            query += " AND poste_demande LIKE ?"
            params.append(f"%{filters['poste_demande']}%")
        if filters.get("email"):
            query += " AND email LIKE ?"
            params.append(f"%{filters['email']}%")
        if filters.get("statut"):
            query += " AND statut = ?"
            params.append(filters["statut"])
        if filters.get("priorite"):
            query += " AND priorite = ?"
            params.append(filters["priorite"])
        with self.connect() as conn:
            c = conn.cursor()
            c.execute(query, params)
            return c.fetchall()

    def add_candidate(self, data):
        with self.connect() as conn:
            c = conn.cursor()
            try:
                c.execute('''
                    INSERT INTO candidates (
                        nom_complet, poste_demande, email, telephone, date_candidature,
                        statut, priorite, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', data)
            except sqlite3.IntegrityError:
                raise Exception("L'email existe déjà.")
    def get_all_candidates(self):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM candidates ORDER BY id DESC")
            return c.fetchall()
    def update_statut(self, candidate_id, new_statut):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("UPDATE candidates SET statut = ? WHERE id = ?", (new_statut, candidate_id))
            conn.commit()

    def update_priorite(self, candidate_id, new_priorite):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("UPDATE candidates SET priorite = ? WHERE id = ?", (new_priorite, candidate_id))
            conn.commit()
    def get_stats(self):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM candidates")
            total = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM candidates WHERE statut='En attente'")
            attente = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM candidates WHERE statut='Entretien'")
            entretien = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM candidates WHERE statut='Accepté'")
            accepte = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM candidates WHERE statut='Refusé'")
            refuse = c.fetchone()[0]
        return dict(total=total, en_attente=attente, entretien=entretien, accepte=accepte, refuse=refuse)

class ModernInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QLineEdit {padding:8px; font-size:14px;}")

class ModernComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QComboBox {padding:8px; font-size:14px;}")

class ModernButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background:#4285f4; color:white; border:none; border-radius:6px;
                font-weight:bold; font-size:14px; padding:10px 20px;
            }
            QPushButton:disabled {background:#ccc; color:#666;}
        """)

class StatCard(QFrame):
    ICONS = {
        "Total": "📊",
        "En Attente": "⏳",
        "Entretien": "🗣️",
        "Accepté": "✅",
        "Refusé": "❌"
    }
    COLORS = {
        "Total": "#4285f4",
        "En Attente": "#fbbc05",
        "Entretien": "#ff6b35",
        "Accepté": "#34a853",
        "Refusé": "#ea4335"
    }
    def __init__(self, label, value, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setStyleSheet("""
            QFrame#statCard {
                background: #fff;
                border-radius: 18px;
                border: 1.5px solid #e0e0e0;
                min-width: 170px;
                min-height: 170px;
                margin: 12px;
            }
        """)
        # Add shadow effect (supported by PyQt)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)
        l = QVBoxLayout(self)
        l.setContentsMargins(22, 18, 22, 18)
        l.setSpacing(8)
        icon = QLabel(self.ICONS[label])
        icon.setAlignment(Qt.AlignHCenter)
        icon.setFont(QFont("Segoe UI Emoji", 32))
        l.addWidget(icon)
        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignHCenter)
        lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl.setStyleSheet("color: #3c4043;")
        l.addWidget(lbl)
        val = QLabel(str(value))
        val.setAlignment(Qt.AlignHCenter)
        val.setFont(QFont("Segoe UI", 36, QFont.Bold))
        val.setStyleSheet(f"color: {self.COLORS[label]}; margin-top:6px;")
        l.addWidget(val)
        l.addStretch()
        self.value_label = val
    def set_value(self, value):
        self.value_label.setText(str(value))

class DashboardWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.cards = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        row = QHBoxLayout()
        row.setSpacing(20)
        for label in ["Total", "En Attente", "Entretien", "Accepté", "Refusé"]:
            card = StatCard(label, 0)
            self.cards[label] = card
            row.addWidget(card)
        layout.addLayout(row)
        layout.addStretch()
        self.refresh_stats()
    def refresh_stats(self):
        stats = self.db.get_stats()
        self.cards["Total"].set_value(stats['total'])
        self.cards["En Attente"].set_value(stats['en_attente'])
        self.cards["Entretien"].set_value(stats['entretien'])
        self.cards["Accepté"].set_value(stats['accepte'])
        self.cards["Refusé"].set_value(stats['refuse'])

class ModernCandidateForm(QWidget):
    def __init__(self, db, dashboard, table, parent=None):
        super().__init__(parent)
        self.db = db
        self.dashboard = dashboard
        self.table = table
        l = QVBoxLayout(self)
        form = QFormLayout()
        self.nom_input = ModernInput()
        self.poste_input = ModernInput()
        self.email_input = ModernInput()
        self.telephone_input = ModernInput()
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.statut_input = ModernComboBox()
        self.statut_input.addItems(["En attente", "Entretien", "Accepté", "Refusé"])
        self.priorite_input = ModernComboBox()
        self.priorite_input.addItems(["Basse", "Moyenne", "Haute", "Urgente"])
        self.notes_input = QTextEdit()
        form.addRow("Nom complet:", self.nom_input)
        form.addRow("Poste:", self.poste_input)
        form.addRow("Email:", self.email_input)
        form.addRow("Téléphone:", self.telephone_input)
        form.addRow("Date:", self.date_input)
        form.addRow("Statut:", self.statut_input)
        form.addRow("Priorité:", self.priorite_input)
        form.addRow("Notes:", self.notes_input)
        l.addLayout(form)
        self.btn = ModernButton("Ajouter le Candidat")
        self.btn.clicked.connect(self.add_candidate)
        l.addWidget(self.btn)
    def add_candidate(self):
        data = (
            self.nom_input.text(),
            self.poste_input.text(),
            self.email_input.text(),
            self.telephone_input.text(),
            self.date_input.date().toString("yyyy-MM-dd"),
            self.statut_input.currentText(),
            self.priorite_input.currentText(),
            self.notes_input.toPlainText()
        )
        if not all(data[:3]):
            QMessageBox.warning(self, "Champs obligatoires", "Remplissez nom, poste et email.")
            return
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', data[2]):
            QMessageBox.warning(self, "Email", "Email invalide.")
            return
        try:
            self.db.add_candidate(data)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))
            return
        self.dashboard.refresh_stats()
        self.table.refresh_table()
        self.nom_input.clear()
        self.poste_input.clear()
        self.email_input.clear()
        self.telephone_input.clear()
        self.notes_input.clear()

class ModernCandidatesTable(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        l = QVBoxLayout(self)

        # --- Ligne de filtres ---
        filters_layout = QHBoxLayout()
        self.filter_nom = QLineEdit()
        self.filter_nom.setPlaceholderText("Nom")
        filters_layout.addWidget(self.filter_nom)

        self.filter_poste = QLineEdit()
        self.filter_poste.setPlaceholderText("Poste")
        filters_layout.addWidget(self.filter_poste)

        self.filter_email = QLineEdit()
        self.filter_email.setPlaceholderText("Email")
        filters_layout.addWidget(self.filter_email)

        self.filter_statut = QComboBox()
        self.filter_statut.addItem("Tous")
        self.filter_statut.addItems(["En attente", "Entretien", "Accepté", "Refusé"])
        filters_layout.addWidget(self.filter_statut)

        self.filter_priorite = QComboBox()
        self.filter_priorite.addItem("Toutes")
        self.filter_priorite.addItems(["Basse", "Moyenne", "Haute", "Urgente"])
        filters_layout.addWidget(self.filter_priorite)

        self.search_btn = QPushButton("Rechercher")
        self.search_btn.clicked.connect(self.apply_filters)
        filters_layout.addWidget(self.search_btn)

        self.reset_btn = QPushButton("Réinitialiser")
        self.reset_btn.clicked.connect(self.reset_filters)
        filters_layout.addWidget(self.reset_btn)

        l.addLayout(filters_layout)

        # --- Tableau ---
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom Complet", "Poste", "Email", "Téléphone",
            "Date", "Statut", "Priorité", "Notes", "Date Création"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        l.addWidget(self.table)

        self.refresh_table()
        
    def on_item_changed(self, item):
        row = item.row()
        col = item.column()
        if col in (6, 7):  # 6 = Statut, 7 = Priorité
            # Récupérer l'ID du candidat (colonne 0)
            candidate_id = self.table.item(row, 0).text()
            new_value = item.text()
            if col == 6:
                # Mise à jour du statut
                self.db.update_statut(candidate_id, new_value)
            elif col == 7:
                # Mise à jour de la priorité
                self.db.update_priorite(candidate_id, new_value)
                
    def get_filters(self):
        # Retourne un dictionnaire des filtres actifs
        return {
            "nom_complet": self.filter_nom.text(),
            "poste_demande": self.filter_poste.text(),
            "email": self.filter_email.text(),
            "statut": self.filter_statut.currentText() if self.filter_statut.currentText() != "Tous" else "",
            "priorite": self.filter_priorite.currentText() if self.filter_priorite.currentText() != "Toutes" else "",
        }

    def apply_filters(self):
        filters = self.get_filters()
        self.refresh_table(filters)

    def reset_filters(self):
        self.filter_nom.clear()
        self.filter_poste.clear()
        self.filter_email.clear()
        self.filter_statut.setCurrentIndex(0)
        self.filter_priorite.setCurrentIndex(0)
        self.refresh_table()

    def refresh_table(self, filters=None):
        if filters:
            candidates = self.db.search_candidates(filters)
        else:
            candidates = self.db.get_all_candidates()
        self.table.setRowCount(len(candidates))
        for row, cand in enumerate(candidates):
            for col, val in enumerate(cand):
                item = QTableWidgetItem(str(val))
                self.table.setItem(row, col, item)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestionnaire de Candidatures Moderne")
        self.setGeometry(100, 100, 1200, 700)
        self.db = DatabaseManager()
        self.tab = QTabWidget()
        self.dashboard = DashboardWidget(self.db)
        self.candidates_table = ModernCandidatesTable(self.db)
        self.candidate_form = ModernCandidateForm(self.db, self.dashboard, self.candidates_table)
        self.tab.addTab(self.dashboard, "Dashboard")
        self.tab.addTab(self.candidate_form, "Ajouter Candidat")
        self.tab.addTab(self.candidates_table, "Candidatures")
        self.setCentralWidget(self.tab)
        self.status = self.statusBar()
        self.update_status()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(10000)
    def update_status(self):
        stats = self.db.get_stats()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status.showMessage(
            f"Candidats: {stats['total']} | Acceptés: {stats['accepte']} | En attente: {stats['en_attente']} | {now}"
        )

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
