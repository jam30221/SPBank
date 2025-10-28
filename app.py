from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import time
import random
import string
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, os
import shutil
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

TX_FILE = "transactions.json"

def load_transactions():
    if not os.path.exists(TX_FILE):
        return []
    with open(TX_FILE, "r") as f:
        return json.load(f)

def save_transactions(transactions):
    with open(TX_FILE, "w") as f:
        json.dump(transactions, f, indent=2)

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_user_by_username(username):
    for u in load_users():
        if u["username"] == username:
            return u
    return None

def get_user_by_email(email):
    for u in load_users():
        if u["email"] == email:
            return u
    return None

app = Flask(__name__)
@app.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        complaint_id = str(uuid.uuid4())[:8]  # short unique ID
        data = {
            "first_name": request.form['first_name'],
            "last_name": request.form['last_name'],
            "email": request.form['email'],
            "phone": request.form.get('phone'),
            "complaint_id": complaint_id,
            "complaint_text": request.form['complaint_text']
        }
        print("Complaint received:", data)
        # Redirect to confirmation page with ticket number
        return redirect(url_for('support_success', ticket=complaint_id))
    return render_template("support.html")

@app.route('/support/success/<ticket>')
def support_success(ticket):
    return render_template("support_success.html", ticket=ticket)
app.secret_key = "spartex_private_bank_secret"

# Site-wide branding and contact
SITE_NAME = "Spartex Private Bank International"
CONTACT_PHONE = "+7(495)8352434"
CONTACT_EMAIL = "info@spbankint.com"

@app.route("/login", methods=["GET", "POST"])
def login_view():
    if "attempts" not in session:
        session["attempts"] = 5

    error_message = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        pin = request.form.get("pin", "").strip()

        user = get_user_by_username(username)

        if user and user["password"] == password and user["pin"] == pin:
            session["user"] = username   # store logged-in user
            # store avatar in session for header display (use ProfileAvatar.png default)
            session["avatar"] = user.get("avatar", "ProfileAvatar.png")
            session["attempts"] = 5      # reset attempts
            return redirect(url_for("dashboard"))  # ✅ correct target
        else:
            session["attempts"] -= 1
            if session["attempts"] <= 0:
                session["attempts"] = 5
                return redirect(url_for("forgot_password_view"))  # make sure this route exists
            error_message = f"Invalid username, password, or PIN. Remaining attempts: {session['attempts']}"

    return render_template("login.html", error_message=error_message)


@app.route("/forgot-username", methods=["GET", "POST"])
def forgot_username_view():
    if request.method == "POST":
        email = request.form.get("email")
        user = get_user_by_email(email)
        if user:
            return render_template("reset_success.html", message="Instructions to recover your username have been sent to your email.")
        return "Email not found"
    return render_template("forgot_form.html", title="Forgot Username")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password_view():
    if request.method == "POST":
        email = request.form.get("email")
        user = get_user_by_email(email)
        if user:
            return render_template("reset_success.html", message="Instructions to reset your password have been sent to your email.")
        return "Email not found"
    return render_template("forgot_form.html", title="Forgot Password")


@app.route("/reset-pin", methods=["GET", "POST"])
def reset_pin_view():
    if request.method == "POST":
        email = request.form.get("email")
        user = get_user_by_email(email)
        if user:
            return render_template("reset_success.html", message="Instructions to reset your PIN have been sent to your email.")
        return "Email not found"
    return render_template("forgot_form.html", title="Reset PIN")


# Utility
def mk_checksum(n=20):
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choice(alphabet) for _ in range(n))

def fmt_amount(value):
    try:
        f = float(value)
        # Show 2–3 decimals when appropriate, else whole number with commas
        if abs(f - int(f)) > 0:
            return f"US$ {f:,.2f}"
        return f"US$ {int(f):,}"
    except:
        return f"US$ {value}"

@app.context_processor
def inject_globals():
    return {
        "SITE_NAME": SITE_NAME,
        "CONTACT_PHONE": CONTACT_PHONE,
        "CONTACT_EMAIL": CONTACT_EMAIL,
        "fmt_amount": fmt_amount
    }


# Helper to resolve avatar URL (search uploads first, then static root)
@app.context_processor
def avatar_helpers():
    def avatar_url(avatar_filename=None):
        # prefer explicit filename passed in, else session, else default
        av = avatar_filename or session.get('avatar') or 'ProfileAvatar.png'
        # build absolute filesystem paths using app.root_path for reliability
        uploads_fs = os.path.join(app.root_path, 'static', 'uploads', 'avatars', av)
        root_fs = os.path.join(app.root_path, 'static', av)
        try:
            if av and os.path.exists(uploads_fs):
                # use forward-slash path for the URL
                return url_for('static', filename=f'uploads/avatars/{av}')
            if av and os.path.exists(root_fs):
                return url_for('static', filename=av)
        except Exception:
            pass
        return url_for('static', filename='ProfileAvatar.png')

    return { 'avatar_url': avatar_url }

# In-memory data (we’ll move to SQLite next)
users = {
    "James Whilfred": {
        "password": "test123",
        "account_number": "765904281",
        "balance": 32102125,
        "deposits_total": 37267.345,
        "withdrawals_total": 15000,
        "transfers_total": 510220,
        "transactions": [
            {"type": "Transfer", "amount": 5000000, "status": "Pending", "owner": "James Whilfred", "timestamp": "17-Oct-2022 08:00:00", "checksum": mk_checksum()},
            {"type": "Deposit",  "amount": 1000000, "status": "Success", "owner": "James Whilfred", "timestamp": "25-Feb-2019 02:10:00", "checksum": mk_checksum()},
            {"type": "Deposit",  "amount": 289.121, "status": "Success", "owner": "James Whilfred", "timestamp": "25-Feb-2019 02:00:00", "checksum": mk_checksum()},
            {"type": "Deposit",  "amount": 15000,   "status": "Success", "owner": "James Whilfred", "timestamp": "25-Feb-2019 01:00:00", "checksum": mk_checksum()},
            {"type": "Deposit",  "amount": 200000,  "status": "Success", "owner": "James Whilfred", "timestamp": "25-Feb-2019 00:00:00", "checksum": mk_checksum()},
            {"type": "Deposit",  "amount": 133300,  "status": "Success", "owner": "James Whilfred", "timestamp": "25-Sep-2018 10:09:00", "checksum": mk_checksum()},
            {"type": "Deposit",  "amount": 100000,  "status": "Success", "owner": "James Whilfred", "timestamp": "25-Sep-2018 09:00:00", "checksum": mk_checksum()},
            {"type": "Deposit",  "amount": 169716,  "status": "Success", "owner": "James Whilfred", "timestamp": "25-Sep-2018 08:00:00", "checksum": mk_checksum()},
            {"type": "Deposit",  "amount": 4342010, "status": "Success", "owner": "James Whilfred", "timestamp": "18-Jun-2018 02:00:00", "checksum": mk_checksum()},
            {"type": "Transfer", "amount": 5000.00, "status": "Success", "owner": "James Whilfred", "timestamp": "01-Oct-2025 11:00:00", "checksum": mk_checksum()},
            {"type": "Deposit",  "amount": 1000.00, "status": "Success", "owner": "James Whilfred", "timestamp": "01-Oct-2025 10:50:00", "checksum": mk_checksum()},
            {"type": "Deposit",  "amount": 289.12,  "status": "Success", "owner": "James Whilfred", "timestamp": "01-Oct-2025 10:40:00", "checksum": mk_checksum()},
        ]
    }
}

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        pin = request.form.get("pin", "").strip()
        email = request.form.get("email", "").strip()

        users = load_users()
        if any(u["username"] == username for u in users):
            message = "Username already exists."
        else:
            new_user = {
                "username": username,
                "password": password,
                "pin": pin,
                "email": email,
                "account_number": str(random.randint(100000000, 999999999)),
                "balance": 0,
                "deposits_total": 0,
                "withdrawals_total": 0,
                "transfers_total": 0,
                "transactions": []
            }
            users.append(new_user)
            save_users(users)
            # ✅ redirect to success page
            return redirect(url_for("signup_success"))

    return render_template("signup.html", message=message)


@app.route("/signup/success")
def signup_success():
    return render_template(
        "success.html",
        message="Your application has been submitted successfully. We will get back to you after processing."
    )


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login_view"))
    uname = session["user"]
    # load the canonical user record from storage (users.json) if present
    user = get_user_by_username(uname)
    # if we don't have a persisted user, fall back to a minimal in-memory user
    if not user:
        user = {"username": uname, "avatar": session.get("avatar", "ProfileAvatar.png"),
                "balance": 0, "withdrawals_total": 0, "deposits_total": 0, "transfers_total": 0,
                "transactions": []}

    # recent transactions from the transactions.json file for this user
    transactions = load_transactions()
    user_tx = [tx for tx in transactions if tx.get("user") == uname]
    # also expose all persisted transactions to the dashboard so it can render
    # a transaction history block (Recent + Pending) without additional requests
    persisted_transactions = transactions

    if "login_time" not in session:
        session["login_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if request.method == "POST":
        # use a consistent timestamp for any transaction created during this POST
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        action = request.form.get("action")
        amount_raw = request.form.get("amount", "").strip()
        recipient = request.form.get("recipient", "").strip()

        # Parse amount safely
        try:
            amount = float(amount_raw)
            if amount <= 0:
                amount = None
        except ValueError:
            amount = None

        # Deposit
        if action == "deposit" and amount:
            user["balance"] += amount
            user["deposits_total"] += amount
            user["transactions"].insert(0, {
                "type": "Deposit",
                "amount": amount,
                "status": "Success",
                "owner": uname,
                "timestamp": timestamp,
                "checksum": mk_checksum()
            })

            users = load_users()
            for u in users:
                if u["username"] == uname:
                    u.update(user)
                    break
            save_users(users)

        # Withdraw
        elif action == "withdraw" and amount:
            status = "Success" if user["balance"] >= amount else "Pending"
            if status == "Success":
                user["balance"] -= amount
                user["withdrawals_total"] += amount
            user["transactions"].insert(0, {
                "type": "Withdraw",
                "amount": amount,
                "status": status,
                "owner": uname,
                "timestamp": timestamp,
                "checksum": mk_checksum()
            })

            users = load_users()
            for u in users:
                if u["username"] == uname:
                    u.update(user)
                    break
            save_users(users)

        # Transfer
        elif action == "transfer" and amount and recipient and recipient != uname and get_user_by_username(recipient):
            status = "Success" if user["balance"] >= amount else "Pending"
            if status == "Success":
                user["balance"] -= amount
                user["transfers_total"] += amount

                recipient_user = get_user_by_username(recipient)
                recipient_user["balance"] += amount
                recipient_user["transactions"].insert(0, {
                    "type": "Transfer",
                    "amount": amount,
                    "status": "Success",
                    "owner": uname,  # sender recorded on recipient side
                    "timestamp": timestamp,
                    "checksum": mk_checksum()
                })

            # Always log sender’s side
            user["transactions"].insert(0, {
                "type": "Transfer",
                "amount": amount,
                "status": status,
                "owner": uname,
                "timestamp": timestamp,
                "checksum": mk_checksum()
            })

            users = load_users()
            for u in users:
                if u["username"] == uname:
                    u.update(user)
                if status == "Success" and u["username"] == recipient:
                    u.update(recipient_user)
            save_users(users)

    # Summary metrics
    summary = {
        "withdrawals": user["withdrawals_total"],
        "transfers": user["transfers_total"],
        "wallet_balance": user["balance"],
        "deposits": user["deposits_total"]
    }

    latest = user["transactions"][:10]
    user_list = [u["username"] for u in load_users() if u["username"] != uname]
    login_time = session.get("login_time", None)

    # Allow the history page to link back into the dashboard and open the
    # pending transfer tax modal. History provides amount/recipient via query
    # string when linking the example Kathi row.
    open_pending = request.args.get('open_pending')
    open_pending_amount = request.args.get('amount')
    open_pending_recipient = request.args.get('recipient')

    return render_template(
        "dashboard.html",
        user=user,
        username=uname,
        summary=summary,
        latest=latest,
        transactions=user_tx,
        persisted_transactions=persisted_transactions,
        user_list=user_list,
        login_time=login_time,
        open_pending=open_pending,
        open_pending_amount=open_pending_amount,
        open_pending_recipient=open_pending_recipient
    )

# Sidebar pages (scaffold)
@app.route("/accounts")
def accounts():
    if "user" not in session: return redirect (url_for("login_view"))
    return render_template("accounts.html")

@app.route("/deposits")
def deposits():
    if "user" not in session: return redirect(url_for("login_view"))
    return render_template("deposits.html")

@app.route("/withdrawals")
def withdrawals():
    if "user" not in session: return redirect(url_for("login_view"))
    return render_template("withdrawals.html")

@app.route("/transfers", methods=["GET", "POST"])
def transfers():
    if "user" not in session:
        return redirect(url_for("login_view"))

    if request.method == "POST":
        # Capture all form fields
        first_name = request.form.get("first_name")
        middle_name = request.form.get("middle_name")
        last_name = request.form.get("last_name")
        bank_name = request.form.get("bank_name")
        account_number = request.form.get("account_number")
        routing_number = request.form.get("routing_number")
        bank_address = request.form.get("bank_address")
        recipient_number = request.form.get("recipient_number")
        amount = request.form.get("amount")
        login_pin = request.form.get("login_pin")

        # Store temporarily in session for the tax verification step
        session["pending_transfer"] = {
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "bank_name": bank_name,
            "account_number": account_number,
            "routing_number": routing_number,
            "bank_address": bank_address,
            "recipient_number": recipient_number,
            "amount": amount,
        }
        # Keep a local reference to the details we just stored in session
        details = session.get("pending_transfer", {})

        # Create a new pending transaction in JSON
        transactions = load_transactions()
        new_id = (transactions[-1]["id"] + 1) if transactions else 1
        new_tx = {
            "id": new_id,
            "user": session["user"],
            "type": "transfer",
            "recipient": f"{details.get('first_name', '')} {details.get('last_name', '')}",
            "bank_name": details.get("bank_name"),
            "amount": details.get("amount"),
            "status": "pending_tax",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        transactions.append(new_tx)
        save_transactions(transactions)

        # NOTE: this script does not configure a DB connection named `db`.
        # If you have a database and a `db` connection, uncomment and adapt the
        # following block. For now we skip DB persistence to avoid NameError.
        #
        # try:
        #     db.execute(
        #         "INSERT INTO transactions (user_id, recipient, bank_name, amount, status) VALUES (?, ?, ?, ?, ?)",
        #         (session.get("user_id"), f"{details.get('first_name', '')} {details.get('last_name', '')}", details.get("bank_name"), details.get("amount"), "pending_tax")
        #     )
        #     db.commit()
        # except NameError:
        #     # No DB configured; JSON file already updated above
        #     pass

        # Redirect to tax code page
        return redirect(url_for("transfer_tax", tx_id=new_id))

    return render_template("transfers.html", username=session["user"])



@app.route("/transfer_tax", methods=["GET", "POST"])
def transfer_tax():
    if "user" not in session:
        return redirect(url_for("login_view"))

    # Get tx_id from query string (linked from dashboard or earlier redirect)
    tx_id = request.args.get("tx_id", type=int)

    # Load stored transactions (if any). If tx_id is provided, try to find the
    # persisted transaction. If no tx_id is provided, allow an in-session
    # pending_transfer to be completed (dashboard-supplied sample row uses this).
    transactions = load_transactions()
    tx = None
    if tx_id:
        tx = next((t for t in transactions if t.get("id") == tx_id and t.get("user") == session["user"]), None)

    # If we don't have a stored tx AND there's no pending_transfer in session,
    # the request is not authorized to continue.
    if not tx and "pending_transfer" not in session:
        flash("Transaction not found or not authorized.", "danger")
        return redirect(url_for("dashboard"))

    # If tx exists but session pending_transfer is missing, rehydrate it.
    if tx and "pending_transfer" not in session:
        recipient = tx.get('recipient', '')
        parts = recipient.split()
        first = parts[0] if parts else ''
        last = ' '.join(parts[1:]) if len(parts) > 1 else ''
        session['pending_transfer'] = {
            'first_name': first,
            'last_name': last,
            'bank_name': tx.get('bank_name', ''),
            'account_number': tx.get('account_number', ''),
            'routing_number': tx.get('routing_number', ''),
            'bank_address': tx.get('bank_address', ''),
            'recipient_number': tx.get('recipient_number', ''),
            'amount': tx.get('amount')
        }

    details = session['pending_transfer']

    if request.method == "POST":
        tax_code = request.form.get("tax_code")

        # Replace with your real validation
        if tax_code == "123456":
            # If we have a stored tx_id, mark that transaction completed.
            if tx_id:
                for t in transactions:
                    if t.get("id") == tx_id:
                        t["status"] = "completed"
                        break
                save_transactions(transactions)
                # Clear pending session if it was rehydrated
                session.pop("pending_transfer", None)
                flash(f"✅ Transfer of {details.get('amount')} to {details.get('first_name','')} {details.get('last_name','')} has been delivered!", "success")
                return redirect(url_for("dashboard"))

            # No tx_id provided: attempt to complete an ad-hoc transfer using posted fields
            # (this happens when clicking a dashboard sample row that didn't create a persisted tx)
            posted_amount = request.form.get('amount') or (details.get('amount') if details else None)
            posted_recipient = request.form.get('recipient') or (f"{details.get('first_name','')} {details.get('last_name','')}" if details else None)

            # Record a completed transaction for traceability
            try:
                new_id = (transactions[-1]["id"] + 1) if transactions else 1
            except Exception:
                new_id = 1
            new_tx = {
                "id": new_id,
                "user": session["user"],
                "type": "transfer",
                "recipient": posted_recipient or "",
                "bank_name": details.get('bank_name','') if details else '',
                "amount": posted_amount,
                "status": "completed",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            transactions.append(new_tx)
            save_transactions(transactions)

            # Clear pending session (if any)
            session.pop("pending_transfer", None)

            flash(f"✅ Transfer of {posted_amount} to {posted_recipient} has been delivered!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("❌ Invalid Tax Payment Code. Please try again.", "danger")

    # Render tax verification page with details
    return render_template("transfer_tax.html", username=session["user"], details=details, tx_id=tx_id)

@app.route("/history")
def history():
    if "user" not in session:
        return redirect(url_for("login_view"))

    uname = session["user"]
    user = get_user_by_username(uname)
    # Also include persisted transactions (pending or pending_tax) so the history
    # page can show Recent and Pending separately.
    persisted = [t for t in load_transactions() if t.get('user') == uname]
    # Identify pending items explicitly so template logic is simpler and robust
    pending = [t for t in persisted if str(t.get('status','')).lower() in ('pending','pending_tax')]
    return render_template(
        "history.html",
        transactions=user["transactions"],
        persisted_transactions=persisted,
        pending_transactions=pending,
        username=uname
    )


@app.route('/api/transactions')
def api_transactions():
    """Return JSON containing the user's recent transactions (from users.json)
    and persisted transactions (from transactions.json). Used by client-side
    history modal so the hamburger menu can show recent + pending items.
    """
    if 'user' not in session:
        return jsonify({'error': 'not authenticated'}), 401
    uname = session['user']
    user = get_user_by_username(uname) or { 'transactions': [] }
    stored = [t for t in load_transactions() if t.get('user') == uname]
    return jsonify({
        'user_transactions': user.get('transactions', []),
        'stored_transactions': stored
    })


@app.route("/reports")
def reports():
    if "user" not in session: return redirect(url_for("login_view"))

    return render_template("reports.html")

@app.route("/logout")
def logout():
    session.clear()  # clears all session data
    return redirect(url_for("login_view"))


UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads", "avatars")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def ensure_default_avatar_in_uploads():
    """Ensure the uploads/avatars folder exists and contains ProfileAvatar.png.
    This makes the default avatar available at the uploads path so templates
    that expect files there won't show a broken image.
    """
    static_root = os.path.join(app.root_path, 'static')
    target_dir = os.path.join(static_root, 'uploads', 'avatars')
    os.makedirs(target_dir, exist_ok=True)

    src = os.path.join(static_root, 'ProfileAvatar.png')
    dst = os.path.join(target_dir, 'ProfileAvatar.png')
    try:
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copyfile(src, dst)
    except Exception:
        # Non-fatal: if copy fails, templates still fall back to static/ProfileAvatar.png
        pass

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload_avatar", methods=["POST"])
def upload_avatar():
    if "user" not in session:
        return redirect(url_for("login_view"))

    if "avatar" not in request.files:
        flash("No file part", "danger")
        return redirect(url_for("dashboard"))

    file = request.files["avatar"]
    if file.filename == "":
        flash("No selected file", "danger")
        return redirect(url_for("dashboard"))

    if file and allowed_file(file.filename):
        filename = secure_filename(session["user"] + "_avatar." + file.filename.rsplit(".", 1)[1].lower())
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Save avatar path to user record
        user = get_user_by_username(session["user"])
        user["avatar"] = filename
        users = load_users()
        for u in users:
            if u["username"] == session["user"]:
                u.update(user)
                break
        save_users(users)

        # Update session avatar so header shows new picture immediately
        session["avatar"] = filename
        # bump avatar timestamp so browser fetches the latest image
        session["avatar_ts"] = str(int(time.time()))

        flash("Avatar updated successfully!", "success")
    else:
        flash("Invalid file type. Allowed: png, jpg, jpeg, gif", "danger")

    return redirect(url_for("dashboard"))


@app.route("/remove_avatar", methods=["POST"])
def remove_avatar():
    if "user" not in session:
        return redirect(url_for("login_view"))

    user = get_user_by_username(session["user"])
    if "avatar" in user:
        # Delete file if exists
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], user["avatar"])
        if os.path.exists(filepath):
            os.remove(filepath)
        user.pop("avatar")

        users = load_users()
        for u in users:
            if u["username"] == session["user"]:
                u.update(user)
                break
        save_users(users)

    # Update session avatar to default so header updates immediately
    session["avatar"] = "ProfileAvatar.png"
    session["avatar_ts"] = str(int(time.time()))
    flash("Avatar removed, reverted to default.", "info")

    return redirect(url_for("dashboard"))
    
@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    # Ensure uploads folder and default avatar are present before serving
    ensure_default_avatar_in_uploads()
    app.run(debug=True)


