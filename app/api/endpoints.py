import json
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from pathlib import Path
from app.core.security import api_key_auth 
from app.core.config import settings
from app.models.schemas import (
    NatalChartRequest, NatalChartResponse,
    SVGRequest, SVGResponse,
    BiwheelRequest,
    SynastryRequest, SynastryResponse,
    CompositeRequest, CompositeResponse,
    ReportRequest, ReportResponse,
    ForecastRequest, ForecastResponse,
    HealthResponse
)
from app.services.chart_service import ChartService
from app.services.svg_service import SVGService
from app.services.report_service import ReportService
from app.services.forecast_service import ForecastService
from app.services.astrology_core import synastry_aspects, composite_midpoints, HAVE_SWE

# Create router
router = APIRouter()

# Initialize services
chart_service = ChartService(swe_path=settings.swe_path)
svg_service = SVGService()
report_service = ReportService()
forecast_service = ForecastService()

# Debug output directory
DEBUG_DIR = Path("debug_outputs")
DEBUG_DIR.mkdir(exist_ok=True)

def save_debug_output(filename: str, data: dict, content_type: str = "json"):
    """Save debug output to filesystem only if debug outputs are enabled."""
    # Check if debug outputs are enabled
    if not settings.enable_debug_outputs:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if content_type == "json":
        filepath = DEBUG_DIR / f"{filename}_{timestamp}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    elif content_type == "svg":
        filepath = DEBUG_DIR / f"{filename}_{timestamp}.svg"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(data)
    elif content_type == "markdown":
        filepath = DEBUG_DIR / f"{filename}_{timestamp}.md"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(data)
    print(f"Debug output saved: {filepath}")
    return filepath

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        swiss_ephemeris=HAVE_SWE
    )

@router.post("/natal", response_model=NatalChartResponse)
async def compute_natal_chart(
    request: NatalChartRequest,
    _: str = Depends(api_key_auth)
):
    """Compute a natal chart."""
    try:
        result = chart_service.compute_natal_chart(request)
        
        # Save debug output
        debug_data = {
            "request": request.model_dump(),
            "response": result.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("natal_chart", debug_data)
        
        return result
    except Exception as e:
        error_data = {
            "request": request.dict(),
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("natal_chart_error", error_data)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute natal chart: {str(e)}"
        )


@router.post("/svg", response_model=SVGResponse)
async def generate_svg(
    request: SVGRequest,
    _: str = Depends(api_key_auth)
):
    """Generate SVG chart wheel."""
    try:
        result = svg_service.generate_wheel(request)
        result = SVGResponse(svg_content=result["svg_content"], size=request.size)
        
        # Save debug outputs
        debug_data = {
            "request": request.model_dump(),
            "response_size": len(result.svg_content),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("svg_request", debug_data)
        save_debug_output("svg_chart", result.svg_content, "svg")
        
        return result
    except Exception as e:
        error_data = {
            "request": request.model_dump(),
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("svg_error", error_data)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SVG: {str(e)}"
        )


@router.post("/biwheel", response_model=SVGResponse)
async def generate_biwheel(
    request: BiwheelRequest,
    _: str = Depends(api_key_auth)
):
    """Generate synastry biwheel SVG."""
    try:
        result = svg_service.generate_biwheel(request)
        result = SVGResponse(svg_content=result["svg_content"], size=request.size)
        
        # Save debug outputs
        debug_data = {
            "request": request.model_dump(),
            "response_size": len(result.svg_content),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("biwheel_request", debug_data)
        save_debug_output("biwheel_chart", result.svg_content, "svg")
        
        return result
    except Exception as e:
        error_data = {
            "request": request.dict(),
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("biwheel_error", error_data)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate biwheel: {str(e)}"
        )


@router.post("/synastry", response_model=SynastryResponse)
async def calculate_synastry(
    request: SynastryRequest,
    _: str = Depends(api_key_auth)
):
    """Calculate synastry aspects between two charts."""
    try:
        aspects = synastry_aspects(request.chart_a, request.chart_b)
        result = SynastryResponse(interaspects=aspects)
        
        # Save debug output
        debug_data = {
            "request": request.model_dump(),
            "response": result.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("synastry", debug_data)
        
        return result
    except Exception as e:
        error_data = {
            "request": request.model_dump(),
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("synastry_error", error_data)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate synastry: {str(e)}"
        )


@router.post("/composite", response_model=CompositeResponse)
async def calculate_composite(
    request: CompositeRequest,
    _: str = Depends(api_key_auth)
):
    """Calculate composite midpoints between two charts."""
    try:
        midpoints = composite_midpoints(request.chart_a, request.chart_b)
        result = CompositeResponse(midpoints=midpoints)
        
        # Save debug output
        debug_data = {
            "request": request.model_dump(),
            "response": result.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("composite", debug_data)
        
        return result
    except Exception as e:
        error_data = {
            "request": request.model_dump(),
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("composite_error", error_data)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate composite: {str(e)}"
        )


@router.post("/report", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    _: str = Depends(api_key_auth)
):
    """Generate markdown report from chart data."""
    try:
        result = report_service.generate_report(request)
        
        # Save debug outputs
        debug_data = {
            "request": request.model_dump(),
            "response_size": len(result.report_content),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("report_request", debug_data)
        save_debug_output("report_content", result.report_content, "markdown")
        
        return result
    except Exception as e:
        error_data = {
            "request": request.model_dump(),
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("report_error", error_data)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.post("/forecast", response_model=ForecastResponse)
async def generate_forecast(
    request: ForecastRequest,
    _: str = Depends(api_key_auth)
):
    """Generate transit forecast."""
    try:
        result = forecast_service.generate_forecast(request)
        
        # Save debug output
        debug_data = {
            "request": request.model_dump(),
            "response": result.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("forecast", debug_data)
        
        return result
    except Exception as e:
        error_data = {
            "request": request.model_dump(),
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        save_debug_output("forecast_error", error_data)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forecast: {str(e)}"
        )
