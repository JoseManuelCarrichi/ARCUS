from weather import mcp

def main():
    # Start the server
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
