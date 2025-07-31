import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt

class StatusChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.canvas = None
        self.last_pie_chart_labels = []
        self._pick_event_cid = None

    def update_chart(self, status_data, slice_picked_callback):
        self.clear_chart()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            if not status_data:
                self.show_no_data_message(self.tr("Aucune donnée de statut client disponible."))
                return

            filtered_status_data = [item for item in status_data if item.get('client_count', 0) > 0]

            if not filtered_status_data:
                self.show_no_data_message(self.tr("Aucun client trouvé pour les statuts existants."))
                return

            labels = [item.get('status_name', 'N/A') for item in filtered_status_data]
            sizes = [item.get('client_count', 0) for item in filtered_status_data]

            plt.style.use('seaborn-v0_8-colorblind')
            fig = Figure(figsize=(5.5, 4.5), dpi=90)
            fig.patch.set_alpha(0)
            ax = fig.add_subplot(111)
            ax.patch.set_alpha(0)

            wedges, texts, autotexts = ax.pie(
                sizes,
                autopct=lambda p: '{:.1f}%\n({:.0f})'.format(p, p * sum(sizes) / 100.0),
                startangle=90,
                pctdistance=0.80,
                wedgeprops=dict(width=0.35, edgecolor='w')
            )
            ax.axis('equal')

            for text_obj in texts + autotexts:
                text_obj.set_fontsize(8)

            for wedge in wedges:
                wedge.set_picker(True)

            self.last_pie_chart_labels = list(labels)

            if len(labels) <= 7:
                ax.legend(wedges, labels, title=self.tr("Statuts"), loc="center left", bbox_to_anchor=(1.05, 0.5), prop={'size': 7})
                fig.subplots_adjust(right=0.75)
            else:
                fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

            self.canvas = FigureCanvas(fig)
            self.canvas.setObjectName("statusPieChartCanvas")
            self._pick_event_cid = self.canvas.mpl_connect('pick_event', slice_picked_callback)

            self.layout.addWidget(self.canvas)
            self.canvas.draw_idle()
            logging.info("Status segmentation chart updated.")

        except Exception as e:
            logging.error(f"Error updating status segmentation chart: {e}", exc_info=True)
            self.show_no_data_message(self.tr("Erreur génération graphique des statuts."))
        finally:
            QApplication.restoreOverrideCursor()

    def clear_chart(self):
        if self.canvas:
            if self._pick_event_cid:
                self.canvas.mpl_disconnect(self._pick_event_cid)
            self.layout.removeWidget(self.canvas)
            self.canvas.deleteLater()
            self.canvas = None
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().deleteLater()

    def show_no_data_message(self, message):
        self.clear_chart()
        no_data_label = QLabel(message)
        no_data_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(no_data_label)
