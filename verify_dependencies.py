#!/usr/bin/env python
"""
Verify all project dependencies are installed and ready
"""

import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Critical packages that must be installed
REQUIRED_PACKAGES = {
    'cv2': 'opencv-python',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'PIL': 'Pillow',
    'fitz': 'PyMuPDF',
    'pytesseract': 'pytesseract',
    'pdfminer': 'pdfminer.six',
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'layoutparser': 'layoutparser',
    'spacy': 'spacy',
    'transformers': 'transformers',
    'torch': 'torch',
    'requests': 'requests',
}

# Optional packages
OPTIONAL_PACKAGES = {
    'dateutil': 'python-dateutil',
    'joblib': 'joblib',
    'scipy': 'scipy',
    'xgboost': 'xgboost',
    'sklearn': 'scikit-learn',
    'imblearn': 'imbalanced-learn',
}

def check_import(module_name):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def check_spacy_model():
    """Check if Spacy English model is installed"""
    try:
        import spacy
        try:
            spacy.load("en_core_web_sm")
            return True
        except OSError:
            return False
    except:
        return False

def main():
    logger.info("=" * 60)
    logger.info("HR Buddy Dependency Verification")
    logger.info("=" * 60)
    
    missing_critical = []
    missing_optional = []
    
    # Check critical packages
    logger.info("\nChecking CRITICAL packages...")
    for module, package_name in REQUIRED_PACKAGES.items():
        if check_import(module):
            logger.info(f"✓ {module} ({package_name})")
        else:
            logger.warning(f"✗ {module} ({package_name}) - MISSING")
            missing_critical.append(package_name)
    
    # Check optional packages
    logger.info("\nChecking OPTIONAL packages...")
    for module, package_name in OPTIONAL_PACKAGES.items():
        if check_import(module):
            logger.info(f"✓ {module} ({package_name})")
        else:
            logger.warning(f"✗ {module} ({package_name}) - MISSING (optional)")
            missing_optional.append(package_name)
    
    # Check Spacy model
    logger.info("\nChecking Spacy models...")
    if check_spacy_model():
        logger.info("✓ en_core_web_sm (Spacy English model)")
    else:
        logger.warning("✗ en_core_web_sm (Spacy English model) - MISSING")
    
    # Summary
    logger.info("\n" + "=" * 60)
    if missing_critical:
        logger.error(f"\nCRITICAL packages missing ({len(missing_critical)}):")
        for pkg in missing_critical:
            logger.error(f"  - {pkg}")
        logger.error("\nInstalling missing critical packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_critical)
    else:
        logger.info("\n✓ All critical packages are installed!")
    
    if missing_optional:
        logger.info(f"\nOptional packages missing ({len(missing_optional)}):")
        for pkg in missing_optional:
            logger.info(f"  - {pkg} (optional)")
    else:
        logger.info("✓ All optional packages are installed!")
    
    # Download Spacy model if missing
    if not check_spacy_model():
        logger.info("\nDownloading Spacy English model...")
        try:
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            logger.info("✓ Spacy model downloaded successfully")
        except Exception as e:
            logger.error(f"✗ Failed to download Spacy model: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Dependency verification complete!")
    logger.info("=" * 60 + "\n")
    
    return 0 if not missing_critical else 1

if __name__ == "__main__":
    sys.exit(main())
