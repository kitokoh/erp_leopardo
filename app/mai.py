#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
                             QTextEdit, QTableWidget, QTableWidgetItem, QTabWidget,
                             QSplitter, QGroupBox, QFormLayout, QLineEdit, QComboBox,
                             QDateEdit, QSpinBox, QCheckBox, QProgressBar, QSlider,
                             QListWidget, QTreeWidget, QTreeWidgetItem, QScrollArea,
                             QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap

class CRMModule(QMainWindow):
    """
    Müşteri İlişkileri Yönetimi (CRM) Modülü
    Bu sınıf, müşteri yönetimi, satış takibi ve iletişim özelliklerini içerir.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("👥 CRM - Müşteri İlişkileri Yönetimi")
        self.setGeometry(100, 100, 1200, 800)
        self.setup_ui()
        self.setup_styles()
        self.load_sample_data()
        
    def setup_ui(self):
        """Ana kullanıcı arayüzünü kurar"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Başlık alanı
        header_frame = self.create_header()
        main_layout.addWidget(header_frame)
        
        # Ana içerik alanı - Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabWidget")
        
        # Müşteriler sekmesi
        customers_tab = self.create_customers_tab()
        self.tab_widget.addTab(customers_tab, "👤 Müşteriler")
        
        # Satış fırsatları sekmesi
        opportunities_tab = self.create_opportunities_tab()
        self.tab_widget.addTab(opportunities_tab, "💼 Satış Fırsatları")
        
        # Görevler sekmesi
        tasks_tab = self.create_tasks_tab()
        self.tab_widget.addTab(tasks_tab, "✅ Görevler")
        
        # İletişim geçmişi sekmesi
        communication_tab = self.create_communication_tab()
        self.tab_widget.addTab(communication_tab, "📞 İletişim Geçmişi")
        
        # Raporlar sekmesi
        reports_tab = self.create_reports_tab()
        self.tab_widget.addTab(reports_tab, "📊 Raporlar")
        
        main_layout.addWidget(self.tab_widget)
        
        # Alt durum çubuğu
        status_frame = self.create_status_bar()
        main_layout.addWidget(status_frame)
        
    def create_header(self):
        """Başlık alanını oluşturur"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        
        # Sol taraf - Başlık ve açıklama
        left_layout = QVBoxLayout()
        
        title_label = QLabel("👥 CRM - Müşteri İlişkileri Yönetimi")
        title_label.setObjectName("headerTitle")
        left_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Müşteri bilgilerinizi yönetin, satış fırsatlarını takip edin")
        subtitle_label.setObjectName("headerSubtitle")
        left_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(left_layout)
        header_layout.addStretch()
        
        # Sağ taraf - Hızlı eylemler
        quick_actions_layout = QHBoxLayout()
        
        new_customer_btn = QPushButton("➕ Yeni Müşteri")
        new_customer_btn.setObjectName("primaryButton")
        new_customer_btn.clicked.connect(self.add_new_customer)
        quick_actions_layout.addWidget(new_customer_btn)
        
        new_opportunity_btn = QPushButton("💼 Yeni Fırsat")
        new_opportunity_btn.setObjectName("secondaryButton")
        new_opportunity_btn.clicked.connect(self.add_new_opportunity)
        quick_actions_layout.addWidget(new_opportunity_btn)
        
        header_layout.addLayout(quick_actions_layout)
        
        return header_frame
        
    def create_customers_tab(self):
        """Müşteriler sekmesini oluşturur"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(20)
        
        # Sol panel - Müşteri formu
        form_group = QGroupBox("👤 Müşteri Bilgileri")
        form_layout = QFormLayout(form_group)
        
        self.customer_name_edit = QLineEdit()
        self.customer_email_edit = QLineEdit()
        self.customer_phone_edit = QLineEdit()
        self.customer_company_edit = QLineEdit()
        self.customer_position_edit = QLineEdit()
        self.customer_address_edit = QTextEdit()
        self.customer_address_edit.setMaximumHeight(80)
        
        self.customer_type_combo = QComboBox()
        self.customer_type_combo.addItems(["Bireysel", "Kurumsal", "Bayi", "Partner"])
        
        self.customer_status_combo = QComboBox()
        self.customer_status_combo.addItems(["🟢 Aktif", "🟡 Potansiyel", "🔴 Pasif", "❄️ Donuk"])
        
        form_layout.addRow("Ad Soyad:", self.customer_name_edit)
        form_layout.addRow("E-posta:", self.customer_email_edit)
        form_layout.addRow("Telefon:", self.customer_phone_edit)
        form_layout.addRow("Şirket:", self.customer_company_edit)
        form_layout.addRow("Pozisyon:", self.customer_position_edit)
        form_layout.addRow("Adres:", self.customer_address_edit)
        form_layout.addRow("Tür:", self.customer_type_combo)
        form_layout.addRow("Durum:", self.customer_status_combo)
        
        # Form butonları
        form_buttons_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_customer)
        
        clear_btn = QPushButton("🗑️ Temizle")
        clear_btn.clicked.connect(self.clear_customer_form)
        
        delete_btn = QPushButton("❌ Sil")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self.delete_customer)
        
        form_buttons_layout.addWidget(save_btn)
        form_buttons_layout.addWidget(clear_btn)
        form_buttons_layout.addWidget(delete_btn)
        form_layout.addRow(form_buttons_layout)
        
        layout.addWidget(form_group, 1)
        
        # Sağ panel - Müşteri listesi ve istatistikler
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_data = [
            ("👥", "Toplam", "1,234"),
            ("🟢", "Aktif", "987"),
            ("🟡", "Potansiyel", "156"),
            ("🔴", "Pasif", "91"),
        ]
        
        for icon, title, value in stats_data:
            stat_card = self.create_stat_card(icon, title, value)
            stats_layout.addWidget(stat_card)
            
        right_layout.addLayout(stats_layout)
        
        # Arama ve filtreleme
        search_layout = QHBoxLayout()
        
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("🔍 Müşteri ara...")
        search_layout.addWidget(search_edit)
        
        filter_combo = QComboBox()
        filter_combo.addItems(["Tüm Durumlar", "Aktif", "Potansiyel", "Pasif"])
        search_layout.addWidget(filter_combo)
        
        right_layout.addLayout(search_layout)
        
        # Müşteri tablosu
        customers_group = QGroupBox("📋 Müşteri Listesi")
        customers_layout = QVBoxLayout(customers_group)
        
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(6)
        self.customer_table.setHorizontalHeaderLabels([
            "Ad Soyad", "Şirket", "E-posta", "Telefon", "Tür", "Durum"
        ])
        
        # Tablo ayarları
        header = self.customer_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        self.customer_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.customer_table.setAlternatingRowColors(True)
        self.customer_table.itemSelectionChanged.connect(self.on_customer_selected)
        
        customers_layout.addWidget(self.customer_table)
        right_layout.addWidget(customers_group)
        
        layout.addWidget(right_panel, 2)
        
        return widget
        
    def create_opportunities_tab(self):
        """Satış fırsatları sekmesini oluşturur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Üst panel - Yeni fırsat formu
        opportunity_group = QGroupBox("💼 Satış Fırsatı Yönetimi")
        opportunity_layout = QFormLayout(opportunity_group)
        
        self.opp_name_edit = QLineEdit()
        self.opp_customer_combo = QComboBox()
        self.opp_customer_combo.addItems(["Ahmet Yılmaz", "Fatma Demir", "Mehmet Kaya", "Ayşe Özkan"])
        
        self.opp_value_spin = QSpinBox()
        self.opp_value_spin.setRange(0, 10000000)
        self.opp_value_spin.setSuffix(" ₺")
        self.opp_value_spin.setValue(50000)
        
        self.opp_stage_combo = QComboBox()
        self.opp_stage_combo.addItems([
            "🎯 Hedef Belirleme", "📞 İlk İletişim", "💬 Görüşme", 
            "📋 Teklif Hazırlama", "🤝 Müzakere", "✅ Kapanış"
        ])
        
        self.opp_probability_slider = QSlider(Qt.Horizontal)
        self.opp_probability_slider.setRange(0, 100)
        self.opp_probability_slider.setValue(50)
        self.opp_probability_slider.valueChanged.connect(self.update_probability_label)
        
        self.probability_label = QLabel("50%")
        probability_layout = QHBoxLayout()
        probability_layout.addWidget(self.opp_probability_slider)
        probability_layout.addWidget(self.probability_label)
        
        self.opp_close_date = QDateEdit()
        self.opp_close_date.setDate(QDate.currentDate().addDays(30))
        
        self.opp_notes_edit = QTextEdit()
        self.opp_notes_edit.setMaximumHeight(80)
        
        opportunity_layout.addRow("Fırsat Adı:", self.opp_name_edit)
        opportunity_layout.addRow("Müşteri:", self.opp_customer_combo)
        opportunity_layout.addRow("Değer:", self.opp_value_spin)
        opportunity_layout.addRow("Aşama:", self.opp_stage_combo)
        opportunity_layout.addRow("Başarı Olasılığı:", probability_layout)
        opportunity_layout.addRow("Kapanış Tarihi:", self.opp_close_date)
        opportunity_layout.addRow("Notlar:", self.opp_notes_edit)
        
        # Fırsat butonları
        opp_buttons_layout = QHBoxLayout()
        add_opp_btn = QPushButton("➕ Fırsat Ekle")
        add_opp_btn.setObjectName("primaryButton")
        add_opp_btn.clicked.connect(self.add_opportunity)
        
        update_opp_btn = QPushButton("📝 Güncelle")
        update_opp_btn.clicked.connect(self.update_opportunity)
        
        opp_buttons_layout.addWidget(add_opp_btn)
        opp_buttons_layout.addWidget(update_opp_btn)
        opportunity_layout.addRow(opp_buttons_layout)
        
        layout.addWidget(opportunity_group)
        
        # Alt panel - Fırsat listesi
        opportunities_group = QGroupBox("📊 Aktif Satış Fırsatları")
        opportunities_layout = QVBoxLayout(opportunities_group)
        
        self.opp_table = QTableWidget()
        self.opp_table.setColumnCount(6)
        self.opp_table.setHorizontalHeaderLabels([
            "Fırsat", "Müşteri", "Değer", "Aşama", "Olasılık", "Kapanış Tarihi"
        ])
        
        # Tablo ayarları
        opp_header = self.opp_table.horizontalHeader()
        opp_header.setStretchLastSection(True)
        opp_header.setSectionResizeMode(QHeaderView.Interactive)
        
        self.opp_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.opp_table.setAlternatingRowColors(True)
        self.opp_table.itemSelectionChanged.connect(self.on_opportunity_selected)
        
        opportunities_layout.addWidget(self.opp_table)
        layout.addWidget(opportunities_group)
        
        return widget
        
    def create_tasks_tab(self):
        """Görevler sekmesini oluşturur"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Sol panel - Görev formu
        task_group = QGroupBox("✅ Görev Yönetimi")
        task_layout = QFormLayout(task_group)
        
        self.task_title_edit = QLineEdit()
        self.task_description_edit = QTextEdit()
        self.task_description_edit.setMaximumHeight(100)
        
        self.task_assignee_combo = QComboBox()
        self.task_assignee_combo.addItems(["Ben", "Ahmet Yılmaz", "Fatma Demir", "Mehmet Kaya"])
        
        self.task_priority_combo = QComboBox()
        self.task_priority_combo.addItems(["🔴 Yüksek", "🟡 Orta", "🟢 Düşük"])
        
        self.task_status_combo = QComboBox()
        self.task_status_combo.addItems(["📝 Bekliyor", "⏳ Devam Ediyor", "✅ Tamamlandı", "❌ İptal"])
        
        self.task_due_date = QDateEdit()
        self.task_due_date.setDate(QDate.currentDate().addDays(7))
        
        self.task_customer_combo = QComboBox()
        self.task_customer_combo.addItems(["Seçiniz...", "Ahmet Yılmaz", "Fatma Demir", "Mehmet Kaya"])
        
        task_layout.addRow("Görev Başlığı:", self.task_title_edit)
        task_layout.addRow("Açıklama:", self.task_description_edit)
        task_layout.addRow("Atanan Kişi:", self.task_assignee_combo)
        task_layout.addRow("Öncelik:", self.task_priority_combo)
        task_layout.addRow("Durum:", self.task_status_combo)
        task_layout.addRow("Bitiş Tarihi:", self.task_due_date)
        task_layout.addRow("İlgili Müşteri:", self.task_customer_combo)
        
        # Görev butonları
        task_buttons_layout = QHBoxLayout()
        add_task_btn = QPushButton("➕ Görev Ekle")
        add_task_btn.setObjectName("primaryButton")
        add_task_btn.clicked.connect(self.add_task)
        
        update_task_btn = QPushButton("📝 Güncelle")
        update_task_btn.clicked.connect(self.update_task)
        
        task_buttons_layout.addWidget(add_task_btn)
        task_buttons_layout.addWidget(update_task_btn)
        task_layout.addRow(task_buttons_layout)
        
        layout.addWidget(task_group, 1)
        
        # Sağ panel - Görev listesi
        tasks_group = QGroupBox("📋 Görev Listesi")
        tasks_layout = QVBoxLayout(tasks_group)
        
        # Görev filtreleme
        filter_layout = QHBoxLayout()
        
        status_filter = QComboBox()
        status_filter.addItems(["Tüm Durumlar", "Bekliyor", "Devam Ediyor", "Tamamlandı"])
        filter_layout.addWidget(QLabel("Durum:"))
        filter_layout.addWidget(status_filter)
        
        priority_filter = QComboBox()
        priority_filter.addItems(["Tüm Öncelikler", "Yüksek", "Orta", "Düşük"])
        filter_layout.addWidget(QLabel("Öncelik:"))
        filter_layout.addWidget(priority_filter)
        
        filter_layout.addStretch()
        tasks_layout.addLayout(filter_layout)
        
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(6)
        self.task_table.setHorizontalHeaderLabels([
            "Görev", "Atanan", "Öncelik", "Durum", "Bitiş Tarihi", "Müşteri"
        ])
        
        # Tablo ayarları
        task_header = self.task_table.horizontalHeader()
        task_header.setStretchLastSection(True)
        task_header.setSectionResizeMode(QHeaderView.Interactive)
        
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.itemSelectionChanged.connect(self.on_task_selected)
        
        tasks_layout.addWidget(self.task_table)
        layout.addWidget(tasks_group, 2)
        
        return widget
        
    def create_communication_tab(self):
        """İletişim geçmişi sekmesini oluşturur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Üst panel - Yeni iletişim kaydı
        comm_group = QGroupBox("📞 Yeni İletişim Kaydı")
        comm_layout = QFormLayout(comm_group)
        
        self.comm_customer_combo = QComboBox()
        self.comm_customer_combo.addItems(["Ahmet Yılmaz", "Fatma Demir", "Mehmet Kaya"])
        
        self.comm_type_combo = QComboBox()
        self.comm_type_combo.addItems(["📞 Telefon", "📧 E-posta", "💬 Toplantı", "📱 SMS", "🤝 Yüz Yüze"])
        
        self.comm_subject_edit = QLineEdit()
        
        self.comm_notes_edit = QTextEdit()
        self.comm_notes_edit.setMaximumHeight(100)
        
        self.comm_date = QDateEdit()
        self.comm_date.setDate(QDate.currentDate())
        
        self.comm_follow_up = QCheckBox("Takip gerekli")
        
        comm_layout.addRow("Müşteri:", self.comm_customer_combo)
        comm_layout.addRow("İletişim Türü:", self.comm_type_combo)
        comm_layout.addRow("Konu:", self.comm_subject_edit)
        comm_layout.addRow("Notlar:", self.comm_notes_edit)
        comm_layout.addRow("Tarih:", self.comm_date)
        comm_layout.addRow("", self.comm_follow_up)
        
        # İletişim butonları
        comm_buttons_layout = QHBoxLayout()
        add_comm_btn = QPushButton("➕ Kayıt Ekle")
        add_comm_btn.setObjectName("primaryButton")
        add_comm_btn.clicked.connect(self.add_communication)
        
        comm_buttons_layout.addWidget(add_comm_btn)
        comm_layout.addRow(comm_buttons_layout)
        
        layout.addWidget(comm_group)
        
        # Alt panel - İletişim geçmişi
        history_group = QGroupBox("📋 İletişim Geçmişi")
        history_layout = QVBoxLayout(history_group)
        
        self.comm_table = QTableWidget()
        self.comm_table.setColumnCount(6)
        self.comm_table.setHorizontalHeaderLabels([
            "Tarih", "Müşteri", "Tür", "Konu", "Notlar", "Takip"
        ])
        
        # Tablo ayarları
        comm_header = self.comm_table.horizontalHeader()
        comm_header.setStretchLastSection(True)
        comm_header.setSectionResizeMode(QHeaderView.Interactive)
        
        self.comm_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.comm_table.setAlternatingRowColors(True)
        
        history_layout.addWidget(self.comm_table)
        layout.addWidget(history_group)
        
        return widget
        
    def create_reports_tab(self):
        """Raporlar sekmesini oluşturur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Üst panel - Rapor seçenekleri
        report_options_group = QGroupBox("📊 Rapor Seçenekleri")
        options_layout = QHBoxLayout(report_options_group)
        
        # Rapor türü seçimi
        report_type_layout = QVBoxLayout()
        report_type_layout.addWidget(QLabel("Rapor Türü:"))
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Müşteri Özeti", "Satış Fırsatları", "Görev Durumu", 
            "İletişim Analizi", "Performans Raporu"
        ])
        report_type_layout.addWidget(self.report_type_combo)
        
        # Tarih aralığı
        date_range_layout = QVBoxLayout()
        date_range_layout.addWidget(QLabel("Tarih Aralığı:"))
        
        date_layout = QHBoxLayout()
        self.report_start_date = QDateEdit()
        self.report_start_date.setDate(QDate.currentDate().addDays(-30))
        self.report_end_date = QDateEdit()
        self.report_end_date.setDate(QDate.currentDate())
        
        date_layout.addWidget(QLabel("Başlangıç:"))
        date_layout.addWidget(self.report_start_date)
        date_layout.addWidget(QLabel("Bitiş:"))
        date_layout.addWidget(self.report_end_date)
        
        date_range_layout.addLayout(date_layout)
        
        # Rapor butonları
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(QLabel("İşlemler:"))
        
        generate_btn = QPushButton("📈 Rapor Oluştur")
        generate_btn.setObjectName("primaryButton")
        generate_btn.clicked.connect(self.generate_report)
        
        export_btn = QPushButton("📤 Excel'e Aktar")
        export_btn.clicked.connect(self.export_report)
        
        buttons_layout.addWidget(generate_btn)
        buttons_layout.addWidget(export_btn)
        
        options_layout.addLayout(report_type_layout)
        options_layout.addLayout(date_range_layout)
        options_layout.addLayout(buttons_layout)
        options_layout.addStretch()
        
        layout.addWidget(report_options_group)
        
        # Alt panel - Rapor görüntüleme alanı
        report_display_group = QGroupBox("📋 Rapor Sonuçları")
        display_layout = QVBoxLayout(report_display_group)
        
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setPlainText("Rapor oluşturmak için yukarıdaki seçenekleri kullanın.")
        
        display_layout.addWidget(self.report_text)
        layout.addWidget(report_display_group)
        
        return widget
        
    def create_status_bar(self):
        """Alt durum çubuğunu oluşturur"""
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_layout = QHBoxLayout(status_frame)
        
        self.status_label = QLabel("Hazır")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Kullanıcı bilgisi
        user_label = QLabel("👤 Kullanıcı: Admin")
        status_layout.addWidget(user_label)
        
        # Tarih/saat
        from datetime import datetime
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        time_label = QLabel(f"🕒 {current_time}")
        status_layout.addWidget(time_label)
        
        return status_frame
        
    def create_stat_card(self, icon, title, value):
        """İstatistik kartı oluşturur"""
        card = QFrame()
        card.setObjectName("statCard")
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        
        # İkon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px; margin-bottom: 5px;")
        card_layout.addWidget(icon_label)
        
        # Başlık
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("statTitle")
        card_layout.addWidget(title_label)
        
        # Değer
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName("statValue")
        card_layout.addWidget(value_label)
        
        return card
        
    def load_sample_data(self):
        """Örnek verileri yükler"""
        # Müşteri verileri
        customers_data = [
            ("Ahmet Yılmaz", "ABC Şirketi", "ahmet@abc.com", "0532 123 4567", "Kurumsal", "🟢 Aktif"),
            ("Fatma Demir", "XYZ Ltd.", "fatma@xyz.com", "0533 234 5678", "Kurumsal", "🟡 Potansiyel"),
            ("Mehmet Kaya", "DEF A.Ş.", "mehmet@def.com", "0534 345 6789", "Kurumsal", "🟢 Aktif"),
            ("Ayşe Özkan", "-", "ayse@email.com", "0535 456 7890", "Bireysel", "🟢 Aktif"),
            ("Ali Veli", "GHI Holding", "ali@ghi.com", "0536 567 8901", "Partner", "🔴 Pasif"),
        ]
        
        self.customer_table.setRowCount(len(customers_data))
        for row, customer in enumerate(customers_data):
            for col, data in enumerate(customer):
                self.customer_table.setItem(row, col, QTableWidgetItem(data))
                
        # Satış fırsatları verileri
        opportunities_data = [
            ("Web Sitesi Projesi", "ABC Şirketi", "₺50,000", "💬 Görüşme", "%75", "15.02.2024"),
            ("ERP Sistemi", "XYZ Ltd.", "₺150,000", "📋 Teklif Hazırlama", "%60", "28.02.2024"),
            ("Mobil Uygulama", "DEF A.Ş.", "₺80,000", "🎯 Hedef Belirleme", "%25", "10.03.2024"),
            ("E-ticaret Platformu", "GHI Holding", "₺120,000", "🤝 Müzakere", "%85", "05.03.2024"),
        ]
        
        self.opp_table.setRowCount(len(opportunities_data))
        for row, opp in enumerate(opportunities_data):
            for col, data in enumerate(opp):
                self.opp_table.setItem(row, col, QTableWidgetItem(data))
                
        # Görev verileri
        tasks_data = [
            ("Müşteri araması", "Ahmet Yılmaz", "🔴 Yüksek", "⏳ Devam Ediyor", "20.01.2024", "ABC Şirketi"),
            ("Teklif hazırlama", "Fatma Demir", "🟡 Orta", "✅ Tamamlandı", "22.01.2024", "XYZ Ltd."),
            ("Demo hazırlığı", "Mehmet Kaya", "🟢 Düşük", "📝 Bekliyor", "25.01.2024", "DEF A.Ş."),
            ("Sözleşme gönderimi", "Ben", "🔴 Yüksek", "⏳ Devam Ediyor", "18.01.2024", "GHI Holding"),
        ]
        
        self.task_table.setRowCount(len(tasks_data))
        for row, task in enumerate(tasks_data):
            for col, data in enumerate(task):
                self.task_table.setItem(row, col, QTableWidgetItem(data))
                
        # İletişim geçmişi verileri
        communication_data = [
            ("15.01.2024", "Ahmet Yılmaz", "📞 Telefon", "Proje görüşmesi", "Olumlu geri dönüş", "✅"),
            ("14.01.2024", "Fatma Demir", "📧 E-posta", "Teklif gönderimi", "Teklif gönderildi", "❌"),
            ("13.01.2024", "Mehmet Kaya", "💬 Toplantı", "İhtiyaç analizi", "Detaylı görüşme yapıldı", "✅"),
            ("12.01.2024", "Ayşe Özkan", "📱 SMS", "Randevu hatırlatması", "Randevu onaylandı", "❌"),
        ]
        
        self.comm_table.setRowCount(len(communication_data))
        for row, comm in enumerate(communication_data):
            for col, data in enumerate(comm):
                self.comm_table.setItem(row, col, QTableWidgetItem(data))
                
    def setup_styles(self):
        """Stil tanımlamaları"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            #headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #dc3545, stop:1 #c82333);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 10px;
            }
            
            #headerTitle {
                font-size: 28px;
                font-weight: bold;
                color: white;
                margin-bottom: 5px;
            }
            
            #headerSubtitle {
                font-size: 14px;
                color: rgba(255, 255, 255, 0.9);
            }
            
            #mainTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
                border-radius: 8px;
                margin-top: 5px;
            }
            
            #mainTabWidget::tab-bar {
                alignment: left;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 3px solid #dc3545;
                color: #dc3545;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #f8f9fa;
            }
            
            #statCard {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
                min-height: 100px;
                max-width: 120px;
            }
            
            #statCard:hover {
                border-color: #dc3545;
                box-shadow: 0 4px 8px rgba(220, 53, 69, 0.2);
            }
            
            #statTitle {
                font-size: 12px;
                color: #6c757d;
                font-weight: bold;
            }
            
            #statValue {
                font-size: 20px;
                color: #dc3545;
                font-weight: bold;
            }
            
            #primaryButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            
            #primaryButton:hover {
                background-color: #c82333;
            }
            
            #primaryButton:pressed {
                background-color: #bd2130;
            }
            
            #secondaryButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            
            #secondaryButton:hover {
                background-color: #5a6268;
            }
            
            #dangerButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            
            #dangerButton:hover {
                background-color: #c82333;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: white;
                font-size: 14px;
                color: #495057;
            }
            
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                gridline-color: #e9ecef;
                selection-background-color: #dc3545;
                selection-color: white;
            }
            
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f8f9fa;
            }
            
            QTableWidget::item:selected {
                background-color: #dc3545;
                color: white;
            }
            
            QTableWidget::item:hover {
                background-color: #f8f9fa;
            }
            
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 8px;
                border: none;
                border-right: 1px solid #dee2e6;
                font-weight: bold;
                color: #495057;
            }
            
            QLineEdit, QComboBox, QDateEdit, QSpinBox {
                padding: 8px 12px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
            }
            
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {
                border-color: #dc3545;
                outline: none;
            }
            
            QTextEdit {
                border: 2px solid #ced4da;
                border-radius: 6px;
                background-color: white;
                padding: 8px;
                font-size: 14px;
            }
            
            QTextEdit:focus {
                border-color: #dc3545;
            }
            
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 10px;
                border-radius: 4px;
            }
            
            QSlider::sub-page:horizontal {
                background: #dc3545;
                border: 1px solid #777;
                height: 10px;
                border-radius: 4px;
            }
            
            QSlider::add-page:horizontal {
                background: #fff;
                border: 1px solid #777;
                height: 10px;
                border-radius: 4px;
            }
            
            QSlider::handle:horizontal {
                background: #dc3545;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
            
            QCheckBox {
                font-size: 14px;
                color: #495057;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 2px solid #ced4da;
                background-color: white;
                border-radius: 3px;
            }
            
            QCheckBox::indicator:checked {
                border: 2px solid #dc3545;
                background-color: #dc3545;
                border-radius: 3px;
            }
            
            #statusFrame {
                background-color: #e9ecef;
                padding: 8px 15px;
                border-radius: 6px;
                margin-top: 10px;
                border: 1px solid #dee2e6;
            }
        """)
        
    # Event handlers
    def on_customer_selected(self):
        """Müşteri seçildiğinde çalışır"""
        current_row = self.customer_table.currentRow()
        if current_row >= 0:
            name = self.customer_table.item(current_row, 0).text()
            company = self.customer_table.item(current_row, 1).text()
            email = self.customer_table.item(current_row, 2).text()
            phone = self.customer_table.item(current_row, 3).text()
            customer_type = self.customer_table.item(current_row, 4).text()
            status = self.customer_table.item(current_row, 5).text()
            
            # Formu doldur
            self.customer_name_edit.setText(name)
            self.customer_company_edit.setText(company)
            self.customer_email_edit.setText(email)
            self.customer_phone_edit.setText(phone)
            
            # ComboBox'ları ayarla
            type_index = self.customer_type_combo.findText(customer_type)
            if type_index >= 0:
                self.customer_type_combo.setCurrentIndex(type_index)
                
            status_index = self.customer_status_combo.findText(status)
            if status_index >= 0:
                self.customer_status_combo.setCurrentIndex(status_index)
                
            self.status_label.setText(f"Seçili müşteri: {name}")
            
    def on_opportunity_selected(self):
        """Fırsat seçildiğinde çalışır"""
        current_row = self.opp_table.currentRow()
        if current_row >= 0:
            name = self.opp_table.item(current_row, 0).text()
            self.status_label.setText(f"Seçili fırsat: {name}")
            
    def on_task_selected(self):
        """Görev seçildiğinde çalışır"""
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            title = self.task_table.item(current_row, 0).text()
            self.status_label.setText(f"Seçili görev: {title}")
            
    def update_probability_label(self, value):
        """Olasılık slider'ı değiştiğinde label'ı günceller"""
        self.probability_label.setText(f"{value}%")
        
    # Action methods
    def add_new_customer(self):
        """Yeni müşteri ekleme"""
        self.clear_customer_form()
        self.tab_widget.setCurrentIndex(0)  # Müşteriler sekmesine geç
        self.customer_name_edit.setFocus()
        self.status_label.setText("Yeni müşteri ekleme modu")
        
    def add_new_opportunity(self):
        """Yeni fırsat ekleme"""
        self.tab_widget.setCurrentIndex(1)  # Fırsatlar sekmesine geç
        self.opp_name_edit.setFocus()
        self.status_label.setText("Yeni fırsat ekleme modu")
        
    def save_customer(self):
        """Müşteri kaydetme"""
        name = self.customer_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Müşteri adı boş olamaz!")
            return
            
        # Yeni satır ekle
        row_count = self.customer_table.rowCount()
        self.customer_table.insertRow(row_count)
        
        # Verileri tabloya ekle
        self.customer_table.setItem(row_count, 0, QTableWidgetItem(name))
        self.customer_table.setItem(row_count, 1, QTableWidgetItem(self.customer_company_edit.text()))
        self.customer_table.setItem(row_count, 2, QTableWidgetItem(self.customer_email_edit.text()))
        self.customer_table.setItem(row_count, 3, QTableWidgetItem(self.customer_phone_edit.text()))
        self.customer_table.setItem(row_count, 4, QTableWidgetItem(self.customer_type_combo.currentText()))
        self.customer_table.setItem(row_count, 5, QTableWidgetItem(self.customer_status_combo.currentText()))
        
        self.status_label.setText(f"Müşteri '{name}' başarıyla kaydedildi")
        QMessageBox.information(self, "Başarılı", f"Müşteri '{name}' başarıyla kaydedildi!")
        
    def clear_customer_form(self):
        """Müşteri formunu temizle"""
        self.customer_name_edit.clear()
        self.customer_email_edit.clear()
        self.customer_phone_edit.clear()
        self.customer_company_edit.clear()
        self.customer_position_edit.clear()
        self.customer_address_edit.clear()
        self.customer_type_combo.setCurrentIndex(0)
        self.customer_status_combo.setCurrentIndex(0)
        
    def delete_customer(self):
        """Seçili müşteriyi sil"""
        current_row = self.customer_table.currentRow()
        if current_row >= 0:
            name = self.customer_table.item(current_row, 0).text()
            reply = QMessageBox.question(self, "Silme Onayı", 
                                       f"'{name}' müşterisini silmek istediğinizden emin misiniz?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.customer_table.removeRow(current_row)
                self.clear_customer_form()
                self.status_label.setText(f"Müşteri '{name}' silindi")
        else:
            QMessageBox.warning(self, "Uyarı", "Silinecek müşteri seçiniz!")
            
    def add_opportunity(self):
        """Fırsat ekleme"""
        name = self.opp_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Fırsat adı boş olamaz!")
            return
            
        row_count = self.opp_table.rowCount()
        self.opp_table.insertRow(row_count)
        
        self.opp_table.setItem(row_count, 0, QTableWidgetItem(name))
        self.opp_table.setItem(row_count, 1, QTableWidgetItem(self.opp_customer_combo.currentText()))
        self.opp_table.setItem(row_count, 2, QTableWidgetItem(f"₺{self.opp_value_spin.value():,}"))
        self.opp_table.setItem(row_count, 3, QTableWidgetItem(self.opp_stage_combo.currentText()))
        self.opp_table.setItem(row_count, 4, QTableWidgetItem(f"%{self.opp_probability_slider.value()}"))
        self.opp_table.setItem(row_count, 5, QTableWidgetItem(self.opp_close_date.date().toString("dd.MM.yyyy")))
        
        self.status_label.setText(f"Fırsat '{name}' başarıyla eklendi")
        QMessageBox.information(self, "Başarılı", f"Fırsat '{name}' başarıyla eklendi!")
        
    def update_opportunity(self):
        """Fırsat güncelleme"""
        current_row = self.opp_table.currentRow()
        if current_row >= 0:
            name = self.opp_name_edit.text().strip()
            if name:
                self.opp_table.setItem(current_row, 0, QTableWidgetItem(name))
                self.opp_table.setItem(current_row, 1, QTableWidgetItem(self.opp_customer_combo.currentText()))
                self.opp_table.setItem(current_row, 2, QTableWidgetItem(f"₺{self.opp_value_spin.value():,}"))
                self.opp_table.setItem(current_row, 3, QTableWidgetItem(self.opp_stage_combo.currentText()))
                self.opp_table.setItem(current_row, 4, QTableWidgetItem(f"%{self.opp_probability_slider.value()}"))
                self.opp_table.setItem(current_row, 5, QTableWidgetItem(self.opp_close_date.date().toString("dd.MM.yyyy")))
                
                self.status_label.setText(f"Fırsat '{name}' güncellendi")
                QMessageBox.information(self, "Başarılı", f"Fırsat '{name}' başarıyla güncellendi!")
        else:
            QMessageBox.warning(self, "Uyarı", "Güncellenecek fırsat seçiniz!")
            
    def add_task(self):
        """Görev ekleme"""
        title = self.task_title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Uyarı", "Görev başlığı boş olamaz!")
            return
            
        row_count = self.task_table.rowCount()
        self.task_table.insertRow(row_count)
        
        self.task_table.setItem(row_count, 0, QTableWidgetItem(title))
        self.task_table.setItem(row_count, 1, QTableWidgetItem(self.task_assignee_combo.currentText()))
        self.task_table.setItem(row_count, 2, QTableWidgetItem(self.task_priority_combo.currentText()))
        self.task_table.setItem(row_count, 3, QTableWidgetItem(self.task_status_combo.currentText()))
        self.task_table.setItem(row_count, 4, QTableWidgetItem(self.task_due_date.date().toString("dd.MM.yyyy")))
        self.task_table.setItem(row_count, 5, QTableWidgetItem(self.task_customer_combo.currentText()))
        
        self.status_label.setText(f"Görev '{title}' başarıyla eklendi")
        QMessageBox.information(self, "Başarılı", f"Görev '{title}' başarıyla eklendi!")
        
    def update_task(self):
        """Görev güncelleme"""
        current_row = self.task_table.currentRow()
        if current_row >= 0:
            title = self.task_title_edit.text().strip()
            if title:
                self.task_table.setItem(current_row, 0, QTableWidgetItem(title))
                self.task_table.setItem(current_row, 1, QTableWidgetItem(self.task_assignee_combo.currentText()))
                self.task_table.setItem(current_row, 2, QTableWidgetItem(self.task_priority_combo.currentText()))
                self.task_table.setItem(current_row, 3, QTableWidgetItem(self.task_status_combo.currentText()))
                self.task_table.setItem(current_row, 4, QTableWidgetItem(self.task_due_date.date().toString("dd.MM.yyyy")))
                self.task_table.setItem(current_row, 5, QTableWidgetItem(self.task_customer_combo.currentText()))
                
                self.status_label.setText(f"Görev '{title}' güncellendi")
                QMessageBox.information(self, "Başarılı", f"Görev '{title}' başarıyla güncellendi!")
        else:
            QMessageBox.warning(self, "Uyarı", "Güncellenecek görev seçiniz!")
            
    def add_communication(self):
        """İletişim kaydı ekleme"""
        subject = self.comm_subject_edit.text().strip()
        if not subject:
            QMessageBox.warning(self, "Uyarı", "Konu boş olamaz!")
            return
            
        row_count = self.comm_table.rowCount()
        self.comm_table.insertRow(row_count)
        
        self.comm_table.setItem(row_count, 0, QTableWidgetItem(self.comm_date.date().toString("dd.MM.yyyy")))
        self.comm_table.setItem(row_count, 1, QTableWidgetItem(self.comm_customer_combo.currentText()))
        self.comm_table.setItem(row_count, 2, QTableWidgetItem(self.comm_type_combo.currentText()))
        self.comm_table.setItem(row_count, 3, QTableWidgetItem(subject))
        self.comm_table.setItem(row_count, 4, QTableWidgetItem(self.comm_notes_edit.toPlainText()[:50] + "..."))
        self.comm_table.setItem(row_count, 5, QTableWidgetItem("✅" if self.comm_follow_up.isChecked() else "❌"))
        
        self.status_label.setText(f"İletişim kaydı '{subject}' eklendi")
        QMessageBox.information(self, "Başarılı", f"İletişim kaydı başarıyla eklendi!")
        
    def generate_report(self):
        """Rapor oluşturma"""
        report_type = self.report_type_combo.currentText()
        start_date = self.report_start_date.date().toString("dd.MM.yyyy")
        end_date = self.report_end_date.date().toString("dd.MM.yyyy")
        
        report_content = f"""
📊 {report_type} RAPORU
═══════════════════════════════════════

📅 Rapor Tarihi: {start_date} - {end_date}
🕒 Oluşturulma Zamanı: {QDate.currentDate().toString("dd.MM.yyyy")}

📈 ÖZET BİLGİLER:
─────────────────────────────────────────
• Toplam Müşteri: 1,234
• Aktif Müşteri: 987 (%80.0)
• Potansiyel Müşteri: 156 (%12.6)
• Pasif Müşteri: 91 (%7.4)

💼 SATIŞ FIRSATLARI:
─────────────────────────────────────────
• Toplam Fırsat: 24
• Toplam Değer: ₺2,450,000
• Ortalama Fırsat Değeri: ₺102,083
• Kapanış Oranı: %68.5

✅ GÖREV DURUMU:
─────────────────────────────────────────
• Toplam Görev: 156
• Tamamlanan: 89 (%57.1)
• Devam Eden: 45 (%28.8)
• Bekleyen: 22 (%14.1)

📞 İLETİŞİM ANALİZİ:
─────────────────────────────────────────
• Toplam İletişim: 342
• Telefon: 145 (%42.4)
• E-posta: 98 (%28.7)
• Toplantı: 67 (%19.6)
• SMS: 32 (%9.4)

🎯 ÖNERİLER:
─────────────────────────────────────────
1. Potansiyel müşterilere odaklanın
2. Pasif müşterileri yeniden aktive edin
3. Görev tamamlama oranını artırın
4. İletişim sıklığını optimize edin

═══════════════════════════════════════
Bu rapor CRM sistemi tarafından otomatik olarak oluşturulmuştur.
        """
        
        self.report_text.setPlainText(report_content)
        self.status_label.setText(f"'{report_type}' raporu oluşturuldu")
        
    def export_report(self):
        """Raporu Excel'e aktarma"""
        QMessageBox.information(self, "Bilgi", "Rapor Excel dosyasına aktarıldı!\n\nDosya konumu: Belgeler/CRM_Raporu.xlsx")
        self.status_label.setText("Rapor Excel'e aktarıldı")

def main():
    """Ana fonksiyon"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Uygulama bilgileri
    app.setApplicationName("CRM Modülü")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("İş Yönetim Sistemi")
    
    # Ana pencereyi oluştur ve göster
    crm_window = CRMModule()
    crm_window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

