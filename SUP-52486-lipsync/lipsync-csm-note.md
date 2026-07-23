# Why lip-sync can slip during playback — a plain-language note

Sometimes a viewer sees the audio drift slightly out of sync with the video, even when the video file itself is perfectly fine. When that happens, the cause is usually **not** the content — it's the conditions in which the video is being watched.

Two everyday things can do it:

**The network.** Online video is streamed in small pieces and its quality adapts to the connection. On an unstable or congested connection, the player is constantly adjusting and occasionally re-buffering. Each of those moments is a chance for the sound and picture to line back up a touch imperfectly — and over a long video, small slips can add up.

**The device.** If the viewer's computer, browser, or phone is under load, it may not render every video frame on time while the audio keeps playing smoothly. The result is a picture that lags slightly behind the sound.

The tell-tale sign of both: the problem is **inconsistent** — worse on a poor connection or a busy device, and often fine on a good one. That's also why our team, testing on strong connections and fast machines, may not see what the customer sees.

**What this means for the customer:** the same file can play perfectly for one viewer and slip for another. It's worth checking their connection quality and trying a different device or browser before assuming the video is at fault.
