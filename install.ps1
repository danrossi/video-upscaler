$latestTag = (Invoke-RestMethod -Uri https://api.github.com/repos/k4yt3x/video2x/releases/latest).tag_name
curl -LO "https://github.com/k4yt3x/video2x/releases/download/$latestTag/video2x-windows-amd64.zip"
New-Item -Path "$env:LOCALAPPDATA\Programs\video2x" -ItemType Directory -Force
Expand-Archive -Path .\video2x-windows-amd64.zip -Force -Verbose -DestinationPath "$env:LOCALAPPDATA\Programs\video2x"

curl -LO 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
Expand-Archive -Path .\ffmpeg-release-essentials.zip -Force -Verbose -DestinationPath "$env:LOCALAPPDATA\Programs\video2x"

if (Test-Path -Path "$env:LOCALAPPDATA\Programs\video2x\ffmpeg") {
    Remove-Item -Force -Recurse "$env:LOCALAPPDATA\Programs\video2x\ffmpeg"
}

$ffmpegFolder = Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\video2x" -Filter "ffmpeg-*" -Directory
Rename-Item -Force -Path $ffmpegFolder -NewName "ffmpeg"

Remove-Item .\ffmpeg-release-essentials.zip
Remove-Item .\video2x-windows-amd64.zip