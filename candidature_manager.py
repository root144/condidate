import sys
import sqlite3
import re
import os
import shutil
from dashboard_widget import DashboardWidget
import subprocess
from datetime import datetime
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLineEdit, QComboBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QMessageBox, QTabWidget,
    QHeaderView, QFileDialog, QDateEdit, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QColor, QPixmap

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

DB_NAME = "candidates_modern.db"
ATTACH_DIR = "attachments"
PHOTO_DIR = "photos"
if not os.path.exists(ATTACH_DIR):
    os.makedirs(ATTACH_DIR)
if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)

THEME_DARK = """
QWidget { 
    background: #232629; 
    color: #e6e6e6; 
}
QMainWindow, QFrame, QTabWidget::pane {
    background: #232629;
}
QTabBar::tab:selected { 
    background: #31363b; 
    color: #e6e6e6;
}
QTabBar::tab { 
    background: #232629; 
    color: #e6e6e6; 
    padding: 8px; 
}
QLineEdit, QComboBox, QTextEdit, QDateEdit {
    background: #292d31; 
    color: #e6e6e6; 
    border: 1px solid #444; 
    border-radius: 6px;
    selection-background-color: #4285f4;
    selection-color: #fff;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {
    border: 1.5px solid #4285f4;
}
QTableWidget {
    background: #232629; 
    color: #e6e6e6; 
    gridline-color: #393c3f;
    alternate-background-color: #222428;
}
QHeaderView::section {
    background: #292d31;
    color: #e6e6e6;
    padding: 5px;
    border: 1px solid #393c3f;
}
QTableCornerButton::section {
    background: #292d31;
    border: 1px solid #393c3f;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background: #232629;
    border: none;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #444;
    border-radius: 6px;
}
QScrollBar::add-line, QScrollBar::sub-line {
    background: none;
    border: none;
}
QPushButton {
    background: #393cfc;
    color: #fff;
    border-radius: 6px;
    font-weight: bold;
    font-size: 10px;
    padding: 6px 18px;
    border: none;
}
QPushButton:hover {
    background: #5c5cff;
}
QPushButton:pressed {
    background: #232669;
}
QPushButton:disabled {
    background: #444;
    color: #888;
}
QLabel, QCheckBox {
    color: #e6e6e6;
}
QStatusBar {
    background: #232629;
    color: #aaa;
    border-top: 1px solid #393c3f;
}
QFrame#statCard {
    background: #292d31;
    border: 1.5px solid #393c3f;
}
QMenuBar, QMenu {
    background: #292d31;
    color: #e6e6e6;
}
QToolTip {
    background: #222428; 
    color: #e6e6e6; 
    border: 1px solid #393c3f;
}
"""

THEME_LIGHT = ""

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
                    cv_path TEXT,
                    attachments TEXT,
                    photo_path TEXT,
                    source TEXT,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Ajout des colonnes si besoin
            for col in ["cv_path", "attachments", "photo_path", "source"]:
                try:
                    c.execute(f"ALTER TABLE candidates ADD COLUMN {col} TEXT")
                except sqlite3.OperationalError:
                    pass
            conn.commit()

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
        if filters.get("source"):
            query += " AND source = ?"
            params.append(filters["source"])
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
                        statut, priorite, notes, cv_path, attachments, photo_path, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', data)
                conn.commit()
            except sqlite3.IntegrityError:
                raise Exception("L'email existe déjà.")

    def get_all_candidates(self):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM candidates ORDER BY id DESC")
            return c.fetchall()

    def get_candidate_by_id(self, candidate_id):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,))
            return c.fetchone()

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

    def delete_candidate(self, candidate_id):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
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

class DropArea(QLabel):
    def __init__(self, parent=None):
        super().__init__("Déposez vos fichiers ici", parent)
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 2px dashed #bbb; padding: 20px;")
        self.dropped_files = []

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                dest = os.path.join(ATTACH_DIR, os.path.basename(path))
                if not os.path.exists(dest):
                    shutil.copy(path, dest)
                self.dropped_files.append(dest)
        self.setText("\n".join(os.path.basename(f) for f in self.dropped_files))

    def clear_files(self):
        self.dropped_files = []
        self.setText("Déposez vos fichiers ici")

class ModernCandidateForm(QWidget):
    SOURCES = ["LinkedIn", "Email", "Indeed", "Site Web", "Recommandation", "Autre"]

    def __init__(self, db, dashboard, table, parent=None):
        super().__init__(parent)
        self.db = db
        self.dashboard = dashboard
        self.table = table
        l = QVBoxLayout(self)
        form = QFormLayout()
        self.nom_input = QLineEdit()
        self.poste_input = QLineEdit()
        self.email_input = QLineEdit()
        self.telephone_input = QLineEdit()
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.statut_input = QComboBox()
        self.statut_input.addItems(["En attente", "Entretien", "Accepté", "Refusé"])
        self.priorite_input = QComboBox()
        self.priorite_input.addItems(["Basse", "Moyenne", "Haute", "Urgente"])
        self.notes_input = QTextEdit()
        self.photo_path = None
        self.photo_label = QLabel("Aucune photo")
        self.photo_label.setFixedSize(80, 80)
        self.photo_label.setStyleSheet("border:1px solid #ccc;")
        self.photo_btn = QPushButton("Sélectionner une photo")
        self.photo_btn.clicked.connect(self.select_photo)
        self.cv_path = None
        self.cv_btn = QPushButton("Joindre un CV (PDF)")
        self.cv_btn.clicked.connect(self.select_cv)
        self.attach_area = DropArea()
        self.attach_btn = QPushButton("Ajouter pièces jointes (dialog)")
        self.attach_btn.clicked.connect(self.select_attachments)
        self.source_input = QComboBox()
        self.source_input.addItems(self.SOURCES)
        self.source_input.setEditable(True)

        form.addRow("Nom complet:", self.nom_input)
        form.addRow("Poste:", self.poste_input)
        form.addRow("Email:", self.email_input)
        form.addRow("Téléphone:", self.telephone_input)
        form.addRow("Date:", self.date_input)
        form.addRow("Statut:", self.statut_input)
        form.addRow("Priorité:", self.priorite_input)
        form.addRow("Source:", self.source_input)
        form.addRow("Notes:", self.notes_input)
        form.addRow("Photo:", self.photo_btn)
        form.addRow("", self.photo_label)
        form.addRow("CV :", self.cv_btn)
        form.addRow("Pièces jointes (Drag & Drop):", self.attach_area)
        form.addRow("", self.attach_btn)

        l.addLayout(form)
        self.btn = QPushButton("Ajouter le Candidat")
        self.btn.clicked.connect(self.add_candidate)
        l.addWidget(self.btn)
        self.setLayout(l)

    def select_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Sélectionner la photo", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            dest = os.path.join(PHOTO_DIR, os.path.basename(path))
            if not os.path.exists(dest):
                shutil.copy(path, dest)
            self.photo_path = dest
            pix = QPixmap(dest)
            self.photo_label.setPixmap(pix.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.photo_label.setText("")

    def select_cv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Sélectionner le CV", "", "PDF Files (*.pdf)")
        if path:
            dest = os.path.join(ATTACH_DIR, os.path.basename(path))
            if not os.path.exists(dest):
                shutil.copy(path, dest)
            self.cv_path = dest
            self.cv_btn.setText(f"CV: {os.path.basename(path)}")

    def select_attachments(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Sélectionner les pièces jointes", "", "Fichiers (*.pdf *.jpg *.png *.jpeg *.doc *.docx *.xls *.xlsx)")
        if files:
            for path in files:
                dest = os.path.join(ATTACH_DIR, os.path.basename(path))
                if not os.path.exists(dest):
                    shutil.copy(path, dest)
                self.attach_area.dropped_files.append(dest)
            self.attach_area.setText("\n".join(os.path.basename(f) for f in self.attach_area.dropped_files))

    def add_candidate(self):
        data = (
            self.nom_input.text(),
            self.poste_input.text(),
            self.email_input.text(),
            self.telephone_input.text(),
            self.date_input.date().toString("yyyy-MM-dd"),
            self.statut_input.currentText(),
            self.priorite_input.currentText(),
            self.notes_input.toPlainText(),
            self.cv_path,
            ";".join(self.attach_area.dropped_files) if self.attach_area.dropped_files else None,
            self.photo_path,
            self.source_input.currentText()
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
        self.cv_path = None
        self.cv_btn.setText("Joindre un CV (PDF)")
        self.attach_area.clear_files()
        self.photo_path = None
        self.photo_label.clear()
        self.photo_label.setText("Aucune photo")

class ModernCandidatesTable(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        l = QVBoxLayout(self)
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
        self.filter_source = QComboBox()
        self.filter_source.addItem("Toutes")
        self.filter_source.addItems(ModernCandidateForm.SOURCES)
        filters_layout.addWidget(self.filter_source)

        self.search_btn = QPushButton("Rechercher")
        self.search_btn.clicked.connect(self.apply_filters)
        filters_layout.addWidget(self.search_btn)
        self.reset_btn = QPushButton("Réinitialiser")
        self.reset_btn.clicked.connect(self.reset_filters)
        filters_layout.addWidget(self.reset_btn)
        self.export_btn = QPushButton("Exporter Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        filters_layout.addWidget(self.export_btn)
        self.import_btn = QPushButton("Importer Excel")
        self.import_btn.clicked.connect(self.import_from_excel)
        filters_layout.addWidget(self.import_btn)

        l.addLayout(filters_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(15)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom", "Poste", "Email", "Téléphone",
            "Date", "Statut", "Priorité", "Source", "Notes", "Photo",
            "CV", "Pièces jointes", "Date Création", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 40)  # Réduit la colonne ID à 50 pixels (tu peux ajuster la valeur)
        l.addWidget(self.table)

        self.statut_delegate = ComboBoxDelegate(
            ["En attente", "Entretien", "Accepté", "Refusé"], self.table
        )
        self.priorite_delegate = ComboBoxDelegate(
            ["Basse", "Moyenne", "Haute", "Urgente"], self.table
        )
        self.table.setItemDelegateForColumn(6, self.statut_delegate)
        self.table.setItemDelegateForColumn(7, self.priorite_delegate)

        self.table.itemChanged.connect(self.on_item_changed)
        self._updating = False
        self.setLayout(l)
        self.refresh_table()

    def on_item_changed(self, item):
        if getattr(self, "_updating", False):
            return
        row = item.row()
        col = item.column()
        if col in (6, 7):  # 6 = Statut, 7 = Priorité
            candidate_id = self.table.item(row, 0).text()
            new_value = item.text()
            if col == 6:
                self.db.update_statut(candidate_id, new_value)
            elif col == 7:
                self.db.update_priorite(candidate_id, new_value)

    def get_filters(self):
        return {
            "nom_complet": self.filter_nom.text(),
            "poste_demande": self.filter_poste.text(),
            "email": self.filter_email.text(),
            "statut": self.filter_statut.currentText() if self.filter_statut.currentText() != "Tous" else "",
            "priorite": self.filter_priorite.currentText() if self.filter_priorite.currentText() != "Toutes" else "",
            "source": self.filter_source.currentText() if self.filter_source.currentText() != "Toutes" else "",
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
        self.filter_source.setCurrentIndex(0)
        self.refresh_table()

    def refresh_table(self, filters=None):
        self._updating = True
        if filters:
            candidates = self.db.search_candidates(filters)
        else:
            candidates = self.db.get_all_candidates()
        self.table.setRowCount(len(candidates))
        for row, cand in enumerate(candidates):
            for col in range(15):
                if col < 10:
                    item = QTableWidgetItem(str(cand[col]) if cand[col] is not None else "")
                    self.table.setItem(row, col, item)
                elif col == 10:  # Photo
                    w = QLabel()
                    if cand[11]:
                        pix = QPixmap(cand[11])
                        if not pix.isNull():
                            w.setPixmap(pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    w.setAlignment(Qt.AlignCenter)
                    self.table.setCellWidget(row, col, w)
                elif col == 11:  # CV
                    if cand[9]:
                        btn = QPushButton("Voir CV")
                        btn.clicked.connect(lambda _, path=cand[9]: self.open_file(path))
                        self.table.setCellWidget(row, col, btn)
                    else:
                        self.table.setItem(row, col, QTableWidgetItem(""))
                elif col == 12:  # Attachments
                    if cand[10]:
                        files = cand[10].split(";")
                        w = QWidget()
                        layout = QHBoxLayout(w)
                        for f in files:
                            if f.strip():
                                btn = QPushButton(os.path.basename(f))
                                btn.clicked.connect(lambda _, path=f: self.open_file(path))
                                layout.addWidget(btn)
                        layout.addStretch()
                        layout.setContentsMargins(0,0,0,0)
                        self.table.setCellWidget(row, col, w)
                    else:
                        self.table.setItem(row, col, QTableWidgetItem(""))
                elif col == 13:
                    item = QTableWidgetItem(str(cand[13]) if len(cand) > 13 else "")
                    self.table.setItem(row, col, item)
                elif col == 14:  # Actions
                    w = QWidget()
                    h = QHBoxLayout(w)
                    btn_delete = QPushButton("Supprimer")
                    candidate_id = cand[0]
                    btn_delete.clicked.connect(lambda _, cid=candidate_id: self.delete_candidate(cid))
                    btn_pdf = QPushButton("PDF")
                    btn_pdf.clicked.connect(lambda _, cid=candidate_id: self.export_pdf(cid))
                    h.addWidget(btn_delete)
                    h.addWidget(btn_pdf)
                    h.setContentsMargins(0,0,0,0)
                    w.setLayout(h)
                    self.table.setCellWidget(row, col, w)
        self._updating = False

    def open_file(self, path):
        if os.path.exists(path):
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', path))
            elif os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                subprocess.call(('xdg-open', path))
        else:
            QMessageBox.warning(self, "Fichier introuvable", "Le fichier n'existe plus à cet emplacement.")

    def delete_candidate(self, candidate_id):
        reply = QMessageBox.question(self, "Suppression", "Supprimer ce candidat ?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_candidate(candidate_id)
            self.refresh_table()

    def export_pdf(self, candidate_id):
        cand = self.db.get_candidate_by_id(candidate_id)
        if not cand:
            QMessageBox.warning(self, "Erreur", "Candidat introuvable")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exporter en PDF", f"{cand[1]}.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        c = canvas.Canvas(path, pagesize=letter)
        c.setFont("Helvetica", 14)
        c.drawString(50, 760, f"Fiche Candidat : {cand[1]}")
        c.setFont("Helvetica", 12)
        infos = [
            f"Poste : {cand[2]}",
            f"Email : {cand[3]}",
            f"Téléphone : {cand[4]}",
            f"Date : {cand[5]}",
            f"Statut : {cand[6]}",
            f"Priorité : {cand[7]}",
            f"Source : {cand[12]}",
            f"Notes : {cand[8]}",
        ]
        y = 740
        for info in infos:
            c.drawString(50, y, info)
            y -= 20
        if cand[11]:
            try:
                from reportlab.lib.utils import ImageReader
                c.drawImage(ImageReader(cand[11]), 400, 700, width=80, height=80)
            except Exception:
                pass
        c.drawString(50, y - 20, "Pièces jointes :")
        y -= 40
        if cand[10]:
            files = cand[10].split(";")
            for f in files:
                c.drawString(70, y, os.path.basename(f))
                y -= 18
        c.save()
        QMessageBox.information(self, "Export PDF", "PDF exporté avec succès !")

    def export_to_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter en Excel", "", "Excel Files (*.xlsx)")
        if not path:
            return
        candidates = self.db.get_all_candidates()
        columns = [
            "ID", "Nom", "Poste", "Email", "Téléphone",
            "Date", "Statut", "Priorité", "Notes", "CV", "Pièces jointes", "Photo", "Source", "Date Création"
        ]
        df = pd.DataFrame(candidates, columns=[
            "ID", "Nom", "Poste", "Email", "Téléphone",
            "Date", "Statut", "Priorité", "Notes", "CV", "Pièces jointes", "Photo", "Source", "Date Création"
        ])
        try:
            df.to_excel(path, index=False)
            QMessageBox.information(self, "Export", "Exportation réussie !")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur export : {e}")

    def import_from_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importer fichier Excel", "", "Excel Files (*.xlsx)")
        if not path:
            return
        try:
            df = pd.read_excel(path)
            required_cols = {"Nom", "Poste", "Email", "Téléphone", "Date", "Statut", "Priorité", "Notes"}
            if not required_cols.issubset(set(df.columns)):
                QMessageBox.warning(self, "Erreur", "Colonnes obligatoires manquantes dans le fichier Excel.")
                return
            for _, row in df.iterrows():
                data = (
                    row.get("Nom", ""), row.get("Poste", ""), row.get("Email", ""), row.get("Téléphone", ""),
                    str(row.get("Date", ""))[:10], row.get("Statut", ""), row.get("Priorité", ""), row.get("Notes", ""),
                    None, None, None, row.get("Source", "")
                )
                try:
                    self.db.add_candidate(data)
                except Exception:
                    continue
            QMessageBox.information(self, "Import", "Importation terminée !")
            self.refresh_table()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur import : {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestionnaire de Candidatures Moderne")
        self.setGeometry(100, 100, 1450, 800)
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

        # Mode sombre/clair
        self.dark_mode = False
        self.mode_btn = QPushButton("Mode sombre")
        self.mode_btn.clicked.connect(self.toggle_theme)
        self.status.addPermanentWidget(self.mode_btn)

    def update_status(self):
        stats = self.db.get_stats()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status.showMessage(
            f"Candidats: {stats['total']} | Acceptés: {stats['accepte']} | En attente: {stats['en_attente']} | {now}"
        )

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        app = QApplication.instance()
        if self.dark_mode:
            app.setStyleSheet(THEME_DARK)
            self.mode_btn.setText("Mode clair")
        else:
            app.setStyleSheet(THEME_LIGHT)
            self.mode_btn.setText("Mode sombre")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
