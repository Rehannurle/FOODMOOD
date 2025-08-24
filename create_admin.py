# create_admin.py - Run this locally to create admin user

from fomo import app, db, User
from werkzeug.security import generate_password_hash
import os

def create_admin():
    """Create admin user locally"""
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            print(f"❌ Admin already exists: {admin.username} ({admin.email})")
            return
        
        # Get admin details from environment or use defaults
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@foodmood.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'Rihu@2004')  # Change this!
        
        # Create admin user
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password_hash=generate_password_hash(admin_password),
            is_admin=True,
            age=25,
            gender='other',
            is_active=True
        )
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Admin created successfully!")
            print(f"   Username: {admin_username}")
            print(f"   Email: {admin_email}")
            print(f"   Password: {admin_password}")
            print(f"⚠️  Please change the password after first login!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin: {str(e)}")

def list_admins():
    """List all admin users"""
    with app.app_context():
        admins = User.query.filter_by(is_admin=True).all()
        if admins:
            print("📋 Current Admin Users:")
            for admin in admins:
                print(f"   - {admin.username} ({admin.email}) - Active: {admin.is_active}")
        else:
            print("❌ No admin users found")

def delete_admin():
    """Delete admin user"""
    with app.app_context():
        email = input("Enter admin email to delete: ")
        admin = User.query.filter_by(email=email, is_admin=True).first()
        
        if admin:
            db.session.delete(admin)
            db.session.commit()
            print(f"✅ Admin {email} deleted successfully!")
        else:
            print(f"❌ Admin {email} not found")

if __name__ == '__main__':
    print("🍽️ Food Mood - Admin Management")
    print("================================")
    
    while True:
        print("\nOptions:")
        print("1. Create Admin")
        print("2. List Admins") 
        print("3. Delete Admin")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            create_admin()
        elif choice == '2':
            list_admins()
        elif choice == '3':
            delete_admin()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice!")