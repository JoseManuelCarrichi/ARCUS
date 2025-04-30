from weather import mcp
from spotify import mcp_spotify

def main():
    # Start the server
    mcp.run(transport='stdio')
    mcp_spotify.run(transport='stdio')


if __name__ == "__main__":
    main()
