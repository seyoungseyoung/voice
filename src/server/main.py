"""
FastAPI server for Sentinel-Voice phishing detection
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import tempfile
import shutil
import logging
from typing import Optional

from src.nlp.phishing_pipeline import PhishingDetectionPipeline
from src.scoring.risk_scorer import RiskScorer
from src.security.pii_masking import PIIMasker
from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sentinel-Voice API",
    description="AI-powered voice phishing detection system",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline components
pipeline = None
risk_scorer = None
pii_masker = None


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    global pipeline, risk_scorer, pii_masker

    logger.info("Initializing Sentinel-Voice pipeline...")

    try:
        pipeline = PhishingDetectionPipeline()
        risk_scorer = RiskScorer()
        pii_masker = PIIMasker()
        logger.info("✓ Pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        raise


# Mount static files
from pathlib import Path
ROOT_DIR = Path(__file__).parent.parent.parent
static_path = ROOT_DIR / "static"

if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


class AnalysisRequest(BaseModel):
    """Request model for text analysis"""
    text: str
    enable_pii_masking: bool = True


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    risk_score: float
    risk_level: str
    is_phishing: bool
    alert_message: str
    component_scores: dict
    techniques_detected: list
    masked_text: Optional[str] = None
    pii_detected: Optional[dict] = None


@app.get("/")
async def root():
    """Serve demo page"""
    demo_page = ROOT_DIR / "static" / "index.html"
    if demo_page.exists():
        return FileResponse(demo_page)

    # Fallback to JSON if demo page doesn't exist
    return {
        "service": "Sentinel-Voice",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "demo": "/",
            "analyze_audio": "/api/analyze/audio",
            "analyze_text": "/api/analyze/text",
            "health": "/health",
            "api_docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pipeline_ready": pipeline is not None,
        "scorer_ready": risk_scorer is not None,
        "masker_ready": pii_masker is not None
    }


@app.post("/api/analyze/audio", response_model=AnalysisResponse)
async def analyze_audio(file: UploadFile = File(...)):
    """
    Analyze audio file for phishing detection

    Args:
        file: Audio file (WAV, MP3, FLAC)

    Returns:
        Analysis results with risk score
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    # Validate file type
    allowed_extensions = [".wav", ".mp3", ".flac", ".m4a"]
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = Path(temp_file.name)

        logger.info(f"Processing audio file: {file.filename}")

        # Analyze audio
        result = pipeline.analyze_audio(temp_path)

        # Calculate detailed risk score
        risk_result = risk_scorer.calculate_risk_score(
            result["transcript"],
            [(case["script"], case["similarity"], {}) for case in result["similar_cases"]]
        )

        # PII masking
        masked_text, pii_metadata = pii_masker.mask_text(result["transcript"])

        response = AnalysisResponse(
            risk_score=risk_result["risk_score"],
            risk_level=risk_result["risk_level"],
            is_phishing=risk_result["is_phishing"],
            alert_message=risk_result["alert_message"],
            component_scores=risk_result["component_scores"],
            techniques_detected=result.get("techniques_detected", []),
            masked_text=masked_text,
            pii_detected=pii_metadata.get("masked_types", {})
        )

        logger.info(
            f"Analysis complete: {file.filename} - "
            f"Risk: {risk_result['risk_score']:.2f}/100 ({risk_result['risk_level']})"
        )

        return response

    except Exception as e:
        logger.error(f"Error analyzing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


@app.post("/api/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    """
    Analyze text for phishing detection

    Args:
        request: Analysis request with text

    Returns:
        Analysis results with risk score
    """
    if risk_scorer is None or pii_masker is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    try:
        logger.info(f"Analyzing text: {request.text[:50]}...")

        # Calculate risk score
        risk_result = risk_scorer.calculate_risk_score(request.text)

        # PII masking
        masked_text = None
        pii_detected = None

        if request.enable_pii_masking:
            masked_text, pii_metadata = pii_masker.mask_text(request.text)
            pii_detected = pii_metadata.get("masked_types", {})

        # Extract techniques from metadata
        techniques = []
        keyword_matches = risk_result["metadata"]["keyword"].get("matches", {})
        for category, data in keyword_matches.items():
            techniques.append(f"{category} ({data['count']}건)")

        response = AnalysisResponse(
            risk_score=risk_result["risk_score"],
            risk_level=risk_result["risk_level"],
            is_phishing=risk_result["is_phishing"],
            alert_message=risk_result["alert_message"],
            component_scores=risk_result["component_scores"],
            techniques_detected=techniques,
            masked_text=masked_text,
            pii_detected=pii_detected
        )

        logger.info(
            f"Text analysis complete - "
            f"Risk: {risk_result['risk_score']:.2f}/100 ({risk_result['risk_level']})"
        )

        return response

    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    if pipeline is None:
        return {"error": "Pipeline not initialized"}

    vector_store_stats = pipeline.vector_store.get_statistics()

    return {
        "vector_db": vector_store_stats,
        "risk_scorer": {
            "keyword_weight": risk_scorer.keyword_weight,
            "sentiment_weight": risk_scorer.sentiment_weight,
            "similarity_weight": risk_scorer.similarity_weight,
            "threshold": risk_scorer.threshold
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.server.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.debug
    )
