# Odoo · Brightloop Subscription Management System

> A comprehensive, unified subscription and recurring billing platform built according to the **Odoo Subscription Management Challenge** specifications.

---

## 🌟 Overview & Problem Statement

Brightloop Software sells everything on subscription: business software billed by the month or year, add-ons customers switch on and off, and products with brand variants.

This platform replaces fragmented spreadsheets, manual billing, and remembered renewals with a unified digital backbone featuring:
- **Role-Based Access Control (RBAC)** for Administrators, Internal Staff, and Customer Self-Service Portals.
- **Strict Customer Sign-Up & Password Validation** ($> 8$ characters, uppercase, lowercase, special character, and unique email check).
- **Products & Brand Variants** (e.g. Standard vs. Odoo Brand $+₹560$).
- **Flexible Plans & Frequencies** (Daily, Weekly, Monthly, Yearly) with auto-close lifecycle rules.
- **Quotation Templates** to launch offers and turn quotes into subscriptions.
- **5-Stage Subscription Lifecycle**: `Draft` ➔ `Quotation` ➔ `Confirmed` ➔ `Active` ➔ `Closed`.
- **Automated "Billing Day" Batch Engine** with duplicate billing prevention and tax calculation.
- **Admin Discount Rules** with usage limits, scope (whole subscription vs. specific product), and automatic invoice application.
- **Finance Lead Executive Reports** providing instant sub-second answers on active subscriptions, revenue inflow, and overdue receivables.

---

## 👥 Personas & Credentials

The system provides 1-click demo sign-in and credential authentication for all three challenge personas:

| Role | Email | Password | Access & Responsibilities |
| :--- | :--- | :--- | :--- |
| 👑 **Administrator** | `admin@brightloop.com` | `Admin@1234` | Full system control: products, variants, plans, tax rules, discount rules, staff directory, and reports. Only admin can add staff and create discount rules. |
| 💼 **Internal Staff** | `staff@brightloop.com` | `Staff@1234` | Day-to-day sales & desk: quotation templates, customer subscriptions, quotes, invoices, and payments. |
| 👤 **Customer Portal** | `hello@northstar.com` | `Northstar@123` | Self-service customer portal: view own active subscriptions, download invoices, and pay pending bills online. |

---

## 🚀 Key Features

### 1. Authentication & Security
- **Authentication Gateway**: Web application starts on the co-branded Odoo login screen before granting access to workspace data.
- **Customer Sign Up Validation**: Live password validation enforcing $> 8$ characters, uppercase letter, lowercase letter, and special character.
- **Unique Account Email**: Guarantees each email belongs to only one account.
- **Password Reset Flow**: Simulated reset link dispatch.

### 2. Products, Variants & Plans
- Product catalog supporting software, add-ons, and services.
- **Brand Variants**: e.g., Odoo Brand variant that adds ₹560 to base sales price.
- **Billing Frequencies**: Daily, Weekly, Monthly, and Yearly.
- **Plan Rules**: Minimum quantity requirements and auto-close lifecycle configurations.

### 3. Quotation Templates to Subscriptions
- Sales reps start from preset templates with pre-configured product lines and validity periods.
- Subscriptions move through the 5 specified lifecycle stages:
  $$\text{Draft} \longrightarrow \text{Quotation} \longrightarrow \text{Confirmed} \longrightarrow \text{Active} \longrightarrow \text{Closed}$$
- Actions for: Send Quote, Confirm Quote, Activate, Renew, Pause, and Close Early.

### 4. Billing Day Batch Invoicing
- **One-Click Batch Invoicing**: Scans all active subscriptions and generates itemized invoices automatically.
- **Duplicate Prevention**: Prevents double-billing for subscriptions already invoiced in the current billing cycle.
- Pre-fills customer details, product lines, taxes (18% GST), and applicable discounts.
- Invoice lifecycle: `Draft` ➔ `Confirmed` ➔ `Paid` (or `Cancelled`), with printing and payment capture.

### 5. Admin Discount Rules Engine
- Restricted strictly to Administrators.
- Fixed amount or percentage discount rules.
- Scope selection: Applies to specific products or whole subscriptions.
- Minimum purchase requirements and maximum usage limit counters.
- Automatically applied during billing day run without manual intervention.

### 6. Finance Lead Reports & Dashboard
- Active subscriptions count and breakdown.
- Realized cash collected across UPI, Card, and Bank Transfer.
- Outstanding receivables and list of overdue invoices.
- Instant response latency ($< 200\text{ms}$).
- Complete CSV export on every table view and JSON database backup/restore.

---

## 🛠️ Tech Stack & Architecture

- **Frontend**: Vanilla HTML5, CSS3, ES6+ JavaScript.
- **Design System**: Odoo-inspired color palette (Deep Amethyst `#714B67` & Teal `#017E84`), responsive layout, dark/light theme support.
- **Storage**: Client-side persistent database with backup, restore, and demo reset utilities.
- **Zero External Dependencies**: Completely self-contained and runs immediately in any modern web browser.

---

## 💻 How to Run Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/sabesh2101-cpu/Subscription-Management-System.git
   ```
2. Navigate into the folder:
   ```bash
   cd Subscription-Management-System
   ```
3. Open `Brightloop_Subscription_Management_System/index.html` in your browser.
4. Use the quick sign-in buttons on the login screen to explore the Admin, Staff, and Customer Portal perspectives.
