"""
Quick deployment script for Spendlot Backend.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description, check=True):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False

def check_prerequisites():
    """Check if required tools are installed."""
    print("🔍 Checking prerequisites...")
    
    tools = [
        ("docker", "Docker"),
        ("docker-compose", "Docker Compose"),
        ("python", "Python"),
        ("pip", "Pip")
    ]
    
    all_good = True
    for tool, name in tools:
        if run_command(f"{tool} --version", f"Checking {name}", check=False):
            print(f"✅ {name} is installed")
        else:
            print(f"❌ {name} is not installed or not in PATH")
            all_good = False
    
    return all_good

def setup_environment():
    """Set up environment configuration."""
    print("🔧 Setting up environment...")
    
    if not Path(".env").exists():
        if Path(".env.example").exists():
            run_command("cp .env.example .env", "Copying environment template")
            print("📝 Please edit .env file with your configuration before continuing")
            print("   Key settings to configure:")
            print("   - DATABASE_URL")
            print("   - REDIS_URL") 
            print("   - SECRET_KEY")
            print("   - GOOGLE_APPLICATION_CREDENTIALS")
            print("   - PLAID_CLIENT_ID and PLAID_SECRET")
            print("   - TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
            print("   - SMTP settings for email")
            return False
        else:
            print("❌ No .env.example file found")
            return False
    else:
        print("✅ Environment file already exists")
        return True

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    return run_command("pip install -r requirements.txt", "Installing Python packages")

def start_services():
    """Start Docker services."""
    print("🐳 Starting Docker services...")
    
    # Start database and Redis first
    if not run_command("docker-compose up -d postgres redis", "Starting PostgreSQL and Redis"):
        return False
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(10)
    
    return True

def setup_database():
    """Set up database schema and initial data."""
    print("🗄️ Setting up database...")
    
    # Run migrations
    if not run_command("alembic upgrade head", "Running database migrations"):
        return False
    
    # Initialize default data
    if not run_command("python scripts/init_db.py", "Initializing default data"):
        return False
    
    return True

def start_application():
    """Start the full application stack."""
    print("🚀 Starting application stack...")
    
    return run_command("docker-compose up -d", "Starting all services")

def verify_deployment():
    """Verify that the deployment is working."""
    print("🔍 Verifying deployment...")
    
    # Wait a bit for services to start
    time.sleep(5)
    
    # Check health endpoint
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def show_next_steps():
    """Show next steps after deployment."""
    print("\n🎉 DEPLOYMENT COMPLETE!")
    print("=" * 50)
    print("\n📍 Your Spendlot Backend is running at:")
    print("   • API: http://localhost:8000")
    print("   • API Docs: http://localhost:8000/api/v1/docs")
    print("   • Health Check: http://localhost:8000/health")
    print("   • Metrics: http://localhost:8000/metrics")
    print("   • Celery Flower: http://localhost:5555")
    
    print("\n🔧 Useful Commands:")
    print("   • View logs: docker-compose logs -f")
    print("   • Stop services: docker-compose down")
    print("   • Restart: docker-compose restart")
    print("   • Run tests: python scripts/run_tests.py")
    
    print("\n📝 Next Steps:")
    print("   1. Test the API endpoints using the interactive docs")
    print("   2. Configure external services (Google Cloud Vision, Plaid, etc.)")
    print("   3. Set up your frontend application")
    print("   4. Configure production environment variables")
    print("   5. Set up monitoring and alerting")

def main():
    """Main deployment function."""
    print("🚀 SPENDLOT BACKEND QUICK DEPLOYMENT")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please install missing tools.")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("\n⚠️  Please configure your .env file and run this script again.")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies.")
        sys.exit(1)
    
    # Start services
    if not start_services():
        print("\n❌ Failed to start Docker services.")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("\n❌ Failed to setup database.")
        sys.exit(1)
    
    # Start application
    if not start_application():
        print("\n❌ Failed to start application.")
        sys.exit(1)
    
    # Verify deployment
    if not verify_deployment():
        print("\n⚠️  Deployment completed but health check failed.")
        print("   Check the logs: docker-compose logs")
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed with error: {e}")
        sys.exit(1)
