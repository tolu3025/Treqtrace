"""
TreqTrace - Software Validation System for Requirement Traceability
Built by Oluwagbemiga Opemipo Stephen
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import io
import csv
from config import Config

# Ensure upload folder exists safely
try:
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
except Exception:
    pass

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# ======================== MODELS ========================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='developer')  # admin, developer, tester
    avatar = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    projects = db.relationship('Project', backref='creator', lazy=True)
    requirements = db.relationship('Requirement', backref='author', lazy=True)
    test_cases = db.relationship('TestCase', backref='executor', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_developer(self):
        return self.role in ['admin', 'developer']

    def is_tester(self):
        return self.role in ['admin', 'tester']

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def create_notification(user_id, message):
    try:
        notif = Notification(user_id=user_id, message=message)
        db.session.add(notif)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Notification error:", e)


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, completed, archived

    requirements = db.relationship('Requirement', backref='project', lazy=True, cascade='all, delete-orphan')
    design_artifacts = db.relationship('DesignArtifact', backref='project', lazy=True, cascade='all, delete-orphan')
    test_cases = db.relationship('TestCase', backref='project', lazy=True, cascade='all, delete-orphan')

class Requirement(db.Model):
    __tablename__ = 'requirements'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    req_id = db.Column(db.String(50), nullable=False)  # e.g., REQ-001
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    req_type = db.Column(db.String(50), default='functional')  # functional, non-functional
    priority = db.Column(db.String(20), default='medium')  # high, medium, low
    status = db.Column(db.String(50), default='draft')  # draft, approved, implemented, tested, validated, deprecated
    version = db.Column(db.Integer, default=1)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = db.relationship('RequirementVersion', backref='requirement', lazy=True, cascade='all, delete-orphan')
    trace_links = db.relationship('TraceabilityLink', backref='requirement', lazy=True, cascade='all, delete-orphan')

    def get_validation_status(self):
        """Returns validation status based on linked test cases"""
        links = TraceabilityLink.query.filter_by(requirement_id=self.id).all()
        test_links = [l for l in links if l.artifact_type == 'test_case']

        if not test_links:
            return {'status': 'not_traced', 'label': 'Not Traced', 'badge': 'secondary'}

        test_case_ids = [l.artifact_id for l in test_links]
        test_cases = TestCase.query.filter(TestCase.id.in_(test_case_ids)).all()

        if not test_cases:
            return {'status': 'not_tested', 'label': 'Not Tested', 'badge': 'warning'}

        passed = sum(1 for t in test_cases if t.status == 'passed')
        failed = sum(1 for t in test_cases if t.status == 'failed')
        total = len(test_cases)

        if failed > 0:
            return {'status': 'failed', 'label': f'Failed ({failed}/{total})', 'badge': 'danger'}
        if passed == total:
            return {'status': 'validated', 'label': f'Validated ({passed}/{total})', 'badge': 'success'}
        return {'status': 'partial', 'label': f'In Progress ({passed}/{total})', 'badge': 'info'}

    def get_design_count(self):
        return TraceabilityLink.query.filter_by(requirement_id=self.id, artifact_type='design').count()

    def get_test_count(self):
        return TraceabilityLink.query.filter_by(requirement_id=self.id, artifact_type='test_case').count()

class RequirementVersion(db.Model):
    __tablename__ = 'requirement_versions'
    id = db.Column(db.Integer, primary_key=True)
    requirement_id = db.Column(db.Integer, db.ForeignKey('requirements.id'), nullable=False)
    title = db.Column(db.String(300))
    description = db.Column(db.Text)
    req_type = db.Column(db.String(50))
    priority = db.Column(db.String(20))
    status = db.Column(db.String(50))
    version = db.Column(db.Integer)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    change_note = db.Column(db.String(500))

    user = db.relationship('User')

class DesignArtifact(db.Model):
    __tablename__ = 'design_artifacts'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    artifact_type = db.Column(db.String(100))  # class diagram, sequence diagram, wireframe, etc.
    description = db.Column(db.Text)
    reference_link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TestCase(db.Model):
    __tablename__ = 'test_cases'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    tc_id = db.Column(db.String(50), nullable=False)  # e.g., TC-001
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    expected_result = db.Column(db.Text)
    actual_result = db.Column(db.Text)
    status = db.Column(db.String(50), default='not_executed')  # not_executed, passed, failed, blocked
    executed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    executed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TraceabilityLink(db.Model):
    __tablename__ = 'traceability_links'
    id = db.Column(db.Integer, primary_key=True)
    requirement_id = db.Column(db.Integer, db.ForeignKey('requirements.id'), nullable=False)
    artifact_id = db.Column(db.Integer, nullable=False)
    artifact_type = db.Column(db.String(50), nullable=False)  # design, test_case
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    user = db.relationship('User')
    __table_args__ = (db.UniqueConstraint('requirement_id', 'artifact_id', 'artifact_type', name='unique_trace_link'),)

# ======================== LOGIN MANAGER ========================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ======================== CONTEXT PROCESSORS ========================

@app.context_processor
def inject_globals():
    return {
        'now': datetime.utcnow(),
        'app_name': 'TreqTrace'
    }

# ======================== ROUTES ========================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

# ---------- AUTH ----------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'developer')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Auto-login after registration
        login_user(user, remember=True)
        flash(f'Welcome to TreqTrace, {user.username}! Your account has been created.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ---------- DASHBOARD ----------

@app.route('/dashboard')
@login_required
def dashboard():
    # Role-based dashboard routing
    if current_user.is_admin():
        return admin_dashboard()
    elif current_user.role == 'tester':
        return tester_dashboard()
    else:
        return developer_dashboard()

def admin_dashboard():
    all_projects = Project.query.order_by(Project.created_at.desc()).all()
    all_users = User.query.all()

    stats = {
        'total_projects': len(all_projects),
        'total_users': len(all_users),
        'total_requirements': 0,
        'total_test_cases': 0,
        'validated_reqs': 0,
        'failed_reqs': 0,
        'pending_reqs': 0,
        'not_traced': 0
    }

    for proj in all_projects:
        reqs = Requirement.query.filter_by(project_id=proj.id).all()
        stats['total_requirements'] += len(reqs)
        stats['total_test_cases'] += TestCase.query.filter_by(project_id=proj.id).count()
        for req in reqs:
            val = req.get_validation_status()
            if val['status'] == 'validated':
                stats['validated_reqs'] += 1
            elif val['status'] == 'failed':
                stats['failed_reqs'] += 1
            elif val['status'] in ['not_traced', 'not_tested']:
                stats['not_traced'] += 1
            else:
                stats['pending_reqs'] += 1

    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    return render_template('dashboard_admin.html', stats=stats, projects=all_projects,
                         users=all_users, recent_projects=recent_projects)

def developer_dashboard():
    projects = Project.query.filter_by(created_by=current_user.id).order_by(Project.created_at.desc()).all()

    stats = {
        'total_projects': len(projects),
        'total_requirements': 0,
        'implemented_reqs': 0,
        'pending_reqs': 0,
        'design_count': 0
    }

    for proj in projects:
        reqs = Requirement.query.filter_by(project_id=proj.id).all()
        stats['total_requirements'] += len(reqs)
        stats['design_count'] += DesignArtifact.query.filter_by(project_id=proj.id).count()
        for req in reqs:
            if req.status in ['implemented', 'tested', 'validated']:
                stats['implemented_reqs'] += 1
            else:
                stats['pending_reqs'] += 1

    recent_requirements = Requirement.query.join(Project).filter(
        Project.created_by == current_user.id
    ).order_by(Requirement.updated_at.desc()).limit(5).all()

    return render_template('dashboard_developer.html', stats=stats, projects=projects,
                         recent_requirements=recent_requirements)

def tester_dashboard():
    # Testers see all projects they can test
    projects = Project.query.order_by(Project.created_at.desc()).all()

    stats = {
        'total_projects': len(projects),
        'total_test_cases': 0,
        'passed_tests': 0,
        'failed_tests': 0,
        'pending_tests': 0,
        'not_executed': 0
    }

    for proj in projects:
        tests = TestCase.query.filter_by(project_id=proj.id).all()
        stats['total_test_cases'] += len(tests)
        for t in tests:
            if t.status == 'passed':
                stats['passed_tests'] += 1
            elif t.status == 'failed':
                stats['failed_tests'] += 1
            elif t.status == 'blocked':
                stats['pending_tests'] += 1
            else:
                stats['not_executed'] += 1

    recent_tests = TestCase.query.order_by(TestCase.created_at.desc()).limit(5).all()
    failed_tests = TestCase.query.filter_by(status='failed').order_by(TestCase.created_at.desc()).limit(5).all()

    return render_template('dashboard_tester.html', stats=stats, projects=projects,
                         recent_tests=recent_tests, failed_tests=failed_tests)

# ---------- PROJECTS ----------

@app.route('/projects')
@login_required
def projects():
    if current_user.is_admin():
        projects = Project.query.order_by(Project.created_at.desc()).all()
    else:
        projects = Project.query.filter_by(created_by=current_user.id).order_by(Project.created_at.desc()).all()
    return render_template('projects.html', projects=projects)

@app.route('/projects/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        project = Project(name=name, description=description, created_by=current_user.id)
        db.session.add(project)
        db.session.commit()
        create_notification(current_user.id, f"Project '{project.name}' has been created successfully.")

        # Handle file uploads
        if 'project_files' in request.files:
            files = request.files.getlist('project_files')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    # Prefix with project id to avoid collisions
                    unique_name = f"project_{project.id}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                    file.save(file_path)

                    # Save as a design artifact reference
                    artifact = DesignArtifact(
                        project_id=project.id,
                        name=filename,
                        artifact_type='Uploaded Document',
                        description=f'Uploaded project file: {filename}',
                        reference_link=unique_name
                    )
                    db.session.add(artifact)
            db.session.commit()

        flash('Project created successfully!', 'success')
        return redirect(url_for('view_project', id=project.id))

    return render_template('project_form.html')

@app.route('/projects/<int:id>')
@login_required
def view_project(id):
    project = Project.query.get_or_404(id)
    requirements = Requirement.query.filter_by(project_id=id).order_by(Requirement.req_id).all()
    design_artifacts = DesignArtifact.query.filter_by(project_id=id).all()
    test_cases = TestCase.query.filter_by(project_id=id).all()
    return render_template('project_detail.html', project=project, requirements=requirements,
                         design_artifacts=design_artifacts, test_cases=test_cases)

@app.route('/projects/<int:id>/delete', methods=['POST'])
@login_required
def delete_project(id):
    project = Project.query.get_or_404(id)
    if not current_user.is_admin() and project.created_by != current_user.id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('projects'))

    db.session.delete(project)
    db.session.commit()
    flash('Project deleted.', 'info')
    return redirect(url_for('projects'))

# ---------- REQUIREMENTS ----------

@app.route('/projects/<int:project_id>/requirements/new', methods=['GET', 'POST'])
@login_required
def new_requirement(project_id):
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        req_id = request.form.get('req_id')
        title = request.form.get('title')
        description = request.form.get('description')
        req_type = request.form.get('req_type', 'functional')
        priority = request.form.get('priority', 'medium')
        status = request.form.get('status', 'draft')

        req = Requirement(
            project_id=project_id,
            req_id=req_id,
            title=title,
            description=description,
            req_type=req_type,
            priority=priority,
            status=status,
            created_by=current_user.id,
            version=1
        )
        db.session.add(req)
        db.session.commit()

        # Save initial version
        version = RequirementVersion(
            requirement_id=req.id,
            title=title,
            description=description,
            req_type=req_type,
            priority=priority,
            status=status,
            version=1,
            changed_by=current_user.id,
            change_note='Initial creation'
        )
        db.session.add(version)
        db.session.commit()
        create_notification(current_user.id, f"Requirement '{req.req_id}' added to project '{project.name}'.")

        flash('Requirement created successfully!', 'success')
        return redirect(url_for('view_project', id=project_id))

    return render_template('requirement_form.html', project=project)

@app.route('/requirements/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_requirement(id):
    req = Requirement.query.get_or_404(id)
    project = Project.query.get(req.project_id)

    if request.method == 'POST':
        change_note = request.form.get('change_note', 'Updated')

        # Save current state as version
        version = RequirementVersion(
            requirement_id=req.id,
            title=req.title,
            description=req.description,
            req_type=req.req_type,
            priority=req.priority,
            status=req.status,
            version=req.version,
            changed_by=current_user.id,
            change_note=change_note
        )
        db.session.add(version)

        # Update requirement
        req.req_id = request.form.get('req_id')
        req.title = request.form.get('title')
        req.description = request.form.get('description')
        req.req_type = request.form.get('req_type')
        req.priority = request.form.get('priority')
        req.status = request.form.get('status')
        req.version += 1
        req.updated_at = datetime.utcnow()

        db.session.commit()
        create_notification(current_user.id, f"Requirement '{req.req_id}' in project '{project.name}' has been updated to version {req.version}.")
        flash('Requirement updated successfully!', 'success')
        return redirect(url_for('view_project', id=req.project_id))

    versions = RequirementVersion.query.filter_by(requirement_id=id).order_by(RequirementVersion.version.desc()).all()
    return render_template('requirement_form.html', project=project, requirement=req, versions=versions)

@app.route('/requirements/<int:id>')
@login_required
def view_requirement(id):
    req = Requirement.query.get_or_404(id)
    project = Project.query.get(req.project_id)
    versions = RequirementVersion.query.filter_by(requirement_id=id).order_by(RequirementVersion.version.desc()).all()

    # Get linked artifacts
    links = TraceabilityLink.query.filter_by(requirement_id=id).all()
    linked_designs = []
    linked_tests = []
    for link in links:
        if link.artifact_type == 'design':
            art = DesignArtifact.query.get(link.artifact_id)
            if art:
                linked_designs.append(art)
        elif link.artifact_type == 'test_case':
            tc = TestCase.query.get(link.artifact_id)
            if tc:
                linked_tests.append(tc)

    return render_template('requirement_detail.html', requirement=req, project=project,
                         versions=versions, linked_designs=linked_designs, linked_tests=linked_tests)

@app.route('/requirements/<int:id>/delete', methods=['POST'])
@login_required
def delete_requirement(id):
    req = Requirement.query.get_or_404(id)
    project_id = req.project_id
    db.session.delete(req)
    db.session.commit()
    flash('Requirement deleted.', 'info')
    return redirect(url_for('view_project', id=project_id))

# ---------- DESIGN ARTIFACTS ----------

@app.route('/projects/<int:project_id>/designs/new', methods=['GET', 'POST'])
@login_required
def new_design(project_id):
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        design = DesignArtifact(
            project_id=project_id,
            name=request.form.get('name'),
            artifact_type=request.form.get('artifact_type'),
            description=request.form.get('description'),
            reference_link=request.form.get('reference_link')
        )
        db.session.add(design)
        db.session.commit()
        flash('Design artifact added!', 'success')
        return redirect(url_for('view_project', id=project_id))

    return render_template('design_form.html', project=project)

@app.route('/designs/<int:id>/delete', methods=['POST'])
@login_required
def delete_design(id):
    design = DesignArtifact.query.get_or_404(id)
    project_id = design.project_id
    db.session.delete(design)
    db.session.commit()
    flash('Design artifact deleted.', 'info')
    return redirect(url_for('view_project', id=project_id))

# ---------- TEST CASES ----------

@app.route('/projects/<int:project_id>/tests/new', methods=['GET', 'POST'])
@login_required
def new_test_case(project_id):
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        tc = TestCase(
            project_id=project_id,
            tc_id=request.form.get('tc_id'),
            title=request.form.get('title'),
            description=request.form.get('description'),
            expected_result=request.form.get('expected_result')
        )
        db.session.add(tc)
        db.session.commit()
        flash('Test case created!', 'success')
        return redirect(url_for('view_project', id=project_id))

    return render_template('test_form.html', project=project)

@app.route('/tests/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_test_case(id):
    tc = TestCase.query.get_or_404(id)
    project = Project.query.get(tc.project_id)

    if request.method == 'POST':
        tc.tc_id = request.form.get('tc_id')
        tc.title = request.form.get('title')
        tc.description = request.form.get('description')
        tc.expected_result = request.form.get('expected_result')
        tc.actual_result = request.form.get('actual_result')
        tc.status = request.form.get('status')
        if tc.status in ['passed', 'failed'] and not tc.executed_at:
            tc.executed_at = datetime.utcnow()
            tc.executed_by = current_user.id
        db.session.commit()
        flash('Test case updated!', 'success')
        return redirect(url_for('view_project', id=tc.project_id))

    return render_template('test_form.html', project=project, test_case=tc)

@app.route('/tests/<int:id>/delete', methods=['POST'])
@login_required
def delete_test_case(id):
    tc = TestCase.query.get_or_404(id)
    project_id = tc.project_id
    db.session.delete(tc)
    db.session.commit()
    flash('Test case deleted.', 'info')
    return redirect(url_for('view_project', id=project_id))

# ---------- TRACEABILITY ----------

@app.route('/projects/<int:project_id>/traceability')
@login_required
def traceability(project_id):
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).order_by(Requirement.req_id).all()
    design_artifacts = DesignArtifact.query.filter_by(project_id=project_id).all()
    test_cases = TestCase.query.filter_by(project_id=project_id).all()

    # Build RTM data
    rtm = []
    for req in requirements:
        links = TraceabilityLink.query.filter_by(requirement_id=req.id).all()
        linked_designs = [l.artifact_id for l in links if l.artifact_type == 'design']
        linked_tests = [l.artifact_id for l in links if l.artifact_type == 'test_case']

        designs = [d for d in design_artifacts if d.id in linked_designs]
        tests = [t for t in test_cases if t.id in linked_tests]
        val = req.get_validation_status()

        rtm.append({
            'requirement': req,
            'designs': designs,
            'tests': tests,
            'validation': val
        })

    return render_template('traceability.html', project=project, rtm=rtm,
                         design_artifacts=design_artifacts, test_cases=test_cases,
                         requirements=requirements)

@app.route('/api/trace-link', methods=['POST'])
@login_required
def add_trace_link():
    data = request.get_json()
    requirement_id = data.get('requirement_id')
    artifact_id = data.get('artifact_id')
    artifact_type = data.get('artifact_type')

    existing = TraceabilityLink.query.filter_by(
        requirement_id=requirement_id,
        artifact_id=artifact_id,
        artifact_type=artifact_type
    ).first()

    if existing:
        return jsonify({'success': False, 'message': 'Link already exists'})

    link = TraceabilityLink(
        requirement_id=requirement_id,
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        created_by=current_user.id
    )
    db.session.add(link)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Link created'})

@app.route('/api/trace-link/<int:link_id>', methods=['DELETE'])
@login_required
def remove_trace_link(link_id):
    link = TraceabilityLink.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Link removed'})

# ---------- REPORTS ----------

@app.route('/projects/<int:project_id>/reports')
@login_required
def reports(project_id):
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).order_by(Requirement.req_id).all()

    report_data = []
    for req in requirements:
        val = req.get_validation_status()
        report_data.append({
            'req_id': req.req_id,
            'title': req.title,
            'type': req.req_type,
            'priority': req.priority,
            'status': req.status,
            'design_count': req.get_design_count(),
            'test_count': req.get_test_count(),
            'validation_status': val['label'],
            'validation_badge': val['badge']
        })

    return render_template('reports.html', project=project, report_data=report_data)

@app.route('/projects/<int:project_id>/reports/export')
@login_required
def export_report(project_id):
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).order_by(Requirement.req_id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Req ID', 'Title', 'Type', 'Priority', 'Status', 'Design Links', 'Test Links', 'Validation Status'])

    for req in requirements:
        val = req.get_validation_status()
        writer.writerow([
            req.req_id,
            req.title,
            req.req_type,
            req.priority,
            req.status,
            req.get_design_count(),
            req.get_test_count(),
            val['label']
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'treqtrace_report_{project.name.replace(" ", "_")}.csv'
    )

# ---------- USER PROFILE & SETTINGS & NOTIFICATIONS ----------

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        avatar_file = request.files.get('avatar')

        # Check unique constraint if changing username
        if username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash('Username already exists.', 'danger')
                return redirect(url_for('profile'))
            current_user.username = username

        # Check unique constraint if changing email
        if email != current_user.email:
            if User.query.filter_by(email=email).first():
                flash('Email already registered.', 'danger')
                return redirect(url_for('profile'))
            current_user.email = email

        if avatar_file and avatar_file.filename:
            filename = secure_filename(avatar_file.filename)
            unique_name = f"avatar_{current_user.id}_{filename}"
            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            avatar_file.save(avatar_path)
            current_user.avatar = unique_name

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')

        if new_password:
            if new_password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('settings'))
            current_user.set_password(new_password)
            flash('Password changed successfully.', 'success')

        if role and role in ['admin', 'developer', 'tester']:
            current_user.role = role
            flash(f'System role updated to {role.capitalize()}', 'success')

        db.session.commit()
        return redirect(url_for('settings'))

    return render_template('settings.html')

@app.route('/api/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({
        'notifications': [{
            'id': n.id,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M')
        } for n in notifications],
        'unread_count': unread_count
    })

@app.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({Notification.is_read: True}, synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True})

# ---------- FILE SERVING & ADMIN ----------

@app.route('/uploads/<filename>')
@login_required
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=False)

@app.route('/projects/<int:project_id>/upload', methods=['POST'])
@login_required
def upload_project_file(project_id):
    project = Project.query.get_or_404(project_id)
    if 'project_files' not in request.files:
        flash('No file selected.', 'warning')
        return redirect(url_for('view_project', id=project_id))

    files = request.files.getlist('project_files')
    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_name = f"project_{project_id}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(file_path)

            artifact = DesignArtifact(
                project_id=project_id,
                name=filename,
                artifact_type='Uploaded Document',
                description=f'Uploaded project file: {filename}',
                reference_link=unique_name
            )
            db.session.add(artifact)
    db.session.commit()
    flash('File(s) uploaded successfully!', 'success')
    return redirect(url_for('view_project', id=project_id))

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('Admin access required.', 'danger')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/<int:id>/role', methods=['POST'])
@login_required
def update_user_role(id):
    if not current_user.is_admin():
        return jsonify({'success': False})
    user = User.query.get_or_404(id)
    user.role = request.form.get('role')
    db.session.commit()
    flash(f'Role updated for {user.username}.', 'success')
    return redirect(url_for('admin_users'))

# ---------- INIT DB ----------

@app.route('/init-db')
def init_db():
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@treqtrace.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    return 'Database initialized! Default admin: admin / admin123'

# ======================== MAIN ========================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        try:
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN avatar VARCHAR(256)"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@treqtrace.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True, host='0.0.0.0', port=5000)
