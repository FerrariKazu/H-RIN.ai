#!/usr/bin/env python
"""
Diagnose Spacy model installation and Python environment
"""

import sys
import os
import subprocess

def check_python_info():
    """Check Python environment info"""
    print("=" * 60)
    print("PYTHON ENVIRONMENT")
    print("=" * 60)
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Prefix: {sys.prefix}")
    print()

def check_spacy_installation():
    """Check if spacy is installed"""
    print("=" * 60)
    print("SPACY INSTALLATION")
    print("=" * 60)
    try:
        import spacy
        print(f"✓ Spacy installed: {spacy.__version__}")
        print(f"  Location: {spacy.__file__}")
    except ImportError:
        print("✗ Spacy not installed in current environment")
    print()

def check_spacy_models():
    """Check available Spacy models"""
    print("=" * 60)
    print("SPACY MODELS")
    print("=" * 60)
    
    models_to_check = [
        "en_core_web_sm",
        "en_core_web_md",
        "en_core_web_lg"
    ]
    
    import spacy
    
    for model_name in models_to_check:
        try:
            nlp = spacy.load(model_name)
            print(f"✓ {model_name} - AVAILABLE")
        except OSError:
            print(f"✗ {model_name} - NOT FOUND")
    
    print()

def check_spacy_cli():
    """Check models via spacy CLI"""
    print("=" * 60)
    print("SPACY CLI MODELS")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "spacy", "info"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("Could not get spacy info")
            if result.stderr:
                print(result.stderr)
    except Exception as e:
        print(f"Error running spacy info: {e}")
    
    print()

def check_conda_models():
    """Check if models installed in conda"""
    print("=" * 60)
    print("CONDA ENVIRONMENT")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["conda", "list", "spacy"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("Conda not available or error occurred")
    except FileNotFoundError:
        print("Conda not found in PATH")
    except Exception as e:
        print(f"Error checking conda: {e}")
    
    print()

def check_venv_status():
    """Check if in virtual environment"""
    print("=" * 60)
    print("VIRTUAL ENVIRONMENT")
    print("=" * 60)
    
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print("✓ Running in a virtual environment")
        print(f"  Virtual Env Path: {sys.prefix}")
        print(f"  Base Python: {sys.base_prefix if hasattr(sys, 'base_prefix') else 'N/A'}")
    else:
        print("✗ Not running in a virtual environment")
    
    print()

def recommend_fix():
    """Recommend solution"""
    print("=" * 60)
    print("RECOMMENDED FIX")
    print("=" * 60)
    print()
    print("If model is in conda but not in .venv:")
    print("  Option 1: Install in .venv with pip")
    print("    python -m pip install spacy")
    print("    python -m spacy download en_core_web_sm")
    print()
    print("  Option 2: Use conda environment instead of .venv")
    print("    Deactivate .venv: deactivate")
    print("    Run: python backend/main.py")
    print()
    print("  Option 3: Install directly in .venv from conda")
    print("    python -m pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.x.x/en_core_web_sm-3.x.x-py3-none-win_amd64.whl")
    print()

if __name__ == "__main__":
    check_python_info()
    check_spacy_installation()
    check_spacy_models()
    check_spacy_cli()
    check_conda_models()
    check_venv_status()
    recommend_fix()
