"""AI Suggestion Card component for displaying classification results.

This component shows the AI's detected species and breed with confidence scores,
and allows the user to accept the suggestion or enter manually.
"""
from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import flet as ft

from models.classification_result import ClassificationResult


def create_ai_suggestion_card(
    result: ClassificationResult,
    on_accept: Optional[Callable[[str, str], None]] = None,
    on_dismiss: Optional[Callable[[], None]] = None,
) -> "ft.Container":
    """Create an AI suggestion card showing classification results.
    
    Args:
        result: The ClassificationResult from AI classification
        on_accept: Callback when user accepts suggestion. Called with (species, breed)
        on_dismiss: Callback when user dismisses the suggestion
    
    Returns:
        Flet Container with the suggestion card
    """
    import flet as ft
    
    if result.error:
        # Error state
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_400, size=20),
                            ft.Text("AI Analysis Failed", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400),
                        ],
                        spacing=8,
                    ),
                    ft.Text(result.error, size=12, color=ft.Colors.RED_300),
                    ft.Row(
                        controls=[
                            ft.TextButton(
                                content=ft.Text("Enter Manually", size=12),
                                on_click=lambda e: on_dismiss() if on_dismiss else None,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.RED),
            border=ft.border.all(1, ft.Colors.RED_700),
            border_radius=10,
            padding=15,
        )
    
    # Success state - show results
    species = result.species
    breed = result.breed
    species_conf = result.species_confidence
    breed_conf = result.breed_confidence
    
    # Confidence color
    def get_confidence_color(conf: float) -> str:
        if conf >= 0.75:
            return ft.Colors.GREEN_400
        elif conf >= 0.50:
            return ft.Colors.YELLOW_600
        else:
            return ft.Colors.ORANGE_400
    
    def format_confidence(conf: float) -> str:
        return f"{conf * 100:.1f}%"
    
    breed_content = []
    
    if result.is_mixed_breed:
        # Mixed breed suggestion
        breed_content.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.PETS, size=16, color=ft.Colors.AMBER_700),
                        ft.Text(
                            breed,
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=ft.Colors.AMBER_700,
                        ),
                    ],
                    spacing=6,
                ),
            )
        )
        
        if result.alternative_breeds:
            alt_text = "Possible breeds: " + ", ".join(
                [f"{alt.breed} ({format_confidence(alt.confidence)})" 
                 for alt in result.alternative_breeds[:2]]
            )
            breed_content.append(
                ft.Text(alt_text, size=11, color=ft.Colors.GREY_600, italic=True)
            )
    else:
        # Specific breed detected
        breed_content.append(
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PETS, size=16, color=ft.Colors.TEAL_700),
                    ft.Text(breed, size=14, weight=ft.FontWeight.W_500, color=ft.Colors.BLACK87),
                    ft.Container(
                        content=ft.Text(
                            format_confidence(breed_conf),
                            size=10,
                            color=ft.Colors.WHITE,
                        ),
                        bgcolor=get_confidence_color(breed_conf),
                        padding=ft.padding.symmetric(horizontal=5, vertical=1),
                        border_radius=8,
                    ),
                ],
                spacing=6,
            )
        )
        
        if result.alternative_breeds:
            alt_text = "Also possible: " + ", ".join(
                [alt.breed for alt in result.alternative_breeds[:2]]
            )
            breed_content.append(
                ft.Text(alt_text, size=11, color=ft.Colors.GREY_600, italic=True)
            )
    
    return ft.Container(
        content=ft.Column(
            controls=[
                # Header
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.PURPLE_700, size=20),
                        ft.Text("AI Suggestion", weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                    ],
                    spacing=8,
                ),
                
                ft.Divider(height=1, color=ft.Colors.PURPLE_200),
                
                # Species row
                ft.Row(
                    controls=[
                        ft.Text(result.species_emoji, size=24),
                        ft.Text(
                            f"Species: {species}",
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=ft.Colors.BLACK87,
                        ),
                        ft.Container(
                            content=ft.Text(
                                format_confidence(species_conf),
                                size=11,
                                color=ft.Colors.WHITE,
                            ),
                            bgcolor=get_confidence_color(species_conf),
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=10,
                        ),
                    ],
                    spacing=8,
                ),
                
                # Breed section
                ft.Container(
                    content=ft.Column(
                        controls=breed_content,
                        spacing=4,
                    ),
                    padding=ft.padding.only(left=32),
                ),
                
                ft.Divider(height=1, color=ft.Colors.PURPLE_200),
                
                # Action buttons
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.EDIT, size=14, color=ft.Colors.GREY_700),
                                    ft.Text("Enter Manually", size=12, color=ft.Colors.GREY_700),
                                ],
                                spacing=4,
                            ),
                            style=ft.ButtonStyle(
                                side=ft.BorderSide(1, ft.Colors.GREY_400),
                            ),
                            on_click=lambda e: on_dismiss() if on_dismiss else None,
                        ),
                        ft.ElevatedButton(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CHECK, size=14, color=ft.Colors.WHITE),
                                    ft.Text("Use Suggestion", size=12, weight=ft.FontWeight.W_500),
                                ],
                                spacing=4,
                            ),
                            bgcolor=ft.Colors.TEAL_600,
                            color=ft.Colors.WHITE,
                            on_click=lambda e: on_accept(species, breed) if on_accept else None,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=8,
                ),
            ],
            spacing=10,
        ),
        bgcolor=ft.Colors.PURPLE_50,
        border=ft.border.all(1, ft.Colors.PURPLE_200),
        border_radius=10,
        padding=15,
    )


def create_ai_loading_card(progress_info: Optional[dict] = None, on_cancel: Optional[Callable[[], None]] = None) -> "ft.Container":
    """Create a loading card while AI is classifying the image.
    
    Args:
        progress_info: Optional dict with 'current', 'total', and 'message' keys for download progress
        on_cancel: Optional callback to cancel download/classification
    """
    import flet as ft
    
    if progress_info and 'message' in progress_info:
        current = progress_info.get('current', 0)
        total = progress_info.get('total', 3)
        message = progress_info.get('message', 'Downloading...')
        progress_value = current / total if total > 0 else 0
        
        controls = [
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.PURPLE_600, size=20),
                    ft.Text(
                        "Downloading AI Models",
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PURPLE_700,
                    ),
                ],
                spacing=10,
            ),
            ft.Text(
                message,
                size=12,
                color=ft.Colors.GREY_700,
            ),
            ft.ProgressBar(
                value=progress_value,
                color=ft.Colors.PURPLE_600,
                bgcolor=ft.Colors.PURPLE_100,
            ),
            ft.Text(
                f"Step {current} of {total}",
                size=11,
                color=ft.Colors.GREY_600,
            ),
        ]

        if on_cancel:
            controls.append(
                ft.Row(
                    controls=[
                        ft.TextButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CLOSE, size=14, color=ft.Colors.PURPLE_700),
                                ft.Text("Cancel", size=12, color=ft.Colors.PURPLE_700),
                            ], spacing=4),
                            style=ft.ButtonStyle(
                                overlay_color=ft.Colors.PURPLE_50,
                            ),
                            on_click=lambda e: on_cancel(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=controls,
                spacing=8,
            ),
            bgcolor=ft.Colors.PURPLE_50,
            border=ft.border.all(1, ft.Colors.PURPLE_200),
            border_radius=10,
            padding=15,
        )
    
    # Regular loading (classification in progress)
    controls = [
        ft.Row(
            controls=[
                ft.ProgressRing(width=20, height=20, stroke_width=2, color=ft.Colors.PURPLE_600),
                ft.Text(
                    "Analyzing image...",
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PURPLE_700,
                ),
            ],
            spacing=10,
        ),
        ft.Text(
            "AI is detecting species and breed. This may take a moment on first run.",
            size=11,
            color=ft.Colors.GREY_600,
        ),
    ]

    if on_cancel:
        controls.append(
            ft.Row(
                controls=[
                    ft.TextButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CLOSE, size=14, color=ft.Colors.PURPLE_700),
                            ft.Text("Cancel", size=12, color=ft.Colors.PURPLE_700),
                        ], spacing=4),
                        style=ft.ButtonStyle(
                            overlay_color=ft.Colors.PURPLE_50,
                        ),
                        on_click=lambda e: on_cancel(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
            )
        )

    return ft.Container(
        content=ft.Column(
            controls=controls,
            spacing=8,
        ),
        bgcolor=ft.Colors.PURPLE_50,
        border=ft.border.all(1, ft.Colors.PURPLE_200),
        border_radius=10,
        padding=15,
    )


def create_ai_analyze_button(
    on_click: Optional[Callable[[], None]] = None,
    disabled: bool = False,
) -> "ft.ElevatedButton":
    """Create the "Analyze with AI" button.
    
    Args:
        on_click: Callback when button is clicked
        disabled: Whether the button is disabled
    
    Returns:
        Flet ElevatedButton
    """
    import flet as ft
    
    return ft.ElevatedButton(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.AUTO_AWESOME, size=16),
                ft.Text("Analyze with AI", size=12),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PURPLE_700 if not disabled else ft.Colors.with_opacity(0.4, ft.Colors.PURPLE_700),
            color=ft.Colors.WHITE if not disabled else ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
        ),
        disabled=disabled,
        on_click=lambda e: on_click() if on_click else None,
        tooltip="Use AI to detect species and breed from the photo",
    )


__all__ = [
    "create_ai_suggestion_card",
    "create_ai_loading_card",
    "create_ai_analyze_button",
]
