# VRChat-OSC-Video

VRChat OSC Video is a simple method for sending VERY low resolution (16x14) live video to a VRChat avatar over OSC.

![App Screenshot](https://github.com/vFeez/VRChat-OSC-Video/blob/main/Demo.gif?raw=true)



## How it to run it?

### Built Executable

1) launch the VRChat_VideoStream.exe (or VRChat_VideoStream(console).exe)

2) Select which webcam you want to stream (you may need to try different options to get your desired webcam)

3) Select your resolution (this deosnt affect the internal resolution of the cam, it is used for scaling the aspect ratio)

4) Choose between a color stream at ~1.5FPS, or a monochrome at ~5fps

6) These options can be changed on the fly without restarting the app

### From Python Code

1) Install all required imported libraries with pip 
(todo: list libraries)

2) Run UI.py (this is the main python code)
3) Follow the steps for Built Executable
