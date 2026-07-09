"""
Module: Personalized Dashboard Builder

This module provides a no-code dashboard creation interface to generate customizable and role-based dashboards for different user profiles.
"""


class PersonalizedDashboardBuilder:
    def __init__(self, user_role):
        self.user_role = user_role
        self.widgets = []

    def add_widget(self, widget_type, data_source):
        """
        Add a widget to the dashboard based on the user role and data source.
        """
        widget = {
            "type": widget_type,
            "data_source": data_source,
            "role": self.user_role,
        }
        self.widgets.append(widget)
        print(f"Added {widget_type} widget for role: {self.user_role}")

    def generate_dashboard(self):
        """
        Generate the dashboard layout with the added widgets.
        """
        print(f"Generating dashboard for role: {self.user_role}")
        return self.widgets
