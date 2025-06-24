# Video Upscaler using video2x

[video2x](https://github.com/k4yt3x/video2x) is a tool for ffmpeg super resolution upscaling using AI models. 

This tool automates the process of batch processing videos in an input directory to an output directly. The GUI has no output directory config and the tool has a bug remuxing and encoding audio if the source audio is not aac. 

By default it's doing an nvenc h264 encode of the upscaling output using the libplacebo model, resizing to 1080p. The settings can be changed and is hardcoded for now.

After it has scaled to 1080p it remuxes the audio back into an output file in the output directory.

It's built for windows only for now. 

# Install the tools

```
./install.ps1
```
# Usage

```
python video_upscaler.py -i D:\videosrc -o D:\videodest
```
