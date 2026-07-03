"""
FormulaIQ — Prediction API Router (Module 3)
POST /predict-race
GET  /predict-race/metadata
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from ml.predict import get_feature_importances, get_model_metadata, predict_race
from models.schemas import RacePredictionRequest, RacePredictionResponse
from utils.cache import cache_get, cache_set, make_cache_key

router = APIRouter(prefix="/predict-race", tags=["Prediction"])


@router.post(
    "",
    response_model=RacePredictionResponse,
    summary="Predict race finishing positions",
    description=(
        "Accepts pre-race driver feature vectors and returns predicted finishing "
        "positions with win/podium/top10/DNF probabilities using XGBoost."
    ),
)
async def predict_race_outcome(request: RacePredictionRequest):
    """Run race outcome prediction model."""
    # Build a cache key from the driver codes + race info
    cache_key = make_cache_key(
        "prediction",
        request.year or "custom",
        request.grand_prix or "custom",
        request.model_version,
        "_".join(sorted(d.driver_code for d in request.drivers)),
    )
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        driver_inputs = [d.model_dump() for d in request.drivers]
        predictions = predict_race(driver_inputs, version=request.model_version)
        importances = get_feature_importances(version=request.model_version)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Model not trained yet. Run train_model.py first. ({exc})"
        )
    except Exception as exc:
        logger.error("Prediction error | {}", exc)
        raise HTTPException(status_code=500, detail="Prediction failed")

    response = RacePredictionResponse(
        race_id=request.race_id,
        year=request.year,
        grand_prix=request.grand_prix,
        model_version=request.model_version,
        predictions=predictions,
        feature_importances=importances,
    )

    await cache_set(cache_key, response.model_dump(), ttl=300)
    return response


@router.get(
    "/metadata",
    summary="Get model metadata and feature importances",
)
async def get_prediction_metadata(version: str = "v1"):
    """Return model training metadata and feature importances."""
    try:
        return get_model_metadata(version=version)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Model not found. Run training first.")
