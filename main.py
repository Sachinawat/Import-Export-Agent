
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse # Import JSONResponse
from pathlib import Path
import json

from config import logger, LOGS_DIR
from models import QueryInput, IntelligenceOutput
from services import perceive_agent, decide_agent, act_agent

app = FastAPI(
    title="Import/Export Intelligence Module",
    description="An AI-powered module for fetching and analyzing import/export trade data.",
    version="1.0.0"
)

# Ensure logs directory exists for static file serving
LOGS_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/analyze-trade", response_model=IntelligenceOutput)
async def analyze_trade(query_input: QueryInput):
    """
    Analyzes user queries to provide import/export intelligence.
    """
    logger.info(f"Received request for analysis: '{query_input.query}'")

    try:
        # 1. Perceive Agent: Parse the natural language query
        parsed_query = perceive_agent.parse_query(query_input.query)
        if not parsed_query.intent:
            raise HTTPException(status_code=400, detail="Could not determine import/export intent from query.")

        # 2. Decide Agent: Determine data fetching strategy
        search_queries = decide_agent.decide_strategy(parsed_query)

        # 3. Act Agent: Fetch data, generate recommendations, export Excel
        trade_data = act_agent.fetch_data(search_queries, parsed_query)
        recommendations = act_agent.generate_recommendations(trade_data, parsed_query)
        
        # Prepare Excel download
        identifier = parsed_query.hsn_code or parsed_query.product_name or 'general'
        intent_str = parsed_query.intent or 'trade'
        # Sanitize filename for spaces and other special chars
        excel_filename = f"trade_data_{identifier.replace(' ', '_').replace('/', '-')}_{intent_str}.xlsx"
        excel_path = act_agent.export_to_excel(trade_data, excel_filename)
        
        # Construct the Pydantic model instance
        response_model_instance = IntelligenceOutput(
            query=query_input.query,
            parsed_query=parsed_query,
            trade_data=trade_data,
            recommendations=recommendations,
            download_link=f"/download/{excel_path.name}"
        )
        
        logger.info(f"Successfully processed query: '{query_input.query}'")

        # Convert Pydantic model to dictionary, excluding fields that are None
        # This is the key change for the "show only available data parameters" JSON output
        response_data = response_model_instance.model_dump(exclude_none=True, by_alias=True)
        return JSONResponse(content=response_data)

    except HTTPException as e:
        logger.error(f"HTTP Error processing query '{query_input.query}': {e.detail}")
        raise e
    except Exception as e:
        logger.critical(f"Unhandled error processing query '{query_input.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Allows downloading of generated Excel files.
    """
    file_path = LOGS_DIR / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    
    logger.info(f"Serving file for download: {file_path}")
    return FileResponse(path=file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=filename)

@app.get("/")
async def root():
    return {"message": "Welcome to the Import/Export Intelligence Module! Use /docs for API documentation."}