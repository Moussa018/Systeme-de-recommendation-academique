import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from core.engine import GraphEngine
from data.loader import populate_graph


@pytest.fixture(scope="module")
def engine():
    e = GraphEngine()
    populate_graph(e)
    return e


class TestGraphPopulation:
    def test_triple_count_positive(self, engine):
        assert engine.triple_count > 100

    def test_all_modules_loaded(self, engine):
        modules = engine.get_all_modules()
        assert len(modules) == 35

    def test_all_students_loaded(self, engine):
        students = engine.get_all_students()
        assert len(students) == 100


class TestStudentProfile:
    def test_existing_student_has_profile(self, engine):
        profile = engine.get_student_profile("STU001")
        assert profile["student_id"] == "STU001"
        assert profile["student_name"] is not None
        assert isinstance(profile["mastered_skills"], list)
        assert isinstance(profile["completed_modules"], list)

    def test_unknown_student_returns_empty(self, engine):
        profile = engine.get_student_profile("UNKNOWN_999")
        assert profile["student_name"] is None


class TestRecommendations:
    def test_recommendations_are_list(self, engine):
        recs = engine.get_recommendations("STU001")
        assert isinstance(recs, list)

    def test_recommendation_has_required_fields(self, engine):
        recs = engine.get_recommendations("STU001")
        for r in recs:
            assert "module_id"        in r
            assert "module_name"      in r
            assert "difficulty_level" in r
            assert "credits"          in r
            assert "score"            in r

    def test_recommendations_not_already_completed(self, engine):
        """Recommended modules must not be in student's completed list."""
        profile = engine.get_student_profile("STU001")
        completed = set(profile["completed_modules"])
        recs = engine.get_recommendations("STU001")
        rec_names = {r["module_name"] for r in recs}
        assert completed.isdisjoint(rec_names), \
            f"Overlap found: {completed & rec_names}"


class TestPrerequisites:
    def test_deep_learning_has_prerequisites(self, engine):
        # m21 = "Deep Learning avec PyTorch" (requires ML + Linear Algebra)
        prereqs = engine.get_module_prerequisites("m21")
        assert len(prereqs) > 0

    def test_intro_python_no_prerequisites(self, engine):
        prereqs = engine.get_module_prerequisites("m01")
        assert prereqs == []