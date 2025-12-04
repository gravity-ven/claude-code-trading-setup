# Manual Installation for Computer Use Bridge

Due to security restrictions, I cannot write files outside of the current project directory or run commands that require `sudo` permissions.

I have created all the necessary files for the Computer Use Bridge in the `.claude` directory within this project. Please follow these steps to complete the installation.

## 1. Move the Files

Move the `.claude` directory from this project to your home directory:

```bash
mv .claude ~/
```

## 2. Run the Installation Script

The setup script will install system dependencies (like `xvfb` and `scrot`), create a Python virtual environment, and install the required packages.

```bash
# Navigate to the script directory
cd ~/.claude/data_agents/computer_use_bridge

# Make the script executable
chmod +x setup_bridge.sh

# Run the installer
# You will be prompted for your password for 'sudo' commands.
./setup_bridge.sh install
```

## 3. Add Your API Key

The installation script will create a `.env` file in `~/.claude/data_agents/`. You need to edit this file to add your Anthropic API key.

```bash
nano ~/.claude/data_agents/.env
```

Find the line `ANTHROPIC_API_KEY=your_api_key_here` and replace `your_api_key_here` with your actual key.

## 4. Gemini and Droid CLI Integration

The setup script configures the bridge for the `claude` command-line tool by creating a file at `~/.config/claude/mcp_servers.json`.

For Gemini CLI and Droid CLI, you will need to find the equivalent configuration file for MCP (Model Context Protocol) servers.

I have created example configuration files for you. You may need to adapt them to the correct location and format for Gemini and Droid CLIs.

- **For Gemini CLI:** I have created `gemini_mcp_servers.json`. If Gemini CLI uses a config file, you may need to copy it to a location like `~/.config/gemini/mcp_servers.json`.

- **For Droid CLI:** I have created `droid_mcp_servers.json`. If Droid CLI uses a config file, you may need to copy it to a location like `~/.config/droid/mcp_servers.json`.

Please check the documentation for your specific CLI tools to find the correct location for MCP server configuration.

The contents of the generated JSON files are based on the Claude setup. You can find them in the `.claude` directory you moved.

## 5. Restart Your Terminals

For the changes to take effect, especially the `DISPLAY` environment variable and the MCP server loading, you should restart your terminal or source your `.bashrc` file:

```bash
source ~/.bashrc
```

After these steps, the Computer Use Bridge should be available as a tool in your CLI.
