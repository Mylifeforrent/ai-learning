---
name: get-weather
description: Get weather information for specified cities. Use this skill when the user asks about local weather, real-time temperature, or outdoor conditions (e.g., "What's the weather like?", "Is it raining?", "Should I bring an umbrella?").
license: Complete terms in LICENSE.txt
---

This skill provides accurate, real-time weather information for any city requested by the user. It extracts location information from user queries and delivers helpful weather forecasts in a natural, conversational tone.

The user provides a weather query: asking about current conditions, temperature, or outdoor activity recommendations for a specific location.

## Goal

Extract the user's weather information needs and provide accurate, helpful weather forecast results for any requested city.

## Workflow

### 1. Extract Location Information

From the user's request, identify the city name:
- If the user says "today" or "here", attempt to infer the specific geographic location from conversation context
- If the location is ambiguous or unclear, proactively ask the user to confirm the precise location
- Handle variations in city names (e.g., "NYC" → "New York City", "SF" → "San Francisco")

### 2. Fetch Weather Data

Retrieve the latest weather information for the specified location:
- **Temperature data** (default to Celsius unless specified otherwise)
- **Weather conditions** (sunny, cloudy, rainy, etc.)
- **Humidity and wind speed** from meteorological reports
- **Air quality index** (if supported by the data source)

### 3. Format Response

Present comprehensive weather information in a natural, conversational tone:
- **For simple queries**: Provide only core information (temperature + basic weather conditions)
- **For detailed queries**: Include additional details like humidity trends, wind speed, and outdoor recommendations
- **For outdoor activity questions**: Combine current weather conditions with proactive advice on outdoor activity feasibility

### 4. Handle Edge Cases

- **Data unavailable**: Explain the objective reason for inability to fetch data and suggest alternative methods
- **Future weather predictions**: Clarify that the service only provides real-time weather data, not long-term forecasts
- **Multi-city comparisons**: Fetch data for each city separately, then provide a consolidated comparison report

## Constraints

- **Temperature units**: Always default to Celsius unless the user explicitly requests Fahrenheit
- **Data freshness**: Strictly provide only the latest weather data for the requested time; never make unauthorized long-term predictions
- **Severe weather alerts**: Proactively warn users about hazardous conditions (sandstorms, heavy fog, etc.) even if not explicitly asked
- **Response brevity**: Keep responses concise while maintaining essential data and information value

## Examples

### Example 1: Simple Single Query
**User**: "What's the weather like in Beijing today?"

**Response**: "Beijing is sunny today with a temperature of 25°C. Air quality is good, suitable for outdoor activities."

---

### Example 2: Multi-City Comparison
**User**: "Compare the weather in Beijing and Shanghai for me"

**Response**: "Beijing: Sunny, 25°C; Shanghai: Cloudy, 28°C. Shanghai is slightly warmer, but both cities are suitable for travel."

---

### Example 3: Activity Recommendation with Context
**User**: "Is tomorrow good for traveling?"

**Response**: "Based on current forecasts (tomorrow: sunny, 25°C), this should be excellent weather for outdoor activities. However, UV levels will be high around noon, so I recommend bringing a hat or sunscreen."

---

### Example 4: Severe Weather Alert
**User**: "What's the weather in Delhi?"

**Response**: "Delhi is currently experiencing heavy smog with an AQI of 350 (hazardous). Temperature is 18°C. ⚠️ **Air quality warning**: Outdoor activities are not recommended. If you must go out, please wear an N95 mask."

---

## Implementation Notes

**For demonstration purposes**: This is a conceptual skill. Actual weather data retrieval requires integration with real weather APIs such as:
- OpenWeatherMap
- WeatherAPI
- 和风天气 (Qweather)
- Visual Crossing Weather

In demonstration mode, you may use simulated data to showcase the functional logic and response formatting.

**API Integration Considerations**:
- Ensure proper error handling for API rate limits
- Cache recent queries to reduce API calls
- Handle timezone conversions appropriately
- Support both metric and imperial units

**Response Quality Guidelines**:
- Use natural language that feels conversational, not robotic
- Tailor detail level to the user's query specificity
- Include actionable advice when relevant (e.g., "bring an umbrella", "apply sunscreen")
- For severe weather, prioritize safety warnings over other information
