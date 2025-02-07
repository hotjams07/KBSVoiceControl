import sys
import site
import subprocess
import os
import requests
import zipfile
from tqdm import tqdm
import shutil
import pyaudio
from vosk import Model, KaldiRecognizer

def check_installation():
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.executable}")
    print("\nInstalled packages:")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error getting package list: {e}")

def download_model():
    """Download and extract the Vosk model"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "vosk-model-small-en-us")
    zip_path = os.path.join(current_dir, "vosk-model-small-en-us-0.22.zip")
    
    # Using the official model repository with newer version
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.22.zip"

    try:
        print("Downloading Vosk model...")
        session = requests.Session()
        
        # Minimal headers
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        
        # Try different download methods
        try:
            # Method 1: Direct download with requests
            response = session.get(model_url, headers=headers, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(zip_path, 'wb') as f, tqdm(
                desc="Downloading",
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        size = f.write(chunk)
                        pbar.update(size)
                        
        except Exception as e:
            print(f"Direct download failed ({str(e)}), trying alternative method...")
            # Method 2: Using curl command
            subprocess.run([
                "curl",
                "-L",
                "-o", zip_path,
                model_url
            ], check=True)
        
        # Verify the downloaded file
        if not os.path.exists(zip_path):
            raise Exception("Download failed - file not found")
            
        if not zipfile.is_zipfile(zip_path):
            raise Exception("Downloaded file is not a valid zip file")
            
        print("\nExtracting model...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract to temporary directory
            temp_dir = os.path.join(current_dir, "temp_extract")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            # List and verify contents before extraction
            contents = zip_ref.namelist()
            required_files = ['am/final.mdl', 'conf/mfcc.conf', 'graph/phones.txt']
            for req_file in required_files:
                if not any(name.endswith(req_file) for name in contents):
                    raise Exception(f"Model archive missing required file: {req_file}")
            
            # Extract files
            zip_ref.extractall(temp_dir)
            
            # Find the model directory
            model_dir = None
            for item in os.listdir(temp_dir):
                if os.path.isdir(os.path.join(temp_dir, item)) and all(
                    os.path.exists(os.path.join(temp_dir, item, f)) 
                    for f in ['am/final.mdl', 'conf/mfcc.conf']
                ):
                    model_dir = item
                    break
                    
            if not model_dir:
                raise Exception("Could not find valid model directory in extracted files")
                
            # Move to final location
            if os.path.exists(model_path):
                shutil.rmtree(model_path)
            shutil.move(os.path.join(temp_dir, model_dir), model_path)
            
            # Clean up
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            
        print("Model downloaded and extracted successfully")
        return True
            
    except Exception as e:
        print(f"Error: {e}")
        cleanup()
        return False

def cleanup():
    """Clean up any partial downloads or extractions"""
    model_path = "vosk-model-small-en-us"
    zip_path = "vosk-model-small-en-us-0.22.zip"
    
    if os.path.exists(model_path):
        shutil.rmtree(model_path)
    if os.path.exists(zip_path):
        os.remove(zip_path)

def verify_model_structure():
    """Verify the model directory structure"""
    model_path = "vosk-model-small-en-us"
    required_files = [
        'am/final.mdl',
        'conf/mfcc.conf',
        'graph/phones.txt',
        'ivector/final.dubm',
        'ivector/final.ie',
        'ivector/final.mat',
        'ivector/global_cmvn.stats'
    ]
    
    print("\nVerifying model structure...")
    all_files_present = True
    for file_path in required_files:
        full_path = os.path.join(model_path, file_path)
        if not os.path.exists(full_path):
            print(f"[MISSING] {file_path}")
            all_files_present = False
        else:
            print(f"[OK] {file_path}")
    return all_files_present

def test_vosk_model():
    try:
        from vosk import Model, KaldiRecognizer
        print("[OK] Vosk imported successfully")
        
        model_path = "vosk-model-small-en-us"
        
        # Check if model exists and download if needed
        if not os.path.exists(model_path) or not verify_model_structure():
            print("\nModel not found or incomplete. Downloading...")
            cleanup()  # Clean up any partial downloads
            if not download_model():
                return False
        
        # Verify model structure
        if not verify_model_structure():
            print("[ERROR] Model verification failed after download")
            return False
            
        # Try to load the model
        print("\nTrying to load Vosk model...")
        model = Model(model_path)
        print("[OK] Model loaded successfully")
        return True
        
    except ImportError as e:
        print(f"[ERROR] Error importing vosk: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error during model test: {e}")
        cleanup()  # Clean up on error
        return False

def clear_terminal():
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For Mac and Linux
    else:
        os.system('clear')

def setup_recognition():
    """Setup the voice recognition system"""
    model_path = "vosk-model-small-en-us"
    if not os.path.exists(model_path):
        print("Model not found. Please run setup first.")
        return None, None
    
    # Initialize voice recognition
    model = Model(model_path)
    
    # Setup audio input
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8000
    )
    
    return KaldiRecognizer(model, 16000), stream

def listen_continuous():
    """Continuously listen and print recognized text"""
    try:
        recognizer, stream = setup_recognition()
        if not recognizer:
            return
        
        print("\nListening... (Ctrl+C to exit)")
        
        while True:
            data = stream.read(4000, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                # Parse the JSON result to get just the text
                text = eval(result)["text"]
                if text.strip():  # Only print if there's actual text
                    print(f"Heard: {text}")
                    
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()

if __name__ == "__main__":
    clear_terminal()
    print("Checking Python environment...\n")
    check_installation()
    
    print("\nTesting Vosk installation and model...")
    success = test_vosk_model()
    
    if success:
        print("\n✓ All tests passed! Vosk is ready to use.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

    print("\nStarting continuous voice recognition...")
    listen_continuous() 