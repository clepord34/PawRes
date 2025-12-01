"""Container components for consistent page layouts."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable

try:
    import flet as ft
except ImportError:
    ft = None


# Standard shadow used across the app
CARD_SHADOW = None  # Will be set when ft is available


def _get_card_shadow():
    """Get the standard card shadow."""
    if ft is None:
        raise RuntimeError("Flet must be installed")
    return ft.BoxShadow(
        blur_radius=8, 
        spread_radius=1, 
        color=ft.Colors.BLACK12, 
        offset=(0, 2)
    )


def create_section_card(
    title: str,
    content: object,
    width: Optional[int] = None,
    padding: int = 20,
    subtitle: Optional[str] = None,
    show_divider: bool = True,
) -> object:
    """Create a titled section card container.
    
    Args:
        title: Section title
        content: Content to display in the card
        width: Optional fixed width
        padding: Card padding
        subtitle: Optional subtitle text
        show_divider: Whether to show divider after title
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create containers")
    
    card_content = [
        ft.Text(title, size=18, weight="w600", color=ft.Colors.BLACK87),
    ]
    
    if subtitle:
        card_content.append(ft.Text(subtitle, size=12, color=ft.Colors.BLACK54))
    
    if show_divider:
        card_content.append(ft.Container(height=10))
    
    card_content.append(content)
    
    container_kwargs = {
        "content": ft.Column(card_content, spacing=0),
        "padding": padding,
        "bgcolor": ft.Colors.WHITE,
        "border_radius": 12,
        "shadow": _get_card_shadow(),
    }
    
    if width:
        container_kwargs["width"] = width
    
    return ft.Container(**container_kwargs)


def create_chart_container(
    title: str,
    chart_image: Optional[str] = None,
    chart_widget: Optional[object] = None,
    width: int = 400,
    height: int = 200,
    padding: int = 12,
    fallback_text: str = "No data available",
) -> object:
    """Create a container for chart images or widgets.
    
    Args:
        title: Chart title
        chart_image: Base64 encoded chart image
        chart_widget: Alternative widget to display (e.g., map)
        width: Container width
        height: Chart height
        padding: Container padding
        fallback_text: Text to show if no chart available
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create containers")
    
    if chart_image:
        chart_content = ft.Image(
            src_base64=chart_image, 
            width=width - 40, 
            height=height, 
            fit=ft.ImageFit.CONTAIN
        )
    elif chart_widget:
        chart_content = ft.Container(
            chart_widget,
            height=height,
            border_radius=8,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )
    else:
        chart_content = ft.Container(
            ft.Text(fallback_text, size=12, color=ft.Colors.BLACK54, text_align="center"),
            height=height,
            alignment=ft.alignment.center,
        )
    
    return ft.Container(
        ft.Column([
            ft.Text(title, size=15, weight="w600", color=ft.Colors.BLACK87),
            chart_content,
        ], horizontal_alignment="center", spacing=8),
        width=width,
        padding=padding,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        shadow=_get_card_shadow(),
    )


def create_page_title(
    title: str,
    size: int = 28,
    padding_bottom: int = 20,
    opacity: float = 0.6,
) -> object:
    """Create a standard page title.
    
    Args:
        title: Title text
        size: Font size
        padding_bottom: Bottom padding
        opacity: Text opacity
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create containers")
    
    return ft.Container(
        ft.Text(
            title, 
            size=size, 
            weight="bold", 
            color=ft.Colors.with_opacity(opacity, ft.Colors.BLACK)
        ),
        padding=ft.padding.only(bottom=padding_bottom),
        alignment=ft.alignment.center,
    )


def create_empty_state(
    message: str = "No data found",
    icon: Optional[object] = None,
    padding: int = 20,
) -> object:
    """Create an empty state placeholder.
    
    Args:
        message: Message to display
        icon: Optional icon to show
        padding: Container padding
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create containers")
    
    content = []
    if icon:
        content.append(ft.Icon(icon, size=48, color=ft.Colors.GREY_400))
        content.append(ft.Container(height=10))
    content.append(ft.Text(message, size=13, color=ft.Colors.BLACK54))
    
    return ft.Container(
        ft.Column(content, horizontal_alignment="center", spacing=0),
        padding=padding,
        alignment=ft.alignment.center,
    )


def create_data_table(
    columns: List[str],
    rows: List[List[object]],
    column_widths: Optional[List[int]] = None,
    empty_message: str = "No data found",
    padding: int = 20,
) -> object:
    """Create a styled data table.
    
    Args:
        columns: List of column header texts
        rows: List of rows, each row is a list of cell contents
        column_widths: Optional list of expand values for columns
        empty_message: Message when no rows
        padding: Container padding
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create containers")
    
    # Build header row
    header_cells = []
    for i, col in enumerate(columns):
        expand = column_widths[i] if column_widths and i < len(column_widths) else 1
        header_cells.append(
            ft.Text(col, size=13, weight="w600", color=ft.Colors.BLACK87, expand=expand)
        )
    
    table_content = [
        ft.Row(header_cells, spacing=15),
        ft.Divider(height=1, color=ft.Colors.GREY_300),
        ft.Container(height=10),
    ]
    
    if rows:
        for row in rows:
            row_cells = []
            for i, cell in enumerate(row):
                expand = column_widths[i] if column_widths and i < len(column_widths) else 1
                if isinstance(cell, str):
                    row_cells.append(
                        ft.Text(cell, size=13, color=ft.Colors.BLACK87, expand=expand)
                    )
                else:
                    row_cells.append(ft.Container(cell, expand=expand))
            
            table_content.append(
                ft.Column([
                    ft.Row(row_cells, spacing=15),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(height=8),
                ], spacing=0)
            )
    else:
        table_content.append(create_empty_state(empty_message))
    
    return ft.Container(
        ft.Column(table_content, spacing=0),
        padding=padding,
        bgcolor=ft.Colors.WHITE,
        border_radius=8,
    )


def create_stat_card(
    title: str,
    value: str,
    change: str = "",
    value_color: Optional[object] = None,
    width: int = 200,
    expand: bool = False,
) -> object:
    """Create a statistics card with value and change indicator.
    
    Args:
        title: Card title
        value: Main value to display
        change: Change text (e.g., "+15% this month")
        value_color: Color for the value text
        width: Card width (ignored if expand=True)
        expand: Whether to expand to fill available space
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create containers")
    
    if value_color is None:
        value_color = ft.Colors.BLACK87
    
    # Determine change color
    if "+" in change:
        change_color = ft.Colors.GREEN_600
    elif "-" in change:
        change_color = ft.Colors.RED_600
    else:
        change_color = ft.Colors.GREY_600
    
    card_content = [
        ft.Text(title, size=12, color=ft.Colors.BLACK54),
        ft.Text(value, size=32, weight="bold", color=value_color),
    ]
    
    if change:
        card_content.append(ft.Text(change, size=11, color=change_color))
    
    container_kwargs = {
        "content": ft.Column(card_content, spacing=5),
        "padding": 20,
        "bgcolor": ft.Colors.WHITE,
        "border_radius": 12,
        "shadow": _get_card_shadow(),
    }
    
    if expand:
        container_kwargs["expand"] = True
    else:
        container_kwargs["width"] = width
    
    return ft.Container(**container_kwargs)


def create_map_container(
    title: str,
    map_widget: Optional[object] = None,
    placeholder_count: int = 0,
    width: int = 370,
    height: int = 200,
    padding: int = 12,
) -> object:
    """Create a container for map widgets.
    
    Args:
        title: Container title
        map_widget: The map widget to display
        placeholder_count: Number of items for placeholder text
        width: Container width
        height: Map height
        padding: Container padding
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create containers")
    
    if map_widget:
        map_content = ft.Container(
            map_widget,
            height=height,
            border_radius=8,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )
    else:
        # Placeholder
        placeholder_text = f"{placeholder_count} mission(s) on map" if placeholder_count else "No missions to display"
        map_content = ft.Container(
            ft.Column([
                ft.Icon(ft.Icons.MAP, size=48, color=ft.Colors.GREY_400),
                ft.Text(placeholder_text, size=12, color=ft.Colors.BLACK54),
            ], horizontal_alignment="center", spacing=10),
            height=height,
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.GREY_100,
            border_radius=8,
        )
    
    return ft.Container(
        ft.Column([
            ft.Text(title, size=15, weight="w600", color=ft.Colors.BLACK87),
            map_content,
        ], horizontal_alignment="center", spacing=8),
        width=width,
        padding=padding,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        shadow=_get_card_shadow(),
    )


def create_animal_card(
    animal_id: int,
    name: str,
    species: str,
    age: int,
    status: str,
    photo_base64: Optional[str] = None,
    on_adopt: Optional[Callable] = None,
    on_edit: Optional[Callable] = None,
    on_archive: Optional[Callable] = None,
    on_remove: Optional[Callable] = None,
    is_admin: bool = False,
    show_adopt_button: bool = True,
    is_rescued: bool = False,
    rescue_info: Optional[Dict[str, Any]] = None,
) -> object:
    """Create an animal display card.
    
    Args:
        animal_id: Animal ID
        name: Animal name
        species: Animal species
        age: Animal age
        status: Health status
        photo_base64: Base64 encoded photo
        on_adopt: Callback for adopt button
        on_edit: Callback for edit button (admin)
        on_archive: Callback for archive action (admin)
        on_remove: Callback for remove action (admin)
        is_admin: Whether to show admin controls
        show_adopt_button: Whether to show the adopt button (for user view)
        is_rescued: Whether this animal came from a rescue mission
        rescue_info: Dict with rescue mission details (location, date, reporter, urgency)
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create containers")
    
    # Strip archived suffix if present - users shouldn't see archive status
    # e.g., "adopted|archived" -> "adopted"
    clean_status = status
    if "|archived" in status.lower():
        clean_status = status.lower().replace("|archived", "")
    
    # Status color mapping
    status_lower = clean_status.lower()
    status_colors = {
        "healthy": ft.Colors.GREEN_600,
        "recovering": ft.Colors.ORANGE_600,
        "injured": ft.Colors.RED_600,
        "adopted": ft.Colors.PURPLE_600,
        "processing": ft.Colors.BLUE_600,  # Needs admin setup
    }
    status_color = status_colors.get(status_lower, ft.Colors.GREY_600)
    
    # Display text for status (show user-friendly text for processing)
    status_display = "Needs Setup" if status_lower == "processing" else clean_status.capitalize()
    
    # Determine if animal is adoptable (only healthy animals can be adopted, not processing)
    is_adoptable = status_lower in ("healthy", "available", "adoptable", "ready")
    
    # Animal image
    if photo_base64:
        animal_image = ft.Container(
            content=ft.Image(
                src_base64=photo_base64,
                width=130,
                height=130,
                fit=ft.ImageFit.COVER,
                border_radius=8,
            ),
            width=130,
            height=130,
            border_radius=8,
        )
    else:
        animal_image = ft.Container(
            ft.Icon(ft.Icons.PETS, size=48, color=ft.Colors.GREY_400),
            width=130,
            height=130,
            bgcolor=ft.Colors.GREY_300,
            border_radius=8,
            alignment=ft.alignment.center,
        )
    
    # Action buttons
    if is_admin and on_edit:
        # For adopted animals, just show Edit (no edit for adopted animals)
        if status_lower == "adopted":
            # Show archive/remove for adopted animals
            if on_archive or on_remove:
                buttons = ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARCHIVE_OUTLINED,
                        icon_color=ft.Colors.AMBER_700,
                        icon_size=20,
                        tooltip="Archive",
                        on_click=lambda e: on_archive(animal_id) if on_archive else None,
                    ) if on_archive else ft.Container(),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ft.Colors.RED_600,
                        icon_size=20,
                        tooltip="Remove",
                        on_click=lambda e: on_remove(animal_id) if on_remove else None,
                    ) if on_remove else ft.Container(),
                ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)
            else:
                buttons = ft.Container()  # No actions for adopted animals
        else:
            # Build admin action buttons
            action_buttons = []
            
            # Edit button
            action_buttons.append(
                ft.ElevatedButton(
                    "Edit",
                    width=80,
                    height=32,
                    on_click=lambda e: on_edit(animal_id) if on_edit else None,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.TEAL_600,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=6),
                        text_style=ft.TextStyle(size=11),
                    )
                ),
            )
            
            # Archive/Remove icons
            if on_archive or on_remove:
                action_buttons.append(
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.ARCHIVE_OUTLINED,
                            icon_color=ft.Colors.AMBER_700,
                            icon_size=18,
                            tooltip="Archive",
                            on_click=lambda e: on_archive(animal_id) if on_archive else None,
                        ) if on_archive else ft.Container(),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_600,
                            icon_size=18,
                            tooltip="Remove",
                            on_click=lambda e: on_remove(animal_id) if on_remove else None,
                        ) if on_remove else ft.Container(),
                    ], spacing=0, tight=True)
                )
            
            buttons = ft.Row(action_buttons, spacing=4, alignment=ft.MainAxisAlignment.CENTER)
    elif show_adopt_button and on_adopt:
        if is_adoptable:
            buttons = ft.Row([
                ft.ElevatedButton(
                    "Adopt",
                    width=120,
                    height=35,
                    on_click=lambda e: on_adopt(animal_id),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.TEAL_400,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=20),
                        text_style=ft.TextStyle(size=12),
                    )
                ),
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER)
        else:
            # Show disabled button or status message for non-adoptable animals
            if status_lower == "adopted":
                buttons = ft.Container(
                    ft.Text("Already Adopted", size=11, color=ft.Colors.PURPLE_600, weight="w500"),
                    padding=ft.padding.symmetric(vertical=8),
                )
            else:
                buttons = ft.Container(
                    ft.Text("Not Available", size=11, color=ft.Colors.GREY_500, weight="w500"),
                    padding=ft.padding.symmetric(vertical=8),
                )
    else:
        buttons = ft.Container()
    
    # Wrap image with "Rescued" badge overlay if animal came from rescue mission
    if is_rescued:
        # For admin, add clickable info button inside the badge
        if is_admin and rescue_info:
            # Format rescue date
            rescue_date = rescue_info.get("date", "")
            if rescue_date:
                try:
                    from datetime import datetime
                    if isinstance(rescue_date, str):
                        dt = datetime.fromisoformat(rescue_date.replace('Z', '+00:00'))
                        rescue_date = dt.strftime("%b %d, %Y")
                except:
                    pass
            
            location = rescue_info.get("location", "Unknown location")
            reporter = rescue_info.get("reporter", "Unknown")
            urgency = rescue_info.get("urgency", "Unknown").capitalize()
            description = rescue_info.get("description", "")
            
            # Store info for the dialog callback
            info_data = {
                "location": location,
                "date": rescue_date,
                "reporter": reporter,
                "urgency": urgency,
                "description": description,
                "name": name,
            }
            
            def show_rescue_info(e, data=info_data):
                page = e.page
                if not page:
                    return
                
                # Build content with description if available
                content_items = [
                    ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=18, color=ft.Colors.TEAL_600), 
                           ft.Text("Location:", weight="w600", size=13)], spacing=8),
                    ft.Text(data["location"], size=12, color=ft.Colors.BLACK87),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Row([ft.Icon(ft.Icons.CALENDAR_TODAY, size=18, color=ft.Colors.TEAL_600),
                           ft.Text("Rescue Date:", weight="w600", size=13)], spacing=8),
                    ft.Text(data["date"] or "Not recorded", size=12, color=ft.Colors.BLACK87),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Row([ft.Icon(ft.Icons.PERSON, size=18, color=ft.Colors.TEAL_600),
                           ft.Text("Reported By:", weight="w600", size=13)], spacing=8),
                    ft.Text(data["reporter"] or "Anonymous", size=12, color=ft.Colors.BLACK87),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, size=18, color=ft.Colors.ORANGE_600),
                           ft.Text("Urgency Level:", weight="w600", size=13)], spacing=8),
                    ft.Text(data["urgency"], size=12, color=ft.Colors.BLACK87),
                ]
                
                # Add description if available
                if data["description"]:
                    content_items.extend([
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        ft.Row([ft.Icon(ft.Icons.DESCRIPTION, size=18, color=ft.Colors.TEAL_600),
                               ft.Text("Description:", weight="w600", size=13)], spacing=8),
                        ft.Text(data["description"], size=12, color=ft.Colors.BLACK87),
                    ])
                
                dlg = ft.AlertDialog(
                    title=ft.Text(f"Rescue Details: {data['name']}", size=16, weight="bold"),
                    content=ft.Container(
                        ft.Column(content_items, spacing=2, tight=True, scroll=ft.ScrollMode.AUTO),
                        width=300,
                        height=280,
                        padding=10,
                    ),
                    actions=[
                        ft.TextButton("Close", on_click=lambda e: page.close(dlg)),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                page.open(dlg)
            
            # Badge with info icon inside
            badge_content = ft.Container(
                ft.Row([
                    ft.Text("Rescued", size=9, color=ft.Colors.WHITE, weight="w600"),
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=12, color=ft.Colors.WHITE),
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.ORANGE_600,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                border_radius=8,
                on_click=show_rescue_info,
                tooltip="Click for rescue details",
            )
        else:
            # Regular badge without info button (for non-admin or no rescue info)
            badge_content = ft.Container(
                ft.Text("Rescued", size=9, color=ft.Colors.WHITE, weight="w600"),
                bgcolor=ft.Colors.ORANGE_600,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                border_radius=8,
            )
        
        image_with_badge = ft.Stack([
            animal_image,
            ft.Container(
                badge_content,
                right=5,
                top=5,
            ),
        ])
    else:
        image_with_badge = animal_image
    
    # Build card content
    card_content = [
        image_with_badge,
        ft.Container(height=10),
        ft.Text(f"{name}, {age}yrs old" if age else name, size=14, weight="bold", color=ft.Colors.BLACK87),
        ft.Text(species.capitalize(), size=12, color=ft.Colors.BLACK54),
        ft.Text(status_display, size=12, color=status_color, weight="w500"),
    ]
    
    card_content.append(ft.Container(height=8))
    card_content.append(buttons)
    
    return ft.Container(
        ft.Column(card_content, horizontal_alignment="center", spacing=0),
        width=180,
        padding=15,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        border=ft.border.all(1, ft.Colors.GREY_300),
        shadow=_get_card_shadow(),
    )


__all__ = [
    "create_section_card",
    "create_chart_container",
    "create_page_title",
    "create_empty_state",
    "create_data_table",
    "create_stat_card",
    "create_map_container",
    "create_animal_card",
]
