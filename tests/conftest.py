"""
Pytest configuration and fixtures for the Mergington High School API tests.

Fixtures in this module:
- app: Provides a fresh FastAPI application instance
- client: Provides a TestClient for making API requests
- reset_activities: Resets the in-memory activities to a clean state
"""

import pytest
import sys
from pathlib import Path

# Add src directory to Python path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app, activities


@pytest.fixture
def client():
    """
    Fixture: Provides a TestClient for the FastAPI app.
    
    Used in every test to make HTTP requests to API endpoints.
    Returns a TestClient instance connected to the app.
    """
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture: Resets activities to initial state before each test.
    
    This ensures test isolation - each test starts with a clean, known state.
    The fixture clears the activities dictionary and repopulates it with
    the default activities.
    
    Yields the activities dict after resetting.
    """
    # Save original activities
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Team-based basketball practice and competitive games",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": ["carter@mergington.edu", "nina@mergington.edu"]
        },
        "Swimming Club": {
            "description": "Swimming techniques, conditioning, and lap practice",
            "schedule": "Mondays and Wednesdays, 5:00 PM - 6:30 PM",
            "max_participants": 18,
            "participants": ["harper@mergington.edu", "dylan@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore painting, drawing, and creative design projects",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": ["lily@mergington.edu", "sam@mergington.edu"]
        },
        "Drama Club": {
            "description": "Acting, theater production, and stage performance practice",
            "schedule": "Fridays, 4:00 PM - 6:00 PM",
            "max_participants": 25,
            "participants": ["ava@mergington.edu", "noah@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop public speaking and reasoning skills for competitions",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["mia@mergington.edu", "jack@mergington.edu"]
        },
        "Robotics Club": {
            "description": "Design and build robots while learning engineering concepts",
            "schedule": "Tuesdays, 4:00 PM - 6:00 PM",
            "max_participants": 14,
            "participants": ["ryan@mergington.edu", "zoe@mergington.edu"]
        }
    }
    
    # Clear current activities and repopulate with originals
    activities.clear()
    activities.update(original_activities)
    
    yield activities
    
    # Cleanup (optional, but good practice)
    activities.clear()


@pytest.fixture
def client_with_reset(reset_activities):
    """
    Fixture: Provides both a fresh client AND reset activities.
    
    Combines reset_activities and client fixtures.
    Use this fixture in tests that need a clean state.
    """
    return TestClient(app)
