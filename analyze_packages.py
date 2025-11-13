"""Script to analyze which packages PyInstaller includes in the build"""

import sys
from pathlib import Path
import json

def analyze_spec_file(spec_path: Path):
    """Analyze a .spec file to see what packages are included"""
    if not spec_path.exists():
        print(f"Spec file not found: {spec_path}")
        return
    
    print(f"\nAnalyzing spec file: {spec_path}")
    print("=" * 60)
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract excludes
    if 'excludes=[' in content:
        start = content.find('excludes=[')
        end = content.find(']', start) + 1
        excludes_section = content[start:end]
        print("\nCurrently excluded modules:")
        print(excludes_section)
    
    # Extract hiddenimports
    if 'hiddenimports' in content:
        print("\nHidden imports found in spec file")
        # This is a simple check, full parsing would be more complex

def analyze_build_logs(build_dir: Path):
    """Analyze build directory for included packages"""
    if not build_dir.exists():
        print(f"Build directory not found: {build_dir}")
        return
    
    print(f"\nAnalyzing build directory: {build_dir}")
    print("=" * 60)
    
    # Check for analysis files
    analysis_file = build_dir / "TankerStowagePlan" / "Analysis-00.toc"
    if analysis_file.exists():
        print("\nFound Analysis file. Checking for potentially unnecessary packages...")
        
        with open(analysis_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Common packages that might be unnecessary
        unnecessary_packages = [
            'numpy', 'scipy', 'pandas', 'matplotlib', 'PIL', 'Pillow',
            'tkinter', 'IPython', 'jupyter', 'notebook', 'pytest', 'unittest',
            'requests', 'sqlite3', 'doctest', 'setuptools', 'pkg_resources'
        ]
        
        found_packages = []
        for line in lines:
            for package in unnecessary_packages:
                if package in line.lower():
                    found_packages.append(package)
                    break
        
        if found_packages:
            print("\n⚠️  Potentially unnecessary packages found in build:")
            for pkg in set(found_packages):
                print(f"  - {pkg}")
        else:
            print("\n✓ No obvious unnecessary packages detected in Analysis file")

def get_installed_packages():
    """Get list of installed packages in the environment"""
    try:
        import pkg_resources
        installed_packages = [d.project_name.lower() for d in pkg_resources.working_set]
        return installed_packages
    except:
        return []

def suggest_excludes():
    """Suggest packages to exclude based on project analysis"""
    print("\n" + "=" * 60)
    print("RECOMMENDED EXCLUDE LIST")
    print("=" * 60)
    
    suggestions = [
        "# Scientific computing (not used)",
        "--exclude-module=numpy",
        "--exclude-module=scipy",
        "--exclude-module=pandas",
        "--exclude-module=matplotlib",
        "",
        "# Image processing (not used)",
        "--exclude-module=PIL",
        "--exclude-module=pillow",
        "",
        "# Alternative GUI (using PyQt6)",
        "--exclude-module=tkinter",
        "",
        "# Development tools (not needed in EXE)",
        "--exclude-module=IPython",
        "--exclude-module=jupyter",
        "--exclude-module=notebook",
        "--exclude-module=pytest",
        "--exclude-module=unittest",
        "--exclude-module=doctest",
        "",
        "# Web libraries (not used)",
        "--exclude-module=requests",
        "--exclude-module=urllib3",
        "",
        "# Database (using JSON only)",
        "--exclude-module=sqlite3",
        "",
        "# Already excluded",
        "--exclude-module=ortools",
    ]
    
    for suggestion in suggestions:
        print(suggestion)

def main():
    """Main analysis function"""
    print("=" * 60)
    print("PyInstaller Package Analysis Tool")
    print("=" * 60)
    
    project_root = Path.cwd()
    
    # Check for spec file
    spec_file = project_root / "TankerStowagePlan.spec"
    if spec_file.exists():
        analyze_spec_file(spec_file)
    
    # Check for build directory
    build_dir = project_root / "build"
    if build_dir.exists():
        analyze_build_logs(build_dir)
    
    # Show recommendations
    suggest_excludes()
    
    print("\n" + "=" * 60)
    print("NOTE: Run build_exe.bat first to generate build files")
    print("=" * 60)

if __name__ == "__main__":
    main()

