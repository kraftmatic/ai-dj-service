"""
Setup script for AI DJ Radio Station
Helps verify dependencies and setup
"""
import subprocess
import sys
import importlib
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is sufficient"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_requirements():
    """Install Python requirements"""
    print("\n📦 Installing Python packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python packages installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python packages")
        return False

def check_dependencies():
    """Check if all required packages are available"""
    required_packages = [
        "pydub",
        "mutagen", 
        "edge_tts",
        "requests",
        "pygame"
    ]
    
    print("\n🔍 Checking dependencies...")
    all_good = True
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - not found")
            all_good = False
    
    return all_good

def check_ffmpeg():
    """Check if FFmpeg is available"""
    print("\n🎵 Checking FFmpeg...")
    try:
        result = subprocess.run(["ffmpeg", "-version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg is installed")
            return True
        else:
            print("❌ FFmpeg found but not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ FFmpeg not found")
        print("   Please install FFmpeg:")
        print("   - Windows: Download from https://ffmpeg.org/ or use 'choco install ffmpeg'")
        print("   - Add FFmpeg to your system PATH")
        return False

def check_ollama():
    """Check if Ollama is running and has the required model"""
    print("\n🤖 Checking Ollama...")
    try:
        import requests
        
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            
            # Check for llamusic model
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            
            if any("llamusic" in name for name in model_names):
                print("✅ llamusic model found")
                return True
            else:
                print("❌ llamusic/llamusic:latest model not found")
                print("   Please install the model: ollama pull llamusic/llamusic:latest")
                return False
        else:
            print("❌ Ollama is not responding properly")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama")
        print("   Please start Ollama: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

def check_music_folders():
    """Check if music folders exist and contain files"""
    print("\n🎼 Checking music folders...")
    
    music_folder = Path("music")
    bg_music_folder = Path("background music")
    
    issues = []
    
    if not music_folder.exists():
        issues.append("music/ folder not found")
    else:
        mp3_files = list(music_folder.glob("*.mp3"))
        if not mp3_files:
            issues.append("No MP3 files found in music/ folder")
        else:
            print(f"✅ Found {len(mp3_files)} MP3 files in music/")
    
    if not bg_music_folder.exists():
        issues.append("background music/ folder not found")
    else:
        bg_mp3_files = list(bg_music_folder.glob("*.mp3"))
        if not bg_mp3_files:
            issues.append("No MP3 files found in background music/ folder")
        else:
            print(f"✅ Found {len(bg_mp3_files)} background music files")
    
    if issues:
        for issue in issues:
            print(f"❌ {issue}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🎵 AI DJ Radio Station Setup 🎵")
    print("=" * 40)
    
    all_checks = [
        check_python_version(),
        install_requirements(),
        check_dependencies(),
        check_ffmpeg(),
        check_ollama(),
        check_music_folders()
    ]
    
    print("\n" + "=" * 40)
    
    if all(all_checks):
        print("🎉 Setup complete! Everything looks good.")
        print("\nTo start the AI DJ, run:")
        print("   python main.py")
    else:
        print("⚠️  Setup incomplete. Please fix the issues above.")
        print("\nSome components may still work, but full functionality requires all checks to pass.")

if __name__ == "__main__":
    main()
