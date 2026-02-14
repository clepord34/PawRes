"""Reusable interactive chart components using Flet's native chart controls.

These components provide interactive charts with tooltips, animations,
hover effects, click handlers, and toggleable legends.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Callable

try:
    import flet as ft
except ImportError:
    ft = None


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
    "healthy": "#4CAF50",
    "recovering": "#FFC107",
    "injured": "#F44336",
    "pending": "#2196F3",
    "on-going": "#FFA726",
    "rescued": "#4CAF50",
    "failed": "#F44336",
    "approved": "#4CAF50",
    "denied": "#F44336",
    "low": "#4CAF50",
    "medium": "#FFA726",
    "high": "#F44336",
    "default": "#9E9E9E",
}


def create_empty_chart_message(message: str = "No Data Available", height: int = 200, width: Optional[int] = None,
                               button_text: Optional[str] = None, button_icon: Optional[object] = None,
                               on_click: Optional[Callable] = None) -> Any:
    """Create an empty state message for charts with no data.
    
    Args:
        message: The message to display
        height: Height of the container
        width: Width of the container (optional)
        button_text: Optional text for an action button
        button_icon: Optional icon for the action button
        on_click: Optional callback when button is clicked
        
    Returns:
        A Flet container with the empty state message
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    content_items = [
        ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, size=48, color=ft.Colors.GREY_400),
        ft.Text(message, size=14, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
    ]
    
    if button_text and on_click:
        content_items.append(ft.Container(height=8))
        content_items.append(
            ft.ElevatedButton(
                text=button_text,
                icon=button_icon,
                on_click=on_click,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.TEAL_600,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                ),
            )
        )
    
    return ft.Container(
        content=ft.Column(
            content_items,
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
    legend_refs: Optional[Dict[str, Any]] = None,
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
        legend_refs: Optional dict to store references for legend sync
        
    Returns:
        A Flet LineChart control or empty state if no data
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
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
    
    chart_data_series = []
    base_colors = []
    original_data_points = []
    
    for series_idx, series in enumerate(data_series):
        label = series.get("label", "")
        color = series.get("color", CHART_COLORS["primary"])
        values = series.get("values", [])
        base_colors.append(color)
        
        data_points = []
        for x, y in values:
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
        
        original_data_points.append([(p.x, p.y) for p in data_points])
        
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
    
    y_max = max(10, int(max_y * 1.2) + 1)
    
    step = max(1, (max_x + 1) // 6)
    bottom_labels = []
    for i in range(0, max_x + 1, step):
        label_text = x_labels[i] if x_labels and i < len(x_labels) else str(i)
        if label_text.startswith("Date: "):
            label_text = label_text[6:]
        bottom_labels.append(
            ft.ChartAxisLabel(
                value=i,
                label=ft.Text(label_text, size=10, color=ft.Colors.GREY_600),
            )
        )
    
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
        tooltip_rounded_radius=8,
        tooltip_padding=8,
        tooltip_max_content_width=100,
        border=ft.border.all(1, ft.Colors.with_opacity(0.30, ft.Colors.GREY_400)),
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
    
    if legend_refs is not None:
        legend_refs["chart"] = chart
        legend_refs["data_series"] = chart_data_series
        legend_refs["base_colors"] = base_colors
        legend_refs["original_data_points"] = original_data_points
    
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
                    border_side=ft.BorderSide(width=0, color=color),
                )
            )
        flet_bar_groups.append(ft.BarChartGroup(x=x, bar_rods=rods))
    
    y_max = max(5, int(max_y * 1.2) + 1)
    
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
            labels=axis_bottom_labels if bottom_labels else [],
            labels_size=0 if not bottom_labels else 40,
            show_labels=bool(bottom_labels),
        ),
        horizontal_grid_lines=ft.ChartGridLines(
            color=ft.Colors.GREY_300,
            width=1,
            dash_pattern=[3, 3],
        ),
    )
    
    if legend_refs is not None:
        legend_refs["chart"] = chart
        legend_refs["bar_groups"] = flet_bar_groups
        if flet_bar_groups and flet_bar_groups[0].bar_rods:
            legend_refs["base_width"] = flet_bar_groups[0].bar_rods[0].width
        else:
            legend_refs["base_width"] = 50
    
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
    title_font_size: int = 11,
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
        title_font_size: Font size for section titles (default 11)
        
    Returns:
        A Flet PieChart control or empty state if no data
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    filtered_sections = [s for s in sections if s.get("value", 0) > 0]
    
    if not filtered_sections:
        return create_empty_chart_message("No Data Available", height, width)
    
    base_radius = section_radius
    
    flet_sections = []
    total_value = sum(s.get("value", 0) for s in filtered_sections)
    
    for i, section in enumerate(filtered_sections):
        value = section.get("value", 0)
        title = section.get("title", "")
        color = section.get("color", PIE_CHART_COLORS[i % len(PIE_CHART_COLORS)])
        
        flet_sections.append(
            ft.PieChartSection(
                value=value,
                color=color,
                radius=section_radius,
                title=title,
                title_style=ft.TextStyle(
                    size=title_font_size,
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
                section.radius = base_radius * 1.1  # Expand radius on hover
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
    line_refs: Optional[Dict[str, Any]] = None,
    text_size: int = 11,
) -> Any:
    """Create a legend for charts with hover effects that sync with chart sections.
    
    Args:
        items: List of dicts with 'label', 'color', and optionally 'value'
        horizontal: Whether to layout horizontally
        pie_refs: Optional dict with 'chart', 'sections', 'base_radius' for pie sync
        bar_refs: Optional dict with 'chart', 'bar_groups' for bar sync
        line_refs: Optional dict with 'chart', 'data_series' for line sync
        
    Returns:
        A Flet control with the legend
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
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
        
        color_box = ft.Container(
            width=12,
            height=12,
            bgcolor=color,
            border_radius=3,
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.BLACK)),
        )
        
        def make_hover_handler(legend_idx: int):
            actual_section_idx = legend_to_section_map.get(legend_idx, -1)
            
            def on_legend_hover(e):
                if e.data == "true":
                    e.control.bgcolor = ft.Colors.with_opacity(0.08, ft.Colors.BLACK)
                    e.control.scale = 1.03
                    if actual_section_idx >= 0 and pie_refs and "sections" in pie_refs and "chart" in pie_refs:
                        sections = pie_refs["sections"]
                        base_radius = pie_refs.get("base_radius", 80)
                        for i, section in enumerate(sections):
                            if i == actual_section_idx:
                                section.radius = base_radius * 1.1
                            else:
                                section.radius = base_radius
                        pie_refs["chart"].update()
                    if actual_section_idx >= 0 and bar_refs and "bar_groups" in bar_refs and "chart" in bar_refs:
                        bar_groups = bar_refs["bar_groups"]
                        base_width = bar_refs.get("base_width", 50)
                        if "original_widths" not in bar_refs:
                            bar_refs["original_widths"] = {}
                            for i, group in enumerate(bar_groups):
                                bar_refs["original_widths"][i] = [rod.width for rod in group.bar_rods]
                        
                        for i, group in enumerate(bar_groups):
                            for rod in group.bar_rods:
                                if i == actual_section_idx:
                                    rod.width = base_width + 10
                                else:
                                    rod.width = base_width
                        bar_refs["chart"].update()
                    if actual_section_idx >= 0 and line_refs and "data_series" in line_refs and "chart" in line_refs:
                        data_series = line_refs["data_series"]
                        base_colors = line_refs.get("base_colors", [])
                        original_data_points = line_refs.get("original_data_points", [])
                        chart = line_refs["chart"]
                        
                        reordered_series = []
                        hovered_series = None
                        
                        for i, series in enumerate(data_series):
                            if i == actual_section_idx:
                                hovered_series = series
                                if i < len(original_data_points):
                                    for j, point in enumerate(series.data_points):
                                        if j < len(original_data_points[i]):
                                            point.y = original_data_points[i][j][1]
                                series.stroke_width = 5
                                if i < len(base_colors):
                                    series.below_line_bgcolor = ft.Colors.with_opacity(0.3, base_colors[i])
                            else:
                                for point in series.data_points:
                                    point.y = 0
                                series.stroke_width = 1
                                if i < len(base_colors):
                                    series.below_line_bgcolor = ft.Colors.with_opacity(0, base_colors[i])
                                reordered_series.append(series)
                        
                        if hovered_series:
                            reordered_series.append(hovered_series)
                        
                        chart.data_series = reordered_series
                        chart.update()
                else:
                    e.control.bgcolor = None
                    e.control.scale = 1.0
                    if pie_refs and "sections" in pie_refs and "chart" in pie_refs:
                        sections = pie_refs["sections"]
                        base_radius = pie_refs.get("base_radius", 80)
                        for section in sections:
                            section.radius = base_radius
                        pie_refs["chart"].update()
                    if bar_refs and "bar_groups" in bar_refs and "chart" in bar_refs:
                        bar_groups = bar_refs["bar_groups"]
                        if "original_widths" in bar_refs:
                            for i, group in enumerate(bar_groups):
                                for j, rod in enumerate(group.bar_rods):
                                    if i in bar_refs["original_widths"] and j < len(bar_refs["original_widths"][i]):
                                        rod.width = bar_refs["original_widths"][i][j]
                        else:
                            base_width = bar_refs.get("base_width", 50)
                            for group in bar_groups:
                                for rod in group.bar_rods:
                                    rod.width = base_width
                        bar_refs["chart"].update()
                    if line_refs and "data_series" in line_refs and "chart" in line_refs:
                        data_series = line_refs["data_series"]
                        base_colors = line_refs.get("base_colors", [])
                        original_data_points = line_refs.get("original_data_points", [])
                        chart = line_refs["chart"]
                        
                        for i, series in enumerate(data_series):
                            if i < len(original_data_points):
                                for j, point in enumerate(series.data_points):
                                    if j < len(original_data_points[i]):
                                        point.y = original_data_points[i][j][1]
                            series.stroke_width = 3
                            if i < len(base_colors):
                                series.below_line_bgcolor = ft.Colors.with_opacity(0.1, base_colors[i])
                        
                        chart.data_series = data_series
                        chart.update()
                e.control.update()
            return on_legend_hover
        
        legend_item = ft.Container(
            content=ft.Row([color_box, ft.Text(text, size=text_size, color=ft.Colors.GREY_700)], spacing=6),
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


def _get_flet_color(color_name: str) -> str:
    """Convert color name string to Flet color constant.
    
    Args:
        color_name: Color name like "GREEN_600", "BLUE_700", etc.
        
    Returns:
        Flet color value
    """
    if ft is None:
        return color_name
    
    color_map = {
        "GREEN_50": ft.Colors.GREEN_50,
        "GREEN_600": ft.Colors.GREEN_600,
        "GREEN_700": ft.Colors.GREEN_700,
        "BLUE_50": ft.Colors.BLUE_50,
        "BLUE_600": ft.Colors.BLUE_600,
        "BLUE_700": ft.Colors.BLUE_700,
        "ORANGE_50": ft.Colors.ORANGE_50,
        "ORANGE_600": ft.Colors.ORANGE_600,
        "ORANGE_700": ft.Colors.ORANGE_700,
        "RED_50": ft.Colors.RED_50,
        "RED_600": ft.Colors.RED_600,
        "RED_700": ft.Colors.RED_700,
        "AMBER_50": ft.Colors.AMBER_50,
        "AMBER_600": ft.Colors.AMBER_600,
        "AMBER_700": ft.Colors.AMBER_700,
        "TEAL_50": ft.Colors.TEAL_50,
        "TEAL_600": ft.Colors.TEAL_600,
        "PURPLE_50": ft.Colors.PURPLE_50,
        "PURPLE_600": ft.Colors.PURPLE_600,
        "PURPLE_700": ft.Colors.PURPLE_700,
        "PURPLE_800": ft.Colors.PURPLE_800,
        "GREY_700": ft.Colors.GREY_700,
        "BLACK87": ft.Colors.BLACK87,
    }
    return color_map.get(color_name, color_name)


def _get_flet_icon(icon_name: str) -> Any:
    """Convert icon name string to Flet icon constant.
    
    Args:
        icon_name: Icon name like "CHECK_CIRCLE", "WARNING_AMBER", etc.
        
    Returns:
        Flet icon value
    """
    if ft is None:
        return icon_name
    
    icon_map = {
        "EMOJI_EVENTS": ft.Icons.EMOJI_EVENTS,
        "TRENDING_UP": ft.Icons.TRENDING_UP,
        "TRENDING_FLAT": ft.Icons.TRENDING_FLAT,
        "WARNING_AMBER": ft.Icons.WARNING_AMBER,
        "WARNING": ft.Icons.WARNING,
        "CHECK_CIRCLE": ft.Icons.CHECK_CIRCLE,
        "ASSIGNMENT": ft.Icons.ASSIGNMENT,
        "SCHEDULE": ft.Icons.SCHEDULE,
        "LOCAL_FIRE_DEPARTMENT": ft.Icons.LOCAL_FIRE_DEPARTMENT,
        "INFO": ft.Icons.INFO,
        "ADD_CIRCLE": ft.Icons.ADD_CIRCLE,
        "THUMB_UP": ft.Icons.THUMB_UP,
        "HELP_OUTLINE": ft.Icons.HELP_OUTLINE,
        "MARK_EMAIL_UNREAD": ft.Icons.MARK_EMAIL_UNREAD,
        "LIGHTBULB": ft.Icons.LIGHTBULB,
        "VERIFIED": ft.Icons.VERIFIED,
        "HEALING": ft.Icons.HEALING,
        "LOCAL_HOSPITAL": ft.Icons.LOCAL_HOSPITAL,
        "PETS": ft.Icons.PETS,
        "HOME": ft.Icons.HOME,
        "FAVORITE": ft.Icons.FAVORITE,
        "VOLUNTEER_ACTIVISM": ft.Icons.VOLUNTEER_ACTIVISM,
        "HOURGLASS_BOTTOM": ft.Icons.HOURGLASS_BOTTOM,
        "WAVING_HAND": ft.Icons.WAVING_HAND,
        "PENDING_ACTIONS": ft.Icons.PENDING_ACTIONS,
        "DIRECTIONS_RUN": ft.Icons.DIRECTIONS_RUN,
        "AUTO_AWESOME": ft.Icons.AUTO_AWESOME,
    }
    return icon_map.get(icon_name, ft.Icons.INFO)


def _build_rich_text(detail_data: Dict[str, Any]) -> Any:
    """Build rich text using TextSpan from structured detail data.
    
    Args:
        detail_data: Dict with 'parts' list containing text segments with styling
        
    Returns:
        A Flet Text control with styled TextSpan elements
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    if not isinstance(detail_data, dict) or "parts" not in detail_data:
        # Fallback for plain string
        return ft.Text(str(detail_data), size=12, color=ft.Colors.BLACK54)
    
    spans = []
    for part in detail_data.get("parts", []):
        text = part.get("text", "")
        weight = part.get("weight", "normal")
        color = part.get("color")
        icon_name = part.get("icon")
        
        font_weight = ft.FontWeight.BOLD if weight == "bold" else ft.FontWeight.NORMAL
        text_color = _get_flet_color(color) if color else ft.Colors.BLACK54
        
        spans.append(
            ft.TextSpan(
                text,
                ft.TextStyle(
                    size=12,
                    color=text_color,
                    weight=font_weight,
                )
            )
        )
    
    return ft.Text(
        spans=spans,
        size=12,
    )


def create_insight_box(
    title: str,
    insight_data: Dict[str, Any],
    icon: Any,
    icon_color: str,
    bg_color: str,
    border_color: str,
) -> Any:
    """Create a styled insight box with headline, detail, and action.
    
    Used in analytics dashboards to display key insights with a consistent
    structure: icon + title header, headline text, optional detail, optional action.
    Uses rich Flet components (TextSpan, Icons) for an AI-like presentation.
    
    Args:
        title: Section title (e.g., "Rescue Insights")
        insight_data: Dict with structured 'headline', 'detail', 'action' objects
            - headline: Dict with 'text', 'icon', 'color'
            - detail: Dict with 'parts' list for rich text
            - action: Dict with 'icon', 'text', 'color', 'bg_color', 'severity'
        icon: Flet icon to display (used as fallback)
        icon_color: Color for icon background and accents
        bg_color: Background color for the box
        border_color: Border color for the box
        
    Returns:
        A Flet container with the styled insight box
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    if isinstance(insight_data, dict):
        headline_data = insight_data.get("headline", {"text": "No data"})
        detail_data = insight_data.get("detail")
        action_data = insight_data.get("action")
    else:
        headline_data = {"text": str(insight_data)}
        detail_data = None
        action_data = None
    
    if isinstance(headline_data, dict):
        headline_text = headline_data.get("text", "No data")
        headline_icon = headline_data.get("icon")
        headline_color = _get_flet_color(headline_data.get("color", "BLACK87"))
    else:
        headline_text = str(headline_data)
        headline_icon = None
        headline_color = ft.Colors.BLACK87
    
    if headline_icon:
        headline_row = ft.Row([
            ft.Icon(_get_flet_icon(headline_icon), size=18, color=headline_color),
            ft.Text(headline_text, size=14, weight=ft.FontWeight.W_600, color=headline_color, expand=True),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    else:
        headline_row = ft.Text(headline_text, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87)
    
    content_items = [
        # Header with icon badge and title
        ft.Row([
            ft.Container(
                ft.Icon(icon, size=20, color=ft.Colors.WHITE),
                width=36,
                height=36,
                bgcolor=icon_color,
                border_radius=18,
                alignment=ft.alignment.center,
                shadow=ft.BoxShadow(blur_radius=4, spread_radius=0, color=ft.Colors.with_opacity(0.3, icon_color), offset=(0, 2)),
            ),
            ft.Text(title, size=14, weight="bold", color=icon_color),
        ], spacing=10),
        ft.Container(height=12),
        # Rich headline
        headline_row,
    ]
    
    if detail_data:
        content_items.append(ft.Container(height=6))
        content_items.append(_build_rich_text(detail_data))
    
    if action_data:
        content_items.append(ft.Container(height=10))
        
        if isinstance(action_data, dict):
            action_icon = action_data.get("icon")
            action_text = action_data.get("text", "")
            action_color = _get_flet_color(action_data.get("color", icon_color))
            action_bg = _get_flet_color(action_data.get("bg_color", "GREY_100"))
            severity = action_data.get("severity", "info")
            
            if action_icon:
                action_row = ft.Row([
                    ft.Icon(_get_flet_icon(action_icon), size=14, color=action_color),
                    ft.Text(action_text, size=11, color=action_color, weight=ft.FontWeight.W_500, expand=True),
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            else:
                action_row = ft.Text(action_text, size=11, color=action_color, weight=ft.FontWeight.W_500)
            
            # Background opacity based on severity
            bg_opacity = 0.2 if severity in ["urgent", "warning"] else 0.15
            
            content_items.append(
                ft.Container(
                    action_row,
                    bgcolor=ft.Colors.with_opacity(bg_opacity, action_color),
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    border_radius=6,
                )
            )
        else:
            # Fallback for old string format
            action_text = str(action_data)
            content_items.append(
                ft.Container(
                    ft.Text(action_text, size=11, color=icon_color, weight=ft.FontWeight.W_500),
                    bgcolor=ft.Colors.with_opacity(0.15, icon_color),
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    border_radius=6,
                )
            )
    
    return ft.Container(
        ft.Column(content_items, spacing=0),
        padding=20,
        bgcolor=bg_color,
        border_radius=12,
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


def create_impact_insight_widgets(insight_data: List[Dict[str, Any]]) -> List[Any]:
    """Create styled insight widgets from service-generated insight data.
    
    Converts backend insight data (from AnalyticsService.get_user_impact_insights)
    into rich Flet UI components using TextSpan for formatted text.
    
    Args:
        insight_data: List of insight dictionaries from the analytics service.
            Each dict contains:
            - icon: Icon name string (e.g., "PENDING_ACTIONS")
            - parts: List of text parts with weight, color properties
            - color: Main color string (e.g., "BLUE_700")
            - bg_color: Background color string (e.g., "BLUE_50")
    
    Returns:
        List of Flet Container widgets ready to be displayed
    """
    if ft is None:
        raise RuntimeError("Flet must be installed")
    
    widgets = []
    
    for insight in insight_data:
        icon_name = insight.get("icon", "INFO")
        parts = insight.get("parts", [])
        color_name = insight.get("color", "TEAL_700")
        bg_color_name = insight.get("bg_color", "TEAL_50")
        
        # Convert color names to Flet colors
        icon_color = _get_flet_color(color_name)
        bg_color = _get_flet_color(bg_color_name)
        flet_icon = _get_flet_icon(icon_name)
        
        spans = []
        for part in parts:
            text = part.get("text", "")
            weight = part.get("weight", "normal")
            part_color = part.get("color")
            
            font_weight = ft.FontWeight.BOLD if weight == "bold" else ft.FontWeight.NORMAL
            text_color = _get_flet_color(part_color) if part_color else icon_color
            
            spans.append(
                ft.TextSpan(
                    text,
                    ft.TextStyle(
                        weight=font_weight,
                        color=text_color,
                    )
                )
            )
        
        text_control = ft.Text(spans=spans, size=12)
        
        widget = ft.Container(
            ft.Row([
                ft.Icon(flet_icon, size=16, color=icon_color),
                text_control,
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=bg_color,
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_radius=20,
        )
        
        widgets.append(widget)
    
    return widgets


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
    "create_insight_box",
    "create_chart_card",
    "create_impact_insight_widgets",
]
