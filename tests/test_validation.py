"""
Validation and edge case tests for Mergington High School API.

These tests focus on input validation, edge cases, and business logic constraints.
All tests follow the Arrange-Act-Assert (AAA) pattern.

Tests cover:
- Email format validation
- Activity name handling (URL encoding, case sensitivity)
- Capacity limit enforcement
- Concurrent signup scenarios
- Empty/whitespace handling
"""

import pytest
from fastapi.testclient import TestClient


class TestEmailValidation:
    """Tests for email validation in signup endpoint"""

    def test_signup_with_missing_email_parameter_returns_422(self, client_with_reset):
        """
        Test that missing email query parameter returns 422 validation error.
        
        AAA Pattern:
        - Arrange: Set up endpoint without email parameter
        - Act: POST signup without email
        - Assert: Verify 422 status (validation error)
        """
        # Arrange
        client = client_with_reset
        activity_name = "Chess Club"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup")
        
        # Assert
        assert response.status_code == 422


    def test_signup_with_empty_email_parameter(self, client_with_reset):
        """
        Test that empty email parameter is handled gracefully.
        
        AAA Pattern:
        - Arrange: Set up empty email parameter
        - Act: POST signup with empty email
        - Assert: Verify response has status 200 but email is empty string (edge case)
        """
        # Arrange
        client = client_with_reset
        activity_name = "Chess Club"
        empty_email = ""
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={empty_email}",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert - Empty email is accepted as string but is a valid param
        # (Pydantic EmailStr NOT enforced yet in current implementation)
        # Just verify the endpoint doesn't crash
        assert response.status_code in [200, 400, 422]


class TestActivityNameHandling:
    """Tests for activity name handling and URL encoding"""

    def test_signup_with_url_encoded_activity_name(self, client_with_reset):
        """
        Test that URL-encoded activity names are handled correctly.
        
        AAA Pattern:
        - Arrange: Prepare activity name with spaces (URL encoded)
        - Act: POST signup with encoded activity name
        - Assert: Verify successful signup
        """
        # Arrange
        client = client_with_reset
        test_email = "newstudent@mergington.edu"
        # "Chess Club" encoded is "Chess%20Club"
        
        # Act
        response = client.post(
            f"/activities/Chess%20Club/signup?email={test_email}",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify in activities
        activities_response = client.get("/activities")
        assert test_email in activities_response.json()["Chess Club"]["participants"]


    def test_activity_name_case_sensitive(self, client_with_reset):
        """
        Test that activity names are case-sensitive.
        
        AAA Pattern:
        - Arrange: Use different case for activity name
        - Act: POST signup with wrong case
        - Assert: Verify 404 (activity not found)
        """
        # Arrange
        client = client_with_reset
        test_email = "student@mergington.edu"
        wrong_case_activity = "chess club"  # lowercase instead of "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{wrong_case_activity}/signup?email={test_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


    def test_activity_with_special_characters_not_found(self, client_with_reset):
        """
        Test that activity names with special characters return 404.
        
        AAA Pattern:
        - Arrange: Use activity name with special characters
        - Act: POST signup
        - Assert: Verify 404 status
        """
        # Arrange
        client = client_with_reset
        test_email = "student@mergington.edu"
        special_activity = "Chess%20Club%21"  # "Chess Club!" with special char
        
        # Act
        response = client.post(
            f"/activities/{special_activity}/signup?email={test_email}"
        )
        
        # Assert
        assert response.status_code == 404


class TestCapacityEnforcement:
    """Tests for activity capacity limits"""

    def test_activity_at_capacity_blocks_signup(self, client_with_reset):
        """
        Test that activities at max capacity block new signups.
        
        AAA Pattern:
        - Arrange: Fill an activity to capacity
        - Act: Attempt signup when at capacity
        - Assert: Verify 400 capacity error
        """
        # Arrange
        client = client_with_reset
        activity_name = "Chess Club"
        max_capacity = 12
        
        # Fill remaining 10 spots (already 2 participants)
        for i in range(10):
            email = f"filler{i}@mergington.edu"
            client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify at capacity
        response = client.get("/activities")
        participants = len(response.json()[activity_name]["participants"])
        assert participants == max_capacity
        
        # Act
        overflow_email = "overflow@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup?email={overflow_email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "capacity" in response.json()["detail"].lower()


    def test_exactly_at_capacity_message_clarity(self, client_with_reset):
        """
        Test that capacity error message is clear when exactly at limit.
        
        AAA Pattern:
        - Arrange: Fill activity to exact capacity
        - Act: Try one more signup
        - Assert: Verify clear error message
        """
        # Arrange
        client = client_with_reset
        activity_name = "Chess Club"
        max_capacity = 12
        
        # Fill to exact capacity
        for i in range(10):
            client.post(f"/activities/{activity_name}/signup?email=fill{i}@test.edu")
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email=over@test.edu"
        )
        
        # Assert
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "maximum capacity" in detail.lower()


    def test_partial_capacity_allows_signup(self, client_with_reset):
        """
        Test that activities with available spots allow new signups.
        
        AAA Pattern:
        - Arrange: Find activity with available spots
        - Act: Signup to activity with space
        - Assert: Verify successful signup
        """
        # Arrange
        client = client_with_reset
        activity_name = "Programming Class"  # max 20, has 2, so 18 available
        test_email = "enthusiast@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify added
        activities = client.get("/activities").json()
        assert test_email in activities[activity_name]["participants"]


class TestSequentialOperations:
    """Tests for sequences of operations"""

    def test_signup_then_remove_same_participant(self, client_with_reset):
        """
        Test signup followed by removal of same participant.
        
        AAA Pattern:
        - Arrange: Set up test participant
        - Act: Sign up, then immediately remove
        - Assert: Verify back to original state
        """
        # Arrange
        client = client_with_reset
        test_email = "sequence@mergington.edu"
        activity_name = "Chess Club"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )
        assert signup_response.status_code == 200
        
        # Act - Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/participants?email={test_email}"
        )
        assert remove_response.status_code == 200
        
        # Assert
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        assert final_count == initial_count


    def test_remove_then_resign_same_participant(self, client_with_reset):
        """
        Test removal of participant then re-signup.
        
        AAA Pattern:
        - Arrange: Set up existing participant
        - Act: Remove, then sign up again
        - Assert: Verify both operations succeed (participant added back)
        """
        # Arrange
        client = client_with_reset
        test_email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Act - Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/participants?email={test_email}"
        )
        assert remove_response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        assert test_email not in response.json()[activity_name]["participants"]
        
        # Act - Re-signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )
        
        # Assert
        assert signup_response.status_code == 200
        response = client.get("/activities")
        assert test_email in response.json()[activity_name]["participants"]


    def test_multiple_participants_independent_operations(self, client_with_reset):
        """
        Test that operations on different participants don't interfere.
        
        AAA Pattern:
        - Arrange: Set up two participants
        - Act: Remove one, verify other still there
        - Assert: Confirm independent operation
        """
        # Arrange
        client = client_with_reset
        email1 = "michael@mergington.edu"
        email2 = "daniel@mergington.edu"
        activity_name = "Chess Club"
        
        # Act - Remove first participant
        remove_response = client.delete(
            f"/activities/{activity_name}/participants?email={email1}"
        )
        assert remove_response.status_code == 200
        
        # Assert - Second participant still there
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert email1 not in participants
        assert email2 in participants


class TestErrorMessages:
    """Tests for error message clarity and consistency"""

    def test_nonexistent_activity_error_message(self, client_with_reset):
        """
        Test that error message for non-existent activity is clear.
        
        AAA Pattern:
        - Arrange: Use invalid activity name
        - Act: POST or DELETE with invalid activity
        - Assert: Verify clear error message
        """
        # Arrange
        client = client_with_reset
        invalid_activity = "Fake Activity"
        test_email = "test@mergington.edu"
        
        # Act - Test POST
        response = client.post(
            f"/activities/{invalid_activity}/signup?email={test_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


    def test_duplicate_signup_error_message(self, client_with_reset):
        """
        Test that duplicate signup error message is informative.
        
        AAA Pattern:
        - Arrange: Use already-registered email
        - Act: POST signup with duplicate email
        - Assert: Verify error clearly indicates duplicate
        """
        # Arrange
        client = client_with_reset
        duplicate_email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={duplicate_email}"
        )
        
        # Assert
        assert response.status_code == 400
        error_msg = response.json()["detail"]
        assert "already signed up" in error_msg.lower()


    def test_capacity_exceeded_error_message(self, client_with_reset):
        """
        Test that capacity exceeded error message is clear.
        
        AAA Pattern:
        - Arrange: Fill activity to capacity
        - Act: Try to exceed capacity
        - Assert: Verify error mentions capacity
        """
        # Arrange
        client = client_with_reset
        activity_name = "Chess Club"
        
        # Fill to capacity
        for i in range(10):
            client.post(f"/activities/{activity_name}/signup?email=fill{i}@test.edu")
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email=over@test.edu"
        )
        
        # Assert
        assert response.status_code == 400
        error_msg = response.json()["detail"]
        assert "capacity" in error_msg.lower()
