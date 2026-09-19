; -----------------------------------------------------------------------------
; tdesktop — Setup Wizard
; -----------------------------------------------------------------------------
; Compile this file with Inno Setup 6 or 7 (https://jrsoftware.org/isdl.php).
; Run build_installer.bat or open this .iss file in Inno Setup Compiler.
; -----------------------------------------------------------------------------

#ifndef BuildType
  #define BuildType "Debug"
#endif
#define BuildDir "out\" + BuildType

[Setup]
; --- Application identity ---
AppId={{B8A3F1D2-E5C7-4A9B-8D3E-1F6C9A2B4E7D}
AppName=tdesktop
AppVersion=7.0.9.0
AppPublisher=tdesktop
AppPublisherURL=https://desktop.telegram.org
AppSupportURL=https://desktop.telegram.org
AppUpdatesURL=https://desktop.telegram.org

; --- Default install location ---
; Uses %LOCALAPPDATA%\tdesktop (per-user, no admin required)
DefaultDirName={localappdata}\tdesktop
DefaultGroupName=tdesktop

; --- Installer behavior ---
AllowNoIcons=yes
DisableWelcomePage=no
LicenseFile=LICENSE
DisableDirPage=no
DisableProgramGroupPage=no
DisableReadyPage=no
DisableStartupPrompt=yes
CloseApplications=force
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; --- Modern look ---
WizardStyle=modern
WizardSizePercent=120,120

; --- Output ---
OutputDir={#BuildDir}
OutputBaseFilename=tdesktop-Setup
Compression=lzma2/max
SolidCompression=yes

; --- Icons & branding ---
SetupIconFile=Telegram\Resources\art\icon256.ico
UninstallDisplayName=tdesktop
UninstallDisplayIcon={app}\Telegram.exe

; --- 64-bit on modern Windows ---
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; --- Version info for Windows Explorer ---
VersionInfoVersion=7.0.9.0
VersionInfoDescription=tdesktop Installer
VersionInfoCopyright=Custom Build

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Desktop shortcut — checked by default
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce
; Start Menu shortcut — checked by default
Name: "startmenuicon"; Description: "Create a &Start Menu shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce

[Files]
; Main executable
Source: "{#BuildDir}\Telegram.exe"; DestDir: "{app}"; Flags: ignoreversion 64bit
; Direct3D shader compiler (required for rendering)
Source: "{#BuildDir}\modules\x64\d3d\d3dcompiler_47.dll"; DestDir: "{app}\modules\x64\d3d"; Flags: ignoreversion 64bit

[Icons]
; Start Menu group icon (controlled by startmenuicon task)
Name: "{group}\tdesktop"; Filename: "{app}\Telegram.exe"; Tasks: startmenuicon
; Uninstaller in Start Menu
Name: "{group}\Uninstall tdesktop"; Filename: "{uninstallexe}"; Tasks: startmenuicon
; Desktop shortcut (controlled by desktopicon task)
Name: "{userdesktop}\tdesktop"; Filename: "{app}\Telegram.exe"; Tasks: desktopicon

[Run]
; Launch after install (checkbox on finish page)
Filename: "{app}\Telegram.exe"; Description: "Launch tdesktop"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up runtime data created by the app
Type: files; Name: "{app}\log.txt"
Type: filesandordirs; Name: "{app}\DebugLogs"
Type: filesandordirs; Name: "{app}\tupdates"
Type: filesandordirs; Name: "{app}\tdata"
Type: filesandordirs; Name: "{app}\tcache"
Type: filesandordirs; Name: "{app}\tdumps"
Type: filesandordirs; Name: "{app}\modules"
Type: dirifempty; Name: "{app}"

[Code]
// -----------------------------------------------------------------------------
// Helper: FindWindow by caption — checks if Telegram is running
// -----------------------------------------------------------------------------
function IsTelegramRunning: Boolean;
begin
  Result := (FindWindowByWindowName('Telegram') <> 0) or
            (FindWindowByWindowName('tdesktop') <> 0) or
            (FindWindowByWindowName('Telegram Desktop') <> 0);
end;

// -----------------------------------------------------------------------------
// Initialize setup — prompt to close Telegram if running
// -----------------------------------------------------------------------------
function InitializeSetup: Boolean;
var
  MessageBoxResult: Integer;
begin
  Result := True;
  if IsTelegramRunning then
  begin
    MessageBoxResult := MsgBox(
      'Telegram appears to be running. Please close it before continuing.' + #13#10 +
      'Click OK to continue (the installer will attempt to close it automatically), or Cancel to exit.',
      mbConfirmation,
      MB_OKCANCEL
    );
    if MessageBoxResult = IDCANCEL then
    begin
      Result := False;
      Exit;
    end;
  end;
end;

// -----------------------------------------------------------------------------
// Before install — close any running Telegram process gracefully
// -----------------------------------------------------------------------------
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  ExecFileName: String;
begin
  if CurStep = ssInstall then
  begin
    // Try to gracefully close any existing Telegram process
    ExecFileName := ExpandConstant('{app}\Telegram.exe');
    if FileExists(ExecFileName) then
    begin
      Exec(ExecFileName, '-quit', '', SW_HIDE, ewNoWait, ResultCode);
      Sleep(1500);
    end;
  end;
end;

// -----------------------------------------------------------------------------
// Uninstall: run cleanup and remove user data
// -----------------------------------------------------------------------------
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
  UninstallPath: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    UninstallPath := ExpandConstant('{app}\Telegram.exe');
    if FileExists(UninstallPath) then
    begin
      // Run cleanup flag to remove temp files and shortcuts
      Exec(UninstallPath, '-cleanup', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
