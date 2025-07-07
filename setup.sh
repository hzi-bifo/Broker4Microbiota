#!/bin/bash

# Broker4Microbiota Setup Script
# This script sets up the development environment for the Django NGS metadata collection project

set -e  # Exit on error

echo "🔧 Setting up Broker4Microbiota development environment..."
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    echo "❌ Error: Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version check passed: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📄 Creating .env file from template..."
    cp TEMPLATE.env .env
    echo "⚠️  Please edit .env file to add your ENA credentials and other settings"
else
    echo "✅ .env file already exists"
fi

# Setup Django
echo "🎯 Setting up Django..."
cd project

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser prompt
echo ""
echo "👤 Would you like to create a superuser account? (y/n)"
read -r CREATE_SUPERUSER

if [[ $CREATE_SUPERUSER == "y" ]] || [[ $CREATE_SUPERUSER == "Y" ]]; then
    python manage.py createsuperuser
fi

cd ..

# Check for Nextflow
if ! command -v nextflow &> /dev/null; then
    echo ""
    echo "⚠️  Warning: Nextflow is not installed"
    echo "   Nextflow is required for running bioinformatics pipelines"
    echo "   Install it from: https://www.nextflow.io/docs/latest/install.html"
    echo "   After installation, test with: nextflow run nf-core/mag -profile test,docker --outdir test"
fi

# Check for conda
if ! command -v conda &> /dev/null; then
    echo ""
    echo "⚠️  Warning: Conda is not installed"
    echo "   Conda is required for some bioinformatics tools (bwa, samtools)"
    echo "   Consider installing Miniconda from: https://docs.conda.io/en/latest/miniconda.html"
else
    echo ""
    echo "📦 To install bioinformatics tools with conda, run:"
    echo "   conda install -c bioconda bwa samtools"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file with your ENA credentials and settings"
echo "   2. Activate the virtual environment: source venv/bin/activate"
echo "   3. Start the development server: cd project && python manage.py runserver"
echo "   4. Access the application at: http://127.0.0.1:8000/"
echo ""
echo "📚 For more information, see README.md"