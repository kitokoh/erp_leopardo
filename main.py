#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import random
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
                             QGridLayout, QSpacerItem, QMessageBox, QProgressDialog,
                             QGraphicsDropShadowEffect, QScrollArea, QToolButton,
                             QGraphicsOpacityEffect)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, 
                          QRect, QParallelAnimationGroup, QSequentialAnimationGroup,
                          QPoint, QSize)
from PyQt5.QtGui import (QFont, QIcon, QPalette, QColor, QPixmap, QFontDatabase, 
                         QPainter, QLinearGradient, QRadialGradient, QPen, QBrush,
                         QPolygon, QFontMetrics)

class ParticleWidget(QWidget):
    """Widget avec effet de particules flottantes"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self.init_particles()
        
        # Timer pour l'animation des particules
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(50)
        
    def init_particles(self):
        """Initialise les particules"""
        for _ in range(15):
            particle = {
                'x': random.randint(0, 800),
                'y': random.randint(0, 600),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.5, 0.5),
                'size': random.randint(2, 6),
                'opacity': random.uniform(0.1, 0.3)
            }
            self.particles.append(particle)
    
    def update_particles(self):
        """Met à jour la position des particules"""
        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            
            # Rebond sur les bords
            if particle['x'] <= 0 or particle['x'] >= self.width():
                particle['vx'] *= -1
            if particle['y'] <= 0 or particle['y'] >= self.height():
                particle['vy'] *= -1
                
        self.update()
    
    def paintEvent(self, event):
        """Dessine les particules"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for particle in self.particles:
            color = QColor(102, 126, 234, int(particle['opacity'] * 255))
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(particle['x']), int(particle['y']), 
                              particle['size'], particle['size'])

class ThemeToggleButton(QToolButton):
    """Bouton de basculement de thème avec animation"""
    theme_changed = pyqtSignal(bool)  # True pour dark, False pour light
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self.setFixedSize(40, 40)
        self.setStyleSheet("""
            QToolButton {
                border: 2px solid #e9ecef;
                border-radius: 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                font-size: 18px;
            }
            QToolButton:hover {
                border: 2px solid #667eea;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
        """)
        self.setText("☀️")
        self.clicked.connect(self.toggle_theme)
        
    def toggle_theme(self):
        """Bascule entre les thèmes"""
        self.is_dark = not self.is_dark
        if self.is_dark:
            self.setText("🌙")
            self.setStyleSheet("""
                QToolButton {
                    border: 2px solid #495057;
                    border-radius: 20px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #343a40, stop:1 #495057);
                    color: white;
                    font-size: 18px;
                }
                QToolButton:hover {
                    border: 2px solid #6c757d;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #495057, stop:1 #6c757d);
                }
            """)
        else:
            self.setText("☀️")
            self.setStyleSheet("""
                QToolButton {
                    border: 2px solid #e9ecef;
                    border-radius: 20px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffffff, stop:1 #f8f9fa);
                    font-size: 18px;
                }
                QToolButton:hover {
                    border: 2px solid #667eea;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f8f9fa, stop:1 #e9ecef);
                }
            """)
        
        self.theme_changed.emit(self.is_dark)

class PositiveProgressDialog(QProgressDialog):
    """Dialogue de progression avec messages positifs et animations"""
    def __init__(self, module_name, parent=None):
        super().__init__(parent)
        self.module_name = module_name
        self.progress_value = 0
        
        # Messages positifs selon le module avec self.tr()
        if module_name == "CRM":
            self.positive_messages = [
                self.tr("🚀 Initialisation du module CRM..."),
                self.tr("👥 Chargement de la base clients..."),
                self.tr("💼 Configuration des outils de vente..."),
                self.tr("📊 Préparation des tableaux de bord..."),
                self.tr("🎯 Optimisation des performances..."),
                self.tr("✨ Module CRM prêt !")
            ]
        else:  # Marketing
            self.positive_messages = [
                self.tr("🚀 Initialisation du module Marketing..."),
                self.tr("📈 Chargement des campagnes..."),
                self.tr("🎨 Configuration de l'interface créative..."),
                self.tr("📊 Préparation des analytics..."),
                self.tr("🎯 Synchronisation des données..."),
                self.tr("✨ Module Marketing prêt !")
            ]
        
        self.current_message_index = 0
        self.setup_dialog()
        
    def setup_dialog(self):
        """Configure le dialogue avec animations"""
        self.setWindowTitle(self.tr("Chargement {0}").format(self.module_name))
        self.setLabelText(self.positive_messages[0])
        self.setRange(0, 100)
        self.setValue(0)
        self.setMinimumDuration(0)
        self.setCancelButton(None)
        self.setWindowModality(Qt.WindowModal)
        self.setFixedSize(450, 140)
        
        # Style moderne avec animations CSS
        self.setStyleSheet("""
            QProgressDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:0.5 #f8f9fa, stop:1 #ffffff);
                border-radius: 15px;
                border: 3px solid #e9ecef;
            }
            QLabel {
                font-family: "Roboto", sans-serif;
                font-size: 15px;
                color: #2c3e50;
                padding: 15px;
                font-weight: 600;
                text-align: center;
            }
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 10px;
                text-align: center;
                font-family: "Roboto", sans-serif;
                font-size: 12px;
                font-weight: bold;
                background-color: #f8f9fa;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:0.3 #764ba2, stop:0.7 #667eea, stop:1 #764ba2);
                border-radius: 8px;
                margin: 1px;
            }
        """)
        
        # Effet d'ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)
        
        # Timer pour les messages
        self.message_timer = QTimer()
        self.message_timer.timeout.connect(self.update_message)
        self.message_timer.start(1000)
        
        # Timer pour la progression
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(150)
        
    def update_message(self):
        """Met à jour le message avec effet de fondu"""
        if self.current_message_index < len(self.positive_messages) - 1:
            self.current_message_index += 1
            self.setLabelText(self.positive_messages[self.current_message_index])
        
    def update_progress(self):
        """Met à jour la progression"""
        self.progress_value += random.randint(1, 4)
        if self.progress_value >= 100:
            self.progress_value = 100
            self.progress_timer.stop()
            self.message_timer.stop()
            self.setValue(100)
            QTimer.singleShot(800, self.accept)
        else:
            self.setValue(self.progress_value)

class AnimatedButton(QPushButton):
    """Bouton avec animations avancées et effets de particules"""
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.base_color = color
        self.hover_color = self.darken_color(color, 0.85)
        self.pressed_color = self.darken_color(color, 0.7)
        self.setup_animations()
        
    def setup_animations(self):
        """Configure les animations complexes"""
        # Animation de position
        self.pos_animation = QPropertyAnimation(self, b"geometry")
        self.pos_animation.setDuration(200)
        self.pos_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Animation d'opacité
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(300)
        
    def darken_color(self, hex_color, factor=0.9):
        """Assombrit une couleur"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        
    def enterEvent(self, event):
        """Animation au survol avec effet de pulsation"""
        super().enterEvent(event)
        current_rect = self.geometry()
        new_rect = QRect(current_rect.x() - 2, current_rect.y() - 3, 
                        current_rect.width() + 4, current_rect.height())
        self.pos_animation.setStartValue(current_rect)
        self.pos_animation.setEndValue(new_rect)
        self.pos_animation.start()
        
        # Effet de pulsation
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.8)
        self.opacity_animation.start()
        
    def leaveEvent(self, event):
        """Animation à la sortie du survol"""
        super().leaveEvent(event)
        current_rect = self.geometry()
        new_rect = QRect(current_rect.x() + 2, current_rect.y() + 3, 
                        current_rect.width() - 4, current_rect.height())
        self.pos_animation.setStartValue(current_rect)
        self.pos_animation.setEndValue(new_rect)
        self.pos_animation.start()
        
        self.opacity_animation.setStartValue(0.8)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()

class MainBusinessApp(QMainWindow):
    """
    Ana İş Yönetim Uygulaması - Version Ultimate avec design avancé
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("🚀 İş Yönetim Sistemi - Ana Panel"))
        
        # Taille optimisée pour éviter le débordement sur les laptops
        self.setGeometry(100, 100, 880, 580)  # Encore plus compact
        self.setMinimumSize(800, 520)
        
        # Supprimer SEULEMENT le bouton d'agrandissement
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        
        # Variables de thème
        self.is_dark_theme = False
        
        # Modül pencere referansları
        self.crm_window = None
        self.marketing_window = None
        
        self.setup_ui()
        self.setup_styles()
        
    def setup_ui(self):
        """Ana kullanıcı arayüzünü kurar avec particules et thèmes"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Widget de particules en arrière-plan
        self.particle_widget = ParticleWidget(central_widget)
        self.particle_widget.setGeometry(0, 0, 880, 580)
        self.particle_widget.lower()
        
        # Scroll area pour éviter le débordement
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        
        # Widget de contenu principal
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        
        # Ana layout avec espacement optimisé
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Barre d'outils avec bouton de thème
        toolbar_frame = self.create_toolbar()
        main_layout.addWidget(toolbar_frame)
        
        # Başlık alanı
        header_frame = self.create_header()
        main_layout.addWidget(header_frame)
        
        # Modül kartları alanı
        modules_frame = self.create_modules_section()
        main_layout.addWidget(modules_frame)
        
        # Alt bilgi alanı (plus compact)
        info_frame = self.create_info_section()
        main_layout.addWidget(info_frame)
        
        # Spacer minimal
        main_layout.addStretch(1)
        
        # Alt durum çubuğu
        status_frame = self.create_status_bar()
        main_layout.addWidget(status_frame)
        
        # Layout principal de la fenêtre
        window_layout = QVBoxLayout(central_widget)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(scroll_area)
        
    def create_toolbar(self):
        """Crée la barre d'outils avec bouton de thème"""
        toolbar_frame = QFrame()
        toolbar_frame.setFixedHeight(50)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(15, 5, 15, 5)
        
        # Logo/titre à gauche
        logo_label = QLabel(self.tr("💼 İş Yönetim"))
        logo_label.setStyleSheet("""
            font-family: "Roboto", sans-serif;
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        """)
        toolbar_layout.addWidget(logo_label)
        
        toolbar_layout.addStretch()
        
        # Bouton de basculement de thème
        self.theme_button = ThemeToggleButton()
        self.theme_button.theme_changed.connect(self.toggle_theme)
        toolbar_layout.addWidget(self.theme_button)
        
        return toolbar_frame
        
    def create_header(self):
        """Başlık alanını oluşturur avec gradient animé et glassmorphism"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setFixedHeight(100)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(6)
        
        # Ana başlık avec effet de brillance
        title_label = QLabel(self.tr("İş Yönetim Sistemi"))
        title_label.setObjectName("mainTitle")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Alt başlık
        subtitle_label = QLabel(self.tr("Profesyonel iş süreçlerinizi tek platformda yönetin"))
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        # Açıklama
        description_label = QLabel(self.tr("CRM ve Marketing modüllerinize aşağıdaki butonlardan erişebilirsiniz"))
        description_label.setObjectName("description")
        description_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(description_label)
        
        return header_frame
        
    def create_modules_section(self):
        """Modül kartları bölümünü oluşturur"""
        modules_frame = QFrame()
        modules_frame.setObjectName("modulesFrame")
        modules_layout = QHBoxLayout(modules_frame)
        modules_layout.setSpacing(20)
        modules_layout.setAlignment(Qt.AlignCenter)
        
        # CRM Modülü Kartı
        crm_card = self.create_module_card(
            icon="👥",
            title=self.tr("CRM"),
            subtitle=self.tr("Müşteri İlişkileri Yönetimi"),
            description=self.tr("Müşteri bilgilerinizi yönetin, satış fırsatlarını takip edin."),
            features=[
                self.tr("✓ Müşteri Veritabanı"),
                self.tr("✓ Satış Fırsatları"),
                self.tr("✓ Görev Yönetimi"),
                self.tr("✓ Raporlama")
            ],
            color="#dc3545",
            gradient_start="#dc3545",
            gradient_end="#c82333",
            callback=self.open_crm_module
        )
        modules_layout.addWidget(crm_card)
        
        # Marketing Modülü Kartı
        marketing_card = self.create_module_card(
            icon="📈",
            title=self.tr("Marketing"),
            subtitle=self.tr("Pazarlama Yönetimi"),
            description=self.tr("Pazarlama kampanyalarınızı oluşturun, performansınızı analiz edin."),
            features=[
                self.tr("✓ Kampanya Yönetimi"),
                self.tr("✓ Sosyal Medya"),
                self.tr("✓ E-posta Pazarlama"),
                self.tr("✓ Analytics")
            ],
            color="#28a745",
            gradient_start="#28a745",
            gradient_end="#218838",
            callback=self.open_marketing_module
        )
        modules_layout.addWidget(marketing_card)
        
        return modules_frame
        
    def create_module_card(self, icon, title, subtitle, description, features, color, gradient_start, gradient_end, callback):
        """Modül kartı oluşturur avec glassmorphism et animations avancées"""
        card = QFrame()
        card.setObjectName("moduleCard")
        card.setFixedSize(300, 340)  # Plus compact
        
        # Effet d'ombre dynamique
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(30)
        shadow_effect.setColor(QColor(0, 0, 0, 30))
        shadow_effect.setOffset(0, 15)
        card.setGraphicsEffect(shadow_effect)
        
        # Style glassmorphism
        card.setStyleSheet(f"""
            #moduleCard {{
                background: rgba(255, 255, 255, 0.25);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.18);
            }}
            #moduleCard:hover {{
                background: rgba(255, 255, 255, 0.35);
                border: 2px solid {color};
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(18, 18, 18, 18)
        
        # En-tête avec icône flottante
        header_frame = QFrame()
        header_frame.setObjectName("cardHeader")
        header_frame.setFixedHeight(70)
        header_frame.setStyleSheet(f"""
            #cardHeader {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {gradient_start}, stop:0.5 {color}, stop:1 {gradient_end});
                border-radius: 15px;
                margin-bottom: 5px;
            }}
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(10)
        
        # İkon avec effet de brillance
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 32px; 
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        """)
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-family: "Roboto", sans-serif;
            font-size: 22px;
            font-weight: bold;
            color: white;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        """)
        header_layout.addWidget(title_label)
        
        card_layout.addWidget(header_frame)
        
        # Contenu compact
        subtitle_label = QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet(f"""
            font-family: "Roboto", sans-serif;
            font-size: 13px;
            color: {color};
            font-weight: 600;
            margin: 3px 0px;
        """)
        card_layout.addWidget(subtitle_label)
        
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            font-family: "Roboto", sans-serif;
            font-size: 11px;
            color: #495057;
            line-height: 1.3;
            margin: 3px 0px;
        """)
        card_layout.addWidget(desc_label)
        
        # Features en grid compact
        features_frame = QFrame()
        features_layout = QGridLayout(features_frame)
        features_layout.setSpacing(3)
        
        for i, feature in enumerate(features):
            feature_label = QLabel(feature)
            feature_label.setStyleSheet(f"""
                font-family: "Roboto", sans-serif;
                font-size: 10px;
                color: {color};
                font-weight: 500;
            """)
            row = i // 2
            col = i % 2
            features_layout.addWidget(feature_label, row, col)
            
        card_layout.addWidget(features_frame)
        card_layout.addStretch()
        
        # Bouton animé
        button = AnimatedButton(self.tr("{0} Modülünü Aç").format(title), color)
        button.setFixedHeight(35)
        button.setStyleSheet(f"""
            QPushButton {{
                font-family: "Roboto", sans-serif;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {gradient_start}, stop:1 {gradient_end});
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 13px;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {gradient_end}, stop:1 {gradient_start});
            }}
        """)
        button.clicked.connect(callback)
        card_layout.addWidget(button)
        
        return card
        
    def create_info_section(self):
        """Bilgi bölümünü oluşturur - version ultra-compacte"""
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_frame.setFixedHeight(80)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setAlignment(Qt.AlignCenter)
        info_layout.setSpacing(6)
        
        info_title = QLabel(self.tr("💡 Sistem Özellikleri"))
        info_title.setObjectName("infoTitle")
        info_title.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(info_title)
        
        # Features en ligne horizontale
        features_layout = QHBoxLayout()
        features_layout.setSpacing(15)
        features_layout.setAlignment(Qt.AlignCenter)
        
        system_features = [
            ("🔒", self.tr("Güvenli")),
            ("⚡", self.tr("Hızlı")),
            ("📱", self.tr("Modern")),
            ("🔄", self.tr("Entegre")),
        ]
        
        for icon, title in system_features:
            feature_widget = self.create_micro_feature_widget(icon, title)
            features_layout.addWidget(feature_widget)
            
        info_layout.addLayout(features_layout)
        
        return info_frame
        
    def create_micro_feature_widget(self, icon, title):
        """Micro widget de fonctionnalité"""
        widget = QFrame()
        widget.setObjectName("microFeatureWidget")
        widget.setFixedSize(60, 45)
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(2)
        
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setObjectName("microFeatureTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        return widget
        
    def create_status_bar(self):
        """Alt durum çubuğunu oluşturur"""
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_frame.setFixedHeight(30)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 3, 12, 3)
        
        self.status_label = QLabel(self.tr("Sistem hazır - Modül seçiniz"))
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Informations système compactes
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M")
        time_label = QLabel(self.tr("🕒 {0}").format(current_time))
        time_label.setObjectName("timeLabel")
        status_layout.addWidget(time_label)
        
        version_label = QLabel(self.tr("v1.0"))
        version_label.setObjectName("versionLabel")
        status_layout.addWidget(version_label)
        
        return status_frame
        
    def toggle_theme(self, is_dark):
        """Bascule entre thème sombre et clair"""
        self.is_dark_theme = is_dark
        self.setup_styles()
        
    def setup_styles(self):
        """Styles avec support thème sombre/clair"""
        if self.is_dark_theme:
            # Thème sombre
            self.setStyleSheet("""
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2c3e50, stop:0.5 #34495e, stop:1 #2c3e50);
                }
                
                #headerFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:0.3 #764ba2, stop:0.7 #667eea, stop:1 #764ba2);
                    border: none;
                    border-radius: 15px;
                    margin-bottom: 8px;
                }
                
                #mainTitle {
                    font-family: "Roboto", sans-serif;
                    font-size: 26px;
                    font-weight: bold;
                    color: white;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                }
                
                #subtitle, #description {
                    font-family: "Roboto", sans-serif;
                    color: rgba(255,255,255,0.9);
                    font-weight: 400;
                }
                
                #infoFrame {
                    background: rgba(52, 73, 94, 0.8);
                    border-radius: 12px;
                    border: 1px solid #495057;
                }
                
                #infoTitle {
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                }
                
                #microFeatureWidget {
                    background: rgba(108, 117, 125, 0.3);
                    border-radius: 8px;
                    border: 1px solid #6c757d;
                }
                
                #microFeatureTitle {
                    color: #adb5bd;
                    font-size: 9px;
                    font-weight: bold;
                }
                
                #statusFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #1a252f, stop:0.5 #2c3e50, stop:1 #1a252f);
                    border-top: 2px solid #34495e;
                }
                
                #statusLabel, #timeLabel, #versionLabel {
                    color: #bdc3c7;
                    font-size: 10px;
                }
            """)
        else:
            # Thème clair
            self.setStyleSheet("""
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f8f9fa, stop:0.5 #e9ecef, stop:1 #dee2e6);
                }
                
                QScrollArea {
                    border: none;
                    background: transparent;
                }
                
                #headerFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:0.3 #764ba2, stop:0.7 #667eea, stop:1 #764ba2);
                    border: none;
                    border-radius: 15px;
                    margin-bottom: 8px;
                }
                
                #mainTitle {
                    font-family: "Roboto", sans-serif;
                    font-size: 26px;
                    font-weight: bold;
                    color: white;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }
                
                #subtitle {
                    font-family: "Roboto", sans-serif;
                    font-size: 14px;
                    color: rgba(255,255,255,0.9);
                    font-weight: 400;
                }
                
                #description {
                    font-family: "Roboto", sans-serif;
                    font-size: 12px;
                    color: rgba(255,255,255,0.8);
                    font-weight: 300;
                }
                
                #modulesFrame {
                    background-color: transparent;
                    padding: 8px;
                }
                
                #infoFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.9));
                    border-radius: 12px;
                    padding: 12px;
                    margin: 6px 0px;
                    border: 1px solid rgba(233,236,239,0.8);
                }
                
                #infoTitle {
                    font-family: "Roboto", sans-serif;
                    font-size: 14px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 6px;
                }
                
                #microFeatureWidget {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255,255,255,0.8), stop:1 rgba(241,243,244,0.8));
                    border-radius: 8px;
                    border: 1px solid rgba(233,236,239,0.6);
                    margin: 2px;
                }
                #microFeatureWidget:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255,255,255,0.95), stop:1 rgba(227,242,253,0.8));
                    border: 2px solid #2196f3;
                }
                
                #microFeatureTitle {
                    font-family: "Roboto", sans-serif;
                    font-size: 9px;
                    font-weight: bold;
                    color: #2c3e50;
                }
                
                #statusFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #2c3e50, stop:0.5 #34495e, stop:1 #2c3e50);
                    border-top: 2px solid #34495e;
                    border-radius: 0px 0px 5px 5px;
                }
                
                #statusLabel {
                    font-family: "Roboto", sans-serif;
                    font-size: 11px;
                    color: white;
                    font-weight: 500;
                }
                
                #timeLabel, #versionLabel {
                    font-family: "Roboto", sans-serif;
                    font-size: 9px;
                    color: #bdc3c7;
                    font-weight: 400;
                    margin-left: 10px;
                }
            """)
        
    # Modül açma metodları - LOGIQUE ORIGINALE AVEC MESSAGES POSITIFS
    def open_crm_module(self):
        """CRM modülünü açar - AVEC OUVERTURE RÉELLE"""
        if self.crm_window is None:
            progress = PositiveProgressDialog("CRM", self)
            
            # Centrer le dialogue
            parent_geometry = self.geometry()
            dialog_geometry = progress.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - dialog_geometry.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - dialog_geometry.height()) // 2
            progress.move(x, y)
            
            progress.show()
            QApplication.processEvents()

            try:
                from main_crm import CRMModule
                self.crm_window = CRMModule()
            except ImportError as e:
                progress.close()
                QMessageBox.warning(self, self.tr("Module manquant"), 
                    self.tr("Le module CRM (main_crm.py) n'a pas été trouvé.\n\n"
                    "Erreur: {0}\n\n"
                    "Veuillez vous assurer que le fichier main_crm.py existe dans le même répertoire.").format(str(e)))
                return
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, self.tr("Erreur"), 
                    self.tr("Erreur lors du chargement du module CRM:\n{0}").format(str(e)))
                return
            
            progress.close()

        self.crm_window.show()
        self.crm_window.raise_()
        self.crm_window.activateWindow()
        self.status_label.setText(self.tr("CRM modülü başarıyla açıldı"))

    def open_marketing_module(self):
        """Marketing modülünü açar - AVEC OUVERTURE RÉELLE"""
        if self.marketing_window is None:
            progress = PositiveProgressDialog("Marketing", self)
            
            # Centrer le dialogue
            parent_geometry = self.geometry()
            dialog_geometry = progress.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - dialog_geometry.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - dialog_geometry.height()) // 2
            progress.move(x, y)
            
            progress.show()
            QApplication.processEvents()

            try:
                from main_marketing import MarketingModule
                self.marketing_window = MarketingModule()
            except ImportError as e:
                progress.close()
                QMessageBox.warning(self, self.tr("Module manquant"), 
                    self.tr("Le module Marketing (main_marketing.py) n'a pas été trouvé.\n\n"
                    "Erreur: {0}\n\n"
                    "Veuillez vous assurer que le fichier main_marketing.py existe dans le même répertoire.").format(str(e)))
                return
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, self.tr("Erreur"), 
                    self.tr("Erreur lors du chargement du module Marketing:\n{0}").format(str(e)))
                return
            
            progress.close()

        self.marketing_window.show()
        self.marketing_window.raise_()
        self.marketing_window.activateWindow()
        self.status_label.setText(self.tr("Marketing modülü başarıyla açıldı"))
            
    def closeEvent(self, event):
        """Uygulama kapatılırken çalışır"""
        if self.crm_window and self.crm_window.isVisible():
            self.crm_window.close()
            
        if self.marketing_window and self.marketing_window.isVisible():
            self.marketing_window.close()
            
        event.accept()

def main():
    """Ana fonksiyon"""
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Uygulama bilgileri
    app.setApplicationName("İş Yönetim Sistemi")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Profesyonel Yazılım Çözümleri")
    
    # Yüksek DPI desteği
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Ana pencereyi oluştur ve göster
    main_window = MainBusinessApp()
    main_window.show()
    
    # Uygulama döngüsünü başlat
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

