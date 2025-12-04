"""Flet app entrypoint with route-based navigation."""
from __future__ import annotations

import sys

try:
	import flet as ft
except Exception:  # pragma: no cover - flet not installed in test env
	ft = None  # type: ignore

from services.auth_service import AuthService
from state import get_app_state
from routes import get_route_handler, _extract_query_params, clear_page, check_route_access
import app_config


def main(page) -> None:
	if ft is None:
		raise RuntimeError("Flet is required to run this app")

	# Initialize auth service and ensure admin user exists
	auth = AuthService(app_config.DB_PATH)

	# Initialize centralized state management
	app_state = get_app_state(app_config.DB_PATH)
	app_state.initialize(page)

	page.title = "Rescue/Adoption App"
	page.window.center()
	page.window.min_width = app_config.DEFAULT_WINDOW_MIN_WIDTH
	page.window.min_height = app_config.DEFAULT_WINDOW_MIN_HEIGHT
	page.vertical_alignment = ft.MainAxisAlignment.CENTER
	page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
	page.padding = 0
	page.spacing = 0
	page.bgcolor = ft.Colors.TRANSPARENT
	page.theme_mode = ft.ThemeMode.LIGHT

	def _render_error_page(message: str, details: str = "") -> None:
		"""Render an error page with a home button."""
		clear_page(page)
		content = ft.Column([
			ft.Text(message, size=20, weight="bold", color=ft.Colors.RED),
			ft.Divider(height=10),
			ft.Text(details, size=12) if details else ft.Container(),
			ft.ElevatedButton("Home", on_click=lambda e: page.go("/")),
		], alignment="center", horizontal_alignment="center")
		page.add(ft.Container(
			content,
			expand=True,
			gradient=ft.LinearGradient(
				begin=ft.alignment.top_center,
				end=ft.alignment.bottom_center,
				colors=[ft.Colors.LIGHT_BLUE_50, ft.Colors.AMBER_50]
			)
		))
		page.update()

	def route_change(route) -> None:
		"""Handle route changes using the route registry with authorization."""
		r = page.route
		route_path = r.split("?")[0] if "?" in r else r
		
		if route_path == "":
			route_path = "/"
		
		try:
			route_config = get_route_handler(route_path)
			
			if route_config:
				params = _extract_query_params(r)
				
				# Check authorization before handling route
				if not check_route_access(page, route_config, route_path):
					# Access denied - middleware handles redirect
					return
				
				handler = route_config["handler"]
				handler(page, params)
			else:
				_render_error_page(f"404 - Route not found: {r}", "Please check the URL and try again.")

		except Exception as e:
			import traceback
			traceback.print_exc()
			_render_error_page(f"Error loading route: {r}", f"Exception: {str(e)}")

	page.on_route_change = route_change

	if not page.route:
		page.go("/")
	else:
		route_change(page.route)


if __name__ == "__main__":
	if ft is None:
		print("Flet is required to run the GUI. Install with: python -m pip install flet")
		sys.exit(1)
	ft.app(target=main, view=ft.WEB_BROWSER)
