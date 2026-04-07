"""
Endpoint tests for Mergington High School API.

All tests follow the Arrange-Act-Assert (AAA) pattern:
- Arrange: Set up test data and initial state
- Act: Call the API endpoint
- Assert: Verify response status, content, and state changes

Tests cover:
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/participants
"""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities_returns_200_and_all_activities(self, client_with_reset):
        """
        Test that GET /activities returns all activities with 200 status.
        
        AAA Pattern:
        - Arrange: Client is ready with reset activities
        - Act: Make GET request to /activities
        - Assert: Verify 200 status and response contains all activity names
        """
        # Arrange
        client = client_with_reset
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball Team", "Swimming Club", "Art Club",
            "Drama Club", "Debate Team", "Robotics Club"
        ]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
        for activity_name in expected_activities:
            assert activity_name in activities


    def test_get_activities_includes_all_required_fields(self, client_with_reset):
        """
        Test that each activity has required fields: description, schedule, 
        max_participants, and participants.
        
        AAA Pattern:
        - Arrange: Client is ready
        - Act: Fetch activities
        - Assert: Verify each activity has all required fields
        """
        # Arrange
        client = client_with_reset
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Activity '{activity_name}' missing field '{field}'"


    def test_get_activities_returns_correct_participant_count(self, client_with_reset):
        """
        Test that participant arrays contain the expected emails.
        
        AAA Pattern:
        - Arrange: Client is ready
        - Act: Fetch activities
        - Assert: Verify Chess Club has 2 participants
        """
        # Arrange
        client = client_with_reset
        expected_chess_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        chess_club = activities["Chess Club"]
        assert chess_club["participants"] == expected_chess_participants


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup_adds_participant(self, client_with_reset):
        """
        Test that successfully signing up adds the email to participants list.
        
        AAA Pattern:
        - Arrange: Set up client and test email
        - Act: POST signup request
        - Assert: Verify 200 status and email now in participants
        """
        # Arrange
        client = client_with_reset
        test_email = "newstudent@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={test_email}",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        assert response.status_code == 200
        assert f"Signed up {test_email}" in response.json()["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert test_email in activities[activity_name]["participants"]


    def test_signup_prevents_duplicate_registration(self, client_with_reset):
        """
        Test that attempting to sign up twice returns 400 error.
        
        AAA Pattern:
        - Arrange: Set up client and an already-registered email
        - Act: POST signup for email already in participants
        - Assert: Verify 400 status and appropriate error message
        """
        # Arrange
        client = client_with_reset
        already_registered_email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={already_registered_email}",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


    def test_signup_returns_404_for_nonexistent_activity(self, client_with_reset):
        """
        Test that signing up for non-existent activity returns 404.
        
        AAA Pattern:
        - Arrange: Set up client with invalid activity name
        - Act: POST signup for non-existent activity
        - Assert: Verify 404 status and error message
        """
        # Arrange
        client = client_with_reset
        test_email = "newstudent@mergington.edu"
        invalid_activity = "Non-Existent Activity"
        
        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup?email={test_email}",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


    def test_signup_returns_400_when_activity_at_capacity(self, client_with_reset):
        """
        Test that signup fails when activity has reached max_participants capacity.
        
        AAA Pattern:
        - Arrange: Find or create an activity at capacity by signing up students
        - Act: Try to sign up one more student when at capacity
        - Assert: Verify 400 status and capacity error message
        """
        # Arrange
        client = client_with_reset
        # Create a minimal activity by resetting just one activity
        # Chess Club has max 12, currently 2, so add 10 more
        test_emails = [f"student{i}@mergington.edu" for i in range(10)]
        activity_name = "Chess Club"
        
        # Fill Chess Club to capacity
        for email in test_emails:
            client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify at capacity
        response = client.get("/activities")
        chess_club = response.json()[activity_name]
        assert len(chess_club["participants"]) == 12  # max_participants
        
        # Act
        over_capacity_email = "capacityoverflow@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup?email={over_capacity_email}",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        assert response.status_code == 400
        assert "maximum capacity" in response.json()["detail"]


    def test_signup_increments_participant_count(self, client_with_reset):
        """
        Test that signing up increments the participant count.
        
        AAA Pattern:
        - Arrange: Get initial participant count
        - Act: Sign up a new student
        - Assert: Verify participant count increased by 1
        """
        # Arrange
        client = client_with_reset
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Programming Class"]["participants"])
        
        # Act
        test_email = "newcomer@mergington.edu"
        client.post(f"/activities/Programming%20Class/signup?email={test_email}")
        
        # Assert
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()["Programming Class"]["participants"])
        assert updated_count == initial_count + 1


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_successful_participant_removal(self, client_with_reset):
        """
        Test that successfully removing a participant deletes them from the list.
        
        AAA Pattern:
        - Arrange: Get a participant to remove
        - Act: DELETE request with participant email
        - Assert: Verify 200 status and email no longer in participants
        """
        # Arrange
        client = client_with_reset
        email_to_remove = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email_to_remove}",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        assert response.status_code == 200
        assert f"Removed {email_to_remove}" in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email_to_remove not in activities[activity_name]["participants"]


    def test_remove_participant_returns_404_for_nonexistent_activity(self, client_with_reset):
        """
        Test that removing from non-existent activity returns 404.
        
        AAA Pattern:
        - Arrange: Set up invalid activity name
        - Act: DELETE from non-existent activity
        - Assert: Verify 404 status
        """
        # Arrange
        client = client_with_reset
        test_email = "anyone@mergington.edu"
        invalid_activity = "Non-Existent Activity"
        
        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/participants?email={test_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


    def test_remove_nonexistent_participant_returns_404(self, client_with_reset):
        """
        Test that removing a non-existent participant returns 404.
        
        AAA Pattern:
        - Arrange: Set up valid activity and non-existent participant email
        - Act: DELETE non-existent participant
        - Assert: Verify 404 status and error message
        """
        # Arrange
        client = client_with_reset
        nonexistent_email = "doesnotexist@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={nonexistent_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]


    def test_remove_decrements_participant_count(self, client_with_reset):
        """
        Test that removing a participant decreases the count by 1.
        
        AAA Pattern:
        - Arrange: Get initial participant count
        - Act: Remove a participant
        - Assert: Verify count decreased by 1
        """
        # Arrange
        client = client_with_reset
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])
        email_to_remove = "michael@mergington.edu"
        
        # Act
        client.delete(f"/activities/Chess%20Club/participants?email={email_to_remove}")
        
        # Assert
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()["Chess Club"]["participants"])
        assert updated_count == initial_count - 1


    def test_remove_participant_response_message_format(self, client_with_reset):
        """
        Test that removal response message has correct format.
        
        AAA Pattern:
        - Arrange: Set up participant to remove
        - Act: DELETE the participant
        - Assert: Verify message format is correct
        """
        # Arrange
        client = client_with_reset
        email = "daniel@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        
        # Assert
        message = response.json()["message"]
        assert "Removed" in message
        assert email in message
        assert activity_name in message
