from flask import render_template, request, send_from_directory, redirect, url_for, flash, abort, send_file
from flask_login import login_required, current_user, logout_user
from app import create_app, db
from app.controllers.content_controller import ContentController
from app.services.format_service import FormatService
from app.services.audio_service import AudioService
from app.models.user import User
from app.models.feedback import Feedback
from app.models.content import Content
from app.models.log import ActivityLog
from app.models.score import Score
import os
import json

app = create_app()

SYSTEM_CONFIG = {'maintenance': False, 'ai_model': 'gemini'}

with app.app_context():
    if not User.query.filter_by(role='Admin').first():
        try:
            u=User(email='admin@admin.com',role='Admin'); u.set_password('admin123')
            db.session.add(u); db.session.commit()
        except: pass

def log_activity(action, details):
    if current_user.is_authenticated:
        try: db.session.add(ActivityLog(user_id=current_user.id, action=action, details=details)); db.session.commit()
        except: pass

def get_smart_title(text): return "Lesson_Summary"

# --- USER ROUTES ---
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    result = None
    if request.method == 'POST':
        result = ContentController().generate_summary(request.form.get('text'), request.files.get('file'), request.form.get('length'), request.form.get('language'))
        if result: log_activity("Generate", "Success")
        else: flash("Please enter text or upload a valid file.", "danger")
    return render_template('index.html', result=result, user=current_user)

@app.route('/dashboard')
@login_required
def dashboard():
    scores = Score.query.filter_by(user_id=current_user.id).all()
    total = len(scores)
    avg = int(sum([s.percentage for s in scores]) / total) if total > 0 else 0
    stats = {'avg': avg, 'quizzes': total, 'summaries': Content.query.filter_by(user_id=current_user.id).count()}
    return render_template('dashboard.html', user=current_user, stats=stats)

@app.route('/profile')
@login_required
def profile(): return render_template('profile.html', user=current_user)

@app.route('/history')
@login_required
def history(): return render_template('history.html', history=ContentController().get_history())

@app.route('/delete-content/<int:id>', methods=['POST'])
@login_required
def delete_content(id):
    c = Content.query.get_or_404(id)
    if c.user_id != current_user.id: abort(403)
    try: Score.query.filter_by(content_id=id).delete(); Feedback.query.filter_by(content_id=id).delete(); db.session.delete(c); db.session.commit(); flash('Content deleted.', 'success')
    except: db.session.rollback(); flash('Error.', 'danger')
    return redirect(url_for('history'))

@app.route('/listen/<int:id>')
@login_required
def listen_summary(id):
    c = Content.query.get_or_404(id)
    if c.user_id != current_user.id: abort(403)
    f = AudioService().generate_audio(c.summary_text)
    return send_file(f, mimetype="audio/mpeg", download_name=f"summary_{id}.mp3") if f else ("Audio Error", 500)

@app.route('/take-quiz/<int:id>', methods=['GET','POST'])
@login_required
def take_quiz(id):
    c = Content.query.get_or_404(id)
    q_data = c.get_quiz_data()
    if request.method == 'POST':
        correct = 0; results = []
        for i, q in enumerate(q_data):
            user_ans = request.form.get(f'question_{i}')
            is_correct = (user_ans == q['answer'])
            if is_correct: correct += 1
            results.append({'question': q['question'], 'user_answer': user_ans, 'correct_answer': q['answer'], 'is_correct': is_correct})
        perc = (correct / len(q_data)) * 100 if q_data else 0
        db.session.add(Score(user_id=current_user.id, content_id=id, correct_count=correct, total_questions=len(q_data), percentage=perc))
        db.session.commit(); log_activity("Take Quiz", f"Score: {int(perc)}%")
        return render_template('quiz_result.html', score=correct, total=len(q_data), results=results, percentage=int(perc))
    return render_template('quiz.html', questions=q_data, content=c)

@app.route('/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):
    c = Content.query.get_or_404(id)
    if request.method == 'POST':
        c.summary_text = request.form.get('summary_text')
        curr = c.get_quiz_data(); new_q = []
        for i in range(len(curr)):
            q_text = request.form.get(f'question_{i}'); ans = request.form.get(f'answer_{i}')
            opts = [request.form.get(k) for k in request.form if k.startswith(f'option_{i}_')]
            new_q.append({'question': q_text, 'answer': ans, 'options': opts + [ans]})
        c.quiz_data_json = json.dumps(new_q); db.session.commit(); flash('Updated!', 'success')
        return redirect(url_for('history'))
    return render_template('edit.html', content=c, quiz_questions=c.get_quiz_data())

@app.route('/download/<int:id>')
@login_required
def dl_pdf(id):
    c = Content.query.get_or_404(id)
    try:
        f = FormatService().generate_pdf({'summary':c.summary_text, 'quiz':c.get_quiz_data()}, id, "Summary")
        d = os.path.join(app.root_path, 'app', 'static')
        if not os.path.exists(os.path.join(d, f)): d = os.path.join(app.root_path, 'static')
        return send_from_directory(d, f, as_attachment=True)
    except Exception as e: return f"Error: {e}", 500

@app.route('/download-word/<int:id>')
@login_required
def dl_word(id):
    c = Content.query.get_or_404(id)
    try:
        f = FormatService().generate_word({'summary':c.summary_text, 'quiz':c.get_quiz_data()}, id, "Summary")
        d = os.path.join(app.root_path, 'app', 'static')
        if not os.path.exists(os.path.join(d, f)): d = os.path.join(app.root_path, 'static')
        return send_from_directory(d, f, as_attachment=True)
    except Exception as e: return f"Error: {e}", 500

@app.route('/feedback/<int:content_id>', methods=['POST'])
@login_required
def submit_feedback(content_id):
    try: db.session.add(Feedback(user_id=current_user.id, content_id=content_id, rating=request.form.get('rating'), comment=request.form.get('comment'))); db.session.commit(); flash('Thanks!', 'success')
    except: pass
    return redirect(url_for('history'))

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    if request.form.get('new_password'): current_user.set_password(request.form.get('new_password')); db.session.commit(); flash('Password Updated', 'success')
    return redirect(url_for('profile'))

@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account(): db.session.delete(current_user); db.session.commit(); return redirect(url_for('login_page'))

# --- AUTH ---
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method=='POST':
        if not User.query.filter_by(email=request.form.get('email')).first():
            u=User(email=request.form.get('email'),role='Student'); u.set_password(request.form.get('password')); db.session.add(u); db.session.commit(); flash('Account created!', 'success'); return redirect(url_for('login_page'))
        else: flash('Email exists.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method=='POST':
        u = User.query.filter_by(email=request.form.get('email')).first()
        if u and u.check_password(request.form.get('password')):
            if SYSTEM_CONFIG['maintenance'] and u.role != 'Admin': flash('⚠️ Maintenance Mode Active.', 'warning'); return redirect(url_for('login_page'))
            from flask_login import login_user; login_user(u)
            return redirect(url_for('admin_dashboard')) if u.role == 'Admin' else redirect(url_for('index'))
        else: flash('Incorrect credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout(): logout_user(); flash('Logged out.', 'success'); return redirect(url_for('login_page'))

# --- ADMIN ---
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin: abort(403)
    metrics = {'users': User.query.count(), 'contents': Content.query.count(), 'feedbacks': Feedback.query.count(), 'avg_rating': db.session.query(db.func.avg(Feedback.rating)).scalar() or 0}
    return render_template('admin/dashboard.html', metrics=metrics, users=User.query.all(), logs=ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all(), feedbacks=Feedback.query.order_by(Feedback.created_at.desc()).limit(5).all(), current_user=current_user, config=SYSTEM_CONFIG)

@app.route('/admin/user/<int:user_id>')
@login_required
def admin_user_detail(user_id):
    if not current_user.is_admin: abort(403)
    target_user = User.query.get_or_404(user_id)
    user_logs = ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.timestamp.desc()).all()
    user_scores = Score.query.filter_by(user_id=user_id).all()
    quiz_count = len(user_scores)
    avg_score = int(sum([s.percentage for s in user_scores]) / quiz_count) if quiz_count > 0 else 0
    return render_template('admin/user_detail.html', user=target_user, logs=user_logs, scores=user_scores, quiz_count=quiz_count, avg_score=avg_score)

@app.route('/admin/create-admin', methods=['POST'])
@login_required
def admin_create_admin():
    if not current_user.is_admin: abort(403)
    if not User.query.filter_by(email=request.form.get('email')).first(): u=User(email=request.form.get('email'),role='Admin'); u.set_password(request.form.get('password')); db.session.add(u); db.session.commit(); flash('Admin added.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin: abort(403)
    if user_id != current_user.id: User.query.filter_by(id=user_id).delete(); db.session.commit(); flash('User deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reset-password/<int:user_id>', methods=['POST'])
@login_required
def admin_reset_password(user_id):
    if not current_user.is_admin: abort(403)
    u=User.query.get(user_id); u.set_password('123456'); db.session.commit(); flash('Password reset.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/config', methods=['POST'])
@login_required
def admin_config():
    if not current_user.is_admin: abort(403)
    action = request.form.get('action')
    if action == 'clear_cache':
        folder = os.path.join(app.root_path, 'static')
        if not os.path.exists(folder): folder = os.path.join(app.root_path, 'app', 'static')
        count = 0
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if f.startswith("summary_"): os.remove(os.path.join(folder, f)); count += 1
        flash(f'Cleared {count} files.', 'success')
    elif action == 'save_settings':
        SYSTEM_CONFIG['ai_model'] = request.form.get('ai_model')
        SYSTEM_CONFIG['maintenance'] = (request.form.get('maintenance_mode') == 'on')
        flash('Settings saved.', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    if not os.path.exists('app/static'): os.makedirs('app/static')
    app.run(debug=True)