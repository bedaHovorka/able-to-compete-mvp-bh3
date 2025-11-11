#!/bin/bash

# AbleToCompete Demo Video Recording Script
# This script helps you record the demo using FFmpeg

echo "======================================"
echo "AbleToCompete MVP - Demo Recording"
echo "======================================"
echo ""

# Get screen resolution
RESOLUTION=$(xdpyinfo | awk '/dimensions/{print $2}')
echo "Detected screen resolution: $RESOLUTION"
echo ""

# Recording options
echo "Recording Options:"
echo "1. Full screen (${RESOLUTION})"
echo "2. 1920x1080 (recommended)"
echo "3. 1280x720 (smaller file)"
echo ""
read -p "Choose option (1-3): " choice

case $choice in
    1)
        VIDEO_SIZE=$RESOLUTION
        ;;
    2)
        VIDEO_SIZE="1920x1080"
        ;;
    3)
        VIDEO_SIZE="1280x720"
        ;;
    *)
        echo "Invalid choice. Using 1920x1080"
        VIDEO_SIZE="1920x1080"
        ;;
esac

# Output filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="AbleToCompete_Demo_${TIMESTAMP}.mp4"

echo ""
echo "======================================"
echo "Recording Configuration:"
echo "  Resolution: $VIDEO_SIZE"
echo "  Frame Rate: 30 fps"
echo "  Output: $OUTPUT_FILE"
echo "======================================"
echo ""
echo "INSTRUCTIONS:"
echo "1. Position your browser window properly"
echo "2. Close unnecessary windows"
echo "3. Set browser to 100% zoom"
echo "4. Review DEMO_SCRIPT.md for guidance"
echo ""
echo "Press ENTER to start recording in 5 seconds..."
read

echo "Starting in 5..."
sleep 1
echo "4..."
sleep 1
echo "3..."
sleep 1
echo "2..."
sleep 1
echo "1..."
sleep 1
echo ""
echo "🔴 RECORDING! Press Ctrl+C to stop."
echo ""

# Record with FFmpeg
ffmpeg -video_size $VIDEO_SIZE \
       -framerate 30 \
       -f x11grab \
       -i :0.0 \
       -c:v libx264 \
       -preset ultrafast \
       -crf 23 \
       -pix_fmt yuv420p \
       "$OUTPUT_FILE"

echo ""
echo "======================================"
echo "✅ Recording saved to: $OUTPUT_FILE"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Review the video"
echo "2. If needed, re-record with better quality:"
echo "   - Use OBS Studio for better control"
echo "   - Or use: sudo dnf install simplescreenrecorder"
echo ""
