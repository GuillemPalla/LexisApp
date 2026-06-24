[Setup]
AppName=LexisApp
AppVersion=1.0
AppPublisher=LexisApp
DefaultDirName={autopf}\LexisApp
DefaultGroupName=LexisApp
OutputBaseFilename=LexisApp-Setup
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "launch.vbs"; DestDir: "{app}"; Flags: ignoreversion

; Your app source code
Source: "app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs

; Embeddable Python runtime
Source: "python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs

; The launcher
Source: "launch.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\LexisApp"; Filename: "{app}\launch.vbs"; \
    WorkingDir: "{app}"; IconFilename: "{app}\app\icon.ico"

Name: "{userdesktop}\LexisApp"; Filename: "{app}\launch.vbs"; \
    WorkingDir: "{app}"; IconFilename: "{app}\app\icon.ico"