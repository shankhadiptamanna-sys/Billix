import json
import os
from urllib.parse import quote
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, session, url_for


BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))
app.secret_key = os.environ.get("BILLIX_SECRET_KEY", "billix-development-key")


DEFAULT_STATE = {
    "invoiceNumber": 1,
    "shopName": "",
    "billTo": "",
    "billToEmail": "",
    "billToAddress": "",
    "billFrom": "",
    "billFromEmail": "",
    "billFromAddress": "",
    "gstin": "",
    "dueDate": "",
    "status": "Draft",
    "paymentTerms": "",
    "bankName": "",
    "bankAccount": "",
    "upiId": "",
    "showPaymentDetails": True,
    "template": "classic",
    "notes": "",
    "taxRate": 0,
    "discountRate": 0,
    "currentDate": date.today().strftime("%d/%m/%Y"),
}


def get_state():
    state = deepcopy(DEFAULT_STATE)
    state.update(session.get("invoice", {}))
    state["invoiceNumber"] = int(state.get("invoiceNumber") or 1)
    return state


def get_items():
    return session.get("items", [{"name": "", "quantity": 0, "price": 1.0}])


def money(value):
    return f"₹{value:,.2f}"


def calculate(state, items):
    subtotal = sum(float(item.get("price") or 0) * int(item.get("quantity") or 0) for item in items)
    tax = subtotal * float(state.get("taxRate") or 0) / 100
    discount = subtotal * float(state.get("discountRate") or 0) / 100
    return {
        "subtotal": subtotal,
        "tax": tax,
        "discount": discount,
        "total": subtotal - discount + tax,
        "subtotal_display": money(subtotal),
        "tax_display": money(tax),
        "discount_display": money(discount),
        "total_display": money(subtotal - discount + tax),
    }


def mailto_link(state, totals, action="share"):
    subject = f"Invoice {state['invoiceNumber']} from {state.get('shopName') or 'Billix'}"
    body = (
        f"{state.get('shopName') or 'Billix'} invoice #{state['invoiceNumber']}\n"
        f"Total: {totals['total_display']}\n"
        f"Status: {state.get('status') or 'Draft'}"
    )
    recipient = state.get("billToEmail", "") if action == "share" else ""
    return f"mailto:{recipient}?subject={quote(subject)}&body={quote(body)}"


def parse_form():
    state = get_state()
    for key in DEFAULT_STATE:
        if key in request.form and key not in {"invoiceNumber", "showPaymentDetails"}:
            state[key] = request.form.get(key, "")
    state["invoiceNumber"] = int(request.form.get("invoiceNumber") or 1)
    state["taxRate"] = float(request.form.get("taxRate") or 0)
    state["discountRate"] = float(request.form.get("discountRate") or 0)
    state["showPaymentDetails"] = request.form.get("showPaymentDetails") == "on"
    state["currentDate"] = state.get("currentDate") or date.today().strftime("%d/%m/%Y")
    logo = request.files.get("logo")
    if logo and logo.filename:
        import base64
        state["logo"] = f"data:{logo.mimetype};base64,{base64.b64encode(logo.read()).decode('ascii')}"
    items = []
    names = request.form.getlist("item_name")
    quantities = request.form.getlist("item_quantity")
    prices = request.form.getlist("item_price")
    for name, quantity, price in zip(names, quantities, prices):
        items.append({"name": name, "quantity": int(quantity or 0), "price": float(price or 0)})
    return state, items or [{"name": "", "quantity": 0, "price": 1.0}]


@app.get("/")
def index():
    state = get_state()
    items = get_items()
    totals = calculate(state, items)
    return render_template(
        "invoice.html",
        state=state,
        items=items,
        totals=totals,
        shops=session.get("shops", []),
        customers=session.get("customers", []),
        history=session.get("history", []),
        preview=False,
        print_mode=False,
        share_link=mailto_link(state, totals),
        send_link=mailto_link(state, totals, "send"),
    )


@app.post("/invoice")
def save_form():
    state, items = parse_form()
    action = request.form.get("action", "preview")
    session["invoice"] = state
    session["items"] = items
    item_action = request.form.get("item_action")
    remove_index = request.form.get("remove_index")
    if item_action == "add":
        items.append({"name": "", "quantity": 0, "price": 1.0})
        session["items"] = items
        return redirect(url_for("index"))
    if remove_index is not None:
        index = int(remove_index)
        if 0 <= index < len(items):
            items.pop(index)
        session["items"] = items or [{"name": "", "quantity": 0, "price": 1.0}]
        return redirect(url_for("index"))

    if action == "new":
        next_number = int(session.get("next_invoice", state["invoiceNumber"] + 1))
        session["invoice"] = {**deepcopy(DEFAULT_STATE), "invoiceNumber": next_number, "currentDate": date.today().strftime("%d/%m/%Y")}
        session["items"] = [{"name": "", "quantity": 0, "price": 1.0}]
        return redirect(url_for("index"))
    if action == "save_shop":
        save_profile("shop", state)
    elif action == "save_customer":
        save_profile("customer", state)
    elif action == "save":
        save_invoice(state, items)
        flash("Invoice saved successfully.", "success")
    elif action == "export":
        return export_backup()
    elif action == "preview":
        totals = calculate(state, items)
        return render_template(
            "invoice.html",
            state=state,
            items=items,
            totals=totals,
            shops=session.get("shops", []),
            customers=session.get("customers", []),
            history=session.get("history", []),
            preview=True,
            print_mode=False,
            share_link=mailto_link(state, totals),
            send_link=mailto_link(state, totals, "send"),
        )
    return redirect(url_for("index"))


def save_profile(profile_type, state):
    key = "shops" if profile_type == "shop" else "customers"
    if profile_type == "shop":
        profile = {field: state.get(field, "") for field in ("shopName", "billFrom", "billFromEmail", "billFromAddress", "gstin", "bankName", "bankAccount", "upiId")}
        profile["id"] = profile["shopName"] or profile["billFrom"]
    else:
        profile = {field: state.get(field, "") for field in ("billTo", "billToEmail", "billToAddress")}
        profile["id"] = profile["billTo"]
    if not profile["id"]:
        flash("Enter a name before saving the profile.", "warning")
        return
    profiles = [item for item in session.get(key, []) if item.get("id") != profile["id"]]
    session[key] = [profile, *profiles]
    flash(f"{profile_type.title()} profile saved.", "success")


def save_invoice(state, items):
    invoice = {
        "id": f"{datetime.now().timestamp()}-{state['invoiceNumber']}",
        "savedAt": datetime.now().isoformat(),
        "info": {**state, "status": "Saved"},
        "items": items,
    }
    history = [item for item in session.get("history", []) if item["id"] != invoice["id"]]
    session["history"] = [invoice, *history][:50]
    session["next_invoice"] = state["invoiceNumber"] + 1
    session["invoice"] = invoice["info"]


@app.post("/profile/<profile_type>")
def load_profile(profile_type):
    profile_id = request.form.get("profile_id", "")
    key = "shops" if profile_type == "shop" else "customers"
    profile = next((item for item in session.get(key, []) if item.get("id") == profile_id), None)
    if profile:
        state = get_state()
        state.update(profile)
        session["invoice"] = state
    return redirect(url_for("index"))


@app.post("/history")
def load_invoice():
    invoice_id = request.form.get("invoice_id", "")
    invoice = next((item for item in session.get("history", []) if item["id"] == invoice_id), None)
    if invoice:
        session["invoice"] = invoice["info"]
        session["items"] = invoice["items"]
    return redirect(url_for("index"))


@app.get("/invoice/print")
def print_invoice():
    state = get_state()
    items = get_items()
    totals = calculate(state, items)
    return render_template(
        "invoice.html",
        state=state,
        items=items,
        totals=totals,
        shops=session.get("shops", []),
        customers=session.get("customers", []),
        history=session.get("history", []),
        preview=True,
        print_mode=True,
        share_link=mailto_link(state, totals),
        send_link=mailto_link(state, totals, "send"),
    )


@app.get("/backup/export")
def export_backup():
    payload = json.dumps({
        "shops": session.get("shops", []),
        "customers": session.get("customers", []),
        "history": session.get("history", []),
    }, indent=2)
    path = BASE_DIR / "billix-backup.json"
    path.write_text(payload, encoding="utf-8")
    return send_file(path, as_attachment=True, download_name="billix-backup.json")


@app.post("/backup/import")
def import_backup():
    upload = request.files.get("backup")
    if upload:
        try:
            backup = json.load(upload)
            session["shops"] = backup.get("shops", [])
            session["customers"] = backup.get("customers", [])
            session["history"] = backup.get("history", [])
            flash("Backup imported successfully.", "success")
        except (json.JSONDecodeError, UnicodeDecodeError):
            flash("The selected backup file is not valid JSON.", "danger")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
