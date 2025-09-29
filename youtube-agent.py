import os
import json
import random
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from googleapiclient.discovery import build

load_dotenv()

# --- Configuration ---


youtube_client = build(
    YOUTUBE_API_SERVICE_NAME, 
    YOUTUBE_API_VERSION, 
    developerKey=YOUTUBE_API_KEY,
    credentials=None  # <-- THIS IS THE CRITICAL FIX
)
# --- TOOL 1: YouTube Data Retrieval ---
def get_trending_videos(region: str, max_results: int = 10):
    """Fetches the top trending video IDs and durations using the YouTube Data API."""
    try:
        request = youtube_client.videos().list(
            part="id,contentDetails",
            chart="mostPopular",
            regionCode=region,
            maxResults=max_results
        )
        response = request.execute()

        video_list = []
        for item in response.get('items', []):
            # Extract duration (requires conversion from ISO 8601 format)
            # This is complex, so we'll use a simplified int for simulation
            # In a real project, you'd use a helper function to convert ISO 8601 to seconds
            duration_iso = item['contentDetails']['duration']
            # For this example, we'll *simulate* a video duration in seconds
            video_duration_sec = random.randint(300, 1800) # 5 to 30 minutes
            
            video_list.append({
                "video_id": item['id'],
                "video_duration": video_duration_sec
            })
        return json.dumps({"trending_videos": video_list})

    except Exception as e:
        return json.dumps({"error": f"YouTube API Error: {str(e)}"})


# --- TOOL 2: Ad Event Simulation (The Inference Part) ---
def simulate_ad_events(video_id: str, video_duration: int) -> list:
    """
    Simulates ad events for a video based on common industry practices.
    This replaces the non-existent direct ad event API call.
    """
    ad_events = []
    
    # 1. Pre-roll Ad (Guaranteed)
    ad_events.append({
        'video_id': video_id,
        'ad_type': 'non-skippable',
        'position': 'pre-roll',
        'duration': random.choice([15, 30]),
        'video_time': 0, # Start time is 0 for pre-roll
        'startTime': datetime.now().timestamp() * 1000 # Milliseconds for pandas conversion
    })
    
    # 2. Mid-roll Ads (Based on length)
    # A common rule is an ad break every 8-10 minutes for long content
    if video_duration > 600: # If video is longer than 10 minutes
        mid_roll_count = (video_duration // 600) 
        
        for i in range(1, mid_roll_count + 1):
            start_time_sec = min(i * 600, video_duration - 60) # Ad starts every 10 mins
            ad_events.append({
                'video_id': video_id,
                'ad_type': random.choice(['skippable', 'bumper']),
                'position': 'mid-roll',
                'duration': random.choice([6, 30]),
                'video_time': start_time_sec,
                'startTime': (datetime.now() + timedelta(seconds=start_time_sec + 5)).timestamp() * 1000 
            })

    # 3. Post-roll Ad (Less common, but possible)
    if random.random() < 0.2: # 20% chance of a post-roll ad
        ad_events.append({
            'video_id': video_id,
            'ad_type': 'display',
            'position': 'post-roll',
            'duration': 5,
            'video_time': video_duration, # Ad starts at the end
            'startTime': (datetime.now() + timedelta(seconds=video_duration + 10)).timestamp() * 1000
        })

    return ad_events


# --- Agent Execution Logic ---
def run_ad_agent():
    """Main function to run the OpenAI Agent process."""
    
    # Map tool names to functions for the API call
    tools = [
        {"type": "function", "function": {"name": "get_trending_videos", "parameters": {"type": "object", "properties": {"region": {"type": "string", "description": "The region code (e.g., 'US', 'IN') for trending videos."}, "max_results": {"type": "integer", "description": "The maximum number of videos to return, default 10."}}}}},
    ]

    # 1. Initial call: Ask the agent to find the trending videos
    # The agent will choose to call the 'get_trending_videos' tool.
    messages = [{"role": "system", "content": f"You are an expert Ad Data Analyst. Your goal is to find the top {MAX_VIDEOS} trending videos in region {TRENDING_REGION} and generate ad event data for them. Start by calling the necessary tool to fetch the videos."}]
    
    # Call 1: Agent decides to call a function
    response = client.chat.completions.create(
        model="gpt-4o-mini", # Use a capable model
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    
    response_message = response.choices[0].message

    # 2. Check if the agent wants to call a function
    if response_message.tool_calls:
        function_call = response_message.tool_calls[0].function
        
        if function_call.name == "get_trending_videos":
            arguments = json.loads(function_call.arguments)
            
            # Execute the function call outside the agent
            tool_output = get_trending_videos(
                region=arguments.get("region", TRENDING_REGION),
                max_results=arguments.get("max_results", MAX_VIDEOS)
            )

            # Send the function output back to the agent
            messages.append(response_message)
            messages.append({
                "tool_call_id": response_message.tool_calls[0].id,
                "role": "tool",
                "content": tool_output,
            })
            
            # Extract video data from the tool output
            video_data = json.loads(tool_output).get("trending_videos", [])
            
            # 3. Data Processing & Simulation (This is where the agent's *output* is generated)
            final_data = []
            
            # Simulate ad events for each trending video
            for video in video_data:
                events = simulate_ad_events(video['video_id'], video['video_duration'])
                final_data.extend(events)
            
            # 4. Format the final output using pandas as requested
            df_data = pd.DataFrame(final_data)
            
            # The requested 'timestamp' conversion using pd.to_datetime
            df_data['timestamp'] = pd.to_datetime(df_data['startTime'], unit='ms')
            df_data = df_data.drop(columns=['startTime']) # Remove original 'startTime' field
            
            # Convert DataFrame to JSON format
            output_json = df_data.to_json(orient='records', date_format='iso', indent=4)
            
            print("\n--- ✅ Final Structured JSON Output ---")
            print(output_json)
            
            # In a real agent workflow, you'd feed this final JSON back to the LLM 
            # to validate or refine, but for a data task, the script takes over here.

    else:
        print("Agent failed to identify the necessary tool call.")

if __name__ == "__main__":
    run_ad_agent()