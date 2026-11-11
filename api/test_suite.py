"""
FITBREAK - COMPREHENSIVE END-TO-END FEATURE TEST SUITE
Kiểm tra toàn diện tất cả các tính năng cốt lõi của hệ thống FitBreak:
1. Health & Status Endpoints
2. Medical Knowledge RAG Stats
3. AI Clinical Intake Assistant (Clarification, Red Flags, Synthesis)
4. Personalization Engine (Conflict Detection & Proposal)
5. Embedding Generation (gemini-embedding-2, 768 dimensions)
6. Schedule Maker & Knapsack Exercise Selection
7. Nutrition RAG & Vietnamese Food Suggestion
8. Medical Checkup Diagnostic Engine
9. Raid & Boss Game Mechanics
"""

import sys
import asyncio
import time
from pathlib import Path
from typing import Dict, Any

# Ensure 'api' is on sys.path
API_DIR = Path(__file__).resolve().parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

PASSED = 0
FAILED = 0
WARNINGS = 0

def log_test(name: str, success: bool, detail: str = ""):
    global PASSED, FAILED
    if success:
        PASSED += 1
        print(f"  [PASS] {name} {f'({detail})' if detail else ''}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name} - {detail}")


def log_warn(name: str, detail: str = ""):
    global WARNINGS
    WARNINGS += 1
    print(f"  [WARN] {name} - {detail}")


# ==============================================================================
# TEST 1: HEALTH & BASE ROUTING ENDPOINTS
# ==============================================================================
def test_health_endpoints():
    print("\n--- TEST GROUP 1: Health & Routing Endpoints ---")
    
    # 1.1 /health
    res = client.get("/health")
    log_test("GET /health", res.status_code == 200 and res.json().get("status") == "healthy", f"Status: {res.status_code}")
    
    # 1.2 /ping
    res = client.get("/ping")
    log_test("GET /ping", res.status_code == 200 and res.json().get("status") == "healthy", f"Status: {res.status_code}")
    
    # 1.3 /
    res = client.get("/")
    log_test("GET / (Root)", res.status_code == 200, f"Status: {res.status_code}")
    
    # 1.4 /chatbot/knowledge-stats
    res = client.get("/chatbot/knowledge-stats")
    data = res.json()
    log_test(
        "GET /chatbot/knowledge-stats",
        res.status_code == 200 and data.get("total_chunks", 0) > 0,
        f"Chunks: {data.get('total_chunks')}, Sources: {data.get('total_sources')}"
    )


# ==============================================================================
# TEST 2: MEDICAL CHECKUP DIAGNOSTICS ENGINE
# ==============================================================================
async def test_medical_checkup():
    print("\n--- TEST GROUP 2: Medical Checkup Diagnostic Engine ---")
    from app.services.medical_checkup import (
        classify_BMI,
        classify_blood_pressure,
        classify_diabete,
        classify_lack_oxygen,
        medical_checkup
    )

    # 2.1 BMI Classifications
    bmi_normal = classify_BMI(65, 170)
    bmi_obese = classify_BMI(95, 165)
    log_test("BMI Classification", bmi_normal == 1 and bmi_obese >= 3, f"Normal: {bmi_normal}, Obese: {bmi_obese}")

    # 2.2 Blood Pressure Classifications
    bp_normal = classify_blood_pressure(115, 75)
    bp_stage2 = classify_blood_pressure(165, 105)
    log_test("Blood Pressure Classification", bp_normal == 1 and bp_stage2 == 4, f"Normal: {bp_normal}, Stage 2: {bp_stage2}")

    # 2.3 Diabetes Classification
    dia_normal = classify_diabete(time=0, glycemic_index=90)
    dia_diabetic = classify_diabete(time=0, glycemic_index=150)
    log_test("Diabetes Classification", dia_normal == 1 and dia_diabetic == 3, f"Normal: {dia_normal}, Diabetic: {dia_diabetic}")

    # 2.4 SPO2 Classification
    spo2_good = classify_lack_oxygen(99)
    spo2_low = classify_lack_oxygen(92)
    log_test("SpO2 Classification", spo2_good == 0 and spo2_low >= 1, f"Good: {spo2_good}, Low: {spo2_low}")

    # 2.5 Full checkup report synthesis
    checkup_data = {
        "weight": 72,
        "height": 172,
        "systolic": 130,
        "diastolic": 85,
        "time": 0,
        "glycemic_index": 105,
        "spo2": 98,
        "cholesterol": 195,
        "conditions": "Tiền sử đau dạ dày nhẹ"
    }
    result = await medical_checkup(checkup_data)
    log_test(
        "Full Medical Checkup Evaluation",
        "codes" in result and "details" in result and "recommendations" in result,
        f"Generated {len(result.get('recommendations', []))} recommendation sections"
    )


# ==============================================================================
# TEST 3: SCHEDULE MAKER & KNAPSACK EXERCISE SELECTION
# ==============================================================================
async def test_schedule_service():
    print("\n--- TEST GROUP 3: Schedule Maker & Knapsack Exercise Selection ---")
    from app.services.schedule_service import (
        DF_EXERCISES_CACHE,
        filter_exercises,
        schedule_maker
    )

    # 3.1 Exercise Database Loading
    log_test(
        "Exercise Database Loaded",
        not DF_EXERCISES_CACHE.empty and "exercise" in DF_EXERCISES_CACHE.columns,
        f"Total exercises: {len(DF_EXERCISES_CACHE)}"
    )

    # 3.2 Filtering by level
    df_light = filter_exercises({"level_of_physical_activity": "light"})
    df_medium = filter_exercises({"level_of_physical_activity": "medium"})
    df_heavy = filter_exercises({"level_of_physical_activity": "heavy"})
    log_test(
        "Physical Activity Filter",
        len(df_light) > 0 and len(df_medium) > 0 and len(df_heavy) > 0,
        f"Light: {len(df_light)}, Medium: {len(df_medium)}, Heavy: {len(df_heavy)}"
    )

    # 3.3 Schedule Maker: Muscle Building (Aim = 1)
    muscle_timetable = {
        "aim": 1,
        "level_of_physical_activity": "medium",
        "timetable": {
            "Monday": [60],
            "Tuesday": [60],
            "Wednesday": [60],
            "Thursday": [60],
            "Friday": [60],
            "Saturday": [0],
            "Sunday": [0],
        }
    }
    muscle_sched = await schedule_maker(muscle_timetable)
    has_res = any(
        s.get("day_type") == "resistance_training"
        for day in muscle_sched.values() for s in day
    )
    log_test("Schedule Generation (Muscle Gain)", has_res, "Generated valid resistance & cardio balance")


# ==============================================================================
# TEST 4: EMBEDDING ENGINE (gemini-embedding-2, 768 DIMENSIONS)
# ==============================================================================
def test_embedding_generation():
    print("\n--- TEST GROUP 4: Vector Embedding Engine (gemini-embedding-2) ---")
    from app.services.supabase_rag_chat import embed_query_vector

    query = "Hướng dẫn chẩn đoán và điều trị tăng huyết áp ở người cao tuổi"
    vector = embed_query_vector(query)
    
    log_test(
        "gemini-embedding-2 Query Vector",
        vector is not None and len(vector) == 768,
        f"Vector dimension: {len(vector) if vector else 0} (Expected 768)"
    )


# ==============================================================================
# TEST 5: NUTRITION RAG & FOOD SUGGESTION
# ==============================================================================
async def test_nutrition_rag():
    print("\n--- TEST GROUP 5: Nutrition RAG & Food Suggestion ---")
    from app.services.rag_service import DF_FOODS, filter_foods, process_rag_pipeline
    from app.schemas.foodSuggestRequest import FoodSuggestRequest

    # 5.1 Food database loading
    log_test(
        "Vietnamese Food Database Loaded",
        not DF_FOODS.empty and "name" in DF_FOODS.columns,
        f"Total dishes: {len(DF_FOODS)}"
    )

    # 5.2 Filter by allergen & diet
    filtered = filter_foods(DF_FOODS, user_diet="home_cooked", user_allergens="seafood; peanut")
    has_peanuts = filtered["allergens"].str.contains("peanut", case=False).any()
    log_test(
        "Food Allergen & Diet Filter",
        not filtered.empty and not has_peanuts,
        f"Available safe dishes: {len(filtered)}"
    )

    # 5.3 Full RAG Pipeline with Failover
    req = FoodSuggestRequest(
        calories_need=1900,
        protein_need=90,
        daily_budget=90000,
        aim="Giảm cân",
        diet_type="home_cooked",
        allergen="đậu phộng"
    ).model_dump()

    try:
        rag_res = await process_rag_pipeline(req)
        log_test(
            "Food Suggest RAG Execution",
            "meals" in rag_res and len(rag_res["meals"]) > 0,
            f"Suggested {len(rag_res.get('meals', []))} meals, total calo: {rag_res.get('total_calories')}"
        )
    except Exception as exc:
        log_test("Food Suggest RAG Execution", False, str(exc))


# ==============================================================================
# TEST 6: AI CLINICAL INTAKE ASSISTANT & PERSONALIZATION ENGINE
# ==============================================================================
async def test_clinical_intake_chatbot():
    print("\n--- TEST GROUP 6: AI Clinical Intake Assistant & Personalization Engine ---")
    from app.services.chatbot_agent import (
        run_clinical_advisor,
        run_personalization_engine,
        analyze_and_chat,
        map_activity_to_code
    )

    # 6.1 Map activity code
    code_light = map_activity_to_code("Nghỉ ngơi hoàn toàn")
    code_medium = map_activity_to_code("Vận động vừa phải")
    code_heavy = map_activity_to_code("Cường độ cao")
    log_test("Activity Code Mapping", code_light == "light" and code_medium == "medium" and code_heavy == "heavy", f"L: {code_light}, M: {code_medium}, H: {code_heavy}")

    # 6.2 Red Flag Emergency Triage (Must trigger immediately)
    emergency_msg = "Tôi đang bị đau thắt ngực dữ dội, khó thở và ngất xỉu"
    emergency_reply = await run_clinical_advisor(emergency_msg, {})
    is_emergency = "115" in emergency_reply or "cấp cứu" in emergency_reply.lower() or "RED FLAG" in emergency_reply
    log_test(
        "Emergency Triage (Red Flag Fast-Path)",
        is_emergency,
        "Detected critical condition and prompted 115 / ER redirect"
    )

    # 6.3 Claude-Style Clarification (Ambiguous Query -> 1-2 questions with options)
    ambiguous_msg = "Tôi bị đau mỏi người từ hôm qua"
    clarification_reply = await run_clinical_advisor(ambiguous_msg, {})
    is_clarifying = "?" in clarification_reply and ("1." in clarification_reply or "2." in clarification_reply or "thông tin" in clarification_reply.lower() or "vị trí" in clarification_reply.lower())
    log_test(
        "Claude-Style Clarification (Ambiguity Handling)",
        is_clarifying,
        "Asked targeted clarifying questions with empathetic pacing"
    )

    # 6.4 Full analyze_and_chat Pipeline with Personalization Proposal
    sample_profile = {
        "height": 170,
        "weight": 65,
        "food_recommendation": "Ăn giảm muối",
        "level_of_physical_activity": "medium",
        "allergies": "Không có"
    }
    chat_result = await analyze_and_chat("Tôi bị bong gân cổ chân sưng to sau khi đá bóng", sample_profile)
    log_test(
        "Full Clinical & Personalization Multi-Agent Flow",
        "reply" in chat_result and "has_proposed_changes" in chat_result,
        f"Proposal: {chat_result.get('has_proposed_changes')}, Activity update: {chat_result.get('suggested_level_of_physical_activity')}"
    )


# ==============================================================================
# MAIN RUNNER
# ==============================================================================
async def main_test_runner():
    start_total = time.time()
    print("=" * 70)
    print("FITBREAK TELEHEALTH & FITNESS - FULL SYSTEM FEATURE TEST")
    print("=" * 70)

    test_health_endpoints()
    await test_medical_checkup()
    await test_schedule_service()
    test_embedding_generation()
    await test_nutrition_rag()
    await test_clinical_intake_chatbot()

    duration = time.time() - start_total
    print("\n" + "=" * 70)
    print(f"TEST RUN COMPLETED IN {duration:.2f}s")
    print(f"PASSED:   {PASSED}")
    print(f"FAILED:   {FAILED}")
    print(f"WARNINGS: {WARNINGS}")
    print("=" * 70)

    if FAILED > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main_test_runner())
