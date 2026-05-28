@echo off
cd /d "%~dp0"

echo 🧪 Запускаем тесты для SoundWave Backend...

python -m pytest tests/ -v --tb=short %*

if %errorlevel% equ 0 (
    echo ✅ Все тесты прошли успешно!
    exit /b 0
) else (
    echo ❌ Некоторые тесты не прошли
    exit /b 1
)