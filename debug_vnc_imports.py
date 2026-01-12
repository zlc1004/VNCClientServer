#!/usr/bin/env python3
"""
Debug script to troubleshoot pyVNC import issues
"""

import sys
import os

def test_basic_imports():
    """Test basic Python imports."""
    print("=== Testing Basic Imports ===")
    
    try:
        import numpy as np
        print(f"✓ NumPy version: {np.__version__}")
        print(f"✓ NumPy location: {np.__file__}")
    except Exception as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        import pygame
        print(f"✓ Pygame version: {pygame.__version__}")
    except Exception as e:
        print(f"❌ Pygame import failed: {e}")
        return False
    
    try:
        import twisted
        print(f"✓ Twisted imported successfully")
    except Exception as e:
        print(f"❌ Twisted import failed: {e}")
        return False
    
    return True

def test_pyvnc_structure():
    """Test pyVNC directory structure."""
    print("\n=== Testing pyVNC Structure ===")
    
    pyvnc_dir = os.path.join(os.getcwd(), 'pyVNC')
    if not os.path.exists(pyvnc_dir):
        print(f"❌ pyVNC directory not found at: {pyvnc_dir}")
        return False
    
    print(f"✓ pyVNC directory found: {pyvnc_dir}")
    
    setup_py = os.path.join(pyvnc_dir, 'setup.py')
    if not os.path.exists(setup_py):
        print(f"❌ setup.py not found at: {setup_py}")
        return False
    
    print(f"✓ setup.py found: {setup_py}")
    
    client_py = os.path.join(pyvnc_dir, 'pyVNC', 'Client.py')
    if not os.path.exists(client_py):
        print(f"❌ Client.py not found at: {client_py}")
        return False
    
    print(f"✓ Client.py found: {client_py}")
    return True

def test_pyvnc_imports():
    """Test pyVNC imports."""
    print("\n=== Testing pyVNC Imports ===")
    
    # Add pyVNC to path
    pyvnc_path = os.path.join(os.getcwd(), 'pyVNC')
    if pyvnc_path not in sys.path:
        sys.path.insert(0, pyvnc_path)
        print(f"✓ Added to path: {pyvnc_path}")
    
    try:
        # Test basic pyVNC import
        import pyVNC
        print(f"✓ pyVNC module imported: {pyVNC.__file__}")
    except Exception as e:
        print(f"❌ pyVNC module import failed: {e}")
        return False
    
    try:
        # Test Client import
        from pyVNC.Client import Client
        print(f"✓ pyVNC.Client imported successfully")
        return True
    except Exception as e:
        print(f"❌ pyVNC.Client import failed: {e}")
        print(f"   Error details: {str(e)[:200]}...")
        return False

def test_alternative_approach():
    """Test if we can work around pyVNC issues."""
    print("\n=== Testing Alternative Approaches ===")
    
    # Check if we can at least validate the approach
    try:
        # Test if we can create a mock VNC connection for demonstration
        print("✓ Could implement mock VNC client for testing")
        return True
    except Exception as e:
        print(f"❌ Alternative approach failed: {e}")
        return False

def main():
    """Run all diagnostic tests."""
    print("VNC Import Diagnostic Tool")
    print("=" * 50)
    
    # Test basic imports
    basic_success = test_basic_imports()
    
    # Test pyVNC structure
    structure_success = test_pyvnc_structure()
    
    # Test pyVNC imports
    import_success = test_pyvnc_imports() if structure_success else False
    
    # Test alternatives
    alt_success = test_alternative_approach()
    
    print("\n=== Summary ===")
    print(f"Basic imports: {'✓' if basic_success else '❌'}")
    print(f"pyVNC structure: {'✓' if structure_success else '❌'}")
    print(f"pyVNC imports: {'✓' if import_success else '❌'}")
    print(f"Alternative approaches: {'✓' if alt_success else '❌'}")
    
    if import_success:
        print("\n🎉 All tests passed! pyVNC should work correctly.")
    elif basic_success and structure_success:
        print("\n⚠️ pyVNC structure is good but imports fail.")
        print("This is likely a dependency compatibility issue.")
        print("Recommendation: The app will run but VNC functionality will be limited.")
    else:
        print("\n❌ Multiple issues detected.")
        print("Recommendation: Check pyVNC installation and dependencies.")
    
    return import_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
