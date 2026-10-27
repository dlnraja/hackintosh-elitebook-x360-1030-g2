# Optional local files

Nothing in this directory is required to build a bootable EFI. The build reads two drop-ins when they exist:

- `smbios.json`, written by `scripts/generate-smbios.sh` or `scripts/generate-smbios.ps1`. It is gitignored. The builder copies it only into `dist/EFI/OC/config.plist`. `config/config.plist` keeps the placeholders.
- `UTBMap.kext`, a USB map made on Windows with USBToolBox. When this folder is present, the builder enables `USBToolBox.kext` and the map.
- `CPUFriendDataProvider.kext`, generated after macOS is installed. When this folder is present, the builder downloads the pinned CPUFriend release and enables both kexts.

Do not commit serial numbers, board serials, ROM values, or a USB map from your own machine.
