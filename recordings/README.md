# Flight Video Recordings

This directory contains video recordings captured during drone flights.

## File Naming Convention

Videos are automatically named using the following pattern:
```
flight_{flight_id}_{timestamp}.mp4
```

Example: `flight_37_2026-01-13_14-30-00.mp4`

## Video Details

- **Source**: RTP stream from drone camera (/dev/video13)
- **Format**: MP4 (H.264 video codec)
- **Resolution**: 640x480
- **Frame Rate**: 15 fps
- **Encoding**: x264 (ultrafast preset, zerolatency tune)

## Storage

- Videos are stored locally on the PC
- Path is saved in the database `flights` table (`video_path` column)
- Videos can be viewed using any standard video player (VLC, Windows Media Player, etc.)

## Notes

- Recording starts automatically when a flight begins
- Recording stops automatically when the flight ends or is aborted
- Both detection and recording read from the same RTP stream (no camera conflict)
- If recording fails to start, the flight will continue with detection only
