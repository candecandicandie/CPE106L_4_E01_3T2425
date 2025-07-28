import flet as ft
import heapq
import requests
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import bcrypt
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

# Load environment variables
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "accessible_transport"

# MongoDB Setup
client = MongoClient(MONGO_URI)
try:
    client.admin.command('ping')
    print("✅ Connected to MongoDB")
except ConnectionFailure:
    print("❌ MongoDB connection failed")
db = client[DB_NAME]

# MongoDB Collections
users_collection = db["users"]
rides_collection = db["rides"]
drivers_collection = db["drivers"]

# Data Models
@dataclass
class User:
    username: str
    password_hash: str
    role: str = "user"
    accessibility_needs: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            username=data["username"],
            password_hash=data["password_hash"],
            role=data.get("role", "user"),
            accessibility_needs=data.get("accessibility_needs", []),
            created_at=data.get("created_at", datetime.now())
        )

@dataclass
class Driver(User):
    vehicle_type: str = ""
    capacity: int = 4
    availability: bool = True
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            "vehicle_type": self.vehicle_type,
            "capacity": self.capacity,
            "availability": self.availability
        })
        return data
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            username=data["username"],
            password_hash=data["password_hash"],
            role=data.get("role", "driver"),
            accessibility_needs=data.get("accessibility_needs", []),
            created_at=data.get("created_at", datetime.now()),
            vehicle_type=data.get("vehicle_type", ""),
            capacity=data.get("capacity", 4),
            availability=data.get("availability", True)
        )

@dataclass
class RideRequest:
    user_id: str
    pickup: str
    dropoff: str
    scheduled_time: datetime
    status: str = "pending"
    accessibility_requirements: List[str] = field(default_factory=list)
    driver_id: Optional[str] = None
    estimated_time: Optional[int] = None
    distance: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data["user_id"],
            pickup=data["pickup"],
            dropoff=data["dropoff"],
            scheduled_time=data["scheduled_time"],
            status=data.get("status", "pending"),
            accessibility_requirements=data.get("accessibility_requirements", []),
            driver_id=data.get("driver_id"),
            estimated_time=data.get("estimated_time"),
            distance=data.get("distance"),
            created_at=data.get("created_at", datetime.now())
        )

# Transportation Graph for route optimization
class TransportationGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
    
    def add_node(self, node_id: int, name: str, location: str):
        self.nodes[node_id] = {"name": name, "location": location}
    
    def add_edge(self, from_node: int, to_node: int, weight: int, time: int):
        if from_node not in self.edges:
            self.edges[from_node] = {}
        self.edges[from_node][to_node] = {"weight": weight, "time": time}
    
    def dijkstra(self, start: int, end: int) -> tuple:
        distances = {node: float('inf') for node in self.nodes}
        previous_nodes = {node: None for node in self.nodes}
        distances[start] = 0
        
        priority_queue = [(0, start)]
        
        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)
            
            if current_distance > distances[current_node]:
                continue
                
            if current_node == end:
                break
                
            if current_node in self.edges:
                for neighbor, edge_data in self.edges[current_node].items():
                    distance = current_distance + edge_data["weight"]
                    if distance < distances[neighbor]:
                        distances[neighbor] = distance
                        previous_nodes[neighbor] = current_node
                        heapq.heappush(priority_queue, (distance, neighbor))
        
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous_nodes[current]
        
        path.reverse()
        return path, distances[end]

# UI Components
class ModernButton(ft.ElevatedButton):
    def __init__(self, text, on_click, icon=None, width=200, height=50, **kwargs):
        super().__init__(
            text=text,
            on_click=on_click,
            icon=icon,
            width=width,
            height=height,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20,
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                overlay_color=ft.Colors.BLUE_900,
            ),
            **kwargs
        )

class ModernTextField(ft.TextField):
    def __init__(self, label, password=False, width=300, **kwargs):
        super().__init__(
            label=label,
            password=password,
            width=width,
            border_radius=10,
            border_color=ft.Colors.GREY_400,
            focused_border_color=ft.Colors.BLUE_700,
            content_padding=15,
            **kwargs
        )

class ModernCard(ft.Card):
    def __init__(self, content, padding=20, elevation=5, **kwargs):
        super().__init__(
            content=ft.Container(
                content=content,
                padding=padding
            ),
            elevation=elevation,
            shape=ft.RoundedRectangleBorder(radius=15),
            **kwargs
        )

# Main Application
class AccessibleTransportScheduler:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Accessible Transportation Scheduler"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 30
        self.page.fonts = {
            "Poppins": "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap"
        }
        self.page.theme = ft.Theme(font_family="Poppins")
        self.page.bgcolor = ft.Colors.GREY_100
        
        self.user = None
        self.transport_graph = self.create_transport_graph()
        
        # Initialize sample data if collections are empty
        self.initialize_sample_data()
        
        self.setup_ui()
        self.show_login()
    
    def create_transport_graph(self) -> TransportationGraph:
        """Create a sample transportation graph"""
        graph = TransportationGraph()
        
        locations = {
            0: "Home (123 Main St)",
            1: "City General Hospital",
            2: "City Center Mall",
            3: "Central Park",
            4: "City Library",
            5: "Senior Center",
            6: "Rehabilitation Center",
            7: "Medical Clinic"
        }
        
        for node_id, name in locations.items():
            graph.add_node(node_id, name, name)
        
        # Add edges (weights represent travel time in minutes)
        graph.add_edge(0, 1, 15, 15)  # home -> hospital
        graph.add_edge(0, 2, 10, 10)  # home -> mall
        graph.add_edge(0, 3, 20, 20)  # home -> park
        graph.add_edge(1, 2, 8, 8)    # hospital -> mall
        graph.add_edge(2, 3, 12, 12)  # mall -> park
        graph.add_edge(3, 4, 7, 7)    # park -> library
        graph.add_edge(4, 0, 18, 18)  # library -> home
        graph.add_edge(5, 1, 5, 5)    # senior center -> hospital
        graph.add_edge(6, 1, 7, 7)    # rehab center -> hospital
        graph.add_edge(7, 1, 3, 3)    # clinic -> hospital
        
        return graph
    
    def initialize_sample_data(self):
        """Initialize sample data if collections are empty"""
        # Create users if collection is empty
        if users_collection.count_documents({}) == 0:
            print("Initializing sample users...")
            users = [
                User(
                    username="user1",
                    password_hash=bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
                    accessibility_needs=["wheelchair ramp"]
                ).to_dict(),
                User(
                    username="user2",
                    password_hash=bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
                    accessibility_needs=["walking assistance"]
                ).to_dict(),
                Driver(
                    username="driver1",
                    password_hash=bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
                    vehicle_type="van with wheelchair ramp",
                    capacity=4
                ).to_dict(),
                Driver(
                    username="driver2",
                    password_hash=bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
                    vehicle_type="sedan",
                    capacity=3
                ).to_dict()
            ]
            users_collection.insert_many(users)
        
        # Create drivers if collection is empty
        if drivers_collection.count_documents({}) == 0:
            print("Initializing sample drivers...")
            drivers = list(users_collection.find({"role": "driver"}))
            for driver in drivers:
                # Convert to Driver object and back to include driver-specific fields
                driver_obj = Driver.from_dict(driver)
                drivers_collection.insert_one(driver_obj.to_dict())
        
        # Create rides if collection is empty
        if rides_collection.count_documents({}) == 0:
            print("Initializing sample rides...")
            rides = [
                RideRequest(
                    user_id="user1",
                    pickup="Home (123 Main St)",
                    dropoff="City General Hospital",
                    scheduled_time=datetime.now() - timedelta(days=1),
                    status="completed",
                    driver_id="driver1",
                    estimated_time=15,
                    distance=5.2
                ).to_dict(),
                RideRequest(
                    user_id="user1",
                    pickup="City General Hospital",
                    dropoff="Home (123 Main St)",
                    scheduled_time=datetime.now() + timedelta(hours=2),
                    status="scheduled",
                    driver_id="driver1",
                    estimated_time=15,
                    distance=5.2
                ).to_dict(),
                RideRequest(
                    user_id="user2",
                    pickup="Senior Center",
                    dropoff="City Center Mall",
                    scheduled_time=datetime.now() + timedelta(days=1),
                    status="pending"
                ).to_dict()
            ]
            rides_collection.insert_many(rides)
    
    def setup_ui(self):
        # Navigation controls
        self.nav_bar = ft.Row(
            controls=[
                ModernButton("Schedule Ride", on_click=lambda _: self.show_scheduler(), icon=ft.icons.CALENDAR_TODAY),
                ModernButton("Ride History", on_click=lambda _: self.show_history(), icon=ft.icons.HISTORY),
                ModernButton("Analytics", on_click=lambda _: self.show_analytics(), icon=ft.icons.ANALYTICS),
                ModernButton("Logout", on_click=lambda _: self.logout(), icon=ft.icons.LOGOUT),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
            visible=False
        )
        
        # Header
        self.header = ft.Row(
            controls=[
                ft.Icon(ft.icons.ACCESSIBLE, size=40, color=ft.Colors.BLUE_700),
                ft.Text("Accessible Transport", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
        
        # Login UI
        self.login_username = ModernTextField("Username")
        self.login_password = ModernTextField("Password", password=True)
        self.login_btn = ModernButton("Login", on_click=self.login, width=300, height=50)
        self.register_btn = ft.TextButton("Create Account", on_click=lambda _: self.show_register())
        self.login_view = ft.Column(
            [
                self.header,
                ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Welcome Back", size=22, weight=ft.FontWeight.BOLD),
                            ft.Text("Sign in to schedule your ride", size=16, color=ft.Colors.GREY),
                            self.login_username,
                            self.login_password,
                            self.login_btn,
                            self.register_btn
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20
                    ),
                    padding=30,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    width=400
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # Registration UI
        self.reg_username = ModernTextField("Username")
        self.reg_password = ModernTextField("Password", password=True)
        self.reg_confirm = ModernTextField("Confirm Password", password=True)
        self.accessibility_needs = ModernTextField("Accessibility Needs (comma separated)", 
                                                 hint_text="e.g., wheelchair ramp, assistance walking")
        self.register_btn_main = ModernButton("Create Account", on_click=self.register, width=300, height=50)
        self.back_to_login = ft.TextButton("Back to Login", on_click=lambda _: self.show_login())
        self.register_view = ft.Column(
            [
                self.header,
                ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Create Account", size=22, weight=ft.FontWeight.BOLD),
                            self.reg_username,
                            self.reg_password,
                            self.reg_confirm,
                            self.accessibility_needs,
                            self.register_btn_main,
                            self.back_to_login
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20
                    ),
                    padding=30,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    width=400
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # Ride Scheduler UI
        self.pickup_location = ft.Dropdown(
            label="Pickup Location",
            width=300,
            options=[
                ft.dropdown.Option(loc) for loc in [
                    "Home (123 Main St)",
                    "City General Hospital",
                    "City Center Mall",
                    "Central Park",
                    "City Library",
                    "Senior Center",
                    "Rehabilitation Center",
                    "Medical Clinic"
                ]
            ],
            border_radius=10,
            content_padding=10
        )
        self.dropoff_location = ft.Dropdown(
            label="Dropoff Location",
            width=300,
            options=[
                ft.dropdown.Option(loc) for loc in [
                    "Home (123 Main St)",
                    "City General Hospital",
                    "City Center Mall",
                    "Central Park",
                    "City Library",
                    "Senior Center",
                    "Rehabilitation Center",
                    "Medical Clinic"
                ]
            ],
            border_radius=10,
            content_padding=10
        )
        self.schedule_time = ModernTextField(
            "Scheduled Time (HH:MM)", 
            value=datetime.now().strftime("%H:%M")
        )
        self.schedule_date = ModernTextField(
            "Scheduled Date (YYYY-MM-DD)", 
            value=datetime.now().strftime("%Y-%m-%d")
        )
        self.accessibility_reqs = ModernTextField(
            "Special Requirements", 
            hint_text="Any special needs for this ride"
        )
        self.schedule_btn = ModernButton("Schedule Ride", on_click=self.schedule_ride)
        self.route_info = ft.Text("", size=16, color=ft.Colors.BLUE_700)
        self.scheduler_view = ft.Column(
            [
                self.header,
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Schedule a Ride", size=24, weight=ft.FontWeight.BOLD),
                            ft.Row([self.pickup_location, self.dropoff_location], spacing=20),
                            ft.Row([self.schedule_date, self.schedule_time], spacing=20),
                            self.accessibility_reqs,
                            self.schedule_btn,
                            self.route_info
                        ],
                        spacing=20,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    padding=30,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    width=700
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # Ride History UI
        self.history_list = ft.ListView(expand=True, spacing=15)
        self.history_view = ft.Column(
            [
                self.header,
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Your Ride History", size=24, weight=ft.FontWeight.BOLD),
                            self.history_list
                        ],
                        expand=True
                    ),
                    padding=30,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    expand=True
                )
            ],
            expand=True
        )
        
        # Analytics UI
        self.visualization_image = ft.Image(width=600, height=400, border_radius=10)
        self.analytics_view = ft.Column(
            [
                self.header,
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Ride Analytics", size=24, weight=ft.FontWeight.BOLD),
                            self.visualization_image,
                            ModernButton("Generate Report", on_click=lambda _: self.generate_analytics())
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=30
                    ),
                    padding=30,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    width=700
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # Driver View
        self.driver_rides = ft.ListView(expand=True, spacing=15)
        self.driver_view = ft.Column(
            [
                self.header,
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Driver Dashboard", size=24, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                [
                                    ModernButton("Mark as Completed", on_click=self.mark_completed),
                                    ModernButton("Start Ride", on_click=self.start_ride),
                                ],
                                spacing=20
                            ),
                            self.driver_rides
                        ],
                        expand=True
                    ),
                    padding=30,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    expand=True
                )
            ],
            expand=True
        )
    
    def show_login(self):
        self.current_view = "login"
        self.nav_bar.visible = False
        self.page.clean()
        self.page.add(self.login_view)
        self.page.update()
    
    def show_register(self):
        self.current_view = "register"
        self.page.clean()
        self.page.add(self.register_view)
        self.page.update()
    
    def show_scheduler(self):
        if not self.user:
            self.show_login()
            return
            
        self.current_view = "scheduler"
        self.nav_bar.visible = True
        self.page.clean()
        self.page.add(ft.Column([self.nav_bar, self.scheduler_view], spacing=20))
        self.page.update()
    
    def show_history(self):
        if not self.user:
            self.show_login()
            return
            
        self.current_view = "history"
        self.nav_bar.visible = True
        self.page.clean()
        self.page.add(ft.Column([self.nav_bar, self.history_view], expand=True))
        self.load_ride_history()
        self.page.update()
    
    def show_analytics(self):
        if not self.user:
            self.show_login()
            return
            
        self.current_view = "analytics"
        self.nav_bar.visible = True
        self.page.clean()
        self.page.add(ft.Column([self.nav_bar, self.analytics_view], spacing=20))
        self.generate_analytics()
        self.page.update()
    
    def show_driver_view(self):
        if not self.user or self.user.role != "driver":
            self.show_scheduler()
            return
            
        self.current_view = "driver"
        self.nav_bar.visible = True
        self.page.clean()
        self.page.add(ft.Column([self.nav_bar, self.driver_view], expand=True))
        self.load_driver_rides()
        self.page.update()
    
    def login(self, e):
        username = self.login_username.value
        password = self.login_password.value
        
        if not username or not password:
            self.show_snackbar("Please enter both username and password")
            return
            
        try:
            user_data = users_collection.find_one({"username": username})
        except PyMongoError as e:
            self.show_snackbar(f"Database error: {str(e)}")
            return
            
        if user_data and bcrypt.checkpw(password.encode(), user_data["password_hash"].encode()):
            if user_data.get("role") == "driver":
                self.user = Driver.from_dict(user_data)
            else:
                self.user = User.from_dict(user_data)
                
            self.nav_bar.visible = True
            
            if self.user.role == "driver":
                self.show_driver_view()
            else:
                self.show_scheduler()
                
            self.show_snackbar(f"Welcome back, {username}!")
        else:
            self.show_snackbar("Invalid username or password")
    
    def register(self, e):
        username = self.reg_username.value
        password = self.reg_password.value
        confirm = self.reg_confirm.value
        needs = [n.strip() for n in self.accessibility_needs.value.split(",") if n.strip()]
        
        if not username or not password:
            self.show_snackbar("Please fill in all required fields")
            return
            
        if password != confirm:
            self.show_snackbar("Passwords do not match")
            return
        
        try:
            if users_collection.find_one({"username": username}):
                self.show_snackbar("Username already exists")
                return
        except PyMongoError as e:
            self.show_snackbar(f"Database error: {str(e)}")
            return
            
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        new_user = User(
            username=username,
            password_hash=hashed_pw,
            accessibility_needs=needs
        )
        
        try:
            users_collection.insert_one(new_user.to_dict())
            self.user = new_user
            self.show_snackbar("Account created successfully!")
            self.show_scheduler()
        except PyMongoError as e:
            self.show_snackbar(f"Failed to create account: {str(e)}")
    
    def calculate_route(self, pickup: str, dropoff: str) -> tuple:
        """Calculate route using Google Maps API or fallback to internal graph"""
        if GOOGLE_MAPS_API_KEY:
            return self.calculate_route_with_google(pickup, dropoff)
        else:
            return self.calculate_route_internal(pickup, dropoff)
    
    def calculate_route_with_google(self, pickup: str, dropoff: str) -> tuple:
        """Calculate route using Google Maps API"""
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": pickup,
            "destination": dropoff,
            "key": GOOGLE_MAPS_API_KEY,
            "mode": "driving"
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] == "OK":
                route = data["routes"][0]["legs"][0]
                distance = route["distance"]["text"]
                duration = route["duration"]["text"]
                steps = [step["html_instructions"] for step in route["steps"]]
                
                # Extract numeric values
                distance_km = route["distance"]["value"] / 1000
                duration_min = route["duration"]["value"] // 60
                
                return distance_km, duration_min, steps
            else:
                return None, None, f"Google Maps error: {data['status']}"
        except Exception as e:
            return None, None, f"API request failed: {str(e)}"
    
    def calculate_route_internal(self, pickup: str, dropoff: str) -> tuple:
        """Calculate route using internal graph (fallback)"""
        # Find node IDs for locations
        node_map = {node["name"]: node_id for node_id, node in self.transport_graph.nodes.items()}
        
        start_id = None
        end_id = None
        
        for name, node_id in node_map.items():
            if pickup in name:
                start_id = node_id
            if dropoff in name:
                end_id = node_id
        
        if start_id is None or end_id is None:
            return None, None, "Locations not found in our system"
        
        # Use Dijkstra's algorithm to find optimal path
        path, total_time = self.transport_graph.dijkstra(start_id, end_id)
        
        # Calculate distance (simplified)
        distance = total_time * 0.5  # approx 0.5 km per minute
        
        # Get human-readable path
        path_names = [self.transport_graph.nodes[node_id]["name"] for node_id in path]
        steps = [f"Travel from {path_names[i]} to {path_names[i+1]}" for i in range(len(path_names)-1)]
        
        return distance, total_time, steps
    
    def schedule_ride(self, e):
        if not self.user:
            self.show_login()
            return
            
        pickup = self.pickup_location.value
        dropoff = self.dropoff_location.value
        date_str = self.schedule_date.value
        time_str = self.schedule_time.value
        requirements = self.accessibility_reqs.value
        
        if not pickup or not dropoff:
            self.show_snackbar("Please select pickup and dropoff locations")
            return
        
        try:
            scheduled_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            self.show_snackbar("Invalid date/time format")
            return
        
        # Calculate route and time
        distance, duration, steps = self.calculate_route(pickup, dropoff)
        
        if not distance or not duration:
            self.route_info.value = f"Route calculation failed: {steps}"
            self.page.update()
            return
        
        self.route_info.value = f"Route: {distance:.1f} km, Estimated Time: {duration} min"
        self.page.update()
        
        # Create ride request
        ride_request = RideRequest(
            user_id=self.user.username,
            pickup=pickup,
            dropoff=dropoff,
            scheduled_time=scheduled_time,
            accessibility_requirements=requirements.split(",") if requirements else [],
            estimated_time=duration,
            distance=distance
        )
        
        # Find available driver
        driver_assigned = False
        try:
            drivers = list(drivers_collection.find({"availability": True}))
        except PyMongoError as e:
            self.show_snackbar(f"Database error: {str(e)}")
            return
            
        for driver_data in drivers:
            driver = Driver.from_dict(driver_data)
            
            # Check if driver meets accessibility requirements
            if "wheelchair" in ride_request.accessibility_requirements:
                if "wheelchair ramp" not in driver.vehicle_type.lower():
                    continue
            
            # Assign driver
            ride_request.driver_id = driver.username
            ride_request.status = "scheduled"
            driver_assigned = True
            break
        
        if not driver_assigned:
            ride_request.status = "pending"
            self.show_snackbar("No available drivers. Your ride is pending assignment.")
        else:
            self.show_snackbar(f"Ride scheduled with driver {ride_request.driver_id}!")
        
        # Save ride to MongoDB
        try:
            rides_collection.insert_one(ride_request.to_dict())
        except PyMongoError as e:
            self.show_snackbar(f"Failed to save ride: {str(e)}")
            return
        
        # Reset form
        self.accessibility_reqs.value = ""
        self.page.update()
    
    def load_ride_history(self):
        self.history_list.controls.clear()
        
        try:
            user_rides = list(rides_collection.find({"user_id": self.user.username}))
        except PyMongoError as e:
            self.show_snackbar(f"Database error: {str(e)}")
            return
        
        if not user_rides:
            self.history_list.controls.append(
                ft.Text("No rides scheduled yet", size=18, color=ft.Colors.GREY)
            )
            return
        
        for ride_data in sorted(user_rides, key=lambda r: r["scheduled_time"], reverse=True):
            ride = RideRequest.from_dict(ride_data)
            status_color = {
                "pending": ft.Colors.ORANGE,
                "scheduled": ft.Colors.BLUE,
                "in_progress": ft.Colors.PURPLE,
                "completed": ft.Colors.GREEN,
                "canceled": ft.Colors.RED
            }.get(ride.status, ft.Colors.BLACK)
            
            self.history_list.controls.append(
                ModernCard(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(f"{ride.pickup} → {ride.dropoff}", 
                                            size=18, weight=ft.FontWeight.BOLD),
                                    ft.Container(
                                        ft.Text(ride.status.upper(), color=ft.Colors.WHITE, size=12),
                                        padding=ft.padding.symmetric(5, 10),
                                        bgcolor=status_color,
                                        border_radius=10
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Divider(height=10),
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text("SCHEDULED", size=12, color=ft.Colors.GREY),
                                            ft.Text(ride.scheduled_time.strftime("%b %d, %Y %H:%M"))
                                        ],
                                        spacing=2
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("DRIVER", size=12, color=ft.Colors.GREY),
                                            ft.Text(ride.driver_id or "Not assigned")
                                        ],
                                        spacing=2
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("DURATION", size=12, color=ft.Colors.GREY),
                                            ft.Text(f"{ride.estimated_time} min")
                                        ],
                                        spacing=2
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("DISTANCE", size=12, color=ft.Colors.GREY),
                                            ft.Text(f"{ride.distance:.1f} km")
                                        ],
                                        spacing=2
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Divider(height=10),
                            ft.Text("Requirements: " + ", ".join(ride.accessibility_requirements) 
                                   or "No special requirements")
                        ]
                    )
                )
            )
    
    def load_driver_rides(self):
        self.driver_rides.controls.clear()
        
        if not self.user or self.user.role != "driver":
            return
            
        try:
            driver_rides = list(rides_collection.find({"driver_id": self.user.username}))
        except PyMongoError as e:
            self.show_snackbar(f"Database error: {str(e)}")
            return
            
        if not driver_rides:
            self.driver_rides.controls.append(
                ft.Text("No scheduled rides", size=18, color=ft.Colors.GREY)
            )
            return
        
        for ride_data in sorted(driver_rides, key=lambda r: r["scheduled_time"]):
            ride = RideRequest.from_dict(ride_data)
            status_color = {
                "scheduled": ft.Colors.BLUE,
                "in_progress": ft.Colors.PURPLE
            }.get(ride.status, ft.Colors.BLACK)
            
            self.driver_rides.controls.append(
                ModernCard(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(f"{ride.pickup} → {ride.dropoff}", 
                                            size=18, weight=ft.FontWeight.BOLD),
                                    ft.Container(
                                        ft.Text(ride.status.upper(), color=ft.Colors.WHITE, size=12),
                                        padding=ft.padding.symmetric(5, 10),
                                        bgcolor=status_color,
                                        border_radius=10
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Divider(height=10),
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text("PASSENGER", size=12, color=ft.Colors.GREY),
                                            ft.Text(ride.user_id)
                                        ],
                                        spacing=2
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("TIME", size=12, color=ft.Colors.GREY),
                                            ft.Text(ride.scheduled_time.strftime("%b %d, %Y %H:%M"))
                                        ],
                                        spacing=2
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("DURATION", size=12, color=ft.Colors.GREY),
                                            ft.Text(f"{ride.estimated_time} min")
                                        ],
                                        spacing=2
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Divider(height=10),
                            ft.Text("Requirements: " + ", ".join(ride.accessibility_requirements) 
                                   or "No special requirements")
                        ]
                    )
                )
            )
    
    def mark_completed(self, e):
        if not self.user or self.user.role != "driver":
            return
        
        try:
            # Find the first scheduled ride for this driver
            ride_data = rides_collection.find_one({
                "driver_id": self.user.username,
                "status": "scheduled"
            })
            
            if ride_data:
                rides_collection.update_one(
                    {"_id": ride_data["_id"]},
                    {"$set": {"status": "completed"}}
                )
                self.show_snackbar("Ride marked as completed!")
                self.load_driver_rides()
            else:
                self.show_snackbar("No scheduled rides to mark as completed")
        except PyMongoError as e:
            self.show_snackbar(f"Database error: {str(e)}")
    
    def start_ride(self, e):
        if not self.user or self.user.role != "driver":
            return
        
        try:
            # Find the first scheduled ride for this driver
            ride_data = rides_collection.find_one({
                "driver_id": self.user.username,
                "status": "scheduled"
            })
            
            if ride_data:
                rides_collection.update_one(
                    {"_id": ride_data["_id"]},
                    {"$set": {"status": "in_progress"}}
                )
                self.show_snackbar("Ride started!")
                self.load_driver_rides()
            else:
                self.show_snackbar("No scheduled rides to start")
        except PyMongoError as e:
            self.show_snackbar(f"Database error: {str(e)}")
    
    def generate_analytics(self):
        try:
            all_rides = list(rides_collection.find())
        except PyMongoError as e:
            self.show_snackbar(f"Database error: {str(e)}")
            return
            
        if not all_rides:
            self.visualization_image.src = None
            self.page.update()
            return
            
        # Create plots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Ride frequency by location
        locations = [ride["pickup"] for ride in all_rides]
        location_counts = {}
        for loc in locations:
            location_counts[loc] = location_counts.get(loc, 0) + 1
        
        # Sort locations by frequency
        sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)
        loc_names = [loc[0] for loc in sorted_locations]
        loc_counts = [loc[1] for loc in sorted_locations]
        
        ax1.bar(loc_names, loc_counts, color='#4285F4')
        ax1.set_title('Ride Frequency by Location')
        ax1.set_xlabel('Location')
        ax1.set_ylabel('Number of Rides')
        ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: Ride status distribution
        status_counts = {}
        for ride in all_rides:
            status_counts[ride["status"]] = status_counts.get(ride["status"], 0) + 1
        
        status_names = list(status_counts.keys())
        status_values = list(status_counts.values())
        
        colors = {
            "pending": "#FBBC05",
            "scheduled": "#4285F4",
            "in_progress": "#34A853",
            "completed": "#0F9D58",
            "canceled": "#EA4335"
        }
        
        status_colors = [colors.get(status, "#999999") for status in status_names]
        
        ax2.pie(status_values, labels=status_names, autopct='%1.1f%%', 
                startangle=90, colors=status_colors)
        ax2.set_title('Ride Status Distribution')
        
        plt.tight_layout()
        
        # Convert plot to base64 for display in Flet
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        self.visualization_image.src_base64 = img_base64
        plt.close(fig)
        self.page.update()
    
    def show_snackbar(self, message: str):
        ft.SnackBar(
            ft.Text(message),
            bgcolor=ft.Colors.BLUE_700,
            behavior=ft.SnackBarBehavior.FLOATING,
            open=True
        ).show(self.page)
    
    def logout(self):
        self.user = None
        self.show_login()
        self.show_snackbar("You have been logged out")

def main(page: ft.Page):
    app = AccessibleTransportScheduler(page)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)