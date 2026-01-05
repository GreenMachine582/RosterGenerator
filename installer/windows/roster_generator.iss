; -----------------------------------------------------------------------------
; Roster Generator — Inno Setup Installer
; File: installer/windows/roster_generator.iss
;
; Recommended build layout for installer payload:
;   PyInstaller --onedir output:
;     dist\RosterGenerator\RosterGenerator.exe
;     dist\RosterGenerator\_internal\...
;
; Portable build layout fallback:
;   PyInstaller --onefile output:
;     dist\RosterGenerator-portable-win-x64.exe
;
; This installer is configured for per-user install (no admin) to reduce
; client interaction and permission prompts.
; -----------------------------------------------------------------------------

#define AppName "Roster Generator"
#define AppExeName "RosterGenerator.exe"
#define AppPublisher "GreenMachine582"
#define AppURL "https://github.com/GreenMachine582/RosterGenerator"

; The version should match your git tag like v0.1.0.
; You can hardcode for now, or update it as part of your release process.
#define AppVersion "0.1.0"

; IMPORTANT: Keep AppId stable forever for smooth upgrades.
; Generate once and never change. (This is a placeholder GUID.)
#define AppId "{{B7B2C6B1-5B9F-4E46-9E57-4D7E10C8B9A1}}"

; -----------------------------------------------------------------------------
; Setup
; -----------------------------------------------------------------------------

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; Per-user install to reduce prompts/admin requirements:
PrivilegesRequired=lowest

; Install location (per-user):
DefaultDirName={localappdata}\{#AppName}

; Create folder in Start Menu:
DefaultGroupName={#AppName}

; Output
OutputDir=dist
OutputBaseFilename=RosterGenerator-Setup
Compression=lzma2
SolidCompression=yes

; UI / behavior
DisableProgramGroupPage=yes
UsePreviousAppDir=yes
UsePreviousGroup=yes

; Recommended for installers used by self-updaters:
CloseApplications=yes
RestartApplications=no

; Wizard tweaks (optional)
WizardStyle=modern

; -----------------------------------------------------------------------------
; Files
; -----------------------------------------------------------------------------

[Files]
; --- Option A (recommended): install onedir payload --------------------------
; Expect PyInstaller onedir build output in: dist\RosterGenerator\*
; This installs the entire folder.
Source: "..\..\dist\RosterGenerator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; --- Option B (fallback): install single portable exe ------------------------
; If you prefer to install the onefile exe instead, comment Option A above and
; uncomment the line below. Also update [Icons] to point to the right exe name.
; Source: "..\..\dist\RosterGenerator-portable-win-x64.exe"; DestDir: "{app}"; DestName: "{#AppExeName}"; Flags: ignoreversion

; -----------------------------------------------------------------------------
; Shortcuts
; -----------------------------------------------------------------------------

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
; Optional desktop icon (user can choose; enabled by Tasks section)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

; -----------------------------------------------------------------------------
; Run the app after install (including in silent mode if you want)
; For silent updates, you may NOT want to auto-run. For a desktop app updater,
; auto-run after install is often useful. Here we run it unless /NORESTART etc.
; -----------------------------------------------------------------------------

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

; -----------------------------------------------------------------------------
; Optional: Ensure old app instances are closed before installing
; CloseApplications=yes handles most cases, but you can add additional logic
; if you see file-lock issues.
; -----------------------------------------------------------------------------

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
