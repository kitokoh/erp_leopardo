# utils/app_constants.py

from license_management import (
    FEATURE_PROJECT_MANAGEMENT, FEATURE_PRODUCT_MANAGEMENT, FEATURE_PARTNER_MANAGEMENT,
    FEATURE_STATISTICS_MODULE, FEATURE_INVENTORY_MANAGEMENT, FEATURE_EXPERIENCE_MANAGEMENT,
    FEATURE_CALENDAR_MODULE, FEATURE_BOTPRESS_INTEGRATION, FEATURE_CALCULATOR_MODULE,
    FEATURE_COMMANDES_MANAGEMENT
    # Note: FEATURE_USER_MANAGEMENT_FULL, FEATURE_SETTINGS_MANAGEMENT,
    # FEATURE_ADVANCED_REPORTING, FEATURE_API_ACCESS are also available in license_management
    # but not directly tied to these configurable modules in the same way.
)

CONFIGURABLE_MODULES = [
    {'key': 'module_project_management_enabled', 'name': 'project_management', 'action_attr': 'project_management_action', 'widget_attr': 'project_management_widget_instance', 'license_feature': FEATURE_PROJECT_MANAGEMENT},
    {'key': 'module_product_management_enabled', 'name': 'product_management', 'action_attr': 'product_list_action', 'widget_attr': 'product_management_page_instance', 'license_feature': FEATURE_PRODUCT_MANAGEMENT},
    {'key': 'module_partner_management_enabled', 'name': 'partner_management', 'action_attr': 'partner_management_action', 'widget_attr': 'partner_management_widget_instance', 'license_feature': FEATURE_PARTNER_MANAGEMENT},
    {'key': 'module_statistics_enabled', 'name': 'statistics', 'action_attr': 'statistics_action', 'widget_attr': 'statistics_dashboard_instance', 'license_feature': FEATURE_STATISTICS_MODULE},
    {'key': 'module_inventory_management_enabled', 'name': 'inventory_management', 'action_attr': 'inventory_browser_action', 'widget_attr': 'inventory_browser_widget_instance', 'license_feature': FEATURE_INVENTORY_MANAGEMENT},
    {'key': 'module_experience_management_enabled', 'name': 'experience_management', 'action_attr': 'experience_management_action', 'widget_attr': 'experience_management_widget_instance', 'license_feature': FEATURE_EXPERIENCE_MANAGEMENT},
    {'key': 'module_botpress_integration_enabled', 'name': 'botpress_integration', 'action_attr': 'botpress_integration_action', 'widget_attr': 'botpress_integration_ui_instance', 'license_feature': FEATURE_BOTPRESS_INTEGRATION},
    {'key': 'module_carrier_map_enabled', 'name': 'carrier_map', 'action_attr': 'open_carrier_map_action', 'widget_attr': None, 'license_feature': None}, # No specific license feature
    {'key': 'module_calendar_enabled', 'name': 'calendar', 'action_attr': 'calendar_module_action', 'widget_attr': 'calendar_module_widget_instance', 'license_feature': FEATURE_CALENDAR_MODULE},
    {'key': 'module_camera_management_enabled', 'name': 'camera_management', 'action_attr': 'camera_management_action', 'widget_attr': 'camera_management_widget_instance', 'license_feature': None}, # No specific license feature
    {'key': 'module_calculator_enabled', 'name': 'calculator', 'action_attr': 'calculator_module_action', 'widget_attr': 'calculator_module_widget_instance', 'license_feature': FEATURE_CALCULATOR_MODULE},
    # Assuming 'commandes_management' is also a module that should be here if configurable via these settings
    # If 'commande_management_action' (from DocumentManager.create_actions_main) refers to a configurable module:
    # {'key': 'module_commandes_management_enabled', 'name': 'commandes_management', 'action_attr': 'commande_management_action', 'widget_attr': 'commandes_dashboard_widget_instance', 'license_feature': FEATURE_COMMANDES_MANAGEMENT}
    # For now, I will assume 'commande_management_action' is a core, non-configurable-via-this-list action,
    # as it was added directly in create_menus_main and not iterated through CONFIGURABLE_MODULES for its license check.
    # If it needs to be configurable like others, its entry should be added above.
]
