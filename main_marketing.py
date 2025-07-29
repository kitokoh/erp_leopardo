#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
                             QTextEdit, QTableWidget, QTableWidgetItem, QTabWidget,
                             QSplitter, QGroupBox, QFormLayout, QLineEdit, QComboBox,
                             QDateEdit, QSpinBox, QCheckBox, QProgressBar, QSlider,
                             QListWidget, QTreeWidget, QTreeWidgetItem, QScrollArea,
                             QHeaderView, QMessageBox, QListWidgetItem)
from PyQt5.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap

class MarketingModule(QMainWindow):
    """
    Marketing Modülü
    Bu sınıf, pazarlama kampanyaları, sosyal medya yönetimi ve analytics özelliklerini içerir.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📈 Marketing - Pazarlama Yönetimi")
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
        
        # Kampanyalar sekmesi
        campaigns_tab = self.create_campaigns_tab()
        self.tab_widget.addTab(campaigns_tab, "🎯 Kampanyalar")
        
        # Sosyal medya sekmesi
        social_tab = self.create_social_media_tab()
        self.tab_widget.addTab(social_tab, "📱 Sosyal Medya")
        
        # E-posta pazarlama sekmesi
        email_tab = self.create_email_marketing_tab()
        self.tab_widget.addTab(email_tab, "📧 E-posta Pazarlama")
        
        # Analytics sekmesi
        analytics_tab = self.create_analytics_tab()
        self.tab_widget.addTab(analytics_tab, "📊 Analytics")
        
        # İçerik yönetimi sekmesi
        content_tab = self.create_content_management_tab()
        self.tab_widget.addTab(content_tab, "📝 İçerik Yönetimi")
        
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
        
        title_label = QLabel("📈 Marketing - Pazarlama Yönetimi")
        title_label.setObjectName("headerTitle")
        left_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Kampanyalarınızı yönetin, sosyal medyayı takip edin, performansı analiz edin")
        subtitle_label.setObjectName("headerSubtitle")
        left_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(left_layout)
        header_layout.addStretch()
        
        # Sağ taraf - Hızlı eylemler
        quick_actions_layout = QHBoxLayout()
        
        new_campaign_btn = QPushButton("🎯 Yeni Kampanya")
        new_campaign_btn.setObjectName("primaryButton")
        new_campaign_btn.clicked.connect(self.create_new_campaign)
        quick_actions_layout.addWidget(new_campaign_btn)
        
        new_post_btn = QPushButton("📱 Yeni Post")
        new_post_btn.setObjectName("secondaryButton")
        new_post_btn.clicked.connect(self.create_new_post)
        quick_actions_layout.addWidget(new_post_btn)
        
        header_layout.addLayout(quick_actions_layout)
        
        return header_frame
        
    def create_campaigns_tab(self):
        """Kampanyalar sekmesini oluşturur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Üst panel - Kampanya oluşturma formu
        campaign_group = QGroupBox("🎯 Kampanya Yönetimi")
        campaign_layout = QFormLayout(campaign_group)
        
        self.campaign_name_edit = QLineEdit()
        self.campaign_type_combo = QComboBox()
        self.campaign_type_combo.addItems([
            "E-posta Kampanyası", "SMS Kampanyası", "Sosyal Medya", 
            "Google Ads", "Facebook Ads", "İnfluencer", "Etkinlik"
        ])
        
        self.campaign_budget_spin = QSpinBox()
        self.campaign_budget_spin.setRange(0, 1000000)
        self.campaign_budget_spin.setSuffix(" ₺")
        self.campaign_budget_spin.setValue(10000)
        
        self.campaign_start_date = QDateEdit()
        self.campaign_start_date.setDate(QDate.currentDate())
        
        self.campaign_end_date = QDateEdit()
        self.campaign_end_date.setDate(QDate.currentDate().addDays(30))
        
        self.campaign_target_combo = QComboBox()
        self.campaign_target_combo.addItems([
            "Tüm Müşteriler", "Yeni Müşteriler", "Mevcut Müşteriler", 
            "VIP Müşteriler", "18-25 Yaş", "26-35 Yaş", "36+ Yaş"
        ])
        
        self.campaign_description_edit = QTextEdit()
        self.campaign_description_edit.setMaximumHeight(80)
        
        campaign_layout.addRow("Kampanya Adı:", self.campaign_name_edit)
        campaign_layout.addRow("Kampanya Türü:", self.campaign_type_combo)
        campaign_layout.addRow("Bütçe:", self.campaign_budget_spin)
        campaign_layout.addRow("Başlangıç Tarihi:", self.campaign_start_date)
        campaign_layout.addRow("Bitiş Tarihi:", self.campaign_end_date)
        campaign_layout.addRow("Hedef Kitle:", self.campaign_target_combo)
        campaign_layout.addRow("Açıklama:", self.campaign_description_edit)
        
        # Kampanya butonları
        campaign_buttons_layout = QHBoxLayout()
        create_campaign_btn = QPushButton("✨ Kampanya Oluştur")
        create_campaign_btn.setObjectName("primaryButton")
        create_campaign_btn.clicked.connect(self.create_campaign)
        
        update_campaign_btn = QPushButton("📝 Güncelle")
        update_campaign_btn.clicked.connect(self.update_campaign)
        
        campaign_buttons_layout.addWidget(create_campaign_btn)
        campaign_buttons_layout.addWidget(update_campaign_btn)
        campaign_layout.addRow(campaign_buttons_layout)
        
        layout.addWidget(campaign_group)
        
        # Alt panel - Kampanya listesi ve performans
        bottom_layout = QHBoxLayout()
        
        # Sol taraf - Kampanya listesi
        campaigns_list_group = QGroupBox("📋 Aktif Kampanyalar")
        campaigns_list_layout = QVBoxLayout(campaigns_list_group)
        
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(6)
        self.campaigns_table.setHorizontalHeaderLabels([
            "Kampanya", "Tür", "Durum", "Bütçe", "Harcanan", "ROI"
        ])
        
        # Tablo ayarları
        campaigns_header = self.campaigns_table.horizontalHeader()
        campaigns_header.setStretchLastSection(True)
        campaigns_header.setSectionResizeMode(QHeaderView.Interactive)
        
        self.campaigns_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.campaigns_table.setAlternatingRowColors(True)
        self.campaigns_table.itemSelectionChanged.connect(self.on_campaign_selected)
        
        campaigns_list_layout.addWidget(self.campaigns_table)
        bottom_layout.addWidget(campaigns_list_group, 2)
        
        # Sağ taraf - Performans kartları
        performance_group = QGroupBox("📊 Performans Özeti")
        performance_layout = QVBoxLayout(performance_group)
        
        # Performans kartları
        perf_cards_layout = QVBoxLayout()
        
        perf_data = [
            ("👁️", "Görüntülenme", "45,678", "#17a2b8"),
            ("👆", "Tıklama", "3,456", "#28a745"),
            ("💰", "Dönüşüm", "234", "#ffc107"),
            ("📈", "CTR", "%7.6", "#dc3545"),
        ]
        
        for icon, title, value, color in perf_data:
            perf_card = self.create_performance_card(icon, title, value, color)
            perf_cards_layout.addWidget(perf_card)
            
        performance_layout.addLayout(perf_cards_layout)
        performance_layout.addStretch()
        
        bottom_layout.addWidget(performance_group, 1)
        layout.addLayout(bottom_layout)
        
        return widget
        
    def create_social_media_tab(self):
        """Sosyal medya sekmesini oluşturur"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(20)
        
        # Sol panel - Post oluşturma
        post_group = QGroupBox("📱 Yeni Post Oluştur")
        post_layout = QVBoxLayout(post_group)
        
        # Platform seçimi
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("Platform:"))
        
        self.platform_combo = QComboBox()
        self.platform_combo.addItems([
            "📘 Facebook", "📷 Instagram", "🐦 Twitter", 
            "💼 LinkedIn", "📺 YouTube", "📌 Pinterest"
        ])
        platform_layout.addWidget(self.platform_combo)
        platform_layout.addStretch()
        
        post_layout.addLayout(platform_layout)
        
        # Post içeriği
        post_layout.addWidget(QLabel("Post İçeriği:"))
        self.post_content_edit = QTextEdit()
        self.post_content_edit.setPlaceholderText("Post içeriğinizi buraya yazın...")
        self.post_content_edit.setMaximumHeight(120)
        post_layout.addWidget(self.post_content_edit)
        
        # Hashtag'ler
        post_layout.addWidget(QLabel("Hashtag'ler:"))
        self.hashtags_edit = QLineEdit()
        self.hashtags_edit.setPlaceholderText("#pazarlama #sosyalmedya #dijital")
        post_layout.addWidget(self.hashtags_edit)
        
        # Zamanlama
        schedule_layout = QHBoxLayout()
        self.schedule_check = QCheckBox("📅 Zamanla")
        schedule_layout.addWidget(self.schedule_check)
        
        self.schedule_date = QDateEdit()
        self.schedule_date.setDate(QDate.currentDate())
        self.schedule_date.setEnabled(False)
        schedule_layout.addWidget(self.schedule_date)
        
        self.schedule_check.toggled.connect(self.schedule_date.setEnabled)
        post_layout.addLayout(schedule_layout)
        
        # Post butonları
        post_buttons_layout = QHBoxLayout()
        post_now_btn = QPushButton("📤 Hemen Paylaş")
        post_now_btn.setObjectName("primaryButton")
        post_now_btn.clicked.connect(self.post_now)
        
        save_draft_btn = QPushButton("💾 Taslak Kaydet")
        save_draft_btn.clicked.connect(self.save_draft)
        
        post_buttons_layout.addWidget(post_now_btn)
        post_buttons_layout.addWidget(save_draft_btn)
        post_layout.addLayout(post_buttons_layout)
        
        post_layout.addStretch()
        layout.addWidget(post_group, 1)
        
        # Sağ panel - Sosyal medya istatistikleri
        stats_group = QGroupBox("📊 Sosyal Medya İstatistikleri")
        stats_layout = QVBoxLayout(stats_group)
        
        # Platform istatistikleri
        platforms_data = [
            ("📘 Facebook", "1,234 Takipçi", "89 Beğeni/Gün", "12 Paylaşım/Hafta"),
            ("📷 Instagram", "2,567 Takipçi", "156 Beğeni/Gün", "8 Post/Hafta"),
            ("🐦 Twitter", "987 Takipçi", "45 RT/Gün", "15 Tweet/Hafta"),
            ("💼 LinkedIn", "543 Bağlantı", "23 Etkileşim/Gün", "5 Post/Hafta"),
        ]
        
        for platform, followers, engagement, frequency in platforms_data:
            platform_frame = QFrame()
            platform_frame.setObjectName("platformFrame")
            platform_layout = QVBoxLayout(platform_frame)
            
            platform_header = QLabel(platform)
            platform_header.setObjectName("platformHeader")
            platform_layout.addWidget(platform_header)
            
            followers_label = QLabel(followers)
            followers_label.setObjectName("platformStat")
            platform_layout.addWidget(followers_label)
            
            engagement_label = QLabel(engagement)
            engagement_label.setObjectName("platformStat")
            platform_layout.addWidget(engagement_label)
            
            frequency_label = QLabel(frequency)
            frequency_label.setObjectName("platformStat")
            platform_layout.addWidget(frequency_label)
            
            stats_layout.addWidget(platform_frame)
            
        # Son postlar
        recent_posts_group = QGroupBox("📝 Son Postlar")
        recent_posts_layout = QVBoxLayout(recent_posts_group)
        
        self.recent_posts_list = QListWidget()
        recent_posts = [
            "📘 Facebook: Yeni ürün lansmanı duyurusu",
            "📷 Instagram: Ofis arkası fotoğrafları",
            "🐦 Twitter: Sektör haberleri paylaşımı",
            "💼 LinkedIn: Şirket başarı hikayesi",
        ]
        
        for post in recent_posts:
            self.recent_posts_list.addItem(post)
            
        recent_posts_layout.addWidget(self.recent_posts_list)
        stats_layout.addWidget(recent_posts_group)
        
        layout.addWidget(stats_group, 1)
        
        return widget
        
    def create_email_marketing_tab(self):
        """E-posta pazarlama sekmesini oluşturur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Üst panel - E-posta kampanyası oluşturma
        email_group = QGroupBox("📧 E-posta Kampanyası")
        email_layout = QFormLayout(email_group)
        
        self.email_subject_edit = QLineEdit()
        self.email_template_combo = QComboBox()
        self.email_template_combo.addItems([
            "Hoş Geldin E-postası", "Promosyon Duyurusu", "Haber Bülteni", 
            "Ürün Lansmanı", "Etkinlik Daveti", "Özel Template"
        ])
        
        self.email_recipient_combo = QComboBox()
        self.email_recipient_combo.addItems([
            "Tüm Aboneler", "Yeni Aboneler", "VIP Müşteriler", 
            "Aktif Müşteriler", "Özel Liste"
        ])
        
        self.email_send_date = QDateEdit()
        self.email_send_date.setDate(QDate.currentDate())
        
        email_layout.addRow("E-posta Konusu:", self.email_subject_edit)
        email_layout.addRow("Template:", self.email_template_combo)
        email_layout.addRow("Alıcı Grubu:", self.email_recipient_combo)
        email_layout.addRow("Gönderim Tarihi:", self.email_send_date)
        
        # E-posta içeriği
        email_layout.addRow("E-posta İçeriği:")
        self.email_content_edit = QTextEdit()
        self.email_content_edit.setMaximumHeight(150)
        self.email_content_edit.setPlaceholderText("E-posta içeriğinizi buraya yazın...")
        email_layout.addRow(self.email_content_edit)
        
        # E-posta butonları
        email_buttons_layout = QHBoxLayout()
        send_test_btn = QPushButton("🧪 Test Gönder")
        send_test_btn.clicked.connect(self.send_test_email)
        
        schedule_email_btn = QPushButton("📅 Zamanla")
        schedule_email_btn.clicked.connect(self.schedule_email)
        
        send_now_btn = QPushButton("📤 Hemen Gönder")
        send_now_btn.setObjectName("primaryButton")
        send_now_btn.clicked.connect(self.send_email_now)
        
        email_buttons_layout.addWidget(send_test_btn)
        email_buttons_layout.addWidget(schedule_email_btn)
        email_buttons_layout.addWidget(send_now_btn)
        email_layout.addRow(email_buttons_layout)
        
        layout.addWidget(email_group)
        
        # Alt panel - E-posta istatistikleri
        email_stats_layout = QHBoxLayout()
        
        # Sol taraf - Gönderim geçmişi
        history_group = QGroupBox("📋 Gönderim Geçmişi")
        history_layout = QVBoxLayout(history_group)
        
        self.email_history_table = QTableWidget()
        self.email_history_table.setColumnCount(5)
        self.email_history_table.setHorizontalHeaderLabels([
            "Konu", "Alıcı Sayısı", "Açılma Oranı", "Tıklama Oranı", "Tarih"
        ])
        
        history_layout.addWidget(self.email_history_table)
        email_stats_layout.addWidget(history_group, 2)
        
        # Sağ taraf - E-posta metrikleri
        metrics_group = QGroupBox("📊 E-posta Metrikleri")
        metrics_layout = QVBoxLayout(metrics_group)
        
        email_metrics = [
            ("📧", "Gönderilen", "12,456"),
            ("👁️", "Açılan", "8,234"),
            ("👆", "Tıklanan", "1,567"),
            ("📈", "Açılma Oranı", "%66.1"),
        ]
        
        for icon, title, value in email_metrics:
            metric_card = self.create_metric_card(icon, title, value)
            metrics_layout.addWidget(metric_card)
            
        metrics_layout.addStretch()
        email_stats_layout.addWidget(metrics_group, 1)
        
        layout.addLayout(email_stats_layout)
        
        return widget
        
    def create_analytics_tab(self):
        """Analytics sekmesini oluşturur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Üst panel - Metrikler
        metrics_layout = QHBoxLayout()
        
        analytics_metrics = [
            ("👁️", "Toplam Görüntülenme", "145,678", "#17a2b8"),
            ("👆", "Toplam Tıklama", "13,456", "#28a745"),
            ("💰", "Toplam Dönüşüm", "1,234", "#ffc107"),
            ("📈", "Ortalama CTR", "%9.2", "#dc3545"),
            ("💵", "Toplam Gelir", "₺234,567", "#6f42c1"),
            ("📊", "ROAS", "4.2x", "#fd7e14"),
        ]
        
        for icon, title, value, color in analytics_metrics:
            metric_card = self.create_analytics_card(icon, title, value, color)
            metrics_layout.addWidget(metric_card)
            
        layout.addLayout(metrics_layout)
        
        # Orta panel - Grafik alanı
        chart_group = QGroupBox("📈 Performans Grafikleri")
        chart_layout = QVBoxLayout(chart_group)
        
        # Grafik seçenekleri
        chart_options_layout = QHBoxLayout()
        
        chart_type_combo = QComboBox()
        chart_type_combo.addItems([
            "Günlük Performans", "Haftalık Trend", "Aylık Özet", 
            "Kanal Karşılaştırması", "Kampanya Analizi"
        ])
        chart_options_layout.addWidget(QLabel("Grafik Türü:"))
        chart_options_layout.addWidget(chart_type_combo)
        
        date_range_combo = QComboBox()
        date_range_combo.addItems([
            "Son 7 Gün", "Son 30 Gün", "Son 3 Ay", "Son Yıl", "Özel Aralık"
        ])
        chart_options_layout.addWidget(QLabel("Tarih Aralığı:"))
        chart_options_layout.addWidget(date_range_combo)
        
        chart_options_layout.addStretch()
        
        update_chart_btn = QPushButton("🔄 Grafiği Güncelle")
        update_chart_btn.setObjectName("primaryButton")
        chart_options_layout.addWidget(update_chart_btn)
        
        chart_layout.addLayout(chart_options_layout)
        
        # Grafik placeholder
        chart_placeholder = QLabel("📊 Grafik Alanı\n\nBurada gerçek zamanlı performans grafikleri gösterilecek")
        chart_placeholder.setAlignment(Qt.AlignCenter)
        chart_placeholder.setObjectName("chartPlaceholder")
        chart_layout.addWidget(chart_placeholder)
        
        layout.addWidget(chart_group)
        
        # Alt panel - Detaylı analiz
        detailed_analysis_layout = QHBoxLayout()
        
        # Sol taraf - Kanal performansı
        channels_group = QGroupBox("📊 Kanal Performansı")
        channels_layout = QVBoxLayout(channels_group)
        
        self.channels_table = QTableWidget()
        self.channels_table.setColumnCount(4)
        self.channels_table.setHorizontalHeaderLabels([
            "Kanal", "Görüntülenme", "Tıklama", "Dönüşüm"
        ])
        
        channels_layout.addWidget(self.channels_table)
        detailed_analysis_layout.addWidget(channels_group, 1)
        
        # Sağ taraf - Top performanslar
        top_performance_group = QGroupBox("🏆 En İyi Performanslar")
        top_performance_layout = QVBoxLayout(top_performance_group)
        
        self.top_campaigns_list = QListWidget()
        top_campaigns = [
            "🥇 Yaz İndirimi 2024 - CTR: %12.5",
            "🥈 Sosyal Medya Boost - CTR: %9.8",
            "🥉 E-posta Kampanyası - CTR: %8.2",
            "4️⃣ Google Ads - CTR: %7.1",
            "5️⃣ Facebook Ads - CTR: %6.9",
        ]
        
        for campaign in top_campaigns:
            self.top_campaigns_list.addItem(campaign)
            
        top_performance_layout.addWidget(self.top_campaigns_list)
        detailed_analysis_layout.addWidget(top_performance_group, 1)
        
        layout.addLayout(detailed_analysis_layout)
        
        return widget
        
    def create_content_management_tab(self):
        """İçerik yönetimi sekmesini oluşturur"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Sol panel - İçerik oluşturma
        content_group = QGroupBox("📝 İçerik Oluştur")
        content_layout = QVBoxLayout(content_group)
        
        # İçerik türü
        content_type_layout = QHBoxLayout()
        content_type_layout.addWidget(QLabel("İçerik Türü:"))
        
        self.content_type_combo = QComboBox()
        self.content_type_combo.addItems([
            "Blog Yazısı", "Sosyal Medya Postu", "E-posta İçeriği", 
            "Reklam Metni", "Ürün Açıklaması", "Haber Bülteni"
        ])
        content_type_layout.addWidget(self.content_type_combo)
        content_type_layout.addStretch()
        
        content_layout.addLayout(content_type_layout)
        
        # İçerik başlığı
        content_layout.addWidget(QLabel("Başlık:"))
        self.content_title_edit = QLineEdit()
        content_layout.addWidget(self.content_title_edit)
        
        # İçerik metni
        content_layout.addWidget(QLabel("İçerik:"))
        self.content_text_edit = QTextEdit()
        self.content_text_edit.setMinimumHeight(200)
        content_layout.addWidget(self.content_text_edit)
        
        # Anahtar kelimeler
        content_layout.addWidget(QLabel("Anahtar Kelimeler:"))
        self.keywords_edit = QLineEdit()
        self.keywords_edit.setPlaceholderText("pazarlama, dijital, sosyal medya")
        content_layout.addWidget(self.keywords_edit)
        
        # İçerik durumu
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Durum:"))
        
        self.content_status_combo = QComboBox()
        self.content_status_combo.addItems([
            "📝 Taslak", "👀 İnceleme", "✅ Onaylandı", "📤 Yayınlandı"
        ])
        status_layout.addWidget(self.content_status_combo)
        status_layout.addStretch()
        
        content_layout.addLayout(status_layout)
        
        # İçerik butonları
        content_buttons_layout = QHBoxLayout()
        save_content_btn = QPushButton("💾 Kaydet")
        save_content_btn.setObjectName("primaryButton")
        save_content_btn.clicked.connect(self.save_content)
        
        preview_btn = QPushButton("👀 Önizleme")
        preview_btn.clicked.connect(self.preview_content)
        
        publish_btn = QPushButton("📤 Yayınla")
        publish_btn.clicked.connect(self.publish_content)
        
        content_buttons_layout.addWidget(save_content_btn)
        content_buttons_layout.addWidget(preview_btn)
        content_buttons_layout.addWidget(publish_btn)
        content_layout.addLayout(content_buttons_layout)
        
        layout.addWidget(content_group, 1)
        
        # Sağ panel - İçerik kütüphanesi
        library_group = QGroupBox("📚 İçerik Kütüphanesi")
        library_layout = QVBoxLayout(library_group)
        
        # Filtreleme
        filter_layout = QHBoxLayout()
        
        type_filter = QComboBox()
        type_filter.addItems(["Tüm Türler", "Blog", "Sosyal Medya", "E-posta", "Reklam"])
        filter_layout.addWidget(QLabel("Tür:"))
        filter_layout.addWidget(type_filter)
        
        status_filter = QComboBox()
        status_filter.addItems(["Tüm Durumlar", "Taslak", "İnceleme", "Onaylandı", "Yayınlandı"])
        filter_layout.addWidget(QLabel("Durum:"))
        filter_layout.addWidget(status_filter)
        
        filter_layout.addStretch()
        library_layout.addLayout(filter_layout)
        
        # İçerik listesi
        self.content_table = QTableWidget()
        self.content_table.setColumnCount(4)
        self.content_table.setHorizontalHeaderLabels([
            "Başlık", "Tür", "Durum", "Tarih"
        ])
        
        # Tablo ayarları
        content_header = self.content_table.horizontalHeader()
        content_header.setStretchLastSection(True)
        content_header.setSectionResizeMode(QHeaderView.Interactive)
        
        self.content_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.content_table.setAlternatingRowColors(True)
        self.content_table.itemSelectionChanged.connect(self.on_content_selected)
        
        library_layout.addWidget(self.content_table)
        layout.addWidget(library_group, 1)
        
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
        user_label = QLabel("👤 Pazarlama Uzmanı: Admin")
        status_layout.addWidget(user_label)
        
        # Tarih/saat
        from datetime import datetime
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        time_label = QLabel(f"🕒 {current_time}")
        status_layout.addWidget(time_label)
        
        return status_frame
        
    def create_performance_card(self, icon, title, value, color):
        """Performans kartı oluşturur"""
        card = QFrame()
        card.setObjectName("performanceCard")
        card.setStyleSheet(f"""
            #performanceCard {{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }}
        """)
        
        card_layout = QHBoxLayout(card)
        
        # İkon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        card_layout.addWidget(icon_label)
        
        # Metin alanı
        text_layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setObjectName("perfCardTitle")
        text_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("perfCardValue")
        text_layout.addWidget(value_label)
        
        card_layout.addLayout(text_layout)
        card_layout.addStretch()
        
        return card
        
    def create_metric_card(self, icon, title, value):
        """Metrik kartı oluşturur"""
        card = QFrame()
        card.setObjectName("metricCard")
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 20px; margin-bottom: 5px;")
        card_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("metricTitle")
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName("metricValue")
        card_layout.addWidget(value_label)
        
        return card
        
    def create_analytics_card(self, icon, title, value, color):
        """Analytics kartı oluşturur"""
        card = QFrame()
        card.setObjectName("analyticsCard")
        card.setStyleSheet(f"""
            #analyticsCard {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
                min-height: 100px;
            }}
            #analyticsCard:hover {{
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                transform: translateY(-2px);
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 28px; margin-bottom: 8px;")
        card_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("analyticsTitle")
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName("analyticsValue")
        value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        card_layout.addWidget(value_label)
        
        return card
        
    def load_sample_data(self):
        """Örnek verileri yükler"""
        # Kampanya verileri
        campaigns_data = [
            ("Yaz İndirimi 2024", "E-posta", "🟢 Aktif", "₺15,000", "₺12,000", "%125"),
            ("Sosyal Medya Boost", "Facebook Ads", "🟡 Beklemede", "₺8,500", "₺5,200", "%89"),
            ("Google Ads Kampanyası", "Google Ads", "🟢 Aktif", "₺25,000", "₺18,000", "%156"),
            ("İnfluencer İşbirliği", "İnfluencer", "🔴 Tamamlandı", "₺10,000", "₺10,000", "%78"),
        ]
        
        self.campaigns_table.setRowCount(len(campaigns_data))
        for row, campaign in enumerate(campaigns_data):
            for col, data in enumerate(campaign):
                self.campaigns_table.setItem(row, col, QTableWidgetItem(data))
                
        # E-posta geçmişi verileri
        email_history_data = [
            ("Yeni Ürün Lansmanı", "2,456", "%68.2", "%12.4", "15.01.2024"),
            ("Haftalık Haber Bülteni", "3,789", "%72.1", "%8.9", "12.01.2024"),
            ("Özel İndirim Teklifi", "1,234", "%81.3", "%15.7", "08.01.2024"),
            ("Etkinlik Daveti", "987", "%65.4", "%22.1", "05.01.2024"),
        ]
        
        self.email_history_table.setRowCount(len(email_history_data))
        for row, email in enumerate(email_history_data):
            for col, data in enumerate(email):
                self.email_history_table.setItem(row, col, QTableWidgetItem(data))
                
        # Kanal performansı verileri
        channels_data = [
            ("Google Ads", "45,678", "3,456", "234"),
            ("Facebook", "32,145", "2,789", "189"),
            ("Instagram", "28,934", "2,234", "156"),
            ("E-posta", "15,678", "1,234", "98"),
        ]
        
        self.channels_table.setRowCount(len(channels_data))
        for row, channel in enumerate(channels_data):
            for col, data in enumerate(channel):
                self.channels_table.setItem(row, col, QTableWidgetItem(data))
                
        # İçerik kütüphanesi verileri
        content_data = [
            ("Dijital Pazarlama Trendleri", "Blog", "✅ Onaylandı", "15.01.2024"),
            ("Sosyal Medya İpuçları", "Sosyal Medya", "📝 Taslak", "14.01.2024"),
            ("Ürün Tanıtım E-postası", "E-posta", "👀 İnceleme", "13.01.2024"),
            ("Google Ads Reklam Metni", "Reklam", "📤 Yayınlandı", "12.01.2024"),
        ]
        
        self.content_table.setRowCount(len(content_data))
        for row, content in enumerate(content_data):
            for col, data in enumerate(content):
                self.content_table.setItem(row, col, QTableWidgetItem(data))
                
    def setup_styles(self):
        """Stil tanımlamaları"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            #headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #28a745, stop:1 #20c997);
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
                border-bottom: 3px solid #28a745;
                color: #28a745;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #f8f9fa;
            }
            
            #primaryButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            
            #primaryButton:hover {
                background-color: #218838;
            }
            
            #primaryButton:pressed {
                background-color: #1e7e34;
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
                selection-background-color: #28a745;
                selection-color: white;
            }
            
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f8f9fa;
            }
            
            QTableWidget::item:selected {
                background-color: #28a745;
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
                border-color: #28a745;
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
                border-color: #28a745;
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
                border: 2px solid #28a745;
                background-color: #28a745;
                border-radius: 3px;
            }
            
            #platformFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
            
            #platformHeader {
                font-size: 16px;
                font-weight: bold;
                color: #495057;
                margin-bottom: 8px;
            }
            
            #platformStat {
                font-size: 12px;
                color: #6c757d;
                margin-bottom: 3px;
            }
            
            #perfCardTitle {
                font-size: 12px;
                color: #6c757d;
                font-weight: bold;
            }
            
            #perfCardValue {
                font-size: 18px;
                color: #495057;
                font-weight: bold;
            }
            
            #metricCard {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
                min-height: 80px;
            }
            
            #metricCard:hover {
                border-color: #28a745;
                box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);
            }
            
            #metricTitle {
                font-size: 11px;
                color: #6c757d;
                font-weight: bold;
            }
            
            #metricValue {
                font-size: 16px;
                color: #28a745;
                font-weight: bold;
            }
            
            #analyticsTitle {
                font-size: 12px;
                color: #6c757d;
                font-weight: bold;
                text-align: center;
            }
            
            #chartPlaceholder {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 8px;
                padding: 80px;
                font-size: 16px;
                color: #6c757d;
                margin: 20px;
            }
            
            QListWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f8f9fa;
            }
            
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
            
            QListWidget::item:selected {
                background-color: #28a745;
                color: white;
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
    def on_campaign_selected(self):
        """Kampanya seçildiğinde çalışır"""
        current_row = self.campaigns_table.currentRow()
        if current_row >= 0:
            name = self.campaigns_table.item(current_row, 0).text()
            self.status_label.setText(f"Seçili kampanya: {name}")
            
    def on_content_selected(self):
        """İçerik seçildiğinde çalışır"""
        current_row = self.content_table.currentRow()
        if current_row >= 0:
            title = self.content_table.item(current_row, 0).text()
            self.status_label.setText(f"Seçili içerik: {title}")
            
    # Action methods
    def create_new_campaign(self):
        """Yeni kampanya oluşturma"""
        self.tab_widget.setCurrentIndex(0)  # Kampanyalar sekmesine geç
        self.campaign_name_edit.setFocus()
        self.status_label.setText("Yeni kampanya oluşturma modu")
        
    def create_new_post(self):
        """Yeni post oluşturma"""
        self.tab_widget.setCurrentIndex(1)  # Sosyal medya sekmesine geç
        self.post_content_edit.setFocus()
        self.status_label.setText("Yeni post oluşturma modu")
        
    def create_campaign(self):
        """Kampanya oluşturma"""
        name = self.campaign_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Kampanya adı boş olamaz!")
            return
            
        row_count = self.campaigns_table.rowCount()
        self.campaigns_table.insertRow(row_count)
        
        self.campaigns_table.setItem(row_count, 0, QTableWidgetItem(name))
        self.campaigns_table.setItem(row_count, 1, QTableWidgetItem(self.campaign_type_combo.currentText()))
        self.campaigns_table.setItem(row_count, 2, QTableWidgetItem("🟡 Beklemede"))
        self.campaigns_table.setItem(row_count, 3, QTableWidgetItem(f"₺{self.campaign_budget_spin.value():,}"))
        self.campaigns_table.setItem(row_count, 4, QTableWidgetItem("₺0"))
        self.campaigns_table.setItem(row_count, 5, QTableWidgetItem("-%"))
        
        self.status_label.setText(f"Kampanya '{name}' başarıyla oluşturuldu")
        QMessageBox.information(self, "Başarılı", f"Kampanya '{name}' başarıyla oluşturuldu!")
        
    def update_campaign(self):
        """Kampanya güncelleme"""
        current_row = self.campaigns_table.currentRow()
        if current_row >= 0:
            name = self.campaign_name_edit.text().strip()
            if name:
                self.campaigns_table.setItem(current_row, 0, QTableWidgetItem(name))
                self.campaigns_table.setItem(current_row, 1, QTableWidgetItem(self.campaign_type_combo.currentText()))
                self.campaigns_table.setItem(current_row, 3, QTableWidgetItem(f"₺{self.campaign_budget_spin.value():,}"))
                
                self.status_label.setText(f"Kampanya '{name}' güncellendi")
                QMessageBox.information(self, "Başarılı", f"Kampanya '{name}' başarıyla güncellendi!")
        else:
            QMessageBox.warning(self, "Uyarı", "Güncellenecek kampanya seçiniz!")
            
    def post_now(self):
        """Hemen post paylaşma"""
        content = self.post_content_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Uyarı", "Post içeriği boş olamaz!")
            return
            
        platform = self.platform_combo.currentText()
        self.status_label.setText(f"Post {platform} platformunda paylaşıldı")
        QMessageBox.information(self, "Başarılı", f"Post başarıyla {platform} platformunda paylaşıldı!")
        
        # Post listesine ekle
        post_text = f"{platform}: {content[:50]}..."
        self.recent_posts_list.insertItem(0, post_text)
        
    def save_draft(self):
        """Taslak kaydetme"""
        content = self.post_content_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Uyarı", "Post içeriği boş olamaz!")
            return
            
        self.status_label.setText("Post taslak olarak kaydedildi")
        QMessageBox.information(self, "Başarılı", "Post taslak olarak kaydedildi!")
        
    def send_test_email(self):
        """Test e-postası gönderme"""
        subject = self.email_subject_edit.text().strip()
        if not subject:
            QMessageBox.warning(self, "Uyarı", "E-posta konusu boş olamaz!")
            return
            
        self.status_label.setText("Test e-postası gönderildi")
        QMessageBox.information(self, "Başarılı", "Test e-postası başarıyla gönderildi!")
        
    def schedule_email(self):
        """E-posta zamanlama"""
        subject = self.email_subject_edit.text().strip()
        if not subject:
            QMessageBox.warning(self, "Uyarı", "E-posta konusu boş olamaz!")
            return
            
        date = self.email_send_date.date().toString("dd.MM.yyyy")
        self.status_label.setText(f"E-posta {date} tarihine zamanlandı")
        QMessageBox.information(self, "Başarılı", f"E-posta {date} tarihine başarıyla zamanlandı!")
        
    def send_email_now(self):
        """E-postayı hemen gönderme"""
        subject = self.email_subject_edit.text().strip()
        if not subject:
            QMessageBox.warning(self, "Uyarı", "E-posta konusu boş olamaz!")
            return
            
        # E-posta geçmişine ekle
        row_count = self.email_history_table.rowCount()
        self.email_history_table.insertRow(row_count)
        
        recipient_count = "1,234"  # Örnek değer
        
        self.email_history_table.setItem(row_count, 0, QTableWidgetItem(subject))
        self.email_history_table.setItem(row_count, 1, QTableWidgetItem(recipient_count))
        self.email_history_table.setItem(row_count, 2, QTableWidgetItem("-%"))
        self.email_history_table.setItem(row_count, 3, QTableWidgetItem("-%"))
        self.email_history_table.setItem(row_count, 4, QTableWidgetItem(QDate.currentDate().toString("dd.MM.yyyy")))
        
        self.status_label.setText("E-posta başarıyla gönderildi")
        QMessageBox.information(self, "Başarılı", "E-posta başarıyla gönderildi!")
        
    def save_content(self):
        """İçerik kaydetme"""
        title = self.content_title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Uyarı", "İçerik başlığı boş olamaz!")
            return
            
        # İçerik tablosuna ekle
        row_count = self.content_table.rowCount()
        self.content_table.insertRow(row_count)
        
        self.content_table.setItem(row_count, 0, QTableWidgetItem(title))
        self.content_table.setItem(row_count, 1, QTableWidgetItem(self.content_type_combo.currentText()))
        self.content_table.setItem(row_count, 2, QTableWidgetItem(self.content_status_combo.currentText()))
        self.content_table.setItem(row_count, 3, QTableWidgetItem(QDate.currentDate().toString("dd.MM.yyyy")))
        
        self.status_label.setText(f"İçerik '{title}' kaydedildi")
        QMessageBox.information(self, "Başarılı", f"İçerik '{title}' başarıyla kaydedildi!")
        
    def preview_content(self):
        """İçerik önizleme"""
        title = self.content_title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Uyarı", "İçerik başlığı boş olamaz!")
            return
            
        self.status_label.setText(f"İçerik '{title}' önizleme modunda")
        QMessageBox.information(self, "Önizleme", f"İçerik '{title}' önizleme penceresinde açılacak.")
        
    def publish_content(self):
        """İçerik yayınlama"""
        title = self.content_title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Uyarı", "İçerik başlığı boş olamaz!")
            return
            
        self.content_status_combo.setCurrentText("📤 Yayınlandı")
        self.status_label.setText(f"İçerik '{title}' yayınlandı")
        QMessageBox.information(self, "Başarılı", f"İçerik '{title}' başarıyla yayınlandı!")

def main():
    """Ana fonksiyon"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Uygulama bilgileri
    app.setApplicationName("Marketing Modülü")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("İş Yönetim Sistemi")
    
    # Ana pencereyi oluştur ve göster
    marketing_window = MarketingModule()
    marketing_window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

