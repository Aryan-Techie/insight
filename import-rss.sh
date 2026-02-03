#!/bin/bash

# RSS Feed Importer Script for Quartz
# This script imports blog posts from your RSS feed and converts them to markdown files

echo "🔄 Starting RSS import..."
echo "=================================="

# Run the Python importer
python3 customs/posts_importer.py

# Check if the import was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 RSS import completed successfully!"
    echo ""
    echo "📝 To rebuild your site with the new posts, run:"
    echo "   npx quartz build"
    echo ""
    echo "🚀 To serve locally, run:"
    echo "   npx quartz serve"
else
    echo ""
    echo "❌ RSS import failed. Check the error messages above."
    exit 1
fi
