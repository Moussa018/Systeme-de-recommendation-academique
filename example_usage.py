#!/usr/bin/env python3
"""
Example script demonstrating the Academic Recommendation System API usage.
Run this after starting the FastAPI server with: python main.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def pretty_print(title, data):
    """Pretty print JSON data"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(json.dumps(data, indent=2))

def check_health():
    """Check API health"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        pretty_print("API Health Check", response.json())
        return response.status_code == 200
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return False

def get_metrics():
    """Get system metrics"""
    try:
        response = requests.get(f"{BASE_URL}/metrics")
        pretty_print("System Metrics", response.json())
    except Exception as e:
        print(f"Error getting metrics: {e}")

def create_student(name, email, major, year):
    """Create a new student"""
    try:
        data = {
            "name": name,
            "email": email,
            "major": major,
            "year": year
        }
        response = requests.post(f"{BASE_URL}/students", json=data)
        if response.status_code == 200:
            pretty_print(f"Created Student: {name}", response.json())
            return response.json()
        else:
            print(f"Error creating student: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error creating student: {e}")
        return None

def create_module(title, code, description, credits, difficulty):
    """Create a new module"""
    try:
        data = {
            "title": title,
            "code": code,
            "description": description,
            "credits": credits,
            "difficulty": difficulty
        }
        response = requests.post(f"{BASE_URL}/modules", json=data)
        if response.status_code == 200:
            pretty_print(f"Created Module: {title}", response.json())
            return response.json()
        else:
            print(f"Error creating module: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error creating module: {e}")
        return None

def get_hybrid_recommendations(student_id, limit=5):
    """Get hybrid recommendations"""
    try:
        response = requests.get(
            f"{BASE_URL}/recommendations",
            params={"student_id": student_id, "limit": limit}
        )
        if response.status_code == 200:
            pretty_print(f"Hybrid Recommendations for Student {student_id}", response.json())
        else:
            print(f"Error getting recommendations: {response.status_code}")
    except Exception as e:
        print(f"Error getting recommendations: {e}")

def get_graph_only_recommendations(student_id, limit=5):
    """Get graph-only recommendations"""
    try:
        response = requests.get(
            f"{BASE_URL}/recommendations/graph-only",
            params={"student_id": student_id, "limit": limit}
        )
        if response.status_code == 200:
            pretty_print(f"Graph-Only Recommendations for Student {student_id}", response.json())
        else:
            print(f"Error getting recommendations: {response.status_code}")
    except Exception as e:
        print(f"Error getting recommendations: {e}")

def get_ml_only_recommendations(student_id, limit=5):
    """Get ML-only recommendations"""
    try:
        response = requests.get(
            f"{BASE_URL}/recommendations/ml-only",
            params={"student_id": student_id, "limit": limit}
        )
        if response.status_code == 200:
            pretty_print(f"ML-Only Recommendations for Student {student_id}", response.json())
        else:
            print(f"Error getting recommendations: {response.status_code}")
    except Exception as e:
        print(f"Error getting recommendations: {e}")

def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Academic Recommendation System - API Examples")
    print("="*60)
    
    # Check API health
    if not check_health():
        print("\nAPI is not running. Start it with: python main.py")
        return
    
    # Get system metrics
    get_metrics()
    
    # Test data
    print("\n" + "="*60)
    print("Testing with existing sample data...")
    print("="*60)
    
    # Try getting recommendations for student 1 (from sample data)
    print("\n1. Getting Hybrid Recommendations (Combined approach)")
    get_hybrid_recommendations(student_id=1, limit=5)
    
    # Get Graph-only recommendations
    print("\n2. Getting Graph-Only Recommendations (Knowledge Graph)")
    get_graph_only_recommendations(student_id=1, limit=5)
    
    # Get ML-only recommendations
    print("\n3. Getting ML-Only Recommendations (Collaborative Filtering)")
    get_ml_only_recommendations(student_id=1, limit=5)
    
    # Try with different student
    print("\n4. Getting recommendations for Student 2")
    get_hybrid_recommendations(student_id=2, limit=5)
    
    # Create new student (optional)
    print("\n5. Creating new student...")
    new_student = create_student(
        name="Dr. Jane Smith",
        email="jane.smith@example.com",
        major="Artificial Intelligence",
        year=3
    )
    
    # Create new module (optional)
    print("\n6. Creating new module...")
    new_module = create_module(
        title="Reinforcement Learning",
        code="AI401",
        description="Advanced reinforcement learning techniques",
        credits=4,
        difficulty="advanced"
    )
    
    print("\n" + "="*60)
    print("API Examples Complete!")
    print("="*60)
    print("\nFor more information:")
    print("- Interactive API docs: http://localhost:8000/docs")
    print("- ReDoc docs: http://localhost:8000/redoc")
    print("- README: See README.md in the project directory")

if __name__ == "__main__":
    main()
