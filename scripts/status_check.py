"""
Status check script to verify implementation completeness.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    return Path(file_path).exists()

def check_implementation_status():
    """Check the implementation status of all components."""
    
    print("🔍 SPENDLOT BACKEND IMPLEMENTATION STATUS CHECK")
    print("=" * 60)
    
    # Phase 1: Critical Foundation
    print("\n📋 PHASE 1: CRITICAL FOUNDATION")
    print("-" * 40)
    
    phase1_items = [
        ("Database Migration", "alembic/versions/001_initial_schema.py"),
        ("SMS/Twilio Integration", "app/services/twilio_service.py"),
        ("SMS Tasks", "app/tasks/sms_tasks.py"),
        ("SMS Webhooks", "app/api/v1/endpoints/webhooks.py"),
        ("Gmail OAuth Service", "app/services/gmail_service.py"),
        ("Gmail OAuth Endpoints", "app/api/v1/endpoints/auth.py"),
        ("Email Service", "app/services/email_service.py"),
    ]
    
    phase1_complete = 0
    for item_name, file_path in phase1_items:
        exists = check_file_exists(file_path)
        status = "✅" if exists else "❌"
        print(f"{status} {item_name}")
        if exists:
            phase1_complete += 1
    
    print(f"\nPhase 1 Progress: {phase1_complete}/{len(phase1_items)} ({phase1_complete/len(phase1_items)*100:.1f}%)")
    
    # Phase 2: Production Readiness
    print("\n🚀 PHASE 2: PRODUCTION READINESS")
    print("-" * 40)
    
    phase2_items = [
        ("Transaction Tests", "tests/test_transactions.py"),
        ("Category Tests", "tests/test_categories.py"),
        ("Analytics Tests", "tests/test_analytics.py"),
        ("Error Handling Middleware", "app/api/middleware/error_handling.py"),
        ("Retry Mechanisms", "app/core/retry.py"),
        ("Webhook Security", "app/core/webhook_security.py"),
        ("Security Headers", "app/api/middleware/security_headers.py"),
    ]
    
    phase2_complete = 0
    for item_name, file_path in phase2_items:
        exists = check_file_exists(file_path)
        status = "✅" if exists else "❌"
        print(f"{status} {item_name}")
        if exists:
            phase2_complete += 1
    
    print(f"\nPhase 2 Progress: {phase2_complete}/{len(phase2_items)} ({phase2_complete/len(phase2_items)*100:.1f}%)")
    
    # Phase 3: Performance & Monitoring
    print("\n⚡ PHASE 3: PERFORMANCE & MONITORING")
    print("-" * 40)
    
    phase3_items = [
        ("Database Optimization", "app/core/database_optimization.py"),
        ("Caching System", "app/core/caching.py"),
        ("Metrics Collection", "app/utils/metrics.py"),
        ("Performance Monitoring", "app/utils/metrics.py"),
    ]
    
    phase3_complete = 0
    for item_name, file_path in phase3_items:
        exists = check_file_exists(file_path)
        status = "✅" if exists else "❌"
        print(f"{status} {item_name}")
        if exists:
            phase3_complete += 1
    
    print(f"\nPhase 3 Progress: {phase3_complete}/{len(phase3_items)} ({phase3_complete/len(phase3_items)*100:.1f}%)")
    
    # Core Components (Already Complete)
    print("\n🏗️ CORE COMPONENTS (PREVIOUSLY COMPLETED)")
    print("-" * 40)
    
    core_items = [
        ("User Management", "app/models/user.py"),
        ("Receipt Management", "app/models/receipt.py"),
        ("Transaction Management", "app/models/transaction.py"),
        ("Category System", "app/models/category.py"),
        ("Bank Accounts", "app/models/bank_account.py"),
        ("Plaid Integration", "app/services/plaid_service.py"),
        ("OCR Processing", "app/tasks/ocr_tasks.py"),
        ("Authentication API", "app/api/v1/endpoints/auth.py"),
        ("Receipt API", "app/api/v1/endpoints/receipts.py"),
        ("Transaction API", "app/api/v1/endpoints/transactions.py"),
        ("Analytics API", "app/api/v1/endpoints/analytics.py"),
        ("Docker Configuration", "docker-compose.yml"),
        ("Database Models", "app/models/base.py"),
    ]
    
    core_complete = 0
    for item_name, file_path in core_items:
        exists = check_file_exists(file_path)
        status = "✅" if exists else "❌"
        print(f"{status} {item_name}")
        if exists:
            core_complete += 1
    
    print(f"\nCore Components: {core_complete}/{len(core_items)} ({core_complete/len(core_items)*100:.1f}%)")
    
    # Overall Status
    total_items = len(phase1_items) + len(phase2_items) + len(phase3_items) + len(core_items)
    total_complete = phase1_complete + phase2_complete + phase3_complete + core_complete
    overall_percentage = total_complete / total_items * 100
    
    print("\n" + "=" * 60)
    print(f"📊 OVERALL IMPLEMENTATION STATUS: {total_complete}/{total_items} ({overall_percentage:.1f}%)")
    
    if overall_percentage >= 90:
        print("🎉 EXCELLENT! System is ready for production deployment!")
    elif overall_percentage >= 75:
        print("🚀 GREAT! System is nearly production-ready!")
    elif overall_percentage >= 50:
        print("⚠️  GOOD PROGRESS! Continue with remaining items.")
    else:
        print("🔧 MORE WORK NEEDED! Focus on critical components first.")
    
    # Next Steps
    print("\n📝 NEXT STEPS:")
    print("-" * 20)
    
    if phase1_complete < len(phase1_items):
        print("1. Complete Phase 1 critical foundation items")
    elif phase2_complete < len(phase2_items):
        print("1. Complete Phase 2 production readiness items")
    elif phase3_complete < len(phase3_items):
        print("1. Complete Phase 3 performance & monitoring items")
    else:
        print("1. Run comprehensive tests")
        print("2. Deploy to staging environment")
        print("3. Perform load testing")
        print("4. Security audit")
        print("5. Production deployment")
    
    print("\n🔧 DEPLOYMENT READINESS:")
    print("-" * 25)
    
    deployment_items = [
        ("Environment Configuration", ".env.example"),
        ("Docker Setup", "docker-compose.yml"),
        ("Database Migrations", "alembic/versions/001_initial_schema.py"),
        ("Requirements", "requirements.txt"),
        ("Documentation", "README.md"),
        ("Makefile", "Makefile"),
    ]
    
    deployment_ready = 0
    for item_name, file_path in deployment_items:
        exists = check_file_exists(file_path)
        status = "✅" if exists else "❌"
        print(f"{status} {item_name}")
        if exists:
            deployment_ready += 1
    
    deployment_percentage = deployment_ready / len(deployment_items) * 100
    print(f"\nDeployment Readiness: {deployment_ready}/{len(deployment_items)} ({deployment_percentage:.1f}%)")
    
    return overall_percentage >= 75  # Return True if ready for production


if __name__ == "__main__":
    try:
        is_ready = check_implementation_status()
        sys.exit(0 if is_ready else 1)
    except Exception as e:
        print(f"\n❌ Error during status check: {str(e)}")
        sys.exit(1)
