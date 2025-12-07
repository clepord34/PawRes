"""Reusable UI components for the Paw Rescue application."""

# Header components
from .header import create_header, create_page_header

from .sidebar import create_admin_sidebar, create_user_sidebar

# Button components
from .buttons import (
    create_nav_button, 
    create_action_button, 
    create_logout_button, 
    create_table_action_button,
    create_ai_download_button,
)

# Status badge components
from .status_badge import create_status_badge, create_mission_status_badge, create_adoption_status_dropdown

# Card components (legacy)
from .card import create_form_card, create_content_card

# Background components
from .background import create_gradient_background

# Photo upload components
from .photo_upload import create_photo_upload_widget, PhotoUploadWidget

# Profile components
from .profile import create_profile_section

# Form field components
from .form_fields import (
    create_form_text_field,
    create_form_dropdown,
    create_form_label,
    create_labeled_field,
)

# Container components
from .containers import (
    create_section_card,
    create_chart_container,
    create_page_title,
    create_section_header,
    create_empty_state,
    create_data_table,
    create_scrollable_data_table,
    create_stat_card,
    create_map_container,
    create_animal_card,
)

# Dialog components
from .dialogs import (
    show_snackbar,
    create_error_dialog,
    create_success_dialog,
    create_confirmation_dialog,
    create_info_dialog,
    create_archive_dialog,
    create_remove_dialog,
    create_permanent_delete_dialog,
    create_restore_dialog,
)

# Utility functions
from .utils import (
    fig_to_base64, 
    is_matplotlib_available, 
    parse_date, 
    parse_datetime,
    is_valid_email,
    is_valid_phone,
    is_valid_contact,
    validate_contact,
    get_contact_type,
    normalize_phone_number,
    format_phone_for_display,
    DEFAULT_PHONE_REGION,
    # Location utilities
    is_coordinate_string,
    parse_coordinates_from_string,
    format_coordinates_display,
    format_location_for_display,
)

# Animal form component
from .animal_form import AnimalFormWidget, create_animal_form

# Map wrapper component
from .map_wrapper import create_interactive_map, create_simple_locked_map

# Chart components (Flet native charts)
from .charts import (
    CHART_COLORS,
    PIE_CHART_COLORS,
    STATUS_COLORS,
    create_empty_chart_message,
    create_line_chart,
    create_bar_chart,
    create_pie_chart,
    create_chart_legend,
    create_clickable_stat_card,
    show_chart_details_dialog,
    create_insight_card,
    create_insight_box,
    create_chart_card,
    create_impact_insight_widgets,
)

# AI suggestion components
from .ai_suggestion_card import (
    create_ai_suggestion_card,
    create_ai_loading_card,
    create_ai_analyze_button,
)

# AI download dialog
from .ai_download_dialog import create_ai_download_dialog

__all__ = [
    # Headers
    "create_header",
    "create_page_header",
    "create_admin_sidebar",
    "create_user_sidebar",
    # Buttons
    "create_nav_button",
    "create_action_button",
    "create_logout_button",
    "create_table_action_button",
    # Status badges
    "create_status_badge",
    "create_mission_status_badge",
    "create_adoption_status_dropdown",
    # Cards (legacy)
    "create_form_card",
    "create_content_card",
    # Background
    "create_gradient_background",
    # Photo upload
    "create_photo_upload_widget",
    "PhotoUploadWidget",
    # Profile
    "create_profile_section",
    # Form fields
    "create_form_text_field",
    "create_form_dropdown",
    "create_form_label",
    "create_labeled_field",
    # Containers
    "create_section_card",
    "create_chart_container",
    "create_page_title",
    "create_section_header",
    "create_empty_state",
    "create_data_table",
    "create_scrollable_data_table",
    "create_stat_card",
    "create_map_container",
    "create_animal_card",
    # Dialogs
    "show_snackbar",
    "create_error_dialog",
    "create_success_dialog",
    "create_confirmation_dialog",
    "create_info_dialog",
    "create_archive_dialog",
    "create_remove_dialog",
    "create_permanent_delete_dialog",
    "create_restore_dialog",
    # Utils
    "fig_to_base64",
    "is_matplotlib_available",
    "parse_date",
    "parse_datetime",
    "is_valid_email",
    "is_valid_phone",
    "is_valid_contact",
    "validate_contact",
    "get_contact_type",
    "normalize_phone_number",
    "format_phone_for_display",
    "DEFAULT_PHONE_REGION",
    # Location utilities
    "is_coordinate_string",
    "parse_coordinates_from_string",
    "format_coordinates_display",
    "format_location_for_display",
    # Animal form
    "AnimalFormWidget",
    "create_animal_form",
    # Map wrapper
    "create_interactive_map",
    "create_simple_locked_map",
    # Charts (Flet native)
    "CHART_COLORS",
    "PIE_CHART_COLORS",
    "STATUS_COLORS",
    "create_empty_chart_message",
    "create_line_chart",
    "create_bar_chart",
    "create_pie_chart",
    "create_chart_legend",
    "create_clickable_stat_card",
    "show_chart_details_dialog",
    "create_insight_card",
    "create_insight_box",
    "create_chart_card",
    "create_impact_insight_widgets",
    # AI suggestion components
    "create_ai_suggestion_card",
    "create_ai_loading_card",
    "create_ai_analyze_button",
    # AI download dialog
    "create_ai_download_dialog",
]
