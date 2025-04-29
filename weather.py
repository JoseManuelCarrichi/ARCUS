from mcp.server.fastmcp import FastMCP 
import httpx 

# Create the server
mcp = FastMCP("Weather")



# Add a tool to the server usign a decorator
@mcp.tool()
async def get_weather(city: str) -> dict:
    """
    Get the current weather for a given city. Returns a summary of the weather for the requested city.
    
    Args:
        city (str): The english name of the city to get the weather for. 
    """

    # Use the Open-Meteo API to get the geocode for the city
    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=10&language=en&format=json"


    async with httpx.AsyncClient() as client:
        try: 
            response = await client.get(geocode_url, timeout=30.0) 
            response.raise_for_status() 
            data = response.json() 

            if data["results"]:
                latitude = data["results"][0]["latitude"]
                longitude = data["results"][0]["longitude"]
            else:
                return {"error": "No results found for the given city."}
            
            # Use the Open-Meteo API to get the weather for the geocode
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,is_day,relative_humidity_2m,precipitation,rain&forecast_days=3"
            weather_response = await client.get(weather_url, timeout=30.0)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            return weather_data

        except httpx.RequestError as e:
            return {"error": f"An error occurred while requesting the weather: {e}"}
