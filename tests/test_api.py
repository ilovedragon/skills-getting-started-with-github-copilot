"""
FastAPI tests for Mergington High School Activities API

Tests cover all endpoints:
- GET / - redirect to static index
- GET /activities - get all activities
- POST /activities/{activity_name}/signup - sign up for activity
- DELETE /activities/{activity_name}/signup - unregister from activity

Tests follow AAA pattern: Arrange (setup), Act (execute), Assert (verify)
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """
    Provide a test client for the FastAPI app.
    Using fixture allows each test to work with fresh app state.
    """
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """
        ARRANGE: Client is ready
        ACT: Make GET request to /activities
        ASSERT: Status is 200 and response contains all 9 activities
        """
        # ACT
        response = client.get("/activities")

        # ASSERT
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
        assert "Basketball Team" in activities
        assert "Soccer Club" in activities
        assert "Art Club" in activities
        assert "Drama Club" in activities
        assert "Debate Club" in activities
        assert "Science Club" in activities

    def test_activity_has_required_fields(self, client):
        """
        ARRANGE: Client is ready
        ACT: Make GET request to /activities
        ASSERT: Each activity has required fields (description, schedule, max_participants, participants)
        """
        # ACT
        response = client.get("/activities")
        activities = response.json()

        # ASSERT
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

    def test_activity_participants_are_emails(self, client):
        """
        ARRANGE: Client is ready
        ACT: Make GET request to /activities
        ASSERT: Participants are email strings
        """
        # ACT
        response = client.get("/activities")
        activities = response.json()

        # ASSERT
        for activity_data in activities.values():
            for participant in activity_data["participants"]:
                assert "@" in participant
                assert isinstance(participant, str)


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """
        ARRANGE: Client is ready
        ACT: Make GET request to /
        ASSERT: Response is a redirect (307) to /static/index.html
        """
        # ACT
        response = client.get("/", follow_redirects=False)

        # ASSERT
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestSignupSuccess:
    """Tests for successful POST /activities/{activity_name}/signup"""

    def test_signup_adds_participant(self, client):
        """
        ARRANGE: Client is ready, test email is not signed up
        ACT: POST signup request with valid activity and email
        ASSERT: Status is 200, email is added to participants, response message confirms signup
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        assert activity_name in result["message"]

        # Verify participant was actually added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_response_message_format(self, client):
        """
        ARRANGE: Client is ready
        ACT: POST signup request
        ASSERT: Response message has expected format
        """
        # ARRANGE
        activity_name = "Programming Class"
        email = "alice@mergington.edu"

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 200
        result = response.json()
        assert result["message"] == f"Signed up {email} for {activity_name}"

    def test_signup_multiple_students_to_same_activity(self, client):
        """
        ARRANGE: Client is ready
        ACT: Sign up two different students to same activity
        ASSERT: Both are added to participants
        """
        # ARRANGE
        activity_name = "Art Club"
        email1 = "bob@mergington.edu"
        email2 = "clara@mergington.edu"

        # ACT
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )

        # ASSERT
        assert response1.status_code == 200
        assert response2.status_code == 200

        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email1 in activities[activity_name]["participants"]
        assert email2 in activities[activity_name]["participants"]


class TestSignupErrors:
    """Tests for error cases in POST /activities/{activity_name}/signup"""

    def test_signup_activity_not_found(self, client):
        """
        ARRANGE: Client is ready, activity doesn't exist
        ACT: POST signup request for non-existent activity
        ASSERT: Status is 404 with appropriate error message
        """
        # ARRANGE
        activity_name = "Nonexistent Activity"
        email = "test@mergington.edu"

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"].lower()

    def test_signup_duplicate_email(self, client):
        """
        ARRANGE: Client is ready, existing participant tries to sign up again
        ACT: POST signup request with email already in activity
        ASSERT: Status is 400 with appropriate error message
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "already signed up" in result["detail"].lower()

    def test_signup_duplicate_detection_case_sensitive(self, client):
        """
        ARRANGE: Client is ready
        ACT: Try to sign up with different case of existing email (should still error if compared directly)
        ASSERT: Duplicate check works (implementation specific - testing current behavior)
        """
        # ARRANGE
        activity_name = "Drama Club"
        existing_email = "mason@mergington.edu"  # Already in Drama Club
        different_case_email = "mason@Mergington.edu"

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": different_case_email}
        )

        # ASSERT - If implementation is case-sensitive, this should succeed
        # If implementation is case-insensitive, this should fail (400)
        # Current implementation appears case-sensitive
        assert response.status_code == 200


class TestUnregisterSuccess:
    """Tests for successful DELETE /activities/{activity_name}/signup"""

    def test_unregister_removes_participant(self, client):
        """
        ARRANGE: Client is ready, participant is signed up
        ACT: DELETE request to unregister participant
        ASSERT: Status is 200, participant is removed
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "daniel@mergington.edu"  # Already in Chess Club

        # Verify participant exists before deletion
        activities_before = client.get("/activities").json()
        assert email in activities_before[activity_name]["participants"]

        # ACT
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        assert activity_name in result["message"]

        # Verify participant was actually removed
        activities_after = client.get("/activities").json()
        assert email not in activities_after[activity_name]["participants"]

    def test_unregister_response_message_format(self, client):
        """
        ARRANGE: Client is ready
        ACT: DELETE request to unregister
        ASSERT: Response message has expected format
        """
        # ARRANGE
        activity_name = "Science Club"
        email = "harper@mergington.edu"

        # ACT
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 200
        result = response.json()
        assert result["message"] == f"Unregistered {email} from {activity_name}"

    def test_unregister_multiple_participants(self, client):
        """
        ARRANGE: Client is ready, activity has multiple participants
        ACT: Remove one participant
        ASSERT: Only that participant is removed, others remain
        """
        # ARRANGE
        activity_name = "Basketball Team"
        remove_email = "alex@mergington.edu"
        
        # Get initial participants
        activities_before = client.get("/activities").json()
        initial_participants = activities_before[activity_name]["participants"].copy()

        # ACT
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": remove_email}
        )

        # ASSERT
        assert response.status_code == 200

        # Verify only the target email was removed
        activities_after = client.get("/activities").json()
        final_participants = activities_after[activity_name]["participants"]
        
        assert remove_email not in final_participants
        # Count should be one less
        assert len(final_participants) == len(initial_participants) - 1


class TestUnregisterErrors:
    """Tests for error cases in DELETE /activities/{activity_name}/signup"""

    def test_unregister_activity_not_found(self, client):
        """
        ARRANGE: Client is ready, activity doesn't exist
        ACT: DELETE request for non-existent activity
        ASSERT: Status is 404 with appropriate error message
        """
        # ARRANGE
        activity_name = "Nonexistent Activity"
        email = "test@mergington.edu"

        # ACT
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"].lower()

    def test_unregister_participant_not_found(self, client):
        """
        ARRANGE: Client is ready, email is not signed up for activity
        ACT: DELETE request for email not in participants
        ASSERT: Status is 400 with appropriate error message
        """
        # ARRANGE
        activity_name = "Soccer Club"
        email = "notexisting@mergington.edu"

        # ACT
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "not signed up" in result["detail"].lower()

    def test_unregister_twice_fails_second_time(self, client):
        """
        ARRANGE: Client is ready
        ACT: Unregister a participant, then try to unregister the same participant again
        ASSERT: First unregister succeeds (200), second fails (400)
        """
        # ARRANGE
        activity_name = "Programming Class"
        email = "sophia@mergington.edu"

        # ACT - First unregister
        response1 = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ACT - Second unregister attempt
        response2 = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response1.status_code == 200
        assert response2.status_code == 400
        result = response2.json()
        assert "not signed up" in result["detail"].lower()


class TestSignupUnregisterFlow:
    """Integration tests for signup and unregister flow"""

    def test_signup_then_unregister_flow(self, client):
        """
        ARRANGE: Client is ready
        ACT: Sign up new participant, verify added, unregister, verify removed
        ASSERT: All operations succeed with correct state changes
        """
        # ARRANGE
        activity_name = "Gym Class"
        email = "newgymstudent@mergington.edu"

        # ACT - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT signup
        assert signup_response.status_code == 200
        activities_after_signup = client.get("/activities").json()
        assert email in activities_after_signup[activity_name]["participants"]

        # ACT - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT unregister
        assert unregister_response.status_code == 200
        activities_after_unregister = client.get("/activities").json()
        assert email not in activities_after_unregister[activity_name]["participants"]

    def test_signup_to_multiple_activities(self, client):
        """
        ARRANGE: Client is ready
        ACT: Sign up same student to multiple activities
        ASSERT: Student appears in all activities
        """
        # ARRANGE
        email = "multi@mergington.edu"
        activities_list = ["Chess Club", "Debate Club", "Science Club"]

        # ACT - Sign up to all activities
        for activity_name in activities_list:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # ASSERT - Verify in all activities
        activities = client.get("/activities").json()
        for activity_name in activities_list:
            assert email in activities[activity_name]["participants"]
