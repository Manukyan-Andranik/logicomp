from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from openpyxl import Workbook
import secrets
import string
from flask_mail import Message

def generate_random_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def generate_leaderboard_pdf(file_path, contest, problems, leaderboard_data):
    try:
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph(f"{contest.title} – Leaderboard", styles['Title']))
        elements.append(Spacer(1, 12))

        headers = ["Participant", "Score", "Total Time"] + [f"P{p.id}" for p in problems]
        data = [headers]

        for entry in leaderboard_data:
            row = [
                entry['user'].username,
                entry['total_score'],
                entry['total_time']
            ]
            for problem in problems:
                pdata = entry['problems'].get(problem.id)
                if pdata:
                    row.append(f"{pdata['time']}s / {pdata['attempts']} tries")
                else:
                    row.append("—")
            data.append(row)

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.gray),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
        ]))

        elements.append(table)
        doc.build(elements)
    except Exception as e:
        raise Exception(f"Error generating PDF: {str(e)}")
from app import db
from app.models import User

def create_admin_if_not_exists():
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(username='Admin_1', email='admin@example.com', role='admin')
        admin.set_password('Admin_1')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created")
    else:
        print("Admin user already exists")

def generate_leaderboard_excel(file_path, contest, problems, leaderboard_data):
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = f"{contest.title} Leaderboard"

        headers = ["Participant", "Score", "Total Time"] + [f"P{p.id}" for p in problems]
        ws.append(headers)

        for entry in leaderboard_data:
            row = [
                entry['user'].username,
                entry['total_score'],
                entry['total_time']
            ]
            for problem in problems:
                pdata = entry['problems'].get(problem.id)
                if pdata:
                    ws.append(f"{pdata['time']}s / {pdata['attempts']} tries")
                else:
                    ws.append("—")
            ws.append(row)

        wb.save(file_path)
    except Exception as e:
        raise Exception(f"Error generating Excel: {str(e)}")
