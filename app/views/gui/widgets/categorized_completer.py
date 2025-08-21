# gui/widgets/categorized_completer.py

from PyQt5.QtWidgets import QCompleter, QListView, QStyledItemDelegate
from PyQt5.QtCore import QStringListModel, QModelIndex, Qt

class CategorizedCompleter(QCompleter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPopup(QListView())

    def update_model(self, categories_dict):
        self.categories = categories_dict
        model = QStringListModel()
        all_items = []
        for category, items in categories_dict.items():
            all_items.append(f"--- {category} ---")
            all_items.extend(items)
        model.setStringList(all_items)
        self.setModel(model)

class CategoryDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        text = index.data(Qt.DisplayRole)
        if text.startswith("---") and text.endswith("---"):
            option.font.setBold(True)
            option.palette.setColor(option.palette.Text, Qt.gray)
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        text = index.data(Qt.DisplayRole)
        if text.startswith("---") and text.endswith("---"):
            size = super().sizeHint(option, index)
            size.setHeight(int(size.height() * 1.5))
            return size
        return super().sizeHint(option, index)
