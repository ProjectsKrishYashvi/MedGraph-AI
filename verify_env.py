"""MedGraph AI — Environment Verification Script"""

checks = [
    ("pandas",                   "pandas"),
    ("pyarrow",                  "pyarrow"),
    ("numpy",                    "numpy"),
    ("xgboost",                  "xgboost"),
    ("sklearn",                  "scikit-learn"),
    ("shap",                     "shap"),
    ("matplotlib",               "matplotlib"),
    ("fitz",                     "pymupdf"),
    ("qdrant_client",            "qdrant-client"),
    ("fastembed",                "fastembed"),
    ("langgraph",                "langgraph"),
    ("langchain_core",           "langchain-core"),
    ("langchain_text_splitters", "langchain-text-splitters"),
    ("requests",                 "requests (Gemini REST API)"),
]

print("=" * 58)
print("MedGraph AI — Environment Check")
print("=" * 58)

all_ok = True
for module, name in checks:
    try:
        import importlib
        m = importlib.import_module(module)
        version = getattr(m, "__version__", "installed")
        print(f"  [OK]   {name:<32} {version}")
    except ImportError:
        print(f"  [MISS] {name:<32} NOT INSTALLED")
        all_ok = False
    except Exception as e:
        print(f"  [WARN] {name:<32} installed (warning: {type(e).__name__})")

print("=" * 58)
if all_ok:
    print("  All packages ready. Proceed to Phase 4.")
else:
    print("  Run: pip install -r requirements.txt")
print("=" * 58)
