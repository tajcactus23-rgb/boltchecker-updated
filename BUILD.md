# BOLTFM Android Build

## Step 1: Install Java & Android SDK
1. Download Java 17: https://adoptium.net/
2. Download Android Studio: https://developer.android.com/studio

## Step 2: Set SDK path
Create `local.properties`:
```
sdk.dir=C:\Users\YourName\AppData\Local\Android\Sdk
```

Or wherever your Android SDK is installed.

## Step 3: Build
```cmd
copy index.html app\src\main\assets\
gradlew.bat assembleDebug
```

## Or just use PWA:
- Go to: https://rehabilitation-hong-drink-extra.trycloudflare.com
- Menu → Add to Home Screen
- Works offline like an app!