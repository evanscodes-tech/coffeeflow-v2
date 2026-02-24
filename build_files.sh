#!/bin/bash
echo "📦 Installing dependencies..."
/usr/local/bin/python3 -m pip install -r requirements.txt

echo "📁 Collecting static files..."
/usr/local/bin/python3 manage.py collectstatic --noinput

echo "📁 Creating output directory..."
mkdir -p /vercel/output/staticfiles

echo "📁 Copying static files..."
cp -r staticfiles/* /vercel/output/staticfiles/ 2>/dev/null || :

echo "✅ Build completed!"