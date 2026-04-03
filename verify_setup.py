"""
================================================================================
  LiveMix AI — Component Verification Script
  Run this AFTER installing dependencies to verify all systems are working
================================================================================
"""

import os
import sys
import importlib

def check_module(name, package_name=None):
    """Check if a module is installed."""
    pkg = package_name or name
    try:
        mod = importlib.import_module(name)
        print(f"✅ {pkg} → {getattr(mod, '__version__', 'installed')}")
        return True
    except ImportError as e:
        print(f"❌ {pkg} → NOT FOUND ({e})")
        return False

def check_backend_files():
    """Check if all backend files exist and are importable."""
    files = [
        "instrument_profiles",
        "instrument_node",
        "feedback_detector",
        "quantitative_analyzer",
        "session_manager",
    ]
    
    print("\n" + "="*70)
    print("BACKEND FILE CHECK")
    print("="*70)
    # D:\the_sound_engineer\backend\instrument_node.py
    all_good = True
    for fname in files:
        try:
            __import__(fname)
            os.path.join("D:\the_sound_engineer\backend", f"{fname}.py")
            
            print(f"✅ {fname}.py")
        except ImportError as e:
            print(f"❌ {fname}.py → {e}")
            all_good = False
    
    return all_good

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("\n" + "="*70)
    print("DEPENDENCY CHECK")
    print("="*70)
    
    deps = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("numpy", "NumPy"),
        ("scipy", "SciPy"),
    ]
    
    results = []
    for module, display_name in deps:
        results.append(check_module(module, display_name))
    
    return all(results)

def test_session_creation():
    """Test creating a session and registering members."""
    print("\n" + "="*70)
    print("SESSION CREATION TEST")
    print("="*70)
    
    try:
        from session_manager import SessionManager
        
        sm = SessionManager()
        
        # Create session
        sid, code = sm.create_session("Test Band")
        print(f"✅ Session created: {sid[:8]}... (code: {code})")
        
        # Register member
        node = sm.add_node(sid, "Test Player", "electric_guitar_lead", "test_phone", "center")
        print(f"✅ Member registered: {node.name}")
        
        # Get recommendation
        rec = node.get_recommendation()
        print(f"✅ Recommendation generated: {rec['member_name']}")
        
        # Get all recommendations
        all_recs = sm.get_all_recommendations(sid)
        print(f"✅ All recommendations: {len(all_recs['members'])} member(s)")
        
        # End session
        sm.end_session(sid)
        print(f"✅ Session ended cleanly")
        
        return True
    except Exception as e:
        print(f"❌ Error during session test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fastapi():
    """Test FastAPI imports."""
    print("\n" + "="*70)
    print("FASTAPI TEST")
    print("="*70)
    
    try:
        from fastapi import FastAPI, WebSocket
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI()
        print(f"✅ FastAPI app created successfully")
        print(f"✅ CORS middleware available")
        print(f"✅ WebSocket support available")
        
        return True
    except Exception as e:
        print(f"❌ FastAPI setup failed: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("  🎵 LIVEMIX AI — VERIFICATION SCRIPT")
    print("="*70 + "\n")
    
    # Run all checks
    deps_ok = check_dependencies()
    files_ok = check_backend_files()
    session_ok = test_session_creation()
    fastapi_ok = test_fastapi()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    checks = {
        "Dependencies": deps_ok,
        "Backend Files": files_ok,
        "Session Creation": session_ok,
        "FastAPI Setup": fastapi_ok,
    }
    
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    all_pass = all(checks.values())
    
    print("\n" + "="*70)
    if all_pass:
        print("🎉 ALL CHECKS PASSED! Ready to run:")
        print("   Backend: python main.py")
        print("   Frontend: npm start")
    else:
        print("⚠️  SOME CHECKS FAILED. See errors above.")
        print("   Fix these issues before running the full system.")
    print("="*70 + "\n")
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())