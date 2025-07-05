# utils/app_constants.py

CONFIGURABLE_MODULES = [
    {'key': 'module_project_management_enabled', 'name': 'project_management', 'action_attr': 'project_management_action', 'widget_attr': 'project_management_widget_instance'},
    {'key': 'module_product_management_enabled', 'name': 'product_management', 'action_attr': 'product_list_action', 'widget_attr': 'product_management_page_instance'},
    {'key': 'module_partner_management_enabled', 'name': 'partner_management', 'action_attr': 'partner_management_action', 'widget_attr': 'partner_management_widget_instance'},
    {'key': 'module_statistics_enabled', 'name': 'statistics', 'action_attr': 'statistics_action', 'widget_attr': 'statistics_dashboard_instance'},
    {'key': 'module_inventory_management_enabled', 'name': 'inventory_management', 'action_attr': 'inventory_browser_action', 'widget_attr': 'inventory_browser_widget_instance'},
    {'key': 'module_experience_management_enabled', 'name': 'experience_management', 'action_attr': 'experience_management_action', 'widget_attr': 'experience_management_widget_instance'}, # Added
    {'key': 'module_botpress_integration_enabled', 'name': 'botpress_integration', 'action_attr': 'botpress_integration_action', 'widget_attr': 'botpress_integration_ui_instance'},
    {'key': 'module_carrier_map_enabled', 'name': 'carrier_map', 'action_attr': 'open_carrier_map_action', 'widget_attr': None}, # Carrier map is a dialog
    {'key': 'module_calendar_enabled', 'name': 'calendar', 'action_attr': 'calendar_module_action', 'widget_attr': 'calendar_module_widget_instance'},
    {'key': 'module_camera_management_enabled', 'name': 'camera_management', 'action_attr': 'camera_management_action', 'widget_attr': 'camera_management_widget_instance'},
    {'key': 'module_calculator_enabled', 'name': 'calculator', 'action_attr': 'calculator_module_action', 'widget_attr': 'calculator_module_widget_instance'} # Added Calculator module
]
