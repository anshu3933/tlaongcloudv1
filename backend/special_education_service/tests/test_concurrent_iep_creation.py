import asyncio
import pytest
import uuid
from uuid import UUID
from typing import List
import logging

from src.utils.retry import RetryableError


class TestConcurrentIEPCreation:
    """Test concurrent IEP creation to validate version conflict resolution"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_sequential_iep_creation_basic(
        self, 
        student_repository, 
        iep_service, 
        sample_student_data, 
        sample_iep_data
    ):
        """Test basic sequential IEP creation works correctly"""
        # Create a student first
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        
        # Create first IEP
        first_iep = await iep_service.create_iep(
            student_id=student_id,
            academic_year=sample_iep_data["academic_year"],
            initial_data=sample_iep_data,
            user_id=uuid.uuid4()
        )
        
        assert first_iep["version"] == 1
        assert first_iep["student_id"] == student_id
        
        # Create second IEP
        second_iep = await iep_service.create_iep(
            student_id=student_id,
            academic_year=sample_iep_data["academic_year"],
            initial_data=sample_iep_data,
            user_id=uuid.uuid4()
        )
        
        assert second_iep["version"] == 2
        assert second_iep["student_id"] == student_id
        assert second_iep["parent_version_id"] == first_iep["id"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.concurrent
    async def test_concurrent_iep_creation_same_student(
        self, 
        student_repository, 
        iep_service, 
        sample_student_data, 
        sample_iep_data
    ):
        """Test concurrent IEP creation for same student resolves conflicts"""
        # Create a student first
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        
        # Create multiple concurrent IEP creation tasks
        async def create_iep_task(task_id: int):
            try:
                iep = await iep_service.create_iep(
                    student_id=student_id,
                    academic_year=sample_iep_data["academic_year"],
                    initial_data={
                        **sample_iep_data,
                        "content": {**sample_iep_data["content"], "task_id": task_id}
                    },
                    user_id=uuid.uuid4()
                )
                return {"success": True, "iep": iep, "task_id": task_id}
            except Exception as e:
                return {"success": False, "error": str(e), "task_id": task_id}
        
        # Run 5 concurrent IEP creation tasks
        tasks = [create_iep_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All tasks should succeed due to retry mechanism
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        print(f"Successful: {len(successful_results)}, Failed: {len(failed_results)}")
        
        # With retry mechanism, all should succeed
        assert len(successful_results) == 5
        assert len(failed_results) == 0
        
        # Verify version numbers are sequential and unique
        versions = [r["iep"]["version"] for r in successful_results]
        versions.sort()
        assert versions == [1, 2, 3, 4, 5]
        
        # Verify each IEP has correct parent relationship
        ieps_by_version = {r["iep"]["version"]: r["iep"] for r in successful_results}
        
        # Version 1 should have no parent
        assert ieps_by_version[1]["parent_version_id"] is None
        
        # Versions 2-5 should have sequential parent relationships
        for version in range(2, 6):
            current_iep = ieps_by_version[version]
            # Parent should be the IEP with version-1
            expected_parent_id = ieps_by_version[version - 1]["id"]
            assert current_iep["parent_version_id"] == expected_parent_id

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.concurrent
    async def test_concurrent_iep_creation_different_students(
        self, 
        student_repository, 
        iep_service, 
        sample_student_data, 
        sample_iep_data
    ):
        """Test concurrent IEP creation for different students works independently"""
        # Create multiple students
        students = []
        for i in range(3):
            student_data = {
                **sample_student_data,
                "student_id": f"TEST-{i:03d}",
                "first_name": f"Student{i}"
            }
            student = await student_repository.create_student(student_data)
            students.append(student)
        
        # Create concurrent IEP creation tasks for different students
        async def create_iep_for_student(student_id: UUID, task_id: int):
            try:
                iep = await iep_service.create_iep(
                    student_id=student_id,
                    academic_year=sample_iep_data["academic_year"],
                    initial_data={
                        **sample_iep_data,
                        "content": {**sample_iep_data["content"], "student_task": task_id}
                    },
                    user_id=uuid.uuid4()
                )
                return {"success": True, "iep": iep, "student_id": student_id}
            except Exception as e:
                return {"success": False, "error": str(e), "student_id": student_id}
        
        # Create 2 IEPs per student concurrently
        tasks = []
        for i, student in enumerate(students):
            for j in range(2):
                tasks.append(create_iep_for_student(student["id"], i * 2 + j))
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed since they're for different students
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        assert len(successful_results) == 6  # 3 students × 2 IEPs each
        assert len(failed_results) == 0
        
        # Check that each student got versions 1 and 2
        for student in students:
            student_ieps = [r["iep"] for r in successful_results if r["student_id"] == student["id"]]
            assert len(student_ieps) == 2
            
            versions = sorted([iep["version"] for iep in student_ieps])
            assert versions == [1, 2]

    @pytest.mark.asyncio
    async def test_concurrent_iep_creation_different_academic_years(
        self, 
        student_repository, 
        iep_service, 
        sample_student_data, 
        sample_iep_data
    ):
        """Test concurrent IEP creation for same student but different academic years"""
        # Create a student
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        
        academic_years = ["2024-2025", "2025-2026", "2026-2027"]
        
        # Create concurrent IEP creation tasks for different academic years
        async def create_iep_for_year(academic_year: str, task_id: int):
            try:
                iep_data = {
                    **sample_iep_data,
                    "academic_year": academic_year,
                    "content": {**sample_iep_data["content"], "year_task": task_id}
                }
                iep = await iep_service.create_iep(
                    student_id=student_id,
                    academic_year=academic_year,
                    initial_data=iep_data,
                    user_id=uuid.uuid4()
                )
                return {"success": True, "iep": iep, "academic_year": academic_year}
            except Exception as e:
                return {"success": False, "error": str(e), "academic_year": academic_year}
        
        # Create 2 IEPs per academic year concurrently
        tasks = []
        for i, year in enumerate(academic_years):
            for j in range(2):
                tasks.append(create_iep_for_year(year, i * 2 + j))
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed since they're for different academic years
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        assert len(successful_results) == 6  # 3 years × 2 IEPs each
        assert len(failed_results) == 0
        
        # Check that each academic year got versions 1 and 2
        for year in academic_years:
            year_ieps = [r["iep"] for r in successful_results if r["academic_year"] == year]
            assert len(year_ieps) == 2
            
            versions = sorted([iep["version"] for iep in year_ieps])
            assert versions == [1, 2]

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.concurrent
    @pytest.mark.slow
    async def test_high_concurrency_stress_test(
        self, 
        student_repository, 
        iep_service, 
        sample_student_data, 
        sample_iep_data
    ):
        """Stress test with high concurrency to validate retry mechanism robustness"""
        # Create a student
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        
        # Create many concurrent IEP creation tasks
        async def create_iep_task(task_id: int):
            try:
                iep = await iep_service.create_iep(
                    student_id=student_id,
                    academic_year=sample_iep_data["academic_year"],
                    initial_data={
                        **sample_iep_data,
                        "content": {**sample_iep_data["content"], "stress_task": task_id}
                    },
                    user_id=uuid.uuid4()
                )
                return {"success": True, "iep": iep, "task_id": task_id}
            except Exception as e:
                return {"success": False, "error": str(e), "task_id": task_id}
        
        # Run 20 concurrent IEP creation tasks
        num_tasks = 20
        tasks = [create_iep_task(i) for i in range(num_tasks)]
        results = await asyncio.gather(*tasks)
        
        # Analyze results
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        print(f"Stress test results - Successful: {len(successful_results)}, Failed: {len(failed_results)}")
        
        # With proper retry mechanism, we should have high success rate
        success_rate = len(successful_results) / num_tasks
        assert success_rate >= 0.95  # At least 95% success rate
        
        # Verify version numbers are sequential and unique for successful ones
        if successful_results:
            versions = [r["iep"]["version"] for r in successful_results]
            versions.sort()
            expected_versions = list(range(1, len(successful_results) + 1))
            assert versions == expected_versions

    @pytest.mark.asyncio
    async def test_retry_mechanism_behavior(
        self, 
        student_repository, 
        iep_repository, 
        sample_student_data
    ):
        """Test the retry mechanism behavior directly"""
        from src.utils.retry import retry_iep_operation, RetryableError
        
        # Create a student
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        
        # Test successful operation
        call_count = 0
        
        async def successful_operation():
            nonlocal call_count
            call_count += 1
            return {"result": "success", "call_count": call_count}
        
        result = await retry_iep_operation(successful_operation)
        assert result["result"] == "success"
        assert call_count == 1
        
        # Test operation that fails then succeeds
        call_count = 0
        
        async def retry_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("Simulated conflict")
            return {"result": "success_after_retry", "call_count": call_count}
        
        result = await retry_iep_operation(retry_operation)
        assert result["result"] == "success_after_retry"
        assert call_count == 3
        
        # Test operation that always fails
        call_count = 0
        
        async def always_fail_operation():
            nonlocal call_count
            call_count += 1
            raise RetryableError("Always fails")
        
        with pytest.raises(RetryableError):
            await retry_iep_operation(always_fail_operation)
        
        # Should have tried 4 times (1 initial + 3 retries)
        assert call_count == 4

    @pytest.mark.asyncio
    async def test_version_constraint_enforcement(
        self, 
        iep_repository, 
        student_repository,
        sample_student_data
    ):
        """Test that version constraints are properly enforced"""
        # Create a student
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        
        academic_year = "2025-2026"
        
        # Test get_next_version_number behavior
        # First call should return 1
        version1 = await iep_repository.get_next_version_number(student_id, academic_year)
        assert version1 == 1
        
        # Create IEP with version 1
        iep_data = {
            "student_id": student_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": {"test": "content1"},
            "version": version1,
            "created_by": uuid.uuid4()
        }
        iep1 = await iep_repository.create_iep(iep_data)
        
        # Next call should return 2
        version2 = await iep_repository.get_next_version_number(student_id, academic_year)
        assert version2 == 2
        
        # Create IEP with version 2
        iep_data2 = {
            "student_id": student_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": {"test": "content2"},
            "version": version2,
            "parent_version_id": iep1["id"],
            "created_by": uuid.uuid4()
        }
        iep2 = await iep_repository.create_iep(iep_data2)
        
        # Next call should return 3
        version3 = await iep_repository.get_next_version_number(student_id, academic_year)
        assert version3 == 3
        
        # Verify the parent-child relationship
        assert iep2["parent_version_id"] == iep1["id"]