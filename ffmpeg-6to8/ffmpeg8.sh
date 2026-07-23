#!/bin/bash
if [[ "$(dpkg --print-architecture)" == "arm64" ]]; then 
	/web/content/shared/bin/ffmpeg-8.1.1-arm-bin/ffmpeg.sh "$@"; 
else 
	/web/content/shared/bin/ffmpeg-8.1.1-x86-bin/ffmpeg.sh "$@"; 
fi

