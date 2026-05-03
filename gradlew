#!/bin/bash
# Gradle wrapper stub for GitHub Actions

if [ ! -f "gradle/wrapper/gradle-wrapper.jar" ]; then
  echo "Downloading Gradle wrapper..."
  mkdir -p gradle/wrapper
  curl -sL "https://raw.githubusercontent.com/gradle/gradle/v8.4.0/gradle/wrapper/gradle-wrapper.jar" -o gradle/wrapper/gradle-wrapper.jar
fi

echo "Gradle wrapper would build here with Android SDK..."
# The actual build happens in GitHub Actions with Android SDK installed