"""Basic test script to verify end-to-end functionality"""
import asyncio
import httpx
from datetime import date, datetime

# Test configuration
BASE_URL = "http://localhost:8006"  # Adjust port as needed
TEST_USER_ID = 1  # Mock auth service user ID

async def test_basic_flow():
    """Test basic IEP creation flow"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🚀 Testing Special Education Service Basic Flow")
        print("=" * 50)
        
        # Wait for service to start and test health endpoint
        print("1. Waiting for service to start...")
        max_retries = 30
        for attempt in range(max_retries):
            try:
                response = await client.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    print("✅ Health check passed")
                    health_data = response.json()
                    print(f"   Database: {health_data.get('database', 'unknown')}")
                    print(f"   Service: {health_data.get('service', 'unknown')}")
                    break
                else:
                    print(f"⏳ Attempt {attempt + 1}: Service not ready (status: {response.status_code})")
            except Exception:
                if attempt == 0:
                    print("⏳ Waiting for service to start...")
                await asyncio.sleep(2)
        else:
            print(f"❌ Service failed to start after {max_retries} attempts")
            print("💡 Make sure to run: python start_test_service.py")
            return
        
        # 2. Test disability types
        print("\n2. Testing disability types...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/templates/disability-types")
            if response.status_code == 200:
                disabilities = response.json()
                print(f"✅ Found {len(disabilities)} disability types")
                if disabilities:
                    print(f"   Example: {disabilities[0]['code']} - {disabilities[0]['name']}")
            else:
                print(f"❌ Disability types failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Disability types error: {e}")
        
        # 3. Create a test student
        print("\n3. Creating test student...")
        student_data = {
            "student_id": f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "2010-05-15",
            "grade_level": "5th",
            "disability_codes": ["SLD"],
            "case_manager_auth_id": TEST_USER_ID,
            "school_district": "Test District",
            "school_name": "Test Elementary"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/students",
                json=student_data,
                params={"current_user_id": TEST_USER_ID}
            )
            if response.status_code == 201:
                student = response.json()
                student_id = student["id"]
                print(f"✅ Created student: {student['full_name']} (ID: {student_id})")
            else:
                print(f"❌ Student creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
        except Exception as e:
            print(f"❌ Student creation error: {e}")
            return
        
        # 4. Create a basic IEP
        print("\n4. Creating test IEP...")
        iep_data = {
            "student_id": student_id,
            "academic_year": "2023-2024",
            "content": {
                "student_info": {
                    "name": f"{student_data['first_name']} {student_data['last_name']}",
                    "grade": student_data["grade_level"],
                    "disability": student_data["disability_codes"]
                },
                "present_levels": "Student demonstrates academic skills below grade level in reading and mathematics.",
                "annual_goals": []
            },
            "meeting_date": date.today().isoformat(),
            "effective_date": date.today().isoformat(),
            "goals": [
                {
                    "domain": "Academic",
                    "goal_text": "Given grade-level reading materials, John will read with 80% accuracy.",
                    "target_criteria": "80% accuracy on grade-level passages",
                    "measurement_method": "Weekly reading assessments",
                    "measurement_frequency": "Weekly"
                }
            ]
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/ieps",
                json=iep_data,
                params={"current_user_id": TEST_USER_ID}
            )
            if response.status_code == 201:
                iep = response.json()
                iep_id = iep["id"]
                print(f"✅ Created IEP: {iep_id}")
                print(f"   Status: {iep['status']}")
                print(f"   Goals: {len(iep.get('goals', []))}")
            else:
                print(f"❌ IEP creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
        except Exception as e:
            print(f"❌ IEP creation error: {e}")
            return
        
        # 5. Test IEP retrieval
        print("\n5. Testing IEP retrieval...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/ieps/{iep_id}", params={"current_user_id": TEST_USER_ID})
            if response.status_code == 200:
                retrieved_iep = response.json()
                print(f"✅ Retrieved IEP: {retrieved_iep['id']}")
                print(f"   Academic Year: {retrieved_iep['academic_year']}")
                print(f"   Goals Count: {len(retrieved_iep.get('goals', []))}")
            else:
                print(f"❌ IEP retrieval failed: {response.status_code}")
        except Exception as e:
            print(f"❌ IEP retrieval error: {e}")
        
        # 6. Test student's IEPs
        print("\n6. Testing student's IEP list...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/ieps/student/{student_id}", params={"current_user_id": TEST_USER_ID})
            if response.status_code == 200:
                student_ieps = response.json()
                print(f"✅ Found {len(student_ieps)} IEPs for student")
            else:
                print(f"❌ Student IEPs retrieval failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Student IEPs error: {e}")
        
        # 7. Test student search
        print("\n7. Testing student search...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/students/search", params={"q": "John", "current_user_id": TEST_USER_ID})
            if response.status_code == 200:
                search_results = response.json()
                print(f"✅ Search found {len(search_results)} students")
            else:
                print(f"❌ Student search failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Student search error: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Basic flow test completed!")
        print("\nAPI Endpoints Available:")
        print("📚 Students: /api/v1/students")
        print("📋 IEPs: /api/v1/ieps")
        print("📝 Templates: /api/v1/templates")
        print("🔬 Advanced IEPs: /api/v1/ieps/advanced")
        print("📊 Health: /health")
        print("📖 Docs: /docs")

if __name__ == "__main__":
    asyncio.run(test_basic_flow())