"""
Launch script for the AI Research Agent with Chatbot
Starts both the API server and Streamlit chat interface
"""
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting API server...")
    api_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--reload", 
        "--port", "8000",
        "--host", "0.0.0.0"
    ])
    return api_process

def start_streamlit_chatbot():
    """Start the Streamlit chatbot interface"""
    print("🤖 Starting Streamlit chatbot interface...")
    streamlit_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", 
        "run", 
        "streamlit_chatbot.py",
        "--server.port", "8502",
        "--server.address", "0.0.0.0"
    ])
    return streamlit_process

def start_streamlit_main():
    """Start the main Streamlit interface"""
    print("📊 Starting main Streamlit interface...")
    streamlit_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", 
        "run", 
        "streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])
    return streamlit_process

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        "fastapi", "uvicorn", "streamlit", "requests", 
        "pydantic", "langchain-core", "supabase"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("📦 Install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def main():
    """Main launcher function"""
    print("🔬 AI Research Agent Launcher")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    print("\nChoose launch mode:")
    print("1. 🤖 Chatbot interface only (recommended)")
    print("2. 📊 Main interface only")
    print("3. 🚀 Both interfaces")
    print("4. 🔧 API server only")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    processes = []
    
    try:
        # Always start API server
        api_process = start_api_server()
        processes.append(("API Server", api_process))
        
        # Wait for API to start
        print("⏳ Waiting for API server to start...")
        time.sleep(3)
        
        if choice == "1":
            # Chatbot only
            chatbot_process = start_streamlit_chatbot()
            processes.append(("Chatbot", chatbot_process))
            
            print("\n✅ Services started successfully!")
            print("🤖 Chatbot interface: http://localhost:8502")
            print("🔧 API documentation: http://localhost:8000/docs")
            
            # Open chatbot in browser
            time.sleep(2)
            webbrowser.open("http://localhost:8502")
            
        elif choice == "2":
            # Main interface only
            main_process = start_streamlit_main()
            processes.append(("Main Interface", main_process))
            
            print("\n✅ Services started successfully!")
            print("📊 Main interface: http://localhost:8501")
            print("🔧 API documentation: http://localhost:8000/docs")
            
            # Open main interface in browser
            time.sleep(2)
            webbrowser.open("http://localhost:8501")
            
        elif choice == "3":
            # Both interfaces
            chatbot_process = start_streamlit_chatbot()
            main_process = start_streamlit_main()
            processes.append(("Chatbot", chatbot_process))
            processes.append(("Main Interface", main_process))
            
            print("\n✅ All services started successfully!")
            print("🤖 Chatbot interface: http://localhost:8502")
            print("📊 Main interface: http://localhost:8501")
            print("🔧 API documentation: http://localhost:8000/docs")
            
            # Open both interfaces
            time.sleep(2)
            webbrowser.open("http://localhost:8502")
            time.sleep(1)
            webbrowser.open("http://localhost:8501")
            
        elif choice == "4":
            # API only
            print("\n✅ API server started successfully!")
            print("🔧 API documentation: http://localhost:8000/docs")
            print("🧪 Test endpoints: http://localhost:8000/health")
            
            # Open API docs
            time.sleep(2)
            webbrowser.open("http://localhost:8000/docs")
            
        else:
            print("❌ Invalid choice")
            api_process.terminate()
            sys.exit(1)
        
        print("\n" + "=" * 40)
        print("🎉 All services are running!")
        print("Press Ctrl+C to stop all services")
        print("=" * 40)
        
        # Wait for processes
        while True:
            time.sleep(1)
            # Check if any process has died
            for name, process in processes:
                if process.poll() is not None:
                    print(f"❌ {name} process stopped unexpectedly")
                    break
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for name, process in processes:
            print(f"   Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("✅ All services stopped")
    
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        for name, process in processes:
            process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()
