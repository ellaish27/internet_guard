[Setup]
AppName=InternetGuard
AppVersion=2026.1.0.0
AppPublisher=Dain Corp
AppPublisherURL=https://example.com/
AppSupportURL=https://example.com/support
AppUpdatesURL=https://example.com/updates
AppCopyright=Copyright (c) 2026 Dain Corp
DefaultDirName={pf}\InternetGuard
DisableDirPage=no
DefaultGroupName=InternetGuard
OutputBaseFilename=InternetGuard_Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico
VersionInfoVersion=2026.1.0.0
VersionInfoCompany=Dain Corp
VersionInfoDescription=InternetGuard - internet access gate
VersionInfoProductName=InternetGuard

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Main executable built by Nuitka (onefile or unpacked). Ensure the file exists in dist\InternetGuard.exe
Source: "dist\InternetGuard.exe"; DestDir: "{app}"; Flags: ignoreversion
; Include application icon so the installer and shortcuts can use it
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Optional README
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: FileExists(Source)

[Icons]
Name: "{group}\InternetGuard"; Filename: "{app}\InternetGuard.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"
Name: "{group}\Uninstall InternetGuard"; Filename: "{uninstallexe}"
Name: "{userdesktop}\InternetGuard"; Filename: "{app}\InternetGuard.exe"; Tasks: desktopicon; IconFilename: "{app}\icon.ico"

[Tasks]
Name: desktopicon; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\InternetGuard.exe"; Description: "Launch InternetGuard"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\icon.ico"
