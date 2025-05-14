Set-Location -Path "E:\INSIGHT"  # Location to The Project Insight
python .\customs\index.py # Python File to update Featured & Recent Section
npx quartz sync --no-pull # Push Changes From Local to Global