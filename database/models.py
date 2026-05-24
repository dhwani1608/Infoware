from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database.db import Base


class Driver(Base):
    __tablename__ = "drivers"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    home_region = Column(String, nullable=False)
    efficiency_score = Column(Float, default=0.75)
    trips = relationship("Trip", back_populates="driver")


class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stop_name = Column(String, unique=True, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    region = Column(String, nullable=False)
    hotspot_score = Column(Float, default=0.5)


class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    driver_id = Column(String, ForeignKey("drivers.id"), nullable=False)
    date = Column(Date, nullable=False)
    stop_name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    visit_time = Column(String, nullable=False)
    visit_duration = Column(Float, nullable=False)
    traffic_level = Column(String, nullable=False)
    weather = Column(String, nullable=False)
    distance_from_previous = Column(Float, nullable=False)
    travel_time = Column(Float, nullable=False)
    fuel_estimate = Column(Float, nullable=False)
    region = Column(String, nullable=False)
    day_of_week = Column(String, nullable=False)
    week_number = Column(Integer, nullable=False)
    driver = relationship("Driver", back_populates="trips")


class RoutePrediction(Base):
    __tablename__ = "route_predictions"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    driver_id = Column(String, ForeignKey("drivers.id"), nullable=False)
    prediction_date = Column(Date, nullable=False)
    recommended_route = Column(Text, nullable=False)
    predicted_time_hours = Column(Float, nullable=False)
    total_distance_km = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    route_efficiency_score = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)


class WeeklyPrediction(Base):
    __tablename__ = "weekly_predictions"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    driver_id = Column(String, ForeignKey("drivers.id"), nullable=False)
    week = Column(String, nullable=False)
    schedule_json = Column(Text, nullable=False)
    weekly_distance_km = Column(Float, nullable=False)
    weekly_efficiency = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)
