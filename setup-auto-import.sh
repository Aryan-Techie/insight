#!/bin/bash

# Setup automated RSS imports using cron
# This script will help you set up automatic imports from your RSS feed

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMPORT_SCRIPT="$SCRIPT_DIR/import-rss.sh"

echo "🔧 RSS Feed Auto-Import Setup"
echo "=============================="
echo ""
echo "This will set up automatic RSS imports to run periodically."
echo ""

# Check if cron is available
if ! command -v crontab &> /dev/null; then
    echo "❌ Error: crontab is not available on this system."
    echo "Please install cron to use automatic imports."
    exit 1
fi

echo "📅 Choose import frequency:"
echo "  1) Every hour"
echo "  2) Every 6 hours"
echo "  3) Every 12 hours"
echo "  4) Daily at 9 AM"
echo "  5) Custom"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        cron_schedule="0 * * * *"
        description="every hour"
        ;;
    2)
        cron_schedule="0 */6 * * *"
        description="every 6 hours"
        ;;
    3)
        cron_schedule="0 */12 * * *"
        description="every 12 hours"
        ;;
    4)
        cron_schedule="0 9 * * *"
        description="daily at 9 AM"
        ;;
    5)
        echo ""
        echo "Enter custom cron schedule (e.g., '0 9 * * *' for daily at 9 AM):"
        read -p "Cron schedule: " cron_schedule
        description="custom schedule: $cron_schedule"
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "📝 Setting up cron job to run $description..."

# Create the cron job entry
cron_job="$cron_schedule cd $SCRIPT_DIR && $IMPORT_SCRIPT >> /tmp/rss-import.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null | grep -v "$IMPORT_SCRIPT"; echo "$cron_job") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job successfully added!"
    echo ""
    echo "📋 Current crontab entries:"
    crontab -l | grep "$IMPORT_SCRIPT"
    echo ""
    echo "📄 Logs will be saved to: /tmp/rss-import.log"
    echo ""
    echo "🗑️  To remove this cron job later, run:"
    echo "   crontab -e"
    echo "   (and delete the line containing $IMPORT_SCRIPT)"
else
    echo "❌ Failed to add cron job. Please check your permissions."
    exit 1
fi

echo ""
echo "🎉 Auto-import setup complete!"
echo "Your RSS feed will now be imported $description."
