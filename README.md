# SubTrack — Subscription Management System

> An Odoo-inspired enterprise subscription and recurring revenue management prototype built with Django 5, Bootstrap 5.3, Chart.js, and MySQL / SQLite.

---

## 📋 Overview

**SubTrack** is a recurring billing and subscription management platform modeled after modern enterprise ERP systems like Odoo. It handles full customer subscription lifecycles, automated multi-cycle billing, discount coupon validation, sequential invoice generation, payment reconciliation, and an executive KPI dashboard featuring Monthly Recurring Revenue (MRR) and Annual Recurring Revenue (ARR) analytics.

---

## ✨ Key Features

### 1. 👥 Role-Based Access Control (RBAC)
- **Admin**: Full control over products, subscription plans, discount codes, team management, customer accounts, and system configuration.
- **Staff / Finance**: Operational access to manage customer subscriptions, issue invoices, reconcile payment remittances, and review MSME economic statistics.
- **Customer**: Dedicated self-service customer portal to view active subscriptions, download printable invoices, track payment histories, and inspect outstanding balances.

### 2. 📦 Product Catalog & Multi-Cycle Plans
- Standalone products and modular recurring plans.
- Flexible billing cycles: **Monthly**, **Quarterly (3 Months)**, and **Yearly (12 Months)**.
- Normalized monthly revenue calculation for accurate MRR/ARR projections.

### 3. 🏷️ Discount & Voucher Engine
- Percentage-based (%) or flat-dollar ($) discount codes.
- Configurable validity ranges (`valid_from` &rarr; `valid_to`) and usage limits (`usage_limit`).
- Live interactive AJAX validation tool on the discount dashboard.
- Safe date comparison engine resistant to type mismatch errors.

### 4. 📄 Invoicing & Sequential Numbering
- Automated and custom invoice generation per billing cycle.
- Standardized fiscal sequential numbering format: `INV-YYYY-XXXX` (e.g. `INV-2026-0001`).
- Clean, print-ready invoice view with customizable CSS print layouts.
- Auto-status progression: `Draft` &rarr; `Sent / Unpaid` &rarr; `Paid` or `Overdue`.

### 5. 💳 Payment Processing & Reconciliation
- Support for multiple payment methods: Credit/Debit Card, UPI / QR, Net Banking, Cash, and Cheque.
- Real-time balance due updates and partial payment support.
- Validation preventing overpayment beyond the outstanding invoice balance.
- Automatic invoice status reconciliation upon settlement.

### 6. 📊 Executive Dashboard & Analytics
- Live KPI cards: **Monthly Recurring Revenue (MRR)**, **Annual Recurring Revenue (ARR)**, **Active Subscriptions**, **Total Collections**, and **Overdue Receivables**.
- **Chart.js** visualizations:
  - 12-Month Historical Revenue Trend bar chart.
  - Subscription status distribution doughnut chart.
- Real-time recent payment stream and MSME enterprise economic sector benchmark data.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.14 / Django 5.x |
| **Database** | SQLite (Default for rapid local prototyping) / MySQL via PyMySQL |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Bootstrap 5.3, Bootstrap Icons |
| **Charts** | Chart.js 4.4 |
| **Configuration** | Python-Decouple (`.env` support) |

---

## 📁 Project Structure

```text
Subscription-Management-System/
├── accounts/               # Custom User model, authentication, RBAC mixins & views
├── catalog/                # Products, subscription plans, pricing tiers
├── subscriptions/          # Subscription lifecycle, next billing date calculator
├── billing/                # Discounts, Invoices, Payments, reconciliation services
├── dashboard/              # Executive KPI aggregation, MSME statistical data, Chart.js views
├── config/                 # Django project settings, URL routing, WSGI/ASGI handlers
├── templates/              # Semantic Bootstrap 5 HTML templates
│   ├── accounts/
│   ├── catalog/
│   ├── subscriptions/
│   ├── billing/
│   ├── dashboard/
│   └── errors/             # Custom 403 Forbidden and 404 Not Found pages
├── static/
│   └── css/style.css       # Unified design system and print stylesheets
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone & Set Up Virtual Environment

```bash
cd Subscription-Management-System

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Copy the provided `.env.example` into `.env`:

```bash
cp .env.example .env
```

*(By default, `DB_ENGINE=sqlite` is enabled for plug-and-play local execution).*

### 4. Run Migrations & Seed Demo Data

```bash
python manage.py migrate
python manage.py seed_demo_data
```

The `seed_demo_data` command populates the database with realistic products, subscription plans, discount vouchers, subscriptions across 6 months, paid/partial/overdue invoices, payments, and MSME sector benchmarks.

### 5. Launch the Development Server

```bash
python manage.py runserver 127.0.0.1:8000
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## 🔑 Demo User Accounts

| Role | Username | Password | Access Capabilities |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Full administrative control, catalog CRUD, discounts, users |
| **Staff** | `staff_priya` | `staff123` | Operational dashboard, subscription management, invoicing, payments |
| **Customer** | `cust_arun` | `cust123` | Customer portal, subscription details, invoices & printable view |
| **Customer** | `cust_meera` | `cust123` | Self-service subscription tracking |
| **Customer** | `cust_karan` | `cust123` | Self-service subscription tracking |

*(Quick demo buttons are also present on the login screen for one-click credentials auto-fill).*

---

## 🧪 Automated Testing

Run the full automated test suite covering permissions, date calculations, discounts, invoice numbering, MRR aggregation, and payment reconciliation:

```bash
python manage.py test
```

All 23 unit and integration tests will execute against an isolated test database.