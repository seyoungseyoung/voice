"""
FastAPI server for Sentinel-Voice phishing detection
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import tempfile
import shutil
import logging
from typing import Optional
import hashlib
from datetime import datetime, timedelta
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.nlp.phishing_pipeline import PhishingDetectionPipeline
from src.scoring.risk_scorer import RiskScorer
from src.security.pii_masking import PIIMasker
from src.llm.multi_agent_detector import MultiAgentPhishingDetector
from src.llm.multi_llm_ensemble import MultiLLMEnsemble
from src.llm.gemini_detector import GeminiPhishingDetector
from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="Sentinel-Voice API",
    description="AI-powered voice phishing detection system",
    version="0.1.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
clovax_client = None
llm_ensemble = None
gemini_detector = None

# Simple in-memory cache with TTL
response_cache = {}
cache_timestamps = {}
CACHE_TTL = 3600  # 1 hour


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    global pipeline, risk_scorer, pii_masker, clovax_client, llm_ensemble, gemini_detector

    logger.info("Initializing Sentinel-Voice pipeline...")

    try:
        pipeline = PhishingDetectionPipeline()
        risk_scorer = RiskScorer()
        pii_masker = PIIMasker()

        # Initialize Gemini + Rule Filter (main detection system)
        try:
            gemini_detector = GeminiPhishingDetector()
            logger.info("✓ Gemini 2.5 Flash + Rule Filter initialized (main system)")
        except Exception as e:
            logger.warning(f"⚠ Gemini detector initialization failed: {e}")

        # Initialize Multi-LLM Ensemble for comparison
        llm_ensemble = MultiLLMEnsemble()

        # Fallback to single multi-agent detector
        clovax_client = MultiAgentPhishingDetector()

        if llm_ensemble.is_available():
            logger.info(f"✓ Multi-LLM Comparison enabled: {len(llm_ensemble.available_llms)} LLMs available")
        elif clovax_client.is_available():
            logger.info("✓ Multi-Agent ClovaX LLM enabled (3 agents)")
        else:
            logger.warning("⚠ No LLM configured, using rule-based fallback")

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


def _get_risk_level(score: float) -> str:
    """Helper function to determine risk level from score"""
    if score >= 90:
        return "CRITICAL"
    elif score >= 70:
        return "HIGH"
    elif score >= 50:
        return "MEDIUM"
    elif score >= 30:
        return "LOW"
    else:
        return "SAFE"


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pipeline_ready": pipeline is not None,
        "scorer_ready": risk_scorer is not None,
        "masker_ready": pii_masker is not None,
        "clovax_ready": clovax_client is not None and clovax_client.is_available()
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

    # Validate file type - allow WebM for browser recordings
    allowed_extensions = [".wav", ".mp3", ".flac", ".m4a", ".webm", ".ogg", ".opus"]
    file_extension = Path(file.filename).suffix.lower()

    # If no extension (browser recording), default to .webm
    if not file_extension:
        file_extension = ".webm"
        logger.info(f"No file extension detected, using default: {file_extension}")

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save uploaded file temporarily
    temp_path = None
    try:
        # Use explicit file handling to ensure proper flushing
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        temp_path = Path(temp_file.name)

        # Copy file content
        shutil.copyfileobj(file.file, temp_file)
        temp_file.flush()  # Force write to disk
        temp_file.close()  # Close file handle

        logger.info(f"Processing audio file: {file.filename}")
        logger.info(f"Temp file path: {temp_path}")
        logger.info(f"Temp file exists: {temp_path.exists()}")
        logger.info(f"Temp file size: {temp_path.stat().st_size} bytes")

        # Verify file exists and has content
        if not temp_path.exists():
            raise HTTPException(status_code=500, detail="Temporary file was not created properly")

        if temp_path.stat().st_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Transcribe audio only (bypass full pipeline to avoid ffmpeg issues)
        transcript = pipeline.transcribe_audio(temp_path)
        logger.info(f"Transcription: {transcript[:100]}...")

        # Use Gemini + Filter for analysis (same as text analysis)
        if gemini_detector:
            gemini_result = gemini_detector.analyze(transcript, enable_filter=True)

            # Convert Gemini result to AnalysisResponse format
            response = AnalysisResponse(
                risk_score=gemini_result["score"],
                risk_level=gemini_result["risk_level"],
                is_phishing=gemini_result["is_phishing"],
                alert_message=gemini_result["reasoning"],
                component_scores={
                    "llm_score": gemini_result.get("llm_score", gemini_result["score"]),
                    "final_score": gemini_result["score"],
                    "filter_applied": gemini_result.get("filter_applied", False)
                },
                techniques_detected=[],
                masked_text=None,
                pii_detected={}
            )

            logger.info(
                f"Analysis complete: {file.filename} - "
                f"Risk: {gemini_result['score']}/100 ({gemini_result['risk_level']})"
            )
        else:
            # Fallback to old pipeline if Gemini not available
            result = pipeline.analyze_audio(temp_path)

            risk_result = risk_scorer.calculate_risk_score(
                result["transcript"],
                [(case["script"], case["similarity"], {}) for case in result["similar_cases"]]
            )

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
        # Clean up temp file (ignore errors if file is still locked by pydub)
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except PermissionError:
                # File still in use by pydub, will be cleaned up by OS
                logger.warning(f"Could not delete temp file (in use): {temp_path}")
            except Exception as e:
                logger.warning(f"Could not delete temp file: {e}")


@app.post("/api/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    """
    Analyze text for phishing detection

    Args:
        request: Analysis request with text

    Returns:
        Analysis results with risk score
    """
    if risk_scorer is None or pii_masker is None or pipeline is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    try:
        logger.info(f"Analyzing text: {request.text[:50]}...")

        # Search for similar cases using Vector DB
        similar_cases = pipeline.search_similar_cases(request.text, top_k=5)

        # Use Multi-LLM Ensemble for comparison if available
        if llm_ensemble and llm_ensemble.is_available():
            logger.info(f"🔬 Using Multi-LLM Comparison ({len(llm_ensemble.available_llms)} LLMs)")
            llm_result = llm_ensemble.analyze(request.text, similar_cases)

            # Print comparison table to console
            if "comparison_table" in llm_result:
                print(llm_result["comparison_table"])
                print(llm_result["detailed_analysis"])

            risk_result = {
                "risk_score": llm_result["risk_score"],
                "risk_level": _get_risk_level(llm_result["risk_score"]),
                "is_phishing": llm_result["is_phishing"],
                "alert_message": llm_result["recommendation"],
                "component_scores": {
                    "llm_confidence": llm_result.get("confidence", 0),
                    "similarity": max([s for _, s, _ in similar_cases], default=0) * 100,
                    **llm_result.get("llm_scores", {})  # Individual LLM scores
                },
                "metadata": {
                    "mode": "Multi-LLM Comparison",
                    "comparison_table": llm_result.get("comparison_table", ""),
                    "detailed_analysis": llm_result.get("detailed_analysis", ""),
                    "statistics": llm_result.get("statistics", {}),
                    "reasoning": llm_result.get("reasoning", ""),
                    "red_flags": llm_result.get("red_flags", [])
                }
            }
            techniques = llm_result.get("techniques", [])

        # Fallback to single multi-agent ClovaX
        elif clovax_client and clovax_client.is_available():
            logger.info("🤖 Using Multi-Agent ClovaX (3 agents) for contextual analysis")
            llm_result = clovax_client.analyze(request.text, similar_cases)

            risk_result = {
                "risk_score": llm_result["risk_score"],
                "risk_level": _get_risk_level(llm_result["risk_score"]),
                "is_phishing": llm_result["is_phishing"],
                "alert_message": llm_result["recommendation"],
                "component_scores": {
                    "llm_confidence": llm_result.get("confidence", 0),
                    "similarity": max([s for _, s, _ in similar_cases], default=0) * 100,
                    "agent_context": llm_result["agent_scores"]["context"],
                    "agent_psychological": llm_result["agent_scores"]["psychological"],
                    "agent_financial": llm_result["agent_scores"]["financial"]
                },
                "metadata": {
                    "mode": "Multi-Agent LLM",
                    "reasoning": llm_result.get("reasoning", ""),
                    "red_flags": llm_result.get("red_flags", [])
                }
            }
            techniques = llm_result.get("techniques", [])

        # Fallback to rule-based
        else:
            logger.info("📊 Using rule-based analysis (No LLM available)")
            risk_result = risk_scorer.calculate_risk_score(request.text, similar_cases)

            # Extract techniques from metadata
            techniques = []
            keyword_matches = risk_result["metadata"]["keyword"].get("matches", {})
            for category, data in keyword_matches.items():
                techniques.append(f"{category} ({data['count']}건)")

        # PII masking
        masked_text = None
        pii_detected = None

        if request.enable_pii_masking:
            masked_text, pii_metadata = pii_masker.mask_text(request.text)
            pii_detected = pii_metadata.get("masked_types", {})

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


def _get_cache_key(text: str) -> str:
    """Generate cache key from text"""
    return hashlib.md5(text.encode()).hexdigest()


def _is_cache_valid(cache_key: str) -> bool:
    """Check if cached response is still valid"""
    if cache_key not in cache_timestamps:
        return False
    elapsed = (datetime.now() - cache_timestamps[cache_key]).total_seconds()
    return elapsed < CACHE_TTL


def _clean_expired_cache():
    """Remove expired cache entries"""
    now = datetime.now()
    expired_keys = [
        key for key, timestamp in cache_timestamps.items()
        if (now - timestamp).total_seconds() >= CACHE_TTL
    ]
    for key in expired_keys:
        response_cache.pop(key, None)
        cache_timestamps.pop(key, None)


class GeminiAnalysisRequest(BaseModel):
    """Request model for Gemini + Filter analysis"""
    text: str
    enable_filter: bool = True


@app.post("/api/analyze/gemini")
@limiter.limit("10/minute")  # 1분당 10회 제한
async def analyze_with_gemini(request: Request, req: GeminiAnalysisRequest):
    """
    Gemini 2.5 Flash + Rule-based Filter를 사용한 피싱 탐지

    - Rate limit: 10 requests/minute per IP
    - Caching: 동일 텍스트 1시간 캐싱
    """
    global gemini_detector

    if not gemini_detector:
        raise HTTPException(status_code=503, detail="Gemini detector not available")

    # 캐시 체크
    cache_key = _get_cache_key(req.text)
    if _is_cache_valid(cache_key):
        logger.info(f"✓ Cache hit for request from {get_remote_address(request)}")
        return response_cache[cache_key]

    # 만료된 캐시 정리
    _clean_expired_cache()

    try:
        # Gemini + Filter 분석
        result = gemini_detector.analyze(req.text, enable_filter=req.enable_filter)

        response = {
            "score": result["score"],
            "risk_level": result["risk_level"],
            "is_phishing": result["is_phishing"],
            "reasoning": result["reasoning"],
            "model": result["model"],
            "filter_applied": result.get("filter_applied", False),
            "llm_score": result.get("llm_score", result["score"]),
            "keyword_analysis": result.get("keyword_analysis", {}),
            "cached": False
        }

        # 결과 캐싱
        response_cache[cache_key] = {**response, "cached": True}
        cache_timestamps[cache_key] = datetime.now()

        logger.info(
            f"✓ Gemini analysis: score={result['score']}, "
            f"is_phishing={result['is_phishing']}, "
            f"filter_applied={result.get('filter_applied', False)}"
        )

        return response

    except Exception as e:
        logger.error(f"Gemini analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/cache/stats")
async def get_cache_stats():
    """캐시 통계 조회"""
    _clean_expired_cache()
    return {
        "cache_size": len(response_cache),
        "cache_hit_rate": "N/A",  # 추적을 위해서는 별도 카운터 필요
        "ttl_seconds": CACHE_TTL
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.server.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.debug
    )
