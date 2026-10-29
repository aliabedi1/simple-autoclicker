#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif
[Setup]
AppId={{0B9D3E9A-972B-48C9-882F-68F24D22A725}
AppName=Simple Autoclicker
AppVersion={#AppVersion}
AppPublisher=aliabedi1
AppPublisherURL=https://github.com/aliabedi1/simple-autoclicker
DefaultDirName={localappdata}\Programs\Simple Autoclicker
DefaultGroupName=Simple Autoclicker
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release-assets
OutputBaseFilename=SimpleAutoclicker-{#AppVersion}-windows-x64-setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\SimpleAutoclicker.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Files]
Source: "..\dist\SimpleAutoclicker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\Simple Autoclicker"; Filename: "{app}\SimpleAutoclicker.exe"
Name: "{autodesktop}\Simple Autoclicker"; Filename: "{app}\SimpleAutoclicker.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\SimpleAutoclicker.exe"; Description: "Open Simple Autoclicker"; Flags: nowait postinstall skipifsilent
