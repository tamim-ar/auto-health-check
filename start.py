import subprocess
import sys
import time
import os

def start_service(command, name):
    try:
        process = subprocess.Popen(command, shell=True)
        print(f"✅ Started {name}")
        return process
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None

def main():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Start test services
    processes = []
    
    # Start Flask test app
    flask_proc = start_service("python test_flask_app.py", "Flask Test App")
    if flask_proc:
        processes.append(flask_proc)
    
    # Start Node.js test app
    node_proc = start_service("node test_node_app.js", "Node.js Test App")
    if node_proc:
        processes.append(node_proc)
    
    time.sleep(2)  # Wait for services to start
    
    # Start health checker
    checker_proc = start_service("python health_check.py", "Health Checker")
    if checker_proc:
        processes.append(checker_proc)

    try:
        print("\n🚀 All services started! Press Ctrl+C to stop everything...\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for proc in processes:
            proc.terminate()
        
        print("✨ Cleanup complete!")

if __name__ == "__main__":
    main()
