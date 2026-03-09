# Netlify Deployment Script
# This script deploys your app to Netlify

Write-Host "🚀 Deploying to Netlify..." -ForegroundColor Cyan
Write-Host ""

# Check if dist folder exists
if (-not (Test-Path "dist")) {
    Write-Host "❌ dist folder not found. Building app first..." -ForegroundColor Red
    npm run build
}

Write-Host "✅ dist folder found" -ForegroundColor Green
Write-Host ""

# Deploy to Netlify
Write-Host "📤 Uploading to Netlify..." -ForegroundColor Cyan
netlify deploy --prod --dir=dist --site=frontend-demo

Write-Host ""
Write-Host "🎉 Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Your app is now live!" -ForegroundColor Cyan
Write-Host "Check the URL above ☝️" -ForegroundColor Yellow
