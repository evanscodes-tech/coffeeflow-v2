 CoffeeFlow - Digital Coffee Collection System 
 
A comprehensive digital platform for coffee cooperatives to manage farmers, track coffee deliveries, and process payments with SMS notifications. 
 
 Features 
 
Farmer Management: Register and manage farmer profiles with contact details, farm information, and SMS preferences 
Coffee Delivery Tracking: Record coffee cherry deliveries with automatic conversion (5kg cherry  1kg dry coffee) 
Payment Processing: Track payments to farmers with auto-calculation based on weight and price per kg 
SMS Ready: Database structure ready for SMS notifications (Celcom Africa/Onfon Media integration) 
Admin Dashboard: Professional coffee-themed admin interface with import/export functionality 
User Roles: Admin, Staff, and Farmer roles with appropriate permissions 
-Mobile API: REST API endpoints ready for mobile app development 
 
Tech Stack 
 
- Backend: Python Django 6.0 
- Database: SQLite (development) / PostgreSQL (production) 
- Frontend: HTML, CSS, Font Awesome 
- API: Django REST Framework 
- Admin: django-admin-interface, django-import-export 
 
 Quick Start 
 

git clone https://github.com/evanscodes-tech/coffeeflow-v2.git 
cd coffeeflow 
python -m venv venv 
venv\Scripts\activate  # Windows 
pip install -r requirements.txt 
python manage.py migrate 
python manage.py createsuperuser 
python manage.py runserver 

 
 Project Structure 
 

coffeeflow/ 
manage.py 
coffeeflow/          # Project settings 
apps/ 
accounts/        # User authentication 
farmers/         # Farmer profiles 
deliveries/      # Coffee batch tracking 
payments/        # Payment processing 
mobile_api/      # REST API endpoints 
templates/           # HTML templates static/              # CSS, JS, images 
media/               # Uploaded files 
 
 
SMS Integration (Coming Soon) 
 
The system is ready for SMS integration with: 
- Celcom Africa 
- Onfon Media 
- Africa's Talking 
 
License 
 
MIT c Evans Ngetich 
