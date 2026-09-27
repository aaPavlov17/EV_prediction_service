import pytest
from fastapi.testclient import TestClient

from ev.service.app import app

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def good_row():
    return {
        "Age": 30,
        "Annual_Income_USD": 60000.0,
        "Daily_Commute_km": 15.0,
        "Number_of_Cars_Owned": 1.0,
        "Charging_Stations_Near_Home": 2.0,
        "Charging_Stations_Near_Work": 1.0,
        "Environmental_Concern_Level": 4.0,
        "Gender": "Male",
        "City_Type": "Urban",
        "Current_Car_Type": "Gasoline",
        "Home_Charging_Possible": "Yes",
        "Subsidy_Available": "No",
        "Range_Anxiety_Level": "Medium"
    }