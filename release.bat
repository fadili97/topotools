@echo off
REM ELFADILY TopoTools - Release Helper Script (Windows)
REM Usage: release.bat 1.2.0 "Description of changes"

setlocal enabledelayedexpansion

if "%~1"=="" (
    echo [ERROR] Version number required
    echo Usage: release.bat ^<version^> [description]
    echo Example: release.bat 1.2.0 "Added new features"
    exit /b 1
)

set VERSION=%~1
set DESCRIPTION=%~2
if "%DESCRIPTION%"=="" set DESCRIPTION=Release version %VERSION%
set TAG=v%VERSION%
set METADATA_FILE=elfadily_topotools\metadata.txt

echo ========================================
echo ELFADILY TopoTools Release Process
echo ========================================
echo Version: %VERSION%
echo Description: %DESCRIPTION%
echo.

REM Check if metadata file exists
if not exist "%METADATA_FILE%" (
    echo [ERROR] %METADATA_FILE% not found
    exit /b 1
)

REM Check if git repo
if not exist ".git" (
    echo [ERROR] Not a git repository
    exit /b 1
)

REM Check for uncommitted changes
git status --porcelain > nul 2>&1
if errorlevel 1 (
    echo [WARNING] You have uncommitted changes
    git status --short
    set /p CONTINUE="Continue anyway? (y/N): "
    if /i not "!CONTINUE!"=="y" exit /b 1
)

REM Update version in metadata.txt
echo [1/4] Updating metadata.txt...
powershell -Command "(Get-Content '%METADATA_FILE%') -replace '^version=.*', 'version=%VERSION%' | Set-Content '%METADATA_FILE%'"
findstr "^version=" "%METADATA_FILE%"

REM Commit the version change
echo [2/4] Committing version bump...
git add "%METADATA_FILE%"
git commit -m "Bump version to %VERSION% - %DESCRIPTION%"

REM Create and push tag
echo [3/4] Creating tag %TAG%...
git tag -a "%TAG%" -m "Release %VERSION%: %DESCRIPTION%"

REM Push to remote
echo [4/4] Pushing to GitHub...
git push origin main
git push origin "%TAG%"

echo.
echo ========================================
echo [SUCCESS] Release process completed!
echo ========================================
echo.
echo Next steps:
echo 1. Check GitHub Actions: https://github.com/elfadily-geoconseil/topotools/actions
echo 2. Verify release: https://github.com/elfadily-geoconseil/topotools/releases
echo 3. Check XML feed (wait 2-5 min): https://elfadily-geoconseil.github.io/topotools/plugins.xml
echo.
echo Team members will receive update notification in QGIS
echo.

endlocal
