from mcp.server.fastmcp import FastMCP
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP server
mcp_spotify = FastMCP("Spotify Controller")

def get_spotify_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id= os.getenv("CLIENT_ID"),
        client_secret= os.getenv("CLIENT_SECRET"),
        #scope= os.getenv("SCOPE"),
        scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-recently-played streaming playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private user-library-modify user-library-read user-library-modify",
        cache_path= os.getenv("CACHE_PATH"),
        redirect_uri="http://127.0.0.1:3000"
    ))

sp = get_spotify_client()

@mcp.tool()
async def get_devices_available() -> str:
    """Get the device ID of the active device on Spotify. Is necesary to play a track or start playback"""
    try:
        devices = sp.devices()
        if devices['devices']:
            return devices['devices'][0]['id']
        else:
            return "No devices found. Please open the Spotify app."
    except Exception as e:
        return f"Error retrieving devices: {e}"


@mcp.tool()
async def start_playback():
    """Start or resume playing music on Spotify"""
    try:
        devices = sp.devices()
        if devices['devices']:
            device = devices['devices'][0]
            if device['is_active']:
                sp.start_playback()
                return "Playback started."
            else:
                device_id = device['id']
                sp.start_playback(device_id=device_id)
                return f"Playback started on device: {device['name']}."
        else:
            return "No devices found. Please open the Spotify app." 

    except Exception as e:
        return f"Error retrieving devices: {e}"


@mcp.tool()
async def pause_playback():
    """Pause the current playback on Spotify"""
    try:
        sp.pause_playback()
        return "Playback paused."
    except Exception as e:
        return f"No active playback found"


@mcp.tool()
async def next_track():
    """Skip to the next track in the current playlist"""
    try:
        sp.next_track()
        return "Skipped to the next track."
    except Exception as e:
        return f"Error skipping track: {e}"

@mcp.tool()
async def previous_track():
    """Go back to the previous track in the current playlist"""
    try:
        sp.previous_track()
        return "Went back to the previous track."
    except Exception as e:
        return f"Error going back to previous track: {e}"

@mcp.tool()
async def get_current_track():
    """Get the currently playing track"""
    current = sp.current_playback()
    if current and current['is_playing']:
        track = current['item']
        track_info = {
            'name': track['name'],
            'id': track['id'],
            'artist': ', '.join([artist['name'] for artist in track['artists']]),
            'album': track['album']['name'],
            'duration_ms': track['duration_ms'],
            'progress_ms': current['progress_ms']
        }
        return track_info
    else:
        return "No track is currently playing."

@mcp.tool()
async def set_volume(volume: int):
    """Set the volume level (0-100)

    Args:
        volume (int): Volume level to set (0-100), if the volume level is lower than 0, set the volume to 0; if is higher than 100, set the volume to 100   
    """
    if 0 <= volume <= 100:
        sp.volume(volume)
        return f"Volume set to {volume}%."
    else:
        return "Volume must be between 0 and 100."


@mcp.tool()
async def add_to_library(id: str):
    """Add a track to the user's library

    Args:
        id (str): Spotify ID of the track to add, its posssible that need to get the current track first
    """
    try:
        sp.current_user_saved_tracks_add([id])
        return f"Track {id} added to your library."
    except Exception as e:
        return f"Error adding track to library: {e}"

@mcp.tool()
async def reproduce_a_specific_track(uri: str, device_id: str = None):
    """Play a specific track by its Spotify URL.

    Args:
        uri (str): Spotify URI of the track to play, its possible that need to search the track first. 
        device (str): Spotify device ID to play the track on, if not specified, it will play on the first available device.
    """
    try:
        if device_id:
            sp.start_playback(device_id=device_id, uris=[uri])
            return f"Playing track with URI: {uri} on device: {device_id}."
        else:
            devices = sp.devices()
            if devices['devices']:
                device = devices['devices'][0]
                if device['is_active']:
                    sp.start_playback(uris=[uri])
                    return f"Playing track with URI: {uri}."
                else:
                    # If the first device is not active, set it as the active device and start playback
                    device_id = device['id']
                    sp.start_playback(device_id=device_id)
                    return f"Playback started on device: {device['name']}."
            else:
                return "No devices found to play the track. Please open the Spotify app."
    except Exception as e:
        return f"Error playing track: {e}"

@mcp.tool()
async def search_track(query: str):
    """ Search for a track and play it

    Args:
        query (str): Search query for the track, can be a song and artist name, or just a song name
    """
    results = sp.search(q=query, type='track,artist', limit=3)
    if results['tracks']['items']:
        # add all the tracks to a list
        tracks  = []
        for track in results['tracks']['items']:
            tracks.append({
                'name': track['name'],
                'id': track['id'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'uri': track['uri']
            })

        return tracks
    else:
        return "No tracks found for the given query."

    
@mcp.tool()
async def search_artist(query: str, device_id: str):
    """Search for an artist and play their top tracks. 

    Args:
        query (str): Search query for the artist, the user can request music from a specific artist.
        device (str): Spotify device ID to play the track on"""
    try:
        results = sp.search(q=query, type='artist', limit=3)
        if not results['artists']['items']:
            return "No artist found for the given query."
        
        artist_id = results['artists']['items'][0]['id']
        top_tracks = sp.artist_top_tracks(artist_id)

        if not top_tracks['tracks']:
            return "No top tracks found for the given artist."
        
        tracks_uris = [track['uri'] for track in top_tracks['tracks']]
        sp.start_playback(uris=tracks_uris, device_id=device_id)
        return f"Playing top tracks of {query}."


    except Exception as e:
        return f"Error searching for artist: {e}"
    
# Function to reproduce the library of the user
@mcp.tool()
async def reproduce_library(device_id: str, shuffle: bool = False):
    """Play the user's library when the user request play his music.

    Args:
        device (str): Spotify device ID to play the library on. Its possible that you need to get the device id first.
        shuffle (bool): If True, shuffle the library. Default is False. 
    """
    try:
        saved_tracks = sp.current_user_saved_tracks(limit=50)
        if not saved_tracks['items']:
            return "No tracks found in your library."
        
        tracks_uris = [track['track']['uri'] for track in saved_tracks['items']]
        sp.shuffle(shuffle)
        sp.start_playback(uris=tracks_uris, device_id=device_id)
        return f"Playing your library on your device."
    except Exception as e:
        return f"Error playing library: {e}"
# Function to search for an album and play it

# function to search for a playlist and play it
