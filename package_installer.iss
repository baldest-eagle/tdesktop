#define MyAppName "Telegram"
#define MyAppExeName "Telegram.exe"
#define MyAppVersion "7.0.9"
#define MyAppPublisher "Telegram"
#define ReleasePath "C:\Users\kyleh\tdesktop\out\Debug"

[Setup]
AppId={{A7C9241B-94E2-4D39-968B-B6543D7E8120}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={userappdata}\{#MyAppName} Desktop
DefaultGroupName={#MyAppName} Desktop
AllowNoIcons=yes
OutputDir={#ReleasePath}
OutputBaseFilename=TelegramSetup
SetupIconFile=C:\Users\kyleh\tdesktop\Telegram\Resources\art\icon256.ico
UninstallDisplayName={#MyAppName} Desktop
UninstallDisplayIcon={app}\Telegram.exe
Compression=lzma2/max
SolidCompression=yes
PrivilegesRequired=lowest
CloseApplications=force
WizardStyle=modern
DisableDirPage=yes
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "{#ReleasePath}\Telegram.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ReleasePath}\modules\x64\d3d\d3dcompiler_47.dll"; DestDir: "{app}\modules\x64\d3d"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
