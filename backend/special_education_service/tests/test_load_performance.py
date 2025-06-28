import asyncio
import pytest
import uuid
import time
from typing import List, Dict, Any
import statistics

from src.utils.retry import RetryableError


class TestLoadPerformance:
    """Test load performance and system behavior under stress"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_students_creation_performance(
        self, 
        student_repository,
        sample_student_data
    ):
        """Test performance of concurrent student creation"""
        num_students = 50
        
        async def create_student_task(student_id: int):
            start_time = time.time()
            try:
                student_data = {
                    **sample_student_data,
                    "student_id": f"PERF-{student_id:03d}",
                    "first_name": f"Student{student_id}",
                    "last_name": f"Test{student_id}"
                }
                student = await student_repository.create_student(student_data)
                end_time = time.time()
                return {
                    "success": True,
                    "student": student,
                    "duration": end_time - start_time,
                    "student_id": student_id
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "success": False,
                    "error": str(e),
                    "duration": end_time - start_time,
                    "student_id": student_id
                }
        
        # Measure total time
        total_start = time.time()
        tasks = [create_student_task(i) for i in range(num_students)]
        results = await asyncio.gather(*tasks)
        total_end = time.time()
        
        # Analyze results
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        success_rate = len(successful_results) / num_students
        total_duration = total_end - total_start
        
        durations = [r["duration"] for r in successful_results]
        avg_duration = statistics.mean(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        
        print(f"Student Creation Performance:")
        print(f"  Total students: {num_students}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Total time: {total_duration:.2f}s")
        print(f"  Average time per student: {avg_duration:.3f}s")
        print(f"  Min time: {min_duration:.3f}s")
        print(f"  Max time: {max_duration:.3f}s")
        print(f"  Throughput: {len(successful_results)/total_duration:.1f} students/sec")
        
        # Assertions for performance expectations
        assert success_rate >= 0.95  # At least 95% success rate
        assert avg_duration < 0.5  # Average should be under 500ms
        assert total_duration < 30  # Should complete in under 30 seconds

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_mixed_workload_performance(
        self, 
        student_repository, 
        iep_service, 
        sample_student_data, 
        sample_iep_data
    ):
        """Test performance with mixed workload: students + IEPs + queries"""
        
        # Create some students first
        students = []
        for i in range(5):
            student_data = {
                **sample_student_data,
                "student_id": f"MIX-{i:03d}",
                "first_name": f"MixStudent{i}"
            }
            student = await student_repository.create_student(student_data)
            students.append(student)
        
        # Define different types of tasks
        async def create_student_task(task_id: int):
            start_time = time.time()
            try:
                student_data = {
                    **sample_student_data,
                    "student_id": f"NEW-{task_id:03d}",
                    "first_name": f"NewStudent{task_id}"
                }
                student = await student_repository.create_student(student_data)
                duration = time.time() - start_time
                return {"task_type": "create_student", "success": True, "duration": duration}
            except Exception as e:
                duration = time.time() - start_time
                return {"task_type": "create_student", "success": False, "duration": duration, "error": str(e)}
        
        async def create_iep_task(student_id: uuid.UUID, task_id: int):
            start_time = time.time()
            try:
                iep = await iep_service.create_iep(
                    student_id=student_id,
                    academic_year=sample_iep_data["academic_year"],
                    initial_data={
                        **sample_iep_data,
                        "content": {**sample_iep_data["content"], "mix_task": task_id}
                    },
                    user_id=uuid.uuid4()
                )
                duration = time.time() - start_time
                return {"task_type": "create_iep", "success": True, "duration": duration}
            except Exception as e:
                duration = time.time() - start_time
                return {"task_type": "create_iep", "success": False, "duration": duration, "error": str(e)}
        
        async def query_student_task(student_id: uuid.UUID):
            start_time = time.time()
            try:
                student = await student_repository.get_student(student_id)
                duration = time.time() - start_time
                return {"task_type": "query_student", "success": True, "duration": duration}
            except Exception as e:
                duration = time.time() - start_time
                return {"task_type": "query_student", "success": False, "duration": duration, "error": str(e)}
        
        # Create mixed workload
        tasks = []
        task_id = 0
        
        # Add student creation tasks
        for i in range(10):
            tasks.append(create_student_task(task_id))
            task_id += 1
        
        # Add IEP creation tasks
        for i in range(20):
            student = students[i % len(students)]
            tasks.append(create_iep_task(student["id"], task_id))
            task_id += 1
        
        # Add query tasks
        for i in range(15):
            student = students[i % len(students)]
            tasks.append(query_student_task(student["id"]))
        
        # Execute all tasks concurrently
        total_start = time.time()
        results = await asyncio.gather(*tasks)
        total_end = time.time()
        
        # Analyze results by task type
        by_task_type = {}
        for result in results:
            task_type = result["task_type"]
            if task_type not in by_task_type:
                by_task_type[task_type] = {"success": [], "failed": []}
            
            if result["success"]:
                by_task_type[task_type]["success"].append(result)
            else:
                by_task_type[task_type]["failed"].append(result)
        
        total_duration = total_end - total_start
        total_tasks = len(results)
        
        print(f"\nMixed Workload Performance:")
        print(f"  Total tasks: {total_tasks}")
        print(f"  Total time: {total_duration:.2f}s")
        print(f"  Throughput: {total_tasks/total_duration:.1f} tasks/sec")
        
        for task_type, data in by_task_type.items():
            success_count = len(data["success"])
            failed_count = len(data["failed"])
            total_count = success_count + failed_count
            success_rate = success_count / total_count if total_count > 0 else 0
            
            if success_count > 0:
                durations = [r["duration"] for r in data["success"]]
                avg_duration = statistics.mean(durations)
                max_duration = max(durations)
            else:
                avg_duration = max_duration = 0
            
            print(f"  {task_type}:")
            print(f"    Total: {total_count}, Success: {success_count}, Failed: {failed_count}")
            print(f"    Success rate: {success_rate:.2%}")
            print(f"    Avg duration: {avg_duration:.3f}s, Max duration: {max_duration:.3f}s")
        
        # Performance assertions
        overall_success_rate = sum(len(data["success"]) for data in by_task_type.values()) / total_tasks
        assert overall_success_rate >= 0.90  # At least 90% overall success rate
        assert total_duration < 60  # Should complete in under 60 seconds

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_retry_mechanism_performance(
        self, 
        student_repository, 
        iep_service, 
        sample_student_data, 
        sample_iep_data
    ):
        """Test performance impact of retry mechanism under contention"""
        # Create a student
        student = await student_repository.create_student(sample_student_data)
        student_id = student["id"]
        
        # Create high contention scenario - many tasks for same student/year
        num_concurrent_tasks = 30
        
        async def create_iep_with_timing(task_id: int):
            start_time = time.time()
            retry_count = 0
            
            # Custom operation that tracks retries
            async def tracked_operation():
                nonlocal retry_count
                retry_count += 1
                # Call the actual IEP creation
                return await iep_service.create_iep(
                    student_id=student_id,
                    academic_year=sample_iep_data["academic_year"],
                    initial_data={
                        **sample_iep_data,
                        "content": {**sample_iep_data["content"], "retry_task": task_id}
                    },
                    user_id=uuid.uuid4()
                )
            
            try:
                iep = await tracked_operation()
                end_time = time.time()
                return {
                    "success": True,
                    "duration": end_time - start_time,
                    "retry_count": retry_count,
                    "version": iep["version"],
                    "task_id": task_id
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "success": False,
                    "duration": end_time - start_time,
                    "retry_count": retry_count,
                    "error": str(e),
                    "task_id": task_id
                }
        
        # Execute concurrent tasks
        total_start = time.time()
        tasks = [create_iep_with_timing(i) for i in range(num_concurrent_tasks)]
        results = await asyncio.gather(*tasks)
        total_end = time.time()
        
        # Analyze retry behavior
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        success_rate = len(successful_results) / num_concurrent_tasks
        total_duration = total_end - total_start
        
        if successful_results:
            durations = [r["duration"] for r in successful_results]
            retry_counts = [r["retry_count"] for r in successful_results]
            versions = [r["version"] for r in successful_results]
            
            avg_duration = statistics.mean(durations)
            max_duration = max(durations)
            avg_retries = statistics.mean(retry_counts)
            max_retries = max(retry_counts)
            
            # Check version uniqueness
            unique_versions = set(versions)
            
            print(f"\nRetry Mechanism Performance:")
            print(f"  Concurrent tasks: {num_concurrent_tasks}")
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Total time: {total_duration:.2f}s")
            print(f"  Average duration: {avg_duration:.3f}s")
            print(f"  Max duration: {max_duration:.3f}s")
            print(f"  Average retries: {avg_retries:.1f}")
            print(f"  Max retries: {max_retries}")
            print(f"  Unique versions created: {len(unique_versions)}")
            print(f"  Version range: {min(versions) if versions else 'N/A'} - {max(versions) if versions else 'N/A'}")
            
            # Performance and correctness assertions
            assert success_rate >= 0.85  # At least 85% success rate under high contention
            assert len(unique_versions) == len(successful_results)  # All versions should be unique
            assert max_retries <= 5  # Retry mechanism should not go crazy
            assert avg_duration < 2.0  # Average should be reasonable even with retries
        
        if failed_results:
            print(f"  Failed tasks: {len(failed_results)}")
            for failed in failed_results[:3]:  # Show first 3 failures
                print(f"    Error: {failed.get('error', 'Unknown')}")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_database_connection_pool_behavior(
        self, 
        student_repository, 
        sample_student_data
    ):
        """Test behavior under database connection pressure"""
        
        async def database_intensive_task(task_id: int):
            start_time = time.time()
            try:
                # Perform multiple database operations
                operations = []
                
                # Create student
                student_data = {
                    **sample_student_data,
                    "student_id": f"DB-{task_id:03d}",
                    "first_name": f"DbStudent{task_id}"
                }
                student = await student_repository.create_student(student_data)
                operations.append("create")
                
                # Read student back
                retrieved = await student_repository.get_student(student["id"])
                operations.append("read")
                
                # Update student
                updates = {"last_name": f"Updated{task_id}"}
                updated = await student_repository.update_student(student["id"], updates)
                operations.append("update")
                
                end_time = time.time()
                return {
                    "success": True,
                    "duration": end_time - start_time,
                    "operations": operations,
                    "task_id": task_id
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "success": False,
                    "duration": end_time - start_time,
                    "error": str(e),
                    "task_id": task_id
                }
        
        # Run many database-intensive tasks concurrently
        num_tasks = 40
        total_start = time.time()
        tasks = [database_intensive_task(i) for i in range(num_tasks)]
        results = await asyncio.gather(*tasks)
        total_end = time.time()
        
        # Analyze results
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        success_rate = len(successful_results) / num_tasks
        total_duration = total_end - total_start
        
        if successful_results:
            durations = [r["duration"] for r in successful_results]
            avg_duration = statistics.mean(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            print(f"\nDatabase Connection Pool Performance:")
            print(f"  Total tasks: {num_tasks}")
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Total time: {total_duration:.2f}s")
            print(f"  Average duration: {avg_duration:.3f}s")
            print(f"  Min duration: {min_duration:.3f}s")
            print(f"  Max duration: {max_duration:.3f}s")
            print(f"  Operations/sec: {len(successful_results) * 3 / total_duration:.1f}")
        
        if failed_results:
            print(f"  Failed tasks: {len(failed_results)}")
            error_types = {}
            for failed in failed_results:
                error = failed.get('error', 'Unknown')
                error_type = error.split(':')[0] if ':' in error else error
                error_types[error_type] = error_types.get(error_type, 0) + 1
            print(f"  Error breakdown: {dict(error_types)}")
        
        # Assertions
        assert success_rate >= 0.90  # At least 90% success rate
        assert total_duration < 45  # Should complete in reasonable time