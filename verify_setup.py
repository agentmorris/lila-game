#!/usr/bin/env python3
"""
Wildlife Camera Trap Game - Setup Verification Script
Verifies that all required files are in their correct locations.
"""

import os
import sys

def check_file_structure():
    """Check that all required files and directories exist."""
    
    print("Wildlife Camera Trap Game - Setup Verification")
    print("=" * 50)
    
    # Define required files and directories
    required_structure = {
        'files': [
            'README.md',
            'design.md', 
            'requirements.txt',
            'db_setup.py',
            'data_processor.py',
            'models.py',
            'game_logic.py',
            'app.py',
            'templates/base.html',
            'templates/index.html',
            'templates/question.html',
            'templates/game_complete.html',
            'templates/high_scores.html',
            'static/style.css',
            'static/game.js'
        ],
        'directories': [
            'templates',
            'static'
        ]
    }
    
    missing_files = []
    missing_dirs = []
    empty_files = []
    found_files = []
    
    # Check directories
    print("\nChecking directories...")
    for directory in required_structure['directories']:
        if os.path.isdir(directory):
            print(f"  ✅ {directory}/")
        else:
            print(f"  ❌ {directory}/ (MISSING)")
            missing_dirs.append(directory)
    
    # Check files
    print("\nChecking files...")
    for file_path in required_structure['files']:
        if os.path.isfile(file_path):
            # Check if file is empty
            try:
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    print(f"  ⚠️  {file_path} (EMPTY)")
                    empty_files.append(file_path)
                else:
                    print(f"  ✅ {file_path} ({file_size:,} bytes)")
                    found_files.append(file_path)
            except OSError:
                print(f"  ❌ {file_path} (ERROR READING)")
                missing_files.append(file_path)
        else:
            print(f"  ❌ {file_path} (MISSING)")
            missing_files.append(file_path)
    
    # Check for database (should not exist initially)
    print("\nChecking database...")
    if os.path.isfile('camera_trap_data.db'):
        db_size = os.path.getsize('camera_trap_data.db')
        print(f"  ℹ️  camera_trap_data.db exists ({db_size:,} bytes)")
        print("     This is normal if you've already run setup")
    else:
        print("  ℹ️  camera_trap_data.db not found (will be created during setup)")
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    total_files = len(required_structure['files'])
    total_dirs = len(required_structure['directories'])
    
    print(f"Files found: {len(found_files)}/{total_files}")
    print(f"Directories found: {len(required_structure['directories']) - len(missing_dirs)}/{total_dirs}")
    
    if missing_dirs:
        print(f"\n❌ Missing directories ({len(missing_dirs)}):")
        for directory in missing_dirs:
            print(f"   - {directory}/")
        print("\n   Create with: mkdir " + " ".join(missing_dirs))
    
    if missing_files:
        print(f"\n❌ Missing files ({len(missing_files)}):")
        for file_path in missing_files:
            print(f"   - {file_path}")
    
    if empty_files:
        print(f"\n⚠️  Empty files ({len(empty_files)}):")
        for file_path in empty_files:
            print(f"   - {file_path}")
        print("   These files exist but are empty - make sure content was copied correctly")
    
    # Overall status
    if not missing_files and not missing_dirs and not empty_files:
        print("\n🎉 SUCCESS: All files are in the correct locations!")
        print("\nNext steps:")
        print("1. pip install -r requirements.txt")
        print("2. python db_setup.py") 
        print("3. python data_processor.py --csv-path /path/to/your/data.csv")
        print("4. python app.py")
        return True
    else:
        print(f"\n❌ SETUP INCOMPLETE: Please fix the issues above")
        if missing_dirs:
            print(f"   - Create {len(missing_dirs)} missing directories")
        if missing_files:
            print(f"   - Copy {len(missing_files)} missing files")
        if empty_files:
            print(f"   - Add content to {len(empty_files)} empty files")
        return False

def check_python_version():
    """Check Python version compatibility."""
    print("\nChecking Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 7:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro} (compatible)")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (requires Python 3.7+)")
        return False

def check_dependencies():
    """Check if required Python packages can be imported."""
    print("\nChecking Python dependencies...")
    
    required_packages = {
        'flask': 'Flask',
        'pandas': 'pandas', 
        'sqlite3': 'sqlite3 (built-in)',
        'requests': 'requests'
    }
    
    missing_packages = []
    
    for package, display_name in required_packages.items():
        try:
            if package == 'sqlite3':
                import sqlite3
            elif package == 'flask':
                import flask
            elif package == 'pandas':
                import pandas
            elif package == 'requests':
                import requests
            
            print(f"  ✅ {display_name}")
            
        except ImportError:
            print(f"  ❌ {display_name} (not installed)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main verification function."""
    
    # Check if we're in the right directory
    if not os.path.exists('app.py') and not os.path.exists('README.md'):
        print("❌ This doesn't appear to be the wildlife-game directory")
        print("   Please run this script from the wildlife-game folder")
        return
    
    # Run all checks
    structure_ok = check_file_structure()
    python_ok = check_python_version()
    deps_available = check_dependencies()
    
    print("\n" + "=" * 50)
    print("FINAL STATUS")
    print("=" * 50)
    
    if structure_ok and python_ok:
        if deps_available:
            print("🎉 READY TO GO! Your setup is complete.")
            print("\nRun the game with:")
            print("   python app.py")
        else:
            print("🔧 ALMOST READY! Install dependencies first:")
            print("   pip install -r requirements.txt")
    else:
        print("❌ SETUP NEEDED: Please fix the issues above first.")
    
    print("\nFor detailed setup instructions, see README.md")

if __name__ == '__main__':
    main()