from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.secret_key = "ecoYugamSecretKey"

# ---------------- DATABASE CONFIG ----------------
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Bindu%40134366@localhost/ecoYugam"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------------- MAIL CONFIG ----------------
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "sharmavinit7348@gmail.com"
app.config["MAIL_PASSWORD"] = "ifwfkpatghvztxlz"
app.config["MAIL_DEBUG"] = True
mail = Mail(app)

# ---------------- MODELS ----------------
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6), nullable=True)

class ContactSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    organization = db.Column(db.String(100))
    involvement_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="New")

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    read = db.Column(db.Boolean, default=False)

# ---------------- ROUTES ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/programs')
def programs():
    return render_template('programs.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/vision')
def vision():
    return render_template('vision.html')

@app.route('/impact')
def impact():
    return render_template('impact.html')

@app.route('/e-waste-to-resources')
def e_waste_to_resources():
    return render_template('e-waste-to-resources.html')

@app.route('/smart_bin_initiative')
def smart_bin_initiative():
    return render_template('smart_bin_initiative.html')

@app.route('/water_body_restoration')
def water_body_restoration():
    return render_template('water_body_restoration.html')

@app.route('/zero_waste_management')
def zero_waste_management():
    return render_template('zero_waste_management.html')

@app.route('/pillars')
def pillars():
    return render_template('pillars.html')

# ---------------- FORM SUBMISSION ----------------
@app.route('/submit_interest', methods=['POST'])
def submit_interest():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        organization = request.form.get('organization')
        involvement_type = request.form.get('involvement_type')
        message = request.form.get('message')

        if not name or not email or not involvement_type:
            flash('Please fill all required fields!', 'error')
            return redirect(url_for('index') + '#get-involved')

        new_submission = ContactSubmission(
            name=name,
            email=email,
            organization=organization,
            involvement_type=involvement_type,
            message=message
        )
        db.session.add(new_submission)
        
        # Create notification for new submission
        notification = Notification(
            message=f"New contact form submission from {name}"
        )
        db.session.add(notification)
        
        db.session.commit()
        flash('Thank you for your interest! We will contact you soon.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error submitting form. Try again.', 'error')
        print("Error:", e)
    return redirect(url_for('index') + '#get-involved')

# ---------------- ADMIN ROUTES ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            flash("Passwords do not match!", "error")
            return render_template("register.html")

        existing = Admin.query.filter_by(email=email).first()
        if existing:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("login"))

        otp = str(random.randint(100000, 999999))
        hashed_pw = generate_password_hash(password)

        new_admin = Admin(username=username, email=email, password=hashed_pw, otp=otp)
        db.session.add(new_admin)
        db.session.commit()

        try:
            msg = Message("EcoYugam Admin Registration OTP",
                          sender=app.config["MAIL_USERNAME"],
                          recipients=[email])
            msg.body = f"Hello {username},\n\nYour OTP for EcoYugam Admin Registration is: {otp}\n\nPlease enter this OTP to verify your account."
            mail.send(msg)
            flash("OTP sent to your email. Please verify.", "info")
            session["pending_email"] = email
            return redirect(url_for("verify_otp"))
        except Exception as e:
            print("❌ Mail Error:", e)
            flash("Failed to send OTP email. Try again.", "error")
            db.session.rollback()

    return render_template("register.html")

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if "pending_email" not in session:
        flash("No registration in progress!", "warning")
        return redirect(url_for("register"))

    email = session["pending_email"]
    admin = Admin.query.filter_by(email=email).first()

    if request.method == "POST":
        entered_otp = request.form.get("otp")

        if admin and admin.otp == entered_otp:
            admin.verified = True
            admin.otp = None
            db.session.commit()
            session.pop("pending_email", None)
            flash("Email verified successfully! You can now log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Invalid OTP. Please try again.", "error")

    return render_template("verify_otp.html", email=email)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        admin = Admin.query.filter_by(email=email).first()

        if not admin:
            flash("No admin found with that email.", "error")
            return render_template("login.html")

        if not admin.verified:
            session["pending_email"] = email
            flash("Please verify your email first.", "warning")
            return redirect(url_for("verify_otp"))

        if check_password_hash(admin.password, password):
            session["admin"] = admin.username
            session["admin_id"] = admin.id
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid password.", "error")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("login"))

    total = ContactSubmission.query.count()
    new_count = ContactSubmission.query.filter_by(status="New").count()
    submissions = ContactSubmission.query.order_by(ContactSubmission.submission_date.desc()).all()
    notifications = Notification.query.filter_by(read=False).order_by(Notification.id.desc()).all()

    return render_template("dashboard.html",
                           total_submissions=total,
                           new_submissions=new_count,
                           submissions=submissions,
                           notifications=notifications,
                           admin=session["admin"])

@app.route("/update_status/<int:submission_id>", methods=["POST"])
def update_status(submission_id):
    if "admin" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("login"))
    
    submission = ContactSubmission.query.get_or_404(submission_id)
    new_status = request.form.get("status")
    
    if new_status in ["New", "Contacted", "In Progress", "Completed"]:
        submission.status = new_status
        db.session.commit()
        flash(f"Status updated to {new_status}!", "success")
    
    return redirect(url_for("dashboard"))

@app.route("/delete_submission/<int:submission_id>")
def delete_submission(submission_id):
    if "admin" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("login"))
    
    submission = ContactSubmission.query.get_or_404(submission_id)
    db.session.delete(submission)
    db.session.commit()
    flash("Submission deleted successfully!", "success")
    return redirect(url_for("dashboard"))

@app.route("/update_submission_status/<int:submission_id>/<string:new_status>")
def update_submission_status(submission_id, new_status):
    if "admin" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("login"))

    submission = ContactSubmission.query.get_or_404(submission_id)
    if new_status in ["New", "Contacted", "In Progress", "Completed", "Read"]:
        submission.status = new_status
        db.session.commit()
        flash(f"Submission status updated to {new_status}.", "success")
    return redirect(url_for("dashboard"))
    
@app.route("/mark_all_read")
def mark_all_read():
    if "admin" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("login"))
    
    Notification.query.update({"read": True})
    db.session.commit()
    flash("All notifications marked as read!", "success")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# ---------------- RUN APPLICATION ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='10.46.149.140', port=5000, debug=True)