"""Reusable interactive chart components using Flet's native chart controls.

These components provide interactive charts with tooltips, animations,
hover effects, click handlers, and toggleable legends.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple, Callable

try:
    import flet as ft
except ImportError:
    ft = None


# Color palettes for charts
CHART_COLORS = {
    "primary": "#26A69A",     # Teal
    "secondary": "#FFA726",    # Orange
    "success": "#4CAF50",      # Green
    "warning": "#FFEB3B",      # Yellow
    "danger": "#F44336",       # Red
    "info": "#2196F3",         # Blue
    "purple": "#9C27B0",       # Purple
    "pink": "#E91E63",         # Pink
}

PIE_CHART_COLORS = [
    "#2196F3",  # Blue
    "#FFA726",  # Orange
    "#66BB6A",  # Green
    "#EF5350",  # Red
    "#AB47BC",  # Purple
    "#26C6DA",  # Cyan
    "#FFEE58",  # Yellow
    "#8D6E63",  # Brown
]

STATUS_COLORS = {
    # Health status
    "healthy": "#4CAF50",
    "recovering": "#FFC107",
    "injured": "#F44336",
    # Rescue status
    "pending": "#2196F3",
    "on-going": "#FFA726",
    "rescued": "#4CAF50",
    "failed": "#F44336",
    # Adoption status
    "approved": "#4CAF50",
    "denied": "#F44336",
    # Urgency
    "low": "#4CAF50",
    "medium": "#FFA726",
    "high": "#F44336",
    # Default fallback
    "default": "#9E9E9E",
}


def create_empty_chart_message(message: str = "No Data Available", height: int = 200, width: Optional[int] = None) -> Any:
    """Create an empty state message for charts with no data.
    
    Args:
        message: The message to display
        height: Height of the container
        width: Width of the container (optional)
        
    Returns:
        A Flet container with the empty state message
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, size=48, color=ft.Colors.GREY_400),
                ft.Text(message, size=14, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
        height=height,
        width=width,
        alignment=ft.alignment.center,
    )


def create_line_chart(
    data_series: List[Dict[str, Any]],
    height: int = 200,
    width: Optional[int] = None,
    show_grid: bool = True,
    animate: bool = True,
    x_labels: Optional[List[str]] = None,
    on_point_click: Optional[Callable[[int, int, float], None]] = None,
) -> Any:
    """Create an interactive line chart using Flet's LineChart control.
    
    Args:
        data_series: List of series dicts with keys:
            - label: Series name for legend
            - color: Line color
            - values: List of (x, y) tuples
        height: Chart height
        width: Chart width (optional)
        show_grid: Whether to show grid lines
        animate: Whether to animate chart
        x_labels: Optional list of labels for x-axis (e.g., dates)
        on_point_click: Callback when a point is clicked (series_idx, x, y)
        
    Returns:
        A Flet LineChart control or empty state if no data
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    # Check if any data exists
    has_data = False
    max_x = 0
    max_y = 0
    
    for series in data_series:
        values = series.get("values", [])
        for x, y in values:
            if y > 0:
                has_data = True
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    
    if not has_data:
        return create_empty_chart_message("No Data Available", height, width)
    
    # Build data series for LineChart
    chart_data_series = []
    
    for series_idx, series in enumerate(data_series):
        label = series.get("label", "")
        color = series.get("color", CHART_COLORS["primary"])
        values = series.get("values", [])
        
        # Create data points with tooltips
        data_points = []
        for x, y in values:
            # Use date label in tooltip if provided
            if x_labels and 0 <= x < len(x_labels):
                tooltip_text = f"{x_labels[x]}\n{label}: {y}"
            else:
                tooltip_text = f"{label}: {y}"
            
            point = ft.LineChartDataPoint(
                x=x,
                y=y,
                tooltip=tooltip_text,
            )
            data_points.append(point)
        
        chart_data_series.append(
            ft.LineChartData(
                data_points=data_points,
                stroke_width=3,
                color=color,
                curved=True,
                stroke_cap_round=True,
                point=True,
                below_line_bgcolor=ft.Colors.with_opacity(0.1, color),
            )
        )
    
    # Calculate y-axis max with padding
    y_max = max(10, int(max_y * 1.2) + 1)
    
    # Create x-axis labels (show every 5th for many points)
    step = max(1, (max_x + 1) // 6)
    bottom_labels = []
    for i in range(0, max_x + 1, step):
        # Use provided labels or default to index
        label_text = x_labels[i] if x_labels and i < len(x_labels) else str(i)
        # Strip "Date: " prefix for x-axis display
        if label_text.startswith("Date: "):
            label_text = label_text[6:]
        bottom_labels.append(
            ft.ChartAxisLabel(
                value=i,
                label=ft.Text(label_text, size=10, color=ft.Colors.GREY_600),
            )
        )
    
    # Create y-axis labels
    y_step = max(1, y_max // 5)
    left_labels = []
    for i in range(0, y_max + 1, y_step):
        left_labels.append(
            ft.ChartAxisLabel(
                value=i,
                label=ft.Text(str(i), size=10, color=ft.Colors.GREY_600),
            )
        )
    
    chart = ft.LineChart(
        data_series=chart_data_series,
        min_x=0,
        max_x=max_x + 2,  # Add padding on right for tooltip overflow
        min_y=0,
        max_y=y_max,
        interactive=True,
        expand=width is None,
        height=height,
        width=width,
        animate=ft.Animation(600, ft.AnimationCurve.EASE_OUT) if animate else None,
        tooltip_bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.GREY_900),
        tooltip_rounded_radius=10,
        left_axis=ft.ChartAxis(
            labels=left_labels,
            labels_size=40,
        ),
        bottom_axis=ft.ChartAxis(
            labels=bottom_labels,
            labels_size=30,
        ),
        horizontal_grid_lines=ft.ChartGridLines(
            color=ft.Colors.GREY_300,
            width=1,
            dash_pattern=[3, 3],
        ) if show_grid else None,
        vertical_grid_lines=ft.ChartGridLines(
            color=ft.Colors.GREY_200,
            width=1,
            dash_pattern=[3, 3],
        ) if show_grid else None,
    )
    
    return chart


def create_bar_chart(
    bar_groups: List[Dict[str, Any]],
    bottom_labels: Optional[Dict[int, str]] = None,
    height: int = 200,
    width: Optional[int] = None,
    animate: bool = True,
    on_bar_click: Optional[Callable[[int, str, float], None]] = None,
    legend_refs: Optional[Dict[str, Any]] = None,
) -> Any:
    """Create an interactive bar chart using Flet's BarChart control.
    
    Args:
        bar_groups: List of group dicts with keys:
            - x: X position (int)
            - rods: List of rod dicts with 'value', 'color', 'width'
        bottom_labels: Dict mapping x position to label string
        height: Chart height
        width: Chart width (optional)
        animate: Whether to animate chart
        on_bar_click: Callback when bar is clicked (x, label, value)
        legend_refs: Optional dict to store references for legend-bar sync
        
    Returns:
        A Flet BarChart control or empty state if no data
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    # Check if any data exists
    has_data = False
    max_y = 0
    for group in bar_groups:
        for rod in group.get("rods", []):
            value = rod.get("value", 0)
            if value > 0:
                has_data = True
            max_y = max(max_y, value)
    
    if not has_data:
        return create_empty_chart_message("No Data Available", height, width)
    
    # Build bar groups for Flet with hover effects
    flet_bar_groups = []
    for group in bar_groups:
        x = group.get("x", 0)
        rods = []
        for rod in group.get("rods", []):
            value = rod.get("value", 0)
            color = rod.get("color", PIE_CHART_COLORS[0])
            rod_width = rod.get("width", 25)
            label = bottom_labels.get(x, "") if bottom_labels else ""
            
            rods.append(
                ft.BarChartRod(
                    from_y=0,
                    to_y=value,
                    width=rod_width,
                    color=color,
                    tooltip=f"{label}: {value}" if label else str(value),
                    border_radius=ft.border_radius.only(top_left=6, top_right=6),
                )
            )
        flet_bar_groups.append(ft.BarChartGroup(x=x, bar_rods=rods))
    
    # Calculate y-axis max with padding
    y_max = max(5, int(max_y * 1.2) + 1)
    
    # Create bottom axis labels
    axis_bottom_labels = []
    if bottom_labels:
        for x_val, label in bottom_labels.items():
            axis_bottom_labels.append(
                ft.ChartAxisLabel(
                    value=x_val,
                    label=ft.Container(
                        ft.Text(label[:12], size=10, color=ft.Colors.GREY_600),
                        padding=ft.padding.only(top=5),
                    ),
                )
            )
    
    # Create left axis labels
    y_step = max(1, y_max // 5)
    left_labels = [
        ft.ChartAxisLabel(
            value=i,
            label=ft.Text(str(i), size=10, color=ft.Colors.GREY_600),
        )
        for i in range(0, y_max + 1, y_step)
    ]
    
    chart = ft.BarChart(
        bar_groups=flet_bar_groups,
        min_y=0,
        max_y=y_max,
        interactive=True,
        expand=width is None,
        height=height,
        width=width,
        animate=ft.Animation(600, ft.AnimationCurve.EASE_OUT) if animate else None,
        tooltip_bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.GREY_900),
        tooltip_rounded_radius=10,
        left_axis=ft.ChartAxis(
            labels=left_labels,
            labels_size=40,
        ),
        bottom_axis=ft.ChartAxis(
            labels=axis_bottom_labels,
            labels_size=40,
        ),
        horizontal_grid_lines=ft.ChartGridLines(
            color=ft.Colors.GREY_300,
            width=1,
            dash_pattern=[3, 3],
        ),
    )
    
    # Store reference to chart and bar groups for legend sync
    if legend_refs is not None:
        legend_refs["chart"] = chart
        legend_refs["bar_groups"] = flet_bar_groups
        legend_refs["base_width"] = 25  # Default rod width for scaling
    
    return chart


def create_pie_chart(
    sections: List[Dict[str, Any]],
    height: int = 200,
    width: Optional[int] = None,
    center_space_radius: int = 0,
    section_radius: int = 80,
    animate: bool = True,
    on_section_click: Optional[Callable[[str, float], None]] = None,
    legend_refs: Optional[Dict[int, Any]] = None,
) -> Any:
    """Create an interactive pie chart with hover expand effect.
    
    Args:
        sections: List of section dicts with keys:
            - value: Numeric value for the section
            - title: Label to display on section
            - color: Section color
        height: Chart height
        width: Chart width (optional)
        center_space_radius: Radius of center space (for donut chart)
        section_radius: Radius of sections
        animate: Whether to animate chart
        on_section_click: Callback when section is clicked (title, value)
        legend_refs: Optional dict to store references for legend-pie sync
        
    Returns:
        A Flet PieChart control or empty state if no data
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    # Filter out zero/empty values
    filtered_sections = [s for s in sections if s.get("value", 0) > 0]
    
    if not filtered_sections:
        return create_empty_chart_message("No Data Available", height, width)
    
    # Store the base radius for hover effects
    base_radius = section_radius
    
    # Build sections for Flet with hover effects
    flet_sections = []
    total_value = sum(s.get("value", 0) for s in filtered_sections)
    
    for i, section in enumerate(filtered_sections):
        value = section.get("value", 0)
        title = section.get("title", "")
        color = section.get("color", PIE_CHART_COLORS[i % len(PIE_CHART_COLORS)])
        
        # Create the section with styling
        flet_sections.append(
            ft.PieChartSection(
                value=value,
                color=color,
                radius=section_radius,
                title=title,
                title_style=ft.TextStyle(
                    size=11,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.BOLD,
                ),
                title_position=0.5,
            )
        )
    
    def on_chart_event(e):
        """Handle pie chart hover events for expand effect."""
        for idx, section in enumerate(flet_sections):
            if idx == e.section_index:
                section.radius = base_radius + 10  # Expand on hover
            else:
                section.radius = base_radius
        e.control.update()
    
    chart = ft.PieChart(
        sections=flet_sections,
        center_space_radius=center_space_radius,
        sections_space=2,
        animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT) if animate else None,
        expand=width is None,
        height=height,
        width=width,
        on_chart_event=on_chart_event,
    )
    
    # Store reference to chart and sections for legend sync
    if legend_refs is not None:
        legend_refs["chart"] = chart
        legend_refs["sections"] = flet_sections
        legend_refs["base_radius"] = base_radius
    
    return chart


def create_chart_legend(
    items: List[Dict[str, Any]],
    horizontal: bool = True,
    pie_refs: Optional[Dict[str, Any]] = None,
    bar_refs: Optional[Dict[str, Any]] = None,
) -> Any:
    """Create a legend for charts with hover effects that sync with chart sections.
    
    Args:
        items: List of dicts with 'label', 'color', and optionally 'value'
        horizontal: Whether to layout horizontally
        pie_refs: Optional dict with 'chart', 'sections', 'base_radius' for pie sync
        bar_refs: Optional dict with 'chart', 'bar_groups' for bar sync
        
    Returns:
        A Flet control with the legend
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    # Build a mapping from legend index to actual chart section index
    # This handles cases where items with value=0 are filtered out of the chart
    legend_to_section_map = {}
    section_idx = 0
    for legend_idx, item in enumerate(items):
        value = item.get("value", 0)
        if value is not None and value > 0:
            legend_to_section_map[legend_idx] = section_idx
            section_idx += 1
        else:
            legend_to_section_map[legend_idx] = -1  # No corresponding section
    
    legend_items = []
    for idx, item in enumerate(items):
        label = item.get("label", "")
        color = item.get("color", ft.Colors.GREY_500)
        value = item.get("value")
        
        text = f"{label}"
        if value is not None:
            text = f"{label} ({value})"
        
        # Color indicator with subtle border
        color_box = ft.Container(
            width=12,
            height=12,
            bgcolor=color,
            border_radius=3,
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.BLACK)),
        )
        
        # Create hover handler that syncs with pie or bar chart
        def make_hover_handler(legend_idx: int):
            # Get the actual section index for this legend item
            actual_section_idx = legend_to_section_map.get(legend_idx, -1)
            
            def on_legend_hover(e):
                # Apply hover effect to legend item
                if e.data == "true":
                    e.control.bgcolor = ft.Colors.with_opacity(0.08, ft.Colors.BLACK)
                    e.control.scale = 1.03
                    # Sync with pie chart section (only if this item has a section)
                    if actual_section_idx >= 0 and pie_refs and "sections" in pie_refs and "chart" in pie_refs:
                        sections = pie_refs["sections"]
                        base_radius = pie_refs.get("base_radius", 80)
                        for i, section in enumerate(sections):
                            if i == actual_section_idx:
                                section.radius = base_radius + 10
                            else:
                                section.radius = base_radius
                        pie_refs["chart"].update()
                    # Sync with bar chart (only if this item has a bar)
                    if actual_section_idx >= 0 and bar_refs and "bar_groups" in bar_refs and "chart" in bar_refs:
                        bar_groups = bar_refs["bar_groups"]
                        for i, group in enumerate(bar_groups):
                            for rod in group.bar_rods:
                                if i == actual_section_idx:
                                    rod.width = 50  # Expand width on hover
                                else:
                                    rod.width = 40  # Normal width
                        bar_refs["chart"].update()
                else:
                    e.control.bgcolor = None
                    e.control.scale = 1.0
                    # Reset pie chart sections
                    if pie_refs and "sections" in pie_refs and "chart" in pie_refs:
                        sections = pie_refs["sections"]
                        base_radius = pie_refs.get("base_radius", 80)
                        for section in sections:
                            section.radius = base_radius
                        pie_refs["chart"].update()
                    # Reset bar chart
                    if bar_refs and "bar_groups" in bar_refs and "chart" in bar_refs:
                        bar_groups = bar_refs["bar_groups"]
                        for group in bar_groups:
                            for rod in group.bar_rods:
                                rod.width = 40  # Reset to normal
                        bar_refs["chart"].update()
                e.control.update()
            return on_legend_hover
        
        # Interactive legend item
        legend_item = ft.Container(
            content=ft.Row([color_box, ft.Text(text, size=11, color=ft.Colors.GREY_700)], spacing=6),
            padding=ft.padding.symmetric(horizontal=6, vertical=4),
            border_radius=6,
            on_hover=make_hover_handler(idx),
            animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
        )
        
        legend_items.append(legend_item)
    
    if horizontal:
        return ft.Row(legend_items, spacing=15, wrap=True)
    else:
        return ft.Column(legend_items, spacing=8)


def create_insight_card(
    text: str,
    bgcolor: Optional[str] = None,
    icon: Optional[str] = None,
) -> Any:
    """Create an insight card to display key findings or text.
    
    Args:
        text: The insight text to display
        bgcolor: Background color (optional)
        icon: Icon name (optional)
        
    Returns:
        A Flet container with the insight
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    # Determine icon and border color based on bgcolor
    if bgcolor == ft.Colors.BLUE_50:
        border_color = ft.Colors.BLUE_200
        icon_color = ft.Colors.BLUE_600
        default_icon = ft.Icons.PETS
    elif bgcolor == ft.Colors.ORANGE_50:
        border_color = ft.Colors.ORANGE_200
        icon_color = ft.Colors.ORANGE_600
        default_icon = ft.Icons.FAVORITE
    elif bgcolor == ft.Colors.GREEN_50:
        border_color = ft.Colors.GREEN_200
        icon_color = ft.Colors.GREEN_600
        default_icon = ft.Icons.HEALTH_AND_SAFETY
    else:
        border_color = ft.Colors.GREY_300
        icon_color = ft.Colors.GREY_600
        default_icon = ft.Icons.LIGHTBULB_OUTLINE
    
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon or default_icon, size=20, color=icon_color),
            ft.Container(width=8),
            ft.Text(text, size=12, color=ft.Colors.BLACK87, expand=True),
        ], vertical_alignment=ft.CrossAxisAlignment.START),
        padding=ft.padding.all(14),
        border_radius=10,
        bgcolor=bgcolor or ft.Colors.GREY_100,
        border=ft.border.all(1, border_color),
        expand=True,
    )


def create_clickable_stat_card(
    title: str,
    value: str,
    subtitle: str = "",
    icon: Optional[object] = None,
    icon_color: Optional[str] = None,
    on_click: Optional[Callable] = None,
) -> object:
    """Create an interactive statistics card with hover glow effect.
    
    Args:
        title: Card title
        value: Main value to display
        subtitle: Subtitle/change indicator
        icon: Icon to display
        icon_color: Color for the icon
        on_click: Callback when card is clicked
        
    Returns:
        A Flet container with the interactive stat card
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    # Determine subtitle styling
    if "+" in subtitle:
        subtitle_color = ft.Colors.GREEN_600
        subtitle_icon = ft.Icons.TRENDING_UP
    elif "-" in subtitle:
        subtitle_color = ft.Colors.RED_600
        subtitle_icon = ft.Icons.TRENDING_DOWN
    else:
        subtitle_color = ft.Colors.GREY_600
        subtitle_icon = ft.Icons.REMOVE
    
    card_content = ft.Column([
        ft.Row([
            ft.Icon(icon or ft.Icons.INFO, size=20, color=icon_color or ft.Colors.TEAL_600),
            ft.Text(title, size=12, color=ft.Colors.BLACK54, weight="w500"),
        ], spacing=8),
        ft.Container(height=5),
        ft.Text(value, size=32, weight="bold", color=icon_color or ft.Colors.BLACK87),
        ft.Row([
            ft.Icon(subtitle_icon, size=14, color=subtitle_color),
            ft.Text(subtitle, size=11, color=subtitle_color),
        ], spacing=4),
    ], spacing=3)
    
    def on_hover(e):
        if e.data == "true":
            # Subtle glow effect (no scale, no layout shift)
            # Keep border width constant at 2px to prevent layout shift
            e.control.shadow = ft.BoxShadow(
                blur_radius=12,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.25, icon_color or ft.Colors.TEAL_600),
                offset=(0, 2),
            )
            e.control.border = ft.border.all(2, ft.Colors.with_opacity(0.5, icon_color or ft.Colors.TEAL_600))
        else:
            e.control.shadow = ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2))
            e.control.border = ft.border.all(2, ft.Colors.TRANSPARENT)  # Keep 2px but transparent
        e.control.update()
    
    return ft.Container(
        content=card_content,
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        border=ft.border.all(2, ft.Colors.TRANSPARENT),  # Start with 2px transparent border
        shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        on_hover=on_hover,
        on_click=on_click,
        expand=True,
    )


def show_chart_details_dialog(
    page: Any,
    title: str,
    data: List[Dict[str, Any]],
    chart_type: str = "bar",
) -> None:
    """Show a dialog with detailed breakdown of chart data.
    
    Args:
        page: Flet page
        title: Dialog title
        data: List of dicts with 'label', 'value', 'color', 'percentage'
        chart_type: Type of chart data ('bar', 'pie', 'line')
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    total = sum(d.get("value", 0) for d in data)
    
    # Build data rows
    rows = []
    for item in data:
        label = item.get("label", "Unknown")
        value = item.get("value", 0)
        color = item.get("color", ft.Colors.GREY_500)
        pct = (value / total * 100) if total > 0 else 0
        
        rows.append(
            ft.Container(
                ft.Row([
                    ft.Container(width=16, height=16, bgcolor=color, border_radius=4),
                    ft.Text(label, size=13, weight="w500", expand=True),
                    ft.Text(str(value), size=13, color=ft.Colors.BLACK87),
                    ft.Container(
                        ft.Text(f"{pct:.1f}%", size=11, color=ft.Colors.WHITE, weight="bold"),
                        bgcolor=color,
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        border_radius=10,
                    ),
                ], spacing=12, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(vertical=8, horizontal=12),
                border_radius=8,
                bgcolor=ft.Colors.with_opacity(0.05, color),
            )
        )
    
    # Add total row
    rows.append(ft.Divider(height=16))
    rows.append(
        ft.Container(
            ft.Row([
                ft.Icon(ft.Icons.SUMMARIZE, size=18, color=ft.Colors.TEAL_600),
                ft.Text("Total", size=14, weight="bold", expand=True),
                ft.Text(str(total), size=14, weight="bold", color=ft.Colors.TEAL_600),
            ], spacing=12),
            padding=ft.padding.symmetric(vertical=8, horizontal=12),
            bgcolor=ft.Colors.TEAL_50,
            border_radius=8,
        )
    )
    
    dlg = ft.AlertDialog(
        title=ft.Row([
            ft.Icon(ft.Icons.ANALYTICS, size=24, color=ft.Colors.TEAL_600),
            ft.Text(title, size=18, weight="bold"),
        ], spacing=10),
        content=ft.Container(
            ft.Column(rows, spacing=6, scroll=ft.ScrollMode.AUTO),
            width=380,
            height=min(len(data) * 60 + 80, 400),
            padding=10,
        ),
        actions=[
            ft.TextButton("Close", on_click=lambda e: page.close(dlg)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(dlg)


def create_chart_card(
    title: str,
    chart: Any,
    legend: Optional[Any] = None,
    insights: Optional[List[Any]] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> Any:
    """Create a card container for a chart with title, legend, and insights.
    
    Args:
        title: Chart title
        chart: The chart control
        legend: Optional legend control
        insights: Optional list of insight cards
        width: Container width
        height: Container height
        
    Returns:
        A styled container with the chart
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    content = [
        ft.Text(title, size=15, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
        ft.Divider(height=10, color=ft.Colors.GREY_300),
        chart,
    ]
    
    if legend:
        content.append(ft.Container(height=10))
        content.append(legend)
    
    if insights:
        content.append(ft.Container(height=10))
        content.append(
            ft.Row(insights, spacing=10, wrap=True)
        )
    
    return ft.Container(
        content=ft.Column(content, spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=width,
        height=height,
        padding=15,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        shadow=ft.BoxShadow(
            blur_radius=8,
            spread_radius=1,
            color=ft.Colors.BLACK12,
            offset=ft.Offset(0, 2),
        ),
    )


__all__ = [
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
    "create_chart_card",
]
