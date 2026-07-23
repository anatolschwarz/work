# Archived — DIY v1 (mediapipe + cross-correlation)

First lip-sync estimator: mouth-openness (mediapipe FaceLandmarker) vs audio
RMS envelope, cross-correlated per window. Worked mechanically but too noisy to
lock on the 540p lecture footage (max confidence ~0.24). Superseded by the
SyncNet approach.

venv (external, left in place): `/home/anatolschwartz/.venvs/sup-52486-lipsync`
