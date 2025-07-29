#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
                             QGridLayout, QSpacerItem, QMessageBox, QProgressDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QFontDatabase

class MainBusinessApp(QMainWindow):
    """
    Ana İş Yönetim Uygulaması
    Bu sınıf, CRM ve Marketing modüllerine erişim sağlayan ana arayüzü içerir.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 İş Yönetim Sistemi - Ana Panel")
        self.setGeometry(100, 100, 1000, 700)
        
        # Modül pencere referansları
        self.crm_window = None
        self.marketing_window = None
        
        self.setup_ui()
        self.setup_styles()
        
    def setup_ui(self):
        """Ana kullanıcı arayüzünü kurar"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Başlık alanı
        header_frame = self.create_header()
        main_layout.addWidget(header_frame)
        
        # Modül kartları alanı
        modules_frame = self.create_modules_section()
        main_layout.addWidget(modules_frame)
        
        # Alt bilgi alanı
        info_frame = self.create_info_section()
        main_layout.addWidget(info_frame)
        
        # Spacer ekle
        main_layout.addStretch()
        
        # Alt durum çubuğu
        status_frame = self.create_status_bar()
        main_layout.addWidget(status_frame)
        
    def create_header(self):
        """Başlık alanını oluşturur"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(15)
        
        # Ana başlık
        title_label = QLabel("💼 İş Yönetim Sistemi")
        title_label.setObjectName("mainTitle")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Alt başlık
        subtitle_label = QLabel("Profesyonel iş süreçlerinizi tek platformda yönetin")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        # Fontları yükle
        QFontDatabase.addApplicationFont("fonts/Roboto-Regular.ttf")
        QFontDatabase.addApplicationFont("fonts/Roboto-Bold.ttf")

        # Açıklama
        description_label = QLabel("CRM ve Marketing modüllerinize aşağıdaki butonlardan erişebilirsiniz")
        description_label.setObjectName("description")
        description_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(description_label)
        
        return header_frame
        
    def create_modules_section(self):
        """Modül kartları bölümünü oluşturur"""
        modules_frame = QFrame()
        modules_frame.setObjectName("modulesFrame")
        modules_layout = QHBoxLayout(modules_frame)
        modules_layout.setSpacing(40)
        modules_layout.setAlignment(Qt.AlignCenter)
        
        # CRM Modülü Kartı
        crm_card = self.create_module_card(
            icon="👥",
            title="CRM",
            subtitle="Müşteri İlişkileri Yönetimi",
            description="Müşteri bilgilerinizi yönetin, satış fırsatlarını takip edin, görevlerinizi organize edin ve iletişim geçmişinizi kaydedin.",
            features=[
                "✓ Müşteri Veritabanı",
                "✓ Satış Fırsatları",
                "✓ Görev Yönetimi",
                "✓ İletişim Takibi",
                "✓ Raporlama"
            ],
            color="#dc3545",
            callback=self.open_crm_module
        )
        modules_layout.addWidget(crm_card)
        
        # Marketing Modülü Kartı
        marketing_card = self.create_module_card(
            icon="📈",
            title="Marketing",
            subtitle="Pazarlama Yönetimi",
            description="Pazarlama kampanyalarınızı oluşturun, sosyal medyayı yönetin, e-posta pazarlama yapın ve performansınızı analiz edin.",
            features=[
                "✓ Kampanya Yönetimi",
                "✓ Sosyal Medya",
                "✓ E-posta Pazarlama",
                "✓ İçerik Yönetimi",
                "✓ Analytics"
            ],
            color="#28a745",
            callback=self.open_marketing_module
        )
        modules_layout.addWidget(marketing_card)
        
        return modules_frame
        
    def create_module_card(self, icon, title, subtitle, description, features, color, callback):
        """Modül kartı oluşturur"""
        card = QFrame()
        card.setObjectName("moduleCard")
        card.setFixedSize(400, 500)
        
        # Kart stilini ayarla
        card.setStyleSheet(f"""
            #moduleCard {{
                background-color: white;
                border-radius: 15px;
                padding: 0px;
                border: 1px solid #e0e0e0;
                transition: all 0.3s ease;
            }}
            #moduleCard:hover {{
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                transform: translateY(-5px);
                border-left: 5px solid {color};
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(30, 30, 30, 30)
        
        # Üst kısım - İkon ve başlık
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(15)
        
        # İkon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 64px;
            color: {color};
            margin-bottom: 10px;
        """)
        header_layout.addWidget(icon_label)
        
        # Ana başlık
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            font-family: "Roboto", sans-serif;
            font-size: 32px;
            font-weight: bold;
            color: {color};
            margin-bottom: 5px;
        """)
        header_layout.addWidget(title_label)
        
        # Alt başlık
        subtitle_label = QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            font-family: "Roboto", sans-serif;
            font-size: 18px;
            color: #6c757d;
            font-weight: 500;
        """)
        header_layout.addWidget(subtitle_label)
        
        card_layout.addLayout(header_layout)
        
        # Açıklama
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            font-family: "Roboto", sans-serif;
            font-size: 16px;
            color: #495057;
            line-height: 1.5;
            margin: 10px 0px;
        """)
        card_layout.addWidget(desc_label)
        
        # Özellikler listesi
        features_layout = QVBoxLayout()
        features_layout.setSpacing(8)
        
        for feature in features:
            feature_label = QLabel(feature)
            feature_label.setStyleSheet(f"""
            font-family: "Roboto", sans-serif;
            font-size: 14px;
                color: {color};
                font-weight: 500;
                padding: 2px 0px;
            """)
            features_layout.addWidget(feature_label)
            
        card_layout.addLayout(features_layout)
        
        # Spacer
        card_layout.addStretch()
        
        # Buton
        button = QPushButton(f"{title} Modülünü Aç")
        button.setObjectName("moduleButton")
        button.setFixedHeight(50)
        button.setStyleSheet(f"""
            QPushButton {{
                font-family: "Roboto", sans-serif;
                background-color: {color};
                color: white;
                border: none;
                padding: 15px 25px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
                transform: translateY(-2px);
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
                transform: translateY(0px);
            }}
        """)
        button.clicked.connect(callback)
        card_layout.addWidget(button)
        
        return card
        
    def create_info_section(self):
        """Bilgi bölümünü oluşturur"""
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setAlignment(Qt.AlignCenter)
        info_layout.setSpacing(15)
        
        # Bilgi başlığı
        info_title = QLabel("💡 Sistem Özellikleri")
        info_title.setObjectName("infoTitle")
        info_title.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(info_title)
        
        # Özellikler grid'i
        features_grid = QGridLayout()
        features_grid.setSpacing(20)
        
        system_features = [
            ("🔒", "Sécurisé", "Vos données sont stockées en toute sécurité"),
            ("⚡", "Rapide", "Performances optimisées"),
            ("📱", "Moderne", "Interface utilisateur conviviale"),
            ("🔄", "Intégré", "Partage de données entre les modules"),
        ]
        
        for i, (icon, title, desc) in enumerate(system_features):
            feature_widget = self.create_feature_widget(icon, title, desc)
            row = i // 2
            col = i % 2
            features_grid.addWidget(feature_widget, row, col)
            
        info_layout.addLayout(features_grid)
        
        return info_frame
        
    def create_feature_widget(self, icon, title, description):
        """Özellik widget'ı oluşturur"""
        widget = QFrame()
        widget.setObjectName("featureWidget")
        layout = QHBoxLayout(widget)
        layout.setSpacing(15)
        
        # İkon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon_label)
        
        # Metin alanı
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setObjectName("featureTitle")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setObjectName("featureDesc")
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        return widget
        
    def create_status_bar(self):
        """Alt durum çubuğunu oluşturur"""
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_layout = QHBoxLayout(status_frame)
        
        # Sol taraf - Durum bilgisi
        self.status_label = QLabel("Sistem hazır - Modül seçiniz")
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Sağ taraf - Sistem bilgileri
        system_info_layout = QHBoxLayout()
        
        # Kullanıcı bilgisi
        user_label = QLabel("👤 Kullanıcı: Admin")
        user_label.setObjectName("userLabel")
        system_info_layout.addWidget(user_label)
        
        # Tarih/saat
        from datetime import datetime
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        time_label = QLabel(f"🕒 {current_time}")
        time_label.setObjectName("timeLabel")
        system_info_layout.addWidget(time_label)
        
        # Sürüm bilgisi
        version_label = QLabel("📦 v1.0.0")
        version_label.setObjectName("versionLabel")
        system_info_layout.addWidget(version_label)
        
        status_layout.addLayout(system_info_layout)
        
        return status_frame
        
    def darken_color(self, hex_color, factor=0.9):
        """Rengi koyulaştırır"""
        # Hex rengi RGB'ye çevir
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Rengi koyulaştır
        darkened = tuple(int(c * factor) for c in rgb)
        
        # RGB'yi hex'e geri çevir
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        
    def setup_styles(self):
        """Stil tanımlamaları"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            
            #headerFrame {
                background: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                padding: 20px 40px;
            }
            
            #mainTitle {
                font-family: "Roboto", sans-serif;
                font-size: 36px;
                font-weight: bold;
                color: #333;
            }
            
            #subtitle {
                font-family: "Roboto", sans-serif;
                font-size: 18px;
                color: #777;
            }
            
            #description {
                font-family: "Roboto", sans-serif;
                font-size: 16px;
                color: #555;
            }
            
            #modulesFrame {
                background-color: transparent;
                padding: 20px;
            }
            
            #moduleCard {
                background-color: white;
                border-radius: 15px;
                padding: 0px;
                border: 1px solid #e0e0e0;
                transition: all 0.3s ease;
            }
            #moduleCard:hover {
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                transform: translateY(-5px);
                border-left: 5px solid #007bff;
            }

            #infoFrame {
                background-color: #ffffff;
                border-radius: 15px;
                padding: 30px;
                margin: 20px 0px;
                border: 1px solid #e0e0e0;
            }
            
            #infoTitle {
                font-family: "Roboto", sans-serif;
                font-size: 24px;
                font-weight: bold;
                color: #333;
                margin-bottom: 20px;
            }
            
            #featureWidget {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
            
            #featureTitle {
                font-family: "Roboto", sans-serif;
                font-size: 16px;
                font-weight: bold;
                color: #333;
            }
            
            #featureDesc {
                font-family: "Roboto", sans-serif;
                font-size: 14px;
                color: #777;
            }
            
            #statusFrame {
                background-color: #343a40;
                color: white;
                padding: 10px 20px;
                border-top: 1px solid #444;
            }
            
            #statusLabel {
                font-family: "Roboto", sans-serif;
                font-size: 14px;
                color: white;
            }
            
            #userLabel, #timeLabel, #versionLabel {
                font-family: "Roboto", sans-serif;
                font-size: 12px;
                color: #ccc;
                margin-left: 20px;
            }
        """)
        
    # Modül açma metodları
    def open_crm_module(self):
        """CRM modülünü açar"""
        if self.crm_window is None:
            progress = QProgressDialog("CRM modülü yükleniyor...", "İptal", 0, 0, self)
            progress.setCancelButton(None)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            QApplication.processEvents()

            from main_crm import CRMModule
            self.crm_window = CRMModule()
            progress.close()

        self.crm_window.show()
        self.crm_window.raise_()
        self.crm_window.activateWindow()
        self.status_label.setText("CRM modülü başarıyla açıldı")

    def open_marketing_module(self):
        """Marketing modülünü açar"""
        if self.marketing_window is None:
            progress = QProgressDialog("Marketing modülü yükleniyor...", "İptal", 0, 0, self)
            progress.setCancelButton(None)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            QApplication.processEvents()

            from main_marketing import MarketingModule
            self.marketing_window = MarketingModule()
            progress.close()

        self.marketing_window.show()
        self.marketing_window.raise_()
        self.marketing_window.activateWindow()
        self.status_label.setText("Marketing modülü başarıyla açıldı")
            
    def closeEvent(self, event):
        """Uygulama kapatılırken çalışır"""
        # Alt modül pencerelerini kapat
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

