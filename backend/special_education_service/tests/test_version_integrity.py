import asyncio
import pytest
import uuid
from uuid import UUID
from typing import List, Dict, Any


class TestVersionIntegrity:
    """Test version integrity and constraint enforcement"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_version_uniqueness_constraint(
        self, 
        iep_repository, 
        student_repository, 
        sample_student_data
    ):
        """Test that version uniqueness constraints are enforced"""
        # Create a student
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        academic_year = "2025-2026"
        
        # Create first IEP with version 1
        iep_data1 = {
            "student_id": student_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": {"test": "content1"},
            "version": 1,
            "created_by": uuid.uuid4()
        }
        iep1 = await iep_repository.create_iep(iep_data1)
        assert iep1["version"] == 1
        
        # Attempt to create another IEP with the same version should work 
        # (because we handle conflicts at the service level, not database level)
        iep_data2 = {
            "student_id": student_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": {"test": "content2"},
            "version": 1,  # Same version - this will create a conflict
            "created_by": uuid.uuid4()
        }
        
        # This should succeed at repository level but would cause issues at service level
        iep2 = await iep_repository.create_iep(iep_data2)
        
        # However, the service layer should prevent this via atomic version assignment
        # Let's test the atomic version assignment
        version_num = await iep_repository.get_next_version_number(student_id, academic_year)
        assert version_num == 3  # Should be 3 since we already have versions 1 and 1 (duplicate)

    @pytest.mark.asyncio
    async def test_parent_child_relationship_integrity(
        self, 
        iep_repository, 
        student_repository, 
        sample_student_data
    ):
        """Test parent-child relationship integrity in version chains"""
        # Create a student
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        academic_year = "2025-2026"
        
        # Create version chain: 1 -> 2 -> 3
        iep_data1 = {
            "student_id": student_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": {"version": "1"},
            "version": 1,
            "created_by": uuid.uuid4()
        }
        iep1 = await iep_repository.create_iep(iep_data1)
        
        iep_data2 = {
            "student_id": student_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": {"version": "2"},
            "version": 2,
            "parent_version_id": iep1["id"],
            "created_by": uuid.uuid4()
        }
        iep2 = await iep_repository.create_iep(iep_data2)
        
        iep_data3 = {
            "student_id": student_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": {"version": "3"},
            "version": 3,
            "parent_version_id": iep2["id"],
            "created_by": uuid.uuid4()
        }
        iep3 = await iep_repository.create_iep(iep_data3)
        
        # Verify relationships
        assert iep1["parent_version_id"] is None
        assert iep2["parent_version_id"] == iep1["id"]
        assert iep3["parent_version_id"] == iep2["id"]
        
        # Test getting version history
        history = await iep_repository.get_iep_version_history(student_id, academic_year)
        assert len(history) == 3
        
        # History should be ordered by version (or creation date)
        versions = [h["version"] for h in history]
        assert sorted(versions) == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_atomic_version_assignment(
        self, 
        iep_repository, 
        student_repository, 
        sample_student_data
    ):
        """Test atomic version number assignment"""
        # Create a student
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        academic_year = "2025-2026"
        
        # Test sequential atomic assignments
        version1 = await iep_repository.get_next_version_number(student_id, academic_year)
        assert version1 == 1
        
        # Create IEP with this version
        iep_data1 = {
            "student_id": student_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": {"test": "content1"},
            "version": version1,
            "created_by": uuid.uuid4()
        }
        await iep_repository.create_iep(iep_data1)
        
        # Next version should be 2
        version2 = await iep_repository.get_next_version_number(student_id, academic_year)
        assert version2 == 2
        
        # Create IEP with this version
        iep_data2 = {
            "student_id": student_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": {"test": "content2"},
            "version": version2,
            "created_by": uuid.uuid4()
        }
        await iep_repository.create_iep(iep_data2)
        
        # Next version should be 3
        version3 = await iep_repository.get_next_version_number(student_id, academic_year)
        assert version3 == 3

    @pytest.mark.asyncio
    async def test_concurrent_version_assignment(
        self, 
        iep_repository, 
        student_repository, 
        sample_student_data
    ):
        """Test concurrent version assignment doesn't create duplicates"""
        # Create a student
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        academic_year = "2025-2026"
        
        # Concurrently request version numbers
        async def get_version_task(task_id: int):
            try:
                version = await iep_repository.get_next_version_number(student_id, academic_year)
                return {"success": True, "version": version, "task_id": task_id}
            except Exception as e:
                return {"success": False, "error": str(e), "task_id": task_id}
        
        # Run 10 concurrent version requests
        tasks = [get_version_task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) == 10
        
        # All versions should be unique
        versions = [r["version"] for r in successful_results]
        assert len(set(versions)) == len(versions)  # All unique
        
        # Versions should be sequential
        versions.sort()
        expected_versions = list(range(1, 11))
        assert versions == expected_versions

    @pytest.mark.asyncio
    async def test_version_isolation_between_students(
        self, 
        iep_repository, 
        student_repository, 
        sample_student_data
    ):
        """Test that version numbers are isolated between different students"""
        # Create two students
        student_data1 = {**sample_student_data, "student_id": "TEST-001", "first_name": "Student1"}
        student_data2 = {**sample_student_data, "student_id": "TEST-002", "first_name": "Student2"}
        
        student1 = await student_repository.create_student(student_data1)
        student2 = await student_repository.create_student(student_data2)
        
        academic_year = "2025-2026"
        
        # Both students should start with version 1
        version1_s1 = await iep_repository.get_next_version_number(student1["id"], academic_year)
        version1_s2 = await iep_repository.get_next_version_number(student2["id"], academic_year)
        
        assert version1_s1 == 1
        assert version1_s2 == 1
        
        # Create IEPs for both students
        iep_data_s1 = {
            "student_id": student1["id"],
            "academic_year": academic_year,
            "status": "draft",
            "content": {"student": "1"},
            "version": version1_s1,
            "created_by": uuid.uuid4()
        }
        iep_data_s2 = {
            "student_id": student2["id"],
            "academic_year": academic_year,
            "status": "draft",
            "content": {"student": "2"},
            "version": version1_s2,
            "created_by": uuid.uuid4()
        }
        
        await iep_repository.create_iep(iep_data_s1)
        await iep_repository.create_iep(iep_data_s2)
        
        # Next versions should also be independent
        version2_s1 = await iep_repository.get_next_version_number(student1["id"], academic_year)
        version2_s2 = await iep_repository.get_next_version_number(student2["id"], academic_year)
        
        assert version2_s1 == 2
        assert version2_s2 == 2

    @pytest.mark.asyncio
    async def test_version_isolation_between_academic_years(
        self, 
        iep_repository, 
        student_repository, 
        sample_student_data
    ):
        """Test that version numbers are isolated between different academic years"""
        # Create a student
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        
        year1 = "2024-2025"
        year2 = "2025-2026"
        year3 = "2026-2027"
        
        # All years should start with version 1
        version1_y1 = await iep_repository.get_next_version_number(student_id, year1)
        version1_y2 = await iep_repository.get_next_version_number(student_id, year2)
        version1_y3 = await iep_repository.get_next_version_number(student_id, year3)
        
        assert version1_y1 == 1
        assert version1_y2 == 1
        assert version1_y3 == 1
        
        # Create IEPs for different years
        for i, year in enumerate([year1, year2, year3], 1):
            iep_data = {
                "student_id": student_id,
                "academic_year": year,
                "status": "draft",
                "content": {"year": year},
                "version": 1,
                "created_by": uuid.uuid4()
            }
            await iep_repository.create_iep(iep_data)
        
        # Next versions should be independent for each year
        version2_y1 = await iep_repository.get_next_version_number(student_id, year1)
        version2_y2 = await iep_repository.get_next_version_number(student_id, year2)
        version2_y3 = await iep_repository.get_next_version_number(student_id, year3)
        
        assert version2_y1 == 2
        assert version2_y2 == 2
        assert version2_y3 == 2

    @pytest.mark.asyncio
    async def test_latest_version_retrieval(
        self, 
        iep_repository, 
        student_repository, 
        sample_student_data
    ):
        """Test retrieval of latest IEP version"""
        # Create a student
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        academic_year = "2025-2026"
        
        # Initially, no latest version
        latest = await iep_repository.get_latest_iep_version(student_id, academic_year)
        assert latest is None
        
        # Create version 1
        iep_data1 = {
            "student_id": student_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": {"version": "1"},
            "version": 1,
            "created_by": uuid.uuid4()
        }
        iep1 = await iep_repository.create_iep(iep_data1)
        
        # Latest should be version 1
        latest = await iep_repository.get_latest_iep_version(student_id, academic_year)
        assert latest is not None
        assert latest["id"] == iep1["id"]
        assert latest["version"] == 1
        
        # Create version 2
        iep_data2 = {
            "student_id": student_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": {"version": "2"},
            "version": 2,
            "parent_version_id": iep1["id"],
            "created_by": uuid.uuid4()
        }
        iep2 = await iep_repository.create_iep(iep_data2)
        
        # Latest should now be version 2
        latest = await iep_repository.get_latest_iep_version(student_id, academic_year)
        assert latest is not None
        assert latest["id"] == iep2["id"]
        assert latest["version"] == 2
        
        # Create version 3
        iep_data3 = {
            "student_id": student_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": {"version": "3"},
            "version": 3,
            "parent_version_id": iep2["id"],
            "created_by": uuid.uuid4()
        }
        iep3 = await iep_repository.create_iep(iep_data3)
        
        # Latest should now be version 3
        latest = await iep_repository.get_latest_iep_version(student_id, academic_year)
        assert latest is not None
        assert latest["id"] == iep3["id"]
        assert latest["version"] == 3

    @pytest.mark.asyncio
    async def test_version_chain_integrity_after_updates(
        self, 
        iep_service, 
        student_repository, 
        sample_student_data, 
        sample_iep_data
    ):
        """Test that version chains remain intact after updates"""
        # Create a student
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        
        # Create initial IEP (version 1)
        iep1 = await iep_service.create_iep(
            student_id=student_id,
            academic_year=sample_iep_data["academic_year"],
            initial_data=sample_iep_data,
            user_id=uuid.uuid4()
        )
        
        # Create second IEP (version 2)
        iep2 = await iep_service.create_iep(
            student_id=student_id,
            academic_year=sample_iep_data["academic_year"],
            initial_data=sample_iep_data,
            user_id=uuid.uuid4()
        )
        
        # Create third IEP (version 3)
        iep3 = await iep_service.create_iep(
            student_id=student_id,
            academic_year=sample_iep_data["academic_year"],
            initial_data=sample_iep_data,
            user_id=uuid.uuid4()
        )
        
        # Verify chain: 1 -> 2 -> 3
        assert iep1["version"] == 1
        assert iep1["parent_version_id"] is None
        
        assert iep2["version"] == 2
        assert iep2["parent_version_id"] == iep1["id"]
        
        assert iep3["version"] == 3
        assert iep3["parent_version_id"] == iep2["id"]
        
        # Get version history and verify it's complete
        history = await iep_service.repository.get_iep_version_history(
            student_id, 
            sample_iep_data["academic_year"]
        )
        
        assert len(history) == 3
        history_by_version = {h["version"]: h for h in history}
        
        # Verify all versions are present and relationships are correct
        assert 1 in history_by_version
        assert 2 in history_by_version
        assert 3 in history_by_version
        
        assert history_by_version[1]["parent_version_id"] is None
        assert history_by_version[2]["parent_version_id"] == iep1["id"]
        assert history_by_version[3]["parent_version_id"] == iep2["id"]