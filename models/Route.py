"""Module for handling route information and operations."""

from utils.json_handler import load_json


class Route:
    """A class to manage route information and display details."""

    def view_route_details(self, route_id):
        """Display detailed information about a specific route.
        
        Args:
            route_id (str): The ID of the route to view.
            
        Returns:
            None: Outputs route details to console.
        """
        routes = load_json("data/routes.json")
        route = next((r for r in routes if r["routeId"] == route_id), None)
        
        if not route:
            print("Route details not found.")
            return
            
        print(f"\n===== Route: {route['routeName']} =====")
        print(f"Start: {route['startStationId']}")
        print(f"End: {route['endStationId']}")
        print(f"Number of stops: {route['numberOfStops']}")
        print("\nStops sequence:")
        for stop in route['stopsSequence']:
            print(f"- {stop}")
        print(f"Base Price: RM{route['basePrice']}")