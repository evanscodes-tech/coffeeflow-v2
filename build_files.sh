#!/bin/bash
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "📁 Creating output directory..."
mkdir -p /vercel/output/staticfiles

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "📁 Copying static files to output..."
cp -r staticfiles /vercel/output/

echo "✅ Build completed!"