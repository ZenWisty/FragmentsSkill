import subprocess
import requests
import json
import os
from pathlib import Path
import wave
import riva.client
from riva.client import ASRService, RecognitionConfig

# ================= Configuration =================
NVIDIA_API_KEY = os.getenv("NVIDIA_RIVA_KEY")                      

# NVIDIA NIM Endpoint for Whisper Large V3
MODEL = "nvidia/whisper-large-v3"

VOICE_FILE = "/storage/emulated/0/MyObsidianVaults/voice_db/20260401_002526.m4a"
#FILE_NAME = "20260401_002526.m4a"
CLI_BASEDIR = "/data/data/com.termux/files/home/storage/shared/Sounds/"  #"/data/data/com.termux/files/home/storage/shared/MyObsidianVaults/voice_db/"
#CLI_FFPEMG_INPUT = CLI_BASEDIR + FILE_NAME
#CLI_FFPEMG_OUTPUT = CLI_BASEDIR + FILE_NAME.replace('.m4a', '.wav')
options = [
        ('grpc.max_receive_essage_length', 64*1024*1024),
        ('grpc.max_send_message_length', 64*1024*1024),
        ]
# =================================================

# 1.setup auth
auth = riva.client.Auth(
        use_ssl=True,
        uri="grpc.nvcf.nvidia.com:443",
        metadata_args=[
            ["function-id", "b702f636-f60c-4a3d-a6f4-f3568c13bd7d"],
            ["authorization", "Bearer "+NVIDIA_API_KEY]
        ],
        options=options,
    )
asr_service = ASRService(auth)

def termux_api(command, input_data=None):
    try:
        process = subprocess.run(
            command,
            input=input_data,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return process.stdout.strip()
    except:
        return None

def show_toast(message):
    termux_api(["termux-toast", "-s", message])

def call_system_recorder():
    print("calling the phone record program...")
    # use am.start
    subprocess.run(["am","start","-a","android.provider.MediaStore.RECORD_SOUND"], capture_output=True)
    input("please record and save, then press enter here in CLI ...")
    potential_paths = [
            "/storage/emulated/0/Sounds",
            ]

    for path in potential_paths:
        if os.path.exists(path):
            files = [os.path.join(path, f) for f in os.listdir(path) if '.backup' not in f]
            if files:
                # time order
                latest_file = max(files, key=os.path.getmtime)
                return latest_file
    return None

def main():
    #if not os.path.exists(VOICE_FILE):
    #    show_toast(f"Error: File not found\n{VOICE_FILE}")
    #    return
    VOICE_FILE = call_system_recorder()
    if not VOICE_FILE:
        show_toast(f"Error:VoiceFile not found")
        return

    show_toast("NVIDIA NIM is transcribing...")

    try:
        # new voice FILE so change CLI_FFPEMG_INPUT & OUTPUT
        global CLI_BASEDIR
        CLI_FFPEMG_INPUT = os.path.join(CLI_BASEDIR, os.path.basename(VOICE_FILE))
        CLI_FFPEMG_OUTPUT = os.path.splitext(CLI_FFPEMG_INPUT)[0]+ '.wav'
        subprocess.run([
            "ffmpeg", "-y", "-i", CLI_FFPEMG_INPUT,
            "-ar", "16000", "-ac", "1", CLI_FFPEMG_OUTPUT
            ], check=True, capture_output=True)

        P_voice_file=Path(os.path.splitext(VOICE_FILE)[0] + '.wav')
        P_voice_file.expanduser()
        # with wave.open(VOICE_FILE.replace('.m4a','.wav'), "rb") as wav_f:
        with P_voice_file.open('rb') as wav_f:
            #audio_bytes = wav_f.readframes(wav_f.getnframes())
            audio_bytes = wav_f.read()

            # Note: Some NIM versions prefer post without 'v1' in path if self-hosted, 
            # but the Hosted Cloud version uses the URL above.
            config = RecognitionConfig(language_code="zh-CN",
                                       model="", #=MODEL
                                       max_alternatives=1,
                                       profanity_filter=False,
                                       enable_automatic_punctuation=True,
                                       verbatim_transcripts=True,
                                       enable_word_time_offsets=True
                                       )
            response = asr_service.offline_recognize(audio_bytes, config)
        
        transcript = response.results[0].alternatives[0].transcript
        print(transcript)
    except Exception as e:
        show_toast(f"NVIDIA API Error: {str(e)}")
        return

    if not transcript:
        show_toast("Recognition failed or empty result")
        return

    # Dialog for editing
    dialog_res = termux_api([
        "termux-dialog", "text", 
        "-t", "Confirm Transcription (NVIDIA NIM)",
        "-i", transcript
    ])

    if dialog_res:
        data = json.loads(dialog_res)
        if data.get("code") == -1:
            final_text = data.get("text", "").strip()
            termux_api(["termux-clipboard-set"], input_data=final_text)
            show_toast("✅ Copied to clipboard")

if __name__ == "__main__":
    main()
