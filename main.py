from fastapi import FastAPI, HTTPException, __version__
from fastapi.middleware.cors import CORSMiddleware
from metar import Metar

from database import Database
from models.airport import Airport
from models.metar_text import MetarText
from utils.liveatc_crawler import LiveATCCrawler

db = Database()
liveatc = LiveATCCrawler()
app = FastAPI(
    title="LiveATC Backend API",
    description="Backend service for LiveATC audio channel metadata and streaming",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthcheck")
async def read_root():
    """Root endpoint to check API status"""
    return {
        "status": "ok",
        "message": "LiveATC Backend API is running",
        "version": __version__,
    }


@app.get("/airport/{icao}", response_model=Airport)
async def get_airport(icao: str):
    """Get airport information and audio channels from database"""
    try:
        # Get airport info from database
        result = db.get_airport_by_icao(icao)

        if not result.data:
            raise HTTPException(status_code=404, detail=f"Airport {icao} not found")

        airport_data = result.data[0]

        # Get associated channels
        channels = db.get_audio_channels(icao)

        # Construct Airport object
        return Airport(
            icao=airport_data["icao"],
            name=airport_data["name"],
            iata=airport_data.get("iata"),
            city=airport_data.get("city"),
            state_province=airport_data.get("state_province"),
            country=airport_data.get("country"),
            continent=airport_data.get("continent"),
            latitude=airport_data.get("latitude"),
            longitude=airport_data.get("longitude"),
            metar=airport_data.get("metar"),
            audio_channels=channels.data,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching airport information: {str(e)}"
        )


@app.post("/airport/{icao}", response_model=Airport)
async def update_airport(icao: str):
    """Fetch latest airport information from LiveATC and update database"""
    airport_info = await liveatc.search_airport(icao)
    if not airport_info:
        raise HTTPException(
            status_code=404, detail=f"Airport {icao} not found on LiveATC"
        )

    try:
        # Update airport information
        airport_data = {
            "icao": airport_info.icao,
            "name": airport_info.name,
            "iata": airport_info.iata,
            "city": airport_info.city,
            "state_province": airport_info.state_province,
            "country": airport_info.country,
            "continent": airport_info.continent,
            "metar": airport_info.metar,
        }

        # Use upsert to insert or update airport
        db.upsert_airport(airport_data)

        # Update audio channels with only essential fields
        for channel in airport_info.audio_channels:
            channel_data = {
                "name": channel.name,
                "airport_icao": channel.airport_icao,
                "feed_status": channel.feed_status,
                "frequencies": channel.frequencies,
                "mp3_url": channel.mp3_url,
            }
            db.upsert_audio_channel(channel_data)

        return airport_info
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating airport information: {str(e)}"
        )
    
@app.post('/metar')
async def add_metar(request: MetarText):
    print(request)
    return Metar.Metar(request.query)