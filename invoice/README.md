# Billix Invoice Studio

Billix is a responsive invoice-generation web application built with Python
and Flask. It helps small businesses create professional invoices, reuse
customer and business details, keep an invoice history, and print or save
invoices as PDF files.

 
## Features

### Invoice creation

- Automatic invoice number and current date
- Bill-to customer information
- Bill-from business information
- Email and address fields
- Invoice status: Draft, Sent, Paid, or Saved
- Due date
- GSTIN or tax ID
- Payment terms
- Bank account and UPI details
- Optional notes

### Items and totals

- Add as many line items as required
- Remove individual line items
- Quantity and price/rate fields
- Automatic subtotal calculation
- Percentage tax calculation
- Percentage discount calculation
- Final total calculation in Indian rupee format

### Profiles and history

- Save and reuse shop profiles
- Save and reuse customer profiles
- Save invoices to invoice history
- Load saved invoices from history
- Start a new invoice without deleting saved data
- Keep up to 50 invoices in the current Flask session

### Preview and delivery

- Full invoice preview before saving
- Classic and Clean invoice templates
- Optional business logo
- Toggle payment information in the preview
- Print invoice or use the browser's **Save as PDF** option
- Share invoice through an email link
- Send invoice through a pre-filled email link

### Backup and responsive design

- Export shops, customers, and invoice history to JSON
- Import a previously exported JSON backup
- Responsive layout for desktop, tablet, and mobile screens
- Mobile-friendly stacked forms and controls
- Horizontally scrollable invoice tables on small screens
- Print-specific styling that removes editing controls

## How the application works

1. Open the Flask application in a browser.
2. Enter the business and customer details.
3. Add invoice items with quantity and price.
4. Enter tax and discount percentages if needed.
5. Add payment information, notes, a logo, or a template choice.
6. Select **Preview invoice** to review the finished invoice.
7. Save the invoice, print it, save it as PDF, or send it by email.
8. Reuse saved profiles and invoices from the toolbar.
9. Export a JSON backup before moving to another browser or clearing session data.

## Technology

- Python 3.10+
- Flask 3.x
- Jinja2 server-side templates
- HTML5 form controls
- CSS3 responsive layout
- Flask signed sessions
- Browser print-to-PDF

## Project structure

```text
invoice/
├── app.py
├── requirements.txt
├── README.md
├── static/
│   └── style.css
└── templates/
    ├── invoice.html
    └── _invoice_preview.html
```

### Main files

- `app.py` contains routes, invoice calculations, session state, profile
  handling, history, backup import/export, and email links.
- `templates/invoice.html` contains the editor, toolbar, forms, and preview
  page layout.
- `templates/_invoice_preview.html` contains the printable invoice document.
- `static/style.css` contains the visual design, responsive breakpoints, and
  print rules.
- `requirements.txt` contains the Python dependency list.

## Installation

### Prerequisites

- Python 3.10 or newer
- pip

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Start the development server

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

### Configure the session key

The development server uses a fallback key. Set a strong secret key before
deployment:

PowerShell:

```powershell
$env:BILLIX_SECRET_KEY = "replace-with-a-long-random-secret"
python app.py
```

Command Prompt:

```cmd
set BILLIX_SECRET_KEY=replace-with-a-long-random-secret
python app.py
```

## Data storage

Invoice data is currently stored in Flask's signed session cookie. This keeps
the application simple and requires no database, but it is intended for local
or small-scale use. Large logos and long invoice histories may exceed cookie
size limits.

For production use, move session data to a server-side store such as Redis,
SQLite, or PostgreSQL and use a production WSGI server.

The JSON backup contains:

- Shop profiles
- Customer profiles
- Saved invoice history

The generated backup file is named `billix-backup.json`.

## Responsive behavior

- Desktop: multi-column party details, settings, and totals
- Tablet: reduced spacing and two-column settings sections
- Mobile: stacked forms, full-width toolbar actions, stacked preview sections,
  and horizontally scrollable item tables
- Print: hides navigation and action buttons and expands the invoice to the
  printable page width

## Limitations

- PDF output uses the browser's native print dialog rather than a server-side
  PDF engine.
- Share and send actions open a `mailto:` link; the user's email application
  completes delivery.
- Session data is not a permanent database.
- No user authentication is included.

## License

MIT
