"""Reusable UI components for the Paw Rescue application."""

# Header components
from .header import create_header, create_page_header

# Sidebar components
from .sidebar import create_admin_sidebar, create_user_sidebar

# Button components
from .buttons import create_nav_button, create_action_button, create_logout_button, create_table_action_button

# Status badge components
from .status_badge import create_status_badge, create_mission_status_badge, create_adoption_status_dropdown

# Card components (legacy)
from .card import create_form_card, create_content_card, create_dashboard_card

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
    create_empty_state,
    create_data_table,
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
    create_archive_dialog,
    create_remove_dialog,
    create_permanent_delete_dialog,
    create_restore_dialog,
)

# Utility functions
from .utils import fig_to_base64, is_matplotlib_available

__all__ = [
    # Headers
    "create_header",
    "create_page_header",
    # Sidebars
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
    "create_dashboard_card",
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
    "create_empty_state",
    "create_data_table",
    "create_stat_card",
    "create_map_container",
    "create_animal_card",
    # Dialogs
    "show_snackbar",
    "create_error_dialog",
    "create_success_dialog",
    "create_confirmation_dialog",
    "create_archive_dialog",
    "create_remove_dialog",
    "create_permanent_delete_dialog",
    "create_restore_dialog",
    # Utils
    "fig_to_base64",
    "is_matplotlib_available",
]
