
import sys
print("Starting import checks...")
try:
    import pandas
    print(f"Pandas version: {pandas.__version__}")
except ImportError as e:
    print(f"Pandas failed: {e}")

try:
    import numpy
    print(f"Numpy version: {numpy.__version__}")
except ImportError as e:
    print(f"Numpy failed: {e}")

try:
    print("Importing matplotlib...")
    import matplotlib
    print(f"Matplotlib version: {matplotlib.__version__}")
    import matplotlib.pyplot as plt
    print("Matplotlib.pyplot imported.")
except ImportError as e:
    print(f"Matplotlib failed: {e}")
except Exception as e:
    print(f"Matplotlib error: {e}")

try:
    import seaborn
    print(f"Seaborn version: {seaborn.__version__}")
except ImportError as e:
    print(f"Seaborn failed: {e}")

print("Check complete.")
