"""Reusable UI components for the Paw Rescue application."""

from .header import create_header, create_page_header
from .sidebar import create_admin_sidebar, create_user_sidebar
from .buttons import create_nav_button, create_action_button, create_logout_button, create_table_action_button
from .status_badge import create_status_badge, create_mission_status_badge, create_adoption_status_dropdown
from .card import create_form_card, create_content_card, create_dashboard_card
from .background import create_gradient_background
from .photo_upload import create_photo_upload_widget, PhotoUploadWidget
from .profile import create_profile_section

__all__ = [
    "create_header",
    "create_page_header",
    "create_admin_sidebar",
    "create_user_sidebar",
    "create_nav_button",
    "create_action_button",
    "create_logout_button",
    "create_table_action_button",
    "create_status_badge",
    "create_mission_status_badge",
    "create_adoption_status_dropdown",
    "create_form_card",
    "create_content_card",
    "create_dashboard_card",
    "create_gradient_background",
    "create_photo_upload_widget",
    "PhotoUploadWidget",
    "create_profile_section",
]
