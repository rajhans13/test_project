Start-Transcript -Path "C:\\Logs\\upgrade.txt"
Mount-DiskImage -ImagePath "D:\\ws2025.iso"
& "D:\\setup.exe" /auto upgrade /quiet /dynamicupdate enable /copylogs C:\\Logs
Dismount-DiskImage -ImagePath "D:\\ws2025.iso"
Restart-Computer -Force
