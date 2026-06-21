@echo off
setlocal EnableExtensions

set "ROOT=%~dp0.."
set "JAVA_HOME=%ROOT%\tools\jdk-17.0.2"
set "ANDROID_HOME=%ROOT%\tools\android-sdk"
set "GRADLE_USER_HOME=D:\gradle-cache\storycraft"
set NODE_ENV=production

echo JAVA_HOME=%JAVA_HOME%
echo ANDROID_HOME=%ANDROID_HOME%
echo GRADLE_USER_HOME=%GRADLE_USER_HOME%

echo sdk.dir=%ANDROID_HOME:\=\\%> "%ROOT%\android\local.properties"

echo [1/3] Cleaning gradle transforms cache...
if exist "%GRADLE_USER_HOME%\caches\8.10.2\transforms" rmdir /s /q "%GRADLE_USER_HOME%\caches\8.10.2\transforms"
if exist "%ROOT%\android\.gradle" rmdir /s /q "%ROOT%\android\.gradle"

cd /d "%ROOT%\android"
echo [2/3] Building release APK...
call gradlew.bat assembleRelease --no-daemon --project-cache-dir D:\gradle-cache\storycraft\project
if errorlevel 1 (
  echo Release failed, trying debug...
  call gradlew.bat assembleDebug --no-daemon
)

if exist "app\build\outputs\apk\release\app-release.apk" (
  copy /y "app\build\outputs\apk\release\app-release.apk" "%ROOT%\storycraft-release.apk"
  copy /y "app\build\outputs\apk\release\app-release.apk" "D:\storycraft-release.apk"
  echo SUCCESS: %ROOT%\storycraft-release.apk
  echo SUCCESS: D:\storycraft-release.apk
  exit /b 0
)

if exist "app\build\outputs\apk\debug\app-debug.apk" (
  copy /y "app\build\outputs\apk\debug\app-debug.apk" "%ROOT%\storycraft-debug.apk"
  echo SUCCESS: %ROOT%\storycraft-debug.apk
  exit /b 0
)

echo FAILED: APK not found
exit /b 1
