# Import assessment routes
try:
    from .assessment_routes import router as assessment_router
except ImportError as e:
    print(f"Warning: Could not import assessment routes: {e}")
    assessment_router = None

# Import pipeline routes
try:
    from .pipeline_routes import router as pipeline_router
except ImportError as e:
    print(f"Warning: Could not import pipeline routes: {e}")
    pipeline_router = None