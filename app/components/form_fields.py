"""Form field components for consistent form styling."""
from __future__ import annotations
from typing import Callable, List, Optional

try:
    import flet as ft
except ImportError:
    ft = None


def create_form_text_field(
    hint_text: str = "",
    label: Optional[str] = None,
    width: Optional[int] = None,
    height: int = 50,
    password: bool = False,
    multiline: bool = False,
    min_lines: int = 1,
    keyboard_type: Optional[object] = None,
    prefix_icon: Optional[object] = None,
    value: str = "",
    on_change: Optional[Callable] = None,
    on_submit: Optional[Callable] = None,
    expand: Optional[bool] = None,
) -> object:
    """Create a standardized text field for forms.
    
    Args:
        hint_text: Placeholder text
        label: Optional label (uses label instead of hint if provided)
        width: Field width (None = expand to fill parent)
        height: Field height (ignored if multiline)
        password: Whether this is a password field
        multiline: Whether to allow multiple lines
        min_lines: Minimum lines for multiline fields
        keyboard_type: Keyboard type (e.g., ft.KeyboardType.NUMBER)
        prefix_icon: Icon to show at start of field
        value: Initial value
        on_change: Callback when value changes
        on_submit: Callback when Enter key is pressed
        expand: Whether to expand to fill parent (auto when width is None)
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create form fields")
    
    field_kwargs = {
        "bgcolor": ft.Colors.WHITE,
        "border_color": ft.Colors.GREY_300,
        "focused_border_color": ft.Colors.TEAL_400,
        "text_size": 14,
        "color": ft.Colors.BLACK,
        "content_padding": ft.padding.symmetric(horizontal=15, vertical=12),
    }
    
    # Responsive: use width if given, otherwise expand to fill parent
    if width is not None:
        field_kwargs["width"] = width
    
    _expand = expand if expand is not None else (width is None)
    if _expand:
        field_kwargs["expand"] = True
    
    if label:
        field_kwargs["label"] = label
    else:
        field_kwargs["hint_text"] = hint_text
    
    if prefix_icon:
        field_kwargs["prefix_icon"] = prefix_icon
    
    if password:
        field_kwargs["password"] = True
        field_kwargs["can_reveal_password"] = True
    
    if multiline:
        field_kwargs["multiline"] = True
        field_kwargs["min_lines"] = min_lines
    else:
        field_kwargs["height"] = height
    
    if keyboard_type:
        field_kwargs["keyboard_type"] = keyboard_type
    
    if value:
        field_kwargs["value"] = value
    
    if on_change:
        field_kwargs["on_change"] = on_change
    
    if on_submit:
        field_kwargs["on_submit"] = on_submit
    
    return ft.TextField(**field_kwargs)


def create_form_dropdown(
    hint_text: str = "",
    label: Optional[str] = None,
    options: Optional[List[str]] = None,
    width: Optional[int] = None,
    prefix_icon: Optional[object] = None,
    leading_icon: Optional[object] = None,
    value: Optional[str] = None,
    on_change: Optional[Callable] = None,
    menu_height: Optional[int] = None,
    expand: Optional[bool] = None,
) -> object:
    """Create a standardized dropdown for forms.
    
    Args:
        hint_text: Placeholder text
        label: Optional label
        options: List of option strings
        width: Dropdown width (None = expand to fill parent)
        prefix_icon: (Deprecated) Icon to show at start - use leading_icon instead
        leading_icon: Icon to show at start of dropdown
        value: Initial selected value
        on_change: Callback when selection changes
        menu_height: Maximum height of the dropdown menu (limits visible items)
        expand: Whether to expand to fill parent (auto when width is None)
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create form fields")
    
    dropdown_options = []
    if options:
        dropdown_options = [ft.dropdown.Option(opt) for opt in options]
    
    dropdown_kwargs = {
        "bgcolor": ft.Colors.WHITE,
        "border_color": ft.Colors.GREY_300,
        "focused_border_color": ft.Colors.TEAL_400,
        "options": dropdown_options,
    }
    
    # Responsive: use width if given, otherwise expand to fill parent
    if width is not None:
        dropdown_kwargs["width"] = width
    
    _expand = expand if expand is not None else (width is None)
    if _expand:
        dropdown_kwargs["expand"] = True
    
    if label:
        dropdown_kwargs["label"] = label
    else:
        dropdown_kwargs["hint_text"] = hint_text
    
    icon = leading_icon or prefix_icon
    if icon:
        dropdown_kwargs["leading_icon"] = icon
    
    if value is not None:
        dropdown_kwargs["value"] = value
    
    if on_change:
        dropdown_kwargs["on_change"] = on_change
    
    if menu_height is not None:
        dropdown_kwargs["menu_height"] = menu_height
    
    return ft.Dropdown(**dropdown_kwargs)


def create_form_label(
    text: str,
    icon: Optional[object] = None,
    size: int = 13,
    weight: str = "w500",
    width: Optional[int] = None,
) -> object:
    """Create a form field label with optional icon.
    
    Args:
        text: Label text
        icon: Optional icon to show before text
        size: Text size
        weight: Font weight
        width: Container width for alignment (None = expand)
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create form fields")
    
    if icon:
        content = ft.Row([
            ft.Icon(icon, size=16, color=ft.Colors.BLACK87),
            ft.Text(text, size=size, weight=weight, color=ft.Colors.BLACK87),
        ], spacing=5)
    else:
        content = ft.Text(text, size=size, weight=weight, color=ft.Colors.BLACK87)
    
    container_kwargs = {"alignment": ft.alignment.center_left}
    if width is not None:
        container_kwargs["width"] = width
    else:
        container_kwargs["expand"] = True
    
    return ft.Container(content, **container_kwargs)


def create_labeled_field(
    label: str,
    field: object,
    icon: Optional[object] = None,
    spacing: int = 8,
    width: Optional[int] = None,
) -> object:
    """Create a label + field combination.
    
    Args:
        label: Label text
        field: The form field control
        icon: Optional icon for label
        spacing: Space between label and field
        width: Width for alignment
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create form fields")
    
    return ft.Column([
        create_form_label(label, icon=icon, width=width),
        ft.Container(height=spacing),
        field,
    ], spacing=0)


__all__ = [
    "create_form_text_field",
    "create_form_dropdown",
    "create_form_label",
    "create_labeled_field",
]
