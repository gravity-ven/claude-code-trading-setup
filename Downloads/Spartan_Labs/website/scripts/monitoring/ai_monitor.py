#!/usr/bin/env python3
"""
SPARTAN RESEARCH STATION - HYBRID AI MONITORING SYSTEM

Primary: Claude Code (when available)
Fallback: Gemini CLI (when Claude unavailable)

Usage:
  python3 ai_monitor.py claude    # Use Claude Code for monitoring
  python3 ai_monitor.py gemini    # Use Gemini CLI for monitoring  
  python3 ai_monitor.py auto      # Auto-select best available AI
"""

import os
import sys
import json
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIMonitor:
    def __init__(self):
        self.monitoring_log = "logs/ai_monitoring.log"
        self.claude_available = None  # Will be determined at runtime
        self.gemini_available = None  # Will be determined at runtime
        self.ensure_log_directory()
        
    def ensure_log_directory(self):
        """Ensure logs directory exists"""
        Path("logs").mkdir(exist_ok=True)
        
    def log_event(self, level, message, ai_used=None):
        """Log monitoring events"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ai_tag = f"[{ai_used}]" if ai_used else ""
        log_entry = f"{timestamp} {level.upper()} {ai_tag} {message}"
        
        print(log_entry)  # Also output to console
        
        with open(self.monitoring_log, "a") as f:
            f.write(log_entry + "\n")
    
    def check_claude_availability(self):
        """Check if Claude Code is available"""
        if self.claude_available is not None:
            return self.claude_available
            
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                self.log_event("info", f"Claude Code available: {version}", "SYSTEM")
                self.claude_available = True
                return True
            else:
                self.log_event("warning", "Claude Code not found in PATH", "SYSTEM")
                self.claude_available = False
                return False
                
        except Exception as e:
            self.log_event("error", f"Claude Code check failed: {str(e)[:50]}", "SYSTEM")
            self.claude_available = False
            return False
    
    def check_gemini_availability(self):
        """Check if Gemini CLI is available"""
        if self.gemini_available is not None:
            return self.gemini_available
            
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                self.log_event("info", f"Gemini CLI available: {version}", "SYSTEM")
                self.gemini_available = True
                return True
            else:
                self.log_event("warning", "Gemini CLI not found in PATH", "SYSTEM")
                self.gemini_available = False
                return False
                
        except Exception as e:
            self.log_event("error", f"Gemini CLI check failed: {str(e)[:50]}", "SYSTEM")
            self.gemini_available = False
            return False
    
    def get_system_status(self):
        """Get current system status for AI analysis"""
        status_data = {}
        
        try:
            # Docker container status
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                services = [line.split() for line in lines[2:] if line.strip()]
                status_data["containers"] = [
                    {
                        "name": service[0],
                        "state": service[1] if len(service) > 1 else "unknown"
                    } for service in services if service
                ]
            
            # Check health endpoints
            endpoints = [
                ("Web Server", "http://localhost:8888/health"),
                ("Daily Planet API", "http://localhost:5000/health"),
                ("GARP API", "http://localhost:5003/health"),
                ("Swing API", "http://localhost:5002/health"),
                ("Correlation API", "http://localhost:5004/health")
            ]
            
            status_data["endpoints"] = []
            for name, url in endpoints:
                try:
                    response = subprocess.run(
                        ["curl", "-s", "--max-time", "5", url],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if response.returncode == 0 and "200" in response.stdout:
                        status_data["endpoints"].append({"name": name, "status": "healthy"})
                    else:
                        status_data["endpoints"].append({"name": name, "status": "unhealthy"})
                except:
                    status_data["endpoints"].append({"name": name, "status": "error"})
            
            # Recent log errors
            try:
                result = subprocess.run(
                    ["tail", "-n", "20", "server.log"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                errors = [line for line in result.stdout.split('\n') if 'ERROR' in line.upper()]
                status_data["recent_errors"] = errors[:5]  # Last 5 errors
            except:
                status_data["recent_errors"] = ["Unable to read logs"]
            
            # Disk and memory usage
            try:
                result = subprocess.run(["df", "-h"], capture_output=True, text=True, timeout=10)
                status_data["disk_usage"] = result.stdout
                
                result = subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=10)
                status_data["memory_usage"] = result.stdout
            except:
                status_data["disk_usage"] = "Unable to get disk usage"
                status_data["memory_usage"] = "Unable to get memory usage"
                
        except Exception as e:
            status_data["error"] = f"Status collection failed: {str(e)[:100]}"
            
        return status_data
    
    def use_claude_code(self, prompt, context=""):
        """Use Claude Code for AI monitoring with unified DNA"""
        if not self.check_claude_availability():
            return None
            
        try:
            # Import DNA bridge for unified prompt
            from ai_dna_bridge import AIDNABridge
            bridge = AIDNABridge()
            
            # Get system status
            system_status = self.get_system_status()
            
            # Use unified prompt from DNA bridge
            full_prompt = bridge.get_claude_prompt_wrapper(
                json.dumps(system_status, indent=2, default=str),
                context
            )
            
            # Write prompt to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(full_prompt)
                temp_file = f.name
            
            try:
                # Run Claude Code
                result = subprocess.run(
                    ["claude"],
                    input=full_prompt,
                    text=True,
                    capture_output=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    self.log_event("info", "Claude Code analysis completed", "CLAUDE")
                    return result.stdout.strip()
                else:
                    error_msg = result.stderr.strip() if result.stderr else "Claude execution failed"
                    self.log_event("error", f"Claude Code failed: {error_msg[:50]}", "CLAUDE")
                    return None
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except Exception as e:
            self.log_event("error", f"Claude Code exception: {str(e)[:50]}", "CLAUDE")
            return None
    
    def use_gemini_cli(self, prompt, context=""):
        """Use Gemini CLI with unified DNA"""
        if not self.check_gemini_availability():
            return None
            
        try:
            # Import DNA bridge for unified prompt
            from ai_dna_bridge import AIDNABridge
            bridge = AIDNABridge()
            
            # Get system status
            system_status = self.get_system_status()
            
            # Use unified prompt from DNA bridge
            full_prompt = bridge.get_gemini_prompt_wrapper(
                json.dumps(system_status, indent=2, default=str),
                context
            )
            
            # Run Gemini CLI
            result = subprocess.run(
                ["gemini"],
                input=full_prompt,
                text=True,
                capture_output=True,
                timeout=45
            )
            
            if result.returncode == 0:
                self.log_event("info", "Gemini CLI analysis completed", "GEMINI")
                return result.stdout.strip()
            else:
                error_msg = result.stderr.strip() if result.stderr else "Gemini execution failed"
                self.log_event("error", f"Gemini CLI failed: {error_msg[:50]}", "GEMINI")
                return None
                
        except Exception as e:
            self.log_event("error", f"Gemini CLI exception: {str(e)[:50]}", "GEMINI")
            return None
    
    def monitor_with_ai(self, ai_preference=None):
        """Main monitoring function with AI fallback"""
        
        # Determine strategy
        if ai_preference == "claude":
            strategy = ["claude"]
        elif ai_preference == "gemini": 
            strategy = ["gemini"]
        elif ai_preference == "auto":
            strategy = ["claude", "gemini"]  # Try Claude first, then Gemini
        else:
            strategy = ["claude", "gemini"]  # Default to auto
            
        self.log_event("info", f"Starting AI monitoring with strategy: {strategy}", "SYSTEM")
        
        # Get system status
        system_status = self.get_system_status()
        containers_down = sum(1 for c in system_status.get("containers", []) 
                            if c.get("state", "").lower() in ["down", "exited", "restarting"])
        endpoints_down = sum(1 for e in system_status.get("endpoints", [])
                           if e.get("status") != "healthy")
        
        # Create monitoring prompt based on issues found
        if containers_down > 0 or endpoints_down > 0:
            prompt = f"URGENT: {containers_down} containers down, {endpoints_down} endpoints unhealthy. Diagnose issues and provide immediate fix actions."
            context = "URGENT_HEALTH_CHECK"
        else:
            prompt = "Routine health check. Assess system performance and identify any optimization opportunities."
            context = "ROUTINE_MONITORING"
        
        # Try each AI in the strategy
        for ai in strategy:
            if ai == "claude":
                response = self.use_claude_code(prompt, context)
                if response:
                    return {"ai": "Claude", "response": response, "status": "success"}
                    
            elif ai == "gemini":
                response = self.use_gemini_cli(prompt, context)  
                if response:
                    return {"ai": "Gemini", "response": response, "status": "success"}
        
        # All AIs failed
        return {"ai": "None", "response": "No AI available for monitoring", "status": "failed"}
    
    def interactive_monitoring(self, ai_preference="auto"):
        """Interactive monitoring session"""
        print("🤖 Spartan Research Station - AI Monitoring System")
        print("=" * 60)
        
        # Check availability
        claude_available = self.check_claude_availability()
        gemini_available = self.check_gemini_availability()
        
        print(f"🔍 AI Status: Claude {'✅' if claude_available else '❌'} | Gemini {'✅' if gemini_available else '❌'}")
        print(f"🎯 Strategy: {ai_preference.upper()}")
        
        if ai_preference == "claude" and not claude_available:
            print("❌ Claude Code not available. Use 'python3 ai_monitor.py gemini' or 'auto'")
            return
        if ai_preference == "gemini" and not gemini_available:
            print("❌ Gemini CLI not available. Install or use 'python3 ai_monitor.py claude' or 'auto'")
            return
        
        print("\n🔄 Running AI analysis...")
        result = self.monitor_with_ai(ai_preference)
        
        if result["status"] == "success":
            print(f"\n🤖 {result['ai']} Analysis:")
            print("-" * 40)
            print(result["response"])
            print("-" * 40)
        else:
            print(f"\n❌ AI Monitoring Failed: {result['response']}")
            print("💡 Suggestions:")
            print("   1. Install Claude Code: https://claude.ai/code")
            print("   2. Install Gemini CLI: gem install google-generative-ai")
            print("   3. Check AI installation and PATH")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Spartan AI Monitoring System")
    parser.add_argument("ai", choices=["claude", "gemini", "auto"], 
                       default="auto", nargs="?",
                       help="AI to use for monitoring (default: auto)")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Start interactive monitoring")
    
    args = parser.parse_args()
    
    monitor = AIMonitor()
    
    if args.interactive:
        monitor.interactive_monitoring(args.ai)
    else:
        # Single monitoring run
        result = monitor.monitor_with_ai(args.ai)
        
        if result["status"] == "success":
            print(f"✅ {result['ai']} Monitoring Complete")
            print(result["response"])
        else:
            print(f"❌ AI Monitoring Failed: {result['response']}")
            exit(1)


if __name__ == "__main__":
    main()
