from utils.json_handler import load_json

class Route:
    def viewRouteDetails(self, route_id):
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