/**
 * Odoo · Brightloop Subscription Management System
 * Production Logic & Business Rules Engine
 * Implements full specification from the Odoo Challenge PDF
 */

(function () {
  'use strict';

  // --- Utility Selectors & Formatters ---
  const $ = selector => document.querySelector(selector);
  const $$ = selector => document.querySelectorAll(selector);

  const formatCurrency = (amount) => {
    return '₹' + Number(amount || 0).toLocaleString('en-IN', {
      maximumFractionDigits: 0
    });
  };

  const escapeHtml = (str) => {
    return String(str ?? '').replace(/[&<>"']/g, match => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    })[match]);
  };

  const generateId = (prefix) => {
    return `${prefix}-${Date.now().toString().slice(-6)}`;
  };

  const getTodayISO = () => {
    return new Date().toISOString().split('T')[0];
  };

  const addDaysISO = (dateStr, days) => {
    const d = new Date(dateStr || new Date());
    d.setDate(d.getDate() + Number(days));
    return d.toISOString().split('T')[0];
  };

  const addMonthsISO = (dateStr, months) => {
    const d = new Date(dateStr || new Date());
    d.setMonth(d.getMonth() + Number(months));
    return d.toISOString().split('T')[0];
  };

  const timeAgo = (dateStr) => {
    if (!dateStr) return 'Just now';
    const diffSec = Math.floor((new Date() - new Date(dateStr)) / 1000);
    if (diffSec < 60) return 'Just now';
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return diffDays === 1 ? 'Yesterday' : `${diffDays}d ago`;
  };

  // --- Seed Database Following Problem Statement Requirements ---
  const SEED_DATA = {
    // Problem Statement Page 2: RBAC Accounts
    users: [
      { id: 'USR-001', name: 'Admin Administrator', email: 'admin@brightloop.com', role: 'admin', designation: 'Managing Director' },
      { id: 'USR-002', name: 'Sarah Miller', email: 'staff@brightloop.com', role: 'staff', designation: 'Senior Sales Representative' },
      { id: 'USR-003', name: 'Northstar Retail Desk', email: 'hello@northstar.com', role: 'customer', customerName: 'Northstar Retail', designation: 'Client Account Manager' }
    ],

    // Problem Statement Page 2: Customers
    customers: [
      { id: 'CUS-001', name: 'Northstar Retail', email: 'hello@northstar.com', company: 'Northstar Retail Pvt Ltd', phone: '+91 98201 44520', status: 'Active', created: '2026-02-15' },
      { id: 'CUS-002', name: 'Maya Stores', email: 'maya@stores.com', company: 'Maya Consumer Goods', phone: '+91 98450 12890', status: 'Active', created: '2026-03-10' },
      { id: 'CUS-003', name: 'Pixel Works Studio', email: 'team@pixelworks.com', company: 'Pixel Works Design Studio', phone: '+91 97110 33499', status: 'Active', created: '2026-01-20' },
      { id: 'CUS-004', name: 'CloudScale Technologies', email: 'billing@cloudscale.io', company: 'CloudScale Technologies Ltd', phone: '+91 99880 77123', status: 'Active', created: '2026-04-05' }
    ],

    // Problem Statement Page 3: Products with Variants (e.g. Odoo brand adds 560)
    products: [
      { id: 'PRD-001', name: 'Brightloop CRM Business', type: 'Software', price: 1499, cost: 500, variant: 'Standard', variantExtra: 0, notes: 'Full CRM & billing software billed monthly or yearly' },
      { id: 'PRD-002', name: 'Brightloop CRM - Odoo Edition', type: 'Software', price: 2059, cost: 650, variant: 'Odoo Brand', variantExtra: 560, notes: 'Enhanced with Odoo integration (+₹560 brand variant)' },
      { id: 'PRD-003', name: 'Analytics & Cohorts Add-on', type: 'Add-on', price: 599, cost: 180, variant: 'Standard', variantExtra: 0, notes: 'Predictive churn and cohort analytics' },
      { id: 'PRD-004', name: '24/7 Priority SLA Support', type: 'Service', price: 2499, cost: 800, variant: 'Standard', variantExtra: 0, notes: '15-minute response SLA guarantee' }
    ],

    // Problem Statement Page 3: Plans (Daily, Weekly, Monthly, Yearly + Lifecycle Rules)
    plans: [
      { id: 'PLN-001', name: 'Monthly Business Plan', frequency: 'Monthly', cost: 1499, minQty: 1, availableFrom: '2026-01-01', availableTo: '2027-12-31', autoCloseOnEnd: false, canPause: true, canRenew: true },
      { id: 'PLN-002', name: 'Yearly Enterprise Contract', frequency: 'Yearly', cost: 14990, minQty: 5, availableFrom: '2026-01-01', availableTo: '2027-12-31', autoCloseOnEnd: false, canPause: false, canRenew: true },
      { id: 'PLN-003', name: 'Weekly Growth Sprint', frequency: 'Weekly', cost: 450, minQty: 1, availableFrom: '2026-06-01', availableTo: '2026-12-31', autoCloseOnEnd: true, canPause: false, canRenew: false },
      { id: 'PLN-004', name: 'Daily High-Compute Pass', frequency: 'Daily', cost: 99, minQty: 1, availableFrom: '2026-01-01', availableTo: '2027-12-31', autoCloseOnEnd: true, canPause: false, canRenew: false }
    ],

    // Problem Statement Page 3: Quotation Templates
    templates: [
      { id: 'TMP-001', name: 'Enterprise Standard Offer', plan: 'Yearly Enterprise Contract', product: 'Brightloop CRM - Odoo Edition', defaultQty: 5, validityDays: 30, notes: 'Preset for large customers with Odoo variant' },
      { id: 'TMP-002', name: 'Retail Starter Offer', plan: 'Monthly Business Plan', product: 'Brightloop CRM Business', defaultQty: 1, validityDays: 15, notes: 'Standard small shop monthly quotation' }
    ],

    // Problem Statement Page 3: Subscriptions (States: Draft -> Quotation -> Confirmed -> Active -> Closed)
    subscriptions: [
      { id: 'SUB-1001', customer: 'Northstar Retail', plan: 'Monthly Business Plan', product: 'Brightloop CRM - Odoo Edition', qty: 1, unitPrice: 2059, taxRate: 18, amount: 2430, frequency: 'Monthly', start: '2026-06-01', expiry: '2026-11-01', paymentTerms: 'Net 7 Days', status: 'Active', autoClose: false },
      { id: 'SUB-1002', customer: 'Maya Stores', plan: 'Monthly Business Plan', product: 'Brightloop CRM Business', qty: 1, unitPrice: 1499, taxRate: 18, amount: 1769, frequency: 'Monthly', start: '2026-08-12', expiry: '2026-11-12', paymentTerms: 'Net 15 Days', status: 'Active', autoClose: false },
      { id: 'SUB-1003', customer: 'Pixel Works Studio', plan: 'Yearly Enterprise Contract', product: 'Brightloop CRM - Odoo Edition', qty: 5, unitPrice: 2059, taxRate: 18, amount: 12148, frequency: 'Yearly', start: '2026-01-01', expiry: '2027-01-01', paymentTerms: 'Net 30 Days', status: 'Active', autoClose: false },
      { id: 'SUB-1004', customer: 'CloudScale Technologies', plan: 'Monthly Business Plan', product: 'Analytics & Cohorts Add-on', qty: 2, unitPrice: 599, taxRate: 18, amount: 1414, frequency: 'Monthly', start: '2026-04-15', expiry: '2026-10-15', paymentTerms: 'Due on Receipt', status: 'Quotation', autoClose: false },
      { id: 'SUB-1005', customer: 'Northstar Retail', plan: 'Weekly Growth Sprint', product: 'Brightloop CRM Business', qty: 1, unitPrice: 450, taxRate: 18, amount: 531, frequency: 'Weekly', start: '2026-09-01', expiry: '2026-09-08', paymentTerms: 'Immediate', status: 'Closed', autoClose: true }
    ],

    // Problem Statement Page 3 & 4: Invoices (States: Draft -> Confirmed -> Paid)
    invoices: [
      { id: 'INV-2026-001', subscriptionId: 'SUB-1001', customer: 'Northstar Retail', date: '2026-10-01', due: '2026-10-08', subtotal: 2059, tax: 371, discount: 0, amount: 2430, paidAmount: 2430, status: 'Paid', notes: 'Monthly Odoo CRM subscription' },
      { id: 'INV-2026-002', subscriptionId: 'SUB-1002', customer: 'Maya Stores', date: '2026-10-12', due: '2026-10-19', subtotal: 1499, tax: 270, discount: 0, amount: 1769, paidAmount: 0, status: 'Confirmed', notes: 'Monthly CRM renewal' },
      { id: 'INV-2026-003', subscriptionId: 'SUB-1003', customer: 'Pixel Works Studio', date: '2026-10-15', due: '2026-10-22', subtotal: 10295, tax: 1853, discount: 1000, amount: 11148, paidAmount: 0, status: 'Confirmed', notes: 'Enterprise renewal (Overdue)' },
      { id: 'INV-2026-004', subscriptionId: 'SUB-1001', customer: 'Northstar Retail', date: '2026-09-01', due: '2026-09-08', subtotal: 2059, tax: 371, discount: 0, amount: 2430, paidAmount: 2430, status: 'Paid', notes: 'September invoice' }
    ],

    // Problem Statement Page 4: Payments
    payments: [
      { id: 'PAY-001', invoice: 'INV-2026-001', customer: 'Northstar Retail', method: 'UPI', date: '2026-10-02', amount: 2430, note: 'Settled via Corporate UPI' },
      { id: 'PAY-002', invoice: 'INV-2026-004', customer: 'Northstar Retail', method: 'Card', date: '2026-09-02', amount: 2430, note: 'Card autopay' },
      { id: 'PAY-003', invoice: 'INV-2026-HIST1', customer: 'Maya Stores', method: 'Bank Transfer', date: '2026-09-15', amount: 1769, note: 'NEFT transfer' },
      { id: 'PAY-004', invoice: 'INV-2026-HIST2', customer: 'Pixel Works Studio', method: 'UPI', date: '2026-08-10', amount: 11148, note: 'Quarterly payment' },
      { id: 'PAY-005', invoice: 'INV-2026-HIST3', customer: 'Northstar Retail', method: 'Card', date: '2026-08-01', amount: 2430, note: 'August settlement' },
      { id: 'PAY-006', invoice: 'INV-2026-HIST4', customer: 'CloudScale Technologies', method: 'Bank Transfer', date: '2026-07-20', amount: 1414, note: 'IMPS payment' }
    ],

    // Problem Statement Page 4: Admin Discount Rules (usage limits, product or whole subscription)
    discounts: [
      { id: 'DSC-001', name: 'High Seat Volume Off', code: 'SEATS1000', type: 'Fixed amount', value: 1000, scope: 'Whole subscription', minQty: 5, minPurchase: 5000, maxUses: 20, usedCount: 3, starts: '2026-01-01', ends: '2026-12-31', status: 'Active' },
      { id: 'DSC-002', name: 'Odoo Variant Special 15%', code: 'ODOO15', type: 'Percentage', value: 15, scope: 'Specific product', targetProduct: 'Brightloop CRM - Odoo Edition', minQty: 1, minPurchase: 1000, maxUses: 50, usedCount: 12, starts: '2026-05-01', ends: '2026-11-30', status: 'Active' },
      { id: 'DSC-003', name: 'Welcome Voucher ₹250', code: 'WELCOME250', type: 'Fixed amount', value: 250, scope: 'Whole subscription', minQty: 1, minPurchase: 1000, maxUses: 100, usedCount: 45, starts: '2026-01-01', ends: '2026-12-31', status: 'Active' }
    ],

    // Taxes configured by Admin (Problem Statement Page 3)
    taxes: [
      { id: 'TAX-001', name: 'Standard GST (18%)', rate: 18, isDefault: true, description: 'CGST 9% + SGST 9%' },
      { id: 'TAX-002', name: 'Inter-State IGST (18%)', rate: 18, isDefault: false, description: 'Integrated Goods and Services Tax' },
      { id: 'TAX-003', name: 'Zero Rated Export (0%)', rate: 0, isDefault: false, description: 'Overseas customers' }
    ],

    // Live Activity Log
    activities: [
      { id: 'ACT-001', type: 'pay', title: 'Payment received', desc: '₹2,430 from Northstar Retail for INV-2026-001', time: '2026-10-31T09:15:00' },
      { id: 'ACT-002', type: 'sub', title: 'Subscription active', desc: 'SUB-1001 Active for Northstar Retail', time: '2026-10-30T14:40:00' },
      { id: 'ACT-003', type: 'inv', title: 'Invoice confirmed', desc: 'INV-2026-003 confirmed for Pixel Works Studio', time: '2026-10-28T11:00:00' }
    ]
  };

  const STORAGE_KEYS = ['users', 'customers', 'products', 'plans', 'templates', 'subscriptions', 'invoices', 'payments', 'discounts', 'taxes', 'activities'];

  // --- Database State ---
  let db = {};

  function loadDatabase() {
    STORAGE_KEYS.forEach(key => {
      try {
        const stored = localStorage.getItem(`bl_odoo_${key}`);
        if (stored) {
          db[key] = JSON.parse(stored);
        } else {
          db[key] = JSON.parse(JSON.stringify(SEED_DATA[key] || []));
        }
      } catch (err) {
        db[key] = JSON.parse(JSON.stringify(SEED_DATA[key] || []));
      }
    });
  }

  function saveDatabase() {
    STORAGE_KEYS.forEach(key => {
      localStorage.setItem(`bl_odoo_${key}`, JSON.stringify(db[key]));
    });
  }

  function logActivity(type, title, desc) {
    if (!db.activities) db.activities = [];
    db.activities.unshift({
      id: generateId('ACT'),
      type: type || 'system',
      title,
      desc,
      time: new Date().toISOString()
    });
    if (db.activities.length > 50) db.activities.pop();
    saveDatabase();
  }

  // --- Current User Session & RBAC State ---
  let currentUser = null; // { email, role: 'admin'|'staff'|'customer', name, customerName }
  let currentPage = 'dashboard';
  let activeFilter = 'All';
  let sortColumn = null;
  let sortDirection = 'asc';

  // --- Theme Management ---
  function initTheme() {
    const saved = localStorage.getItem('bl_odoo_theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('bl_odoo_theme', next);
    showToast(`Switched to ${next} theme`, 'info');
  }

  // --- Toast Notification Center ---
  function showToast(message, type = 'success') {
    const toast = $('#toast');
    const msg = $('#toast-msg');
    const icon = $('#toast-icon');
    if (!toast || !msg) return;

    toast.className = `toast ${type}`;
    msg.textContent = message;
    icon.textContent = type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ');
    toast.classList.add('show');

    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => {
      toast.classList.remove('show');
    }, 2800);
  }

  // --- Confirmation Modal ---
  function confirmAction(title, message, onProceed) {
    const dialog = $('#confirm-dialog');
    $('#confirm-title').textContent = title;
    $('#confirm-message').textContent = message;

    const cancelBtn = $('#confirm-cancel');
    const proceedBtn = $('#confirm-proceed');

    const handleProceed = () => {
      dialog.close();
      cleanup();
      onProceed();
    };

    const handleCancel = () => {
      dialog.close();
      cleanup();
    };

    const cleanup = () => {
      proceedBtn.removeEventListener('click', handleProceed);
      cancelBtn.removeEventListener('click', handleCancel);
    };

    proceedBtn.addEventListener('click', handleProceed);
    cancelBtn.addEventListener('click', handleCancel);
    dialog.showModal();
  }

  // ================= AUTHENTICATION & RBAC LOGIC =================
  // Problem Statement Page 2: Strict password rules & unique emails

  window.switchAuthTab = (tab) => {
    $$('.auth-tab').forEach(b => b.classList.remove('active'));
    $$('.auth-pane').forEach(p => p.classList.remove('active'));

    if (tab === 'signin') {
      $('#tab-sign-in').classList.add('active');
      $('#signin-pane').classList.add('active');
    } else {
      $('#tab-sign-up').classList.add('active');
      $('#signup-pane').classList.add('active');
    }
  };

  window.togglePasswordVisibility = (inputId) => {
    const input = document.getElementById(inputId);
    if (!input) return;
    const isPw = input.type === 'password';
    input.type = isPw ? 'text' : 'password';
  };

  // Password rules validator (Page 2: > 8 chars, uppercase, lowercase, special char)
  window.validatePasswordStrength = (pw) => {
    const isLen = pw.length > 8;
    const isUpper = /[A-Z]/.test(pw);
    const isLower = /[a-z]/.test(pw);
    const isSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(pw);

    updateRuleState('rule-len', isLen);
    updateRuleState('rule-upper', isUpper);
    updateRuleState('rule-lower', isLower);
    updateRuleState('rule-special', isSpecial);

    return isLen && isUpper && isLower && isSpecial;
  };

  function updateRuleState(elemId, valid) {
    const el = document.getElementById(elemId);
    if (!el) return;
    el.classList.toggle('valid', valid);
    const icon = el.querySelector('.rule-icon');
    if (icon) icon.textContent = valid ? '✓' : '○';
  }

  window.submitLogin = () => {
    const email = $('#login-email').value.trim();
    const password = $('#login-password').value;

    if (!email || !password) {
      showToast('Please enter both email and password', 'error');
      return;
    }

    // Check registered accounts
    const user = db.users.find(u => u.email.toLowerCase() === email.toLowerCase());

    if (!user) {
      // Auto-fallback for demo: if email matches a customer, log in as customer
      const cust = db.customers.find(c => c.email.toLowerCase() === email.toLowerCase());
      if (cust) {
        setSession({
          email: cust.email,
          name: cust.name,
          role: 'customer',
          customerName: cust.name,
          designation: 'Client Account Manager'
        });
        return;
      }
      showToast('No registered account found with this email', 'error');
      return;
    }

    setSession(user);
  };

  window.submitSignUp = () => {
    const name = $('#signup-name').value.trim();
    const email = $('#signup-email').value.trim();
    const password = $('#signup-password').value;

    if (!name || !email || !password) {
      showToast('All fields are required', 'error');
      return;
    }

    // Check unique email requirement (Problem statement Page 2: "Each email can belong to only one account")
    const existing = db.users.find(u => u.email.toLowerCase() === email.toLowerCase()) ||
                     db.customers.find(c => c.email.toLowerCase() === email.toLowerCase());
    if (existing) {
      showToast('This email is already registered! Please sign in.', 'error');
      $('#email-unique-msg').style.color = 'var(--danger)';
      return;
    }

    // Check password rules (>8 chars, uppercase, lowercase, special char)
    const isValidPw = window.validatePasswordStrength(password);
    if (!isValidPw) {
      showToast('Password must be >8 chars with uppercase, lowercase, and a special character', 'error');
      return;
    }

    // Create customer account
    const newCustomer = {
      id: generateId('CUS'),
      name: name,
      email: email,
      company: name,
      status: 'Active',
      created: getTodayISO()
    };
    db.customers.push(newCustomer);

    const newUser = {
      id: generateId('USR'),
      name: name,
      email: email,
      role: 'customer',
      customerName: name,
      designation: 'Customer Representative'
    };
    db.users.push(newUser);
    saveDatabase();

    logActivity('customer', 'New customer registered', `${name} signed up with email ${email}`);
    showToast('Account created successfully! Entering Customer Portal...');
    setSession(newUser);
  };

  window.quickLogin = (role) => {
    if (role === 'admin') {
      const user = db.users.find(u => u.role === 'admin') || SEED_DATA.users[0];
      setSession(user);
    } else if (role === 'staff') {
      const user = db.users.find(u => u.role === 'staff') || SEED_DATA.users[1];
      setSession(user);
    } else {
      const user = db.users.find(u => u.role === 'customer') || SEED_DATA.users[2];
      setSession(user);
    }
  };

  window.switchRole = (role) => {
    window.quickLogin(role);
  };

  function setSession(user) {
    currentUser = user;
    localStorage.setItem('bl_odoo_session', JSON.stringify(user));

    $('#auth-screen').style.display = 'none';
    $('#app-layout').style.display = 'flex';

    // Update sidebar UI
    $('#sidebar-user-name').textContent = user.name;
    $('#sidebar-user-role').textContent = user.designation || user.role.toUpperCase();
    $('#sidebar-avatar').textContent = user.name.slice(0, 2).toUpperCase();

    const roleBadge = $('#sidebar-role-indicator');
    if (roleBadge) {
      roleBadge.textContent = user.role === 'admin' ? '👑 Administrator' : (user.role === 'staff' ? '💼 Internal Staff' : '👤 Customer Portal');
    }

    const roleSelector = $('#role-quick-switcher');
    if (roleSelector) roleSelector.value = user.role;

    // Render navigation according to RBAC
    renderNavigationForRole(user.role);

    // Default starting page
    currentPage = user.role === 'customer' ? 'my-subscriptions' : 'dashboard';
    showToast(`Welcome, ${user.name}! (Role: ${user.role.toUpperCase()})`);
    render();
  }

  window.handleLogout = () => {
    confirmAction(
      'Sign Out of Brightloop?',
      'You will be returned to the authentication gateway.',
      () => {
        currentUser = null;
        localStorage.removeItem('bl_odoo_session');
        $('#app-layout').style.display = 'none';
        $('#auth-screen').style.display = 'flex';
        showToast('You have been signed out', 'info');
      }
    );
  };

  window.openForgotPasswordModal = () => {
    $('#reset-password-dialog').showModal();
  };

  window.sendPasswordResetLink = () => {
    const email = $('#reset-email').value;
    $('#reset-password-dialog').close();
    showToast(`A secure reset link has been dispatched to ${email}`, 'info');
  };

  // ================= RBAC DYNAMIC NAVIGATION =================
  function renderNavigationForRole(role) {
    const nav = $('#main-nav-menu');
    let html = '';

    if (role === 'admin') {
      html = `
        <div class="nav-section-label">EXECUTIVE & SALES</div>
        <button class="nav-link active" data-page="dashboard"><span>▦</span> Dashboard</button>
        <button class="nav-link" data-page="subscriptions"><span>▤</span> Subscriptions</button>
        <button class="nav-link" data-page="templates"><span>⚡</span> Quotation Templates</button>
        <button class="nav-link" data-page="customers"><span>♙</span> Customers</button>

        <div class="nav-section-label">CONFIGURATION</div>
        <button class="nav-link" data-page="products"><span>◇</span> Products & Variants</button>
        <button class="nav-link" data-page="plans"><span>⏱</span> Plan Frequencies</button>
        <button class="nav-link" data-page="staff"><span>👥</span> Staff Directory</button>

        <div class="nav-section-label">BILLING & REVENUE</div>
        <button class="nav-link" data-page="invoices"><span>▧</span> Invoices</button>
        <button class="nav-link" data-page="payments"><span>⇄</span> Payments</button>
        <button class="nav-link" data-page="discounts"><span>％</span> Discount Rules</button>
        <button class="nav-link" data-page="taxes"><span>⚖</span> Tax Rules</button>
        <button class="nav-link" data-page="reports"><span>▥</span> Finance Reports</button>
      `;
    } else if (role === 'staff') {
      html = `
        <div class="nav-section-label">SALES & DESK</div>
        <button class="nav-link active" data-page="dashboard"><span>▦</span> Staff Overview</button>
        <button class="nav-link" data-page="subscriptions"><span>▤</span> Subscriptions & Quotes</button>
        <button class="nav-link" data-page="templates"><span>⚡</span> Quotation Templates</button>
        <button class="nav-link" data-page="customers"><span>♙</span> Customers</button>

        <div class="nav-section-label">BILLING</div>
        <button class="nav-link" data-page="invoices"><span>▧</span> Invoices</button>
        <button class="nav-link" data-page="payments"><span>⇄</span> Payments</button>
        <button class="nav-link" data-page="products"><span>◇</span> Catalog & Plans</button>
      `;
    } else {
      // Customer Portal: Problem statement Page 2: "customers see only their own subscriptions and invoices through a portal"
      html = `
        <div class="nav-section-label">MY CUSTOMER PORTAL</div>
        <button class="nav-link active" data-page="my-subscriptions"><span>▤</span> My Subscriptions</button>
        <button class="nav-link" data-page="my-invoices"><span>▧</span> My Invoices</button>
        <button class="nav-link" data-page="my-payments"><span>⇄</span> Payment History</button>
        <button class="nav-link" data-page="my-profile"><span>♙</span> Account Details</button>
      `;
    }

    nav.innerHTML = html;
    nav.querySelectorAll('.nav-link').forEach(btn => {
      btn.addEventListener('click', () => setPage(btn.dataset.page));
    });
  }

  // ================= SUBSCRIPTION LIFECYCLE CONTROLS =================
  // Problem statement Page 3: Draft -> Quotation -> Confirmed -> Active -> Closed

  window.advanceSubscriptionState = (subId, targetState) => {
    const sub = db.subscriptions.find(s => s.id === subId);
    if (!sub) return;

    sub.status = targetState;
    if (targetState === 'Active') {
      sub.start = getTodayISO();
      sub.expiry = sub.frequency === 'Yearly' ? addMonthsISO(getTodayISO(), 12) : addMonthsISO(getTodayISO(), 1);
    }

    logActivity('sub', `Subscription state: ${targetState}`, `${sub.id} (${sub.customer}) updated to ${targetState}`);
    saveDatabase();
    showToast(`Subscription ${sub.id} moved to ${targetState}`);
    render();
  };

  window.renewSubscription = (subId) => {
    const sub = db.subscriptions.find(s => s.id === subId);
    if (!sub) return;

    confirmAction(
      'Renew Subscription?',
      `Extend ${sub.customer}'s plan by 1 cycle and create renewal invoice?`,
      () => {
        sub.expiry = sub.frequency === 'Yearly' ? addMonthsISO(sub.expiry, 12) : addMonthsISO(sub.expiry, 1);
        sub.status = 'Active';

        const invId = generateId('INV');
        db.invoices.unshift({
          id: invId,
          subscriptionId: sub.id,
          customer: sub.customer,
          date: getTodayISO(),
          due: addDaysISO(getTodayISO(), 7),
          subtotal: sub.unitPrice * sub.qty,
          tax: Math.round(sub.unitPrice * sub.qty * (sub.taxRate / 100)),
          discount: 0,
          amount: sub.amount,
          paidAmount: 0,
          status: 'Confirmed',
          notes: `Automatic renewal for ${sub.plan}`
        });

        logActivity('sub', 'Subscription renewed', `${sub.customer} plan renewed. Invoice ${invId} created.`);
        saveDatabase();
        showToast(`Subscription renewed! Invoice ${invId} generated.`);
        render();
      }
    );
  };

  // Convert Quotation Template into Subscription (Problem statement Page 3)
  window.createSubFromTemplate = (templateId) => {
    const tmpl = db.templates.find(t => t.id === templateId);
    if (!tmpl) return;

    const custName = prompt('Enter customer name for this quotation (e.g. Northstar Retail):', 'Northstar Retail');
    if (!custName) return;

    const prod = db.products.find(p => p.name === tmpl.product) || db.products[0];
    const subId = generateId('SUB');
    const taxRate = 18;
    const subtotal = prod.price * tmpl.defaultQty;
    const tax = Math.round(subtotal * 0.18);
    const total = subtotal + tax;

    const newSub = {
      id: subId,
      customer: custName,
      plan: tmpl.plan,
      product: tmpl.product,
      qty: tmpl.defaultQty,
      unitPrice: prod.price,
      taxRate: taxRate,
      amount: total,
      frequency: tmpl.plan.includes('Yearly') ? 'Yearly' : 'Monthly',
      start: getTodayISO(),
      expiry: addDaysISO(getTodayISO(), tmpl.validityDays),
      paymentTerms: 'Net 15 Days',
      status: 'Quotation',
      autoClose: false
    };

    db.subscriptions.unshift(newSub);
    logActivity('sub', 'Quote generated from template', `${subId} created for ${custName} from ${tmpl.name}`);
    saveDatabase();
    showToast(`Quotation ${subId} generated from template!`);
    setPage('subscriptions');
  };

  // ================= BILLING DAY BATCH ENGINE =================
  // Problem statement Page 3: "It is billing day, and hundreds of subscriptions are due at once.
  // Nobody should be typing invoices by hand. Each one should be created from its subscription...
  // Nothing should be billed twice or skipped."

  window.openBillingDayModal = () => {
    const activeSubs = db.subscriptions.filter(s => s.status === 'Active');
    const previewEl = $('#billing-due-preview');

    let html = `
      <div style="background:var(--bg-subtle);padding:12px;border-radius:var(--radius-sm);border:1px solid var(--border-color);font-size:12.5px">
        <strong>${activeSubs.length} Active Subscriptions Ready for Billing:</strong>
        <ul style="margin:8px 0 0 16px;display:flex;flex-direction:column;gap:4px">
          ${activeSubs.map(s => `
            <li>${escapeHtml(s.customer)} · <strong>${escapeHtml(s.plan)}</strong> (${formatCurrency(s.amount)})</li>
          `).join('')}
        </ul>
      </div>
    `;
    previewEl.innerHTML = html;
    $('#billing-day-dialog').showModal();
  };
  $('#btn-billing-day').onclick = window.openBillingDayModal;

  window.executeBillingDay = () => {
    const activeSubs = db.subscriptions.filter(s => s.status === 'Active');
    let billedCount = 0;

    activeSubs.forEach(sub => {
      // Duplicate prevention: check if an invoice for this sub was already generated this month
      const currentMonth = getTodayISO().slice(0, 7); // e.g. 2026-10
      const alreadyBilled = db.invoices.some(i => i.subscriptionId === sub.id && i.date.startsWith(currentMonth));

      if (!alreadyBilled) {
        // Calculate discounts if applicable (Problem statement Page 4)
        let discountAmt = 0;
        const matchingDiscount = db.discounts.find(d => d.status === 'Active' && (d.scope === 'Whole subscription' || d.targetProduct === sub.product));
        if (matchingDiscount && matchingDiscount.usedCount < matchingDiscount.maxUses) {
          if (matchingDiscount.type === 'Percentage') {
            discountAmt = Math.round(sub.amount * (matchingDiscount.value / 100));
          } else {
            discountAmt = matchingDiscount.value;
          }
          matchingDiscount.usedCount++;
        }

        const invId = generateId('INV');
        const finalAmount = Math.max(0, sub.amount - discountAmt);

        db.invoices.unshift({
          id: invId,
          subscriptionId: sub.id,
          customer: sub.customer,
          date: getTodayISO(),
          due: addDaysISO(getTodayISO(), 7),
          subtotal: sub.unitPrice * sub.qty,
          tax: Math.round(sub.unitPrice * sub.qty * (sub.taxRate / 100)),
          discount: discountAmt,
          amount: finalAmount,
          paidAmount: 0,
          status: 'Confirmed',
          notes: `Batch Billing Day statement for ${sub.plan}`
        });

        billedCount++;
      }
    });

    saveDatabase();
    $('#billing-day-dialog').close();
    logActivity('inv', 'Batch billing day executed', `${billedCount} recurring invoices generated automatically`);
    showToast(`Billing Day Complete: ${billedCount} invoices created without duplicates!`);
    render();
  };

  // ================= INVOICE WORKFLOW & BRANDED VIEWER =================
  // Problem statement: Draft -> Confirmed -> Paid

  window.confirmInvoice = (invId) => {
    const inv = db.invoices.find(i => i.id === invId);
    if (!inv) return;
    inv.status = 'Confirmed';
    saveDatabase();
    showToast(`Invoice ${invId} Confirmed`);
    render();
  };

  window.cancelInvoice = (invId) => {
    confirmAction(
      'Cancel Invoice?',
      `Are you sure you want to cancel invoice ${invId}?`,
      () => {
        const inv = db.invoices.find(i => i.id === invId);
        if (inv) inv.status = 'Closed';
        saveDatabase();
        showToast(`Invoice ${invId} cancelled`);
        render();
      }
    );
  };

  window.viewInvoiceDoc = (invId) => {
    const inv = db.invoices.find(i => i.id === invId);
    if (!inv) return;

    const cust = db.customers.find(c => c.name === inv.customer) || {
      name: inv.customer,
      company: inv.customer,
      email: 'customer@company.com'
    };

    const balance = Math.max(0, Number(inv.amount) - Number(inv.paidAmount || 0));

    $('#detail-eyebrow').textContent = 'TAX INVOICE · ODOO BILLING';
    $('#detail-title').textContent = inv.id;

    const html = `
      <div class="invoice-view">
        <div class="invoice-brand-row">
          <div>
            <div style="font-size:24px;font-weight:900;color:var(--odoo-purple)">odoo <span style="font-weight:400;color:var(--text-muted)">| Brightloop</span></div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:2px">Brightloop Software Technologies Pvt Ltd</div>
            <div style="font-size:11px;color:var(--text-subtle)">GSTIN: 29AABCU9603R1Z7 · Bangalore, India</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:18px;font-weight:800;font-family:var(--font-mono)">${inv.id}</div>
            <div style="margin-top:4px"><span class="badge badge-${inv.status.toLowerCase()}">${inv.status}</span></div>
          </div>
        </div>

        <div class="invoice-party-row">
          <div>
            <h4 style="font-size:10.5px;color:var(--text-subtle);text-transform:uppercase;margin-bottom:4px">Customer Details</h4>
            <div style="font-weight:800;font-size:14px">${escapeHtml(cust.company || cust.name)}</div>
            <div style="color:var(--text-muted)">Attn: ${escapeHtml(cust.name)}</div>
            <div style="color:var(--text-muted)">${escapeHtml(cust.email)}</div>
          </div>
          <div style="text-align:right">
            <div><strong>Invoice Date:</strong> ${inv.date}</div>
            <div><strong>Due Date:</strong> ${inv.due}</div>
            <div><strong>Payment Terms:</strong> Net 7 Days</div>
          </div>
        </div>

        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Description</th>
                <th style="text-align:center">Qty</th>
                <th style="text-align:right">Subtotal</th>
                <th style="text-align:right">Tax (18%)</th>
                <th style="text-align:right">Net Total</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>${escapeHtml(inv.notes || 'Subscription Platform Usage')}</strong></td>
                <td style="text-align:center">1</td>
                <td style="text-align:right">${formatCurrency(inv.subtotal || inv.amount)}</td>
                <td style="text-align:right">${formatCurrency(inv.tax || 0)}</td>
                <td style="text-align:right"><strong>${formatCurrency(inv.amount)}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="invoice-summary-box">
          <div class="invoice-summary-line">
            <span>Subtotal:</span>
            <span>${formatCurrency(inv.subtotal || inv.amount)}</span>
          </div>
          ${inv.discount ? `
            <div class="invoice-summary-line" style="color:var(--success)">
              <span>Discount Rule Applied:</span>
              <span>-${formatCurrency(inv.discount)}</span>
            </div>
          ` : ''}
          <div class="invoice-summary-line">
            <span>Taxes:</span>
            <span>${formatCurrency(inv.tax || 0)}</span>
          </div>
          <div class="invoice-summary-line total">
            <span>Amount Due:</span>
            <span>${formatCurrency(inv.amount)}</span>
          </div>
          <div class="invoice-summary-line" style="color:var(--success)">
            <span>Paid:</span>
            <span>${formatCurrency(inv.paidAmount || 0)}</span>
          </div>
          <div class="invoice-summary-line" style="font-weight:800;color:${balance > 0 ? 'var(--danger)' : 'var(--success)'}">
            <span>Balance:</span>
            <span>${formatCurrency(balance)}</span>
          </div>
        </div>

        ${balance > 0 ? `
          <div style="display:flex;justify-content:flex-end;padding-top:12px;border-top:1px solid var(--border-color)">
            <button class="btn btn-odoo" onclick="$('#detail-dialog').close(); recordPaymentForInvoice('${inv.id}')">
              Record / Pay Bill
            </button>
          </div>
        ` : ''}
      </div>
    `;

    $('#detail-content').innerHTML = html;
    $('#detail-dialog').showModal();
  };

  window.recordPaymentForInvoice = (invId) => {
    openAdd('payments');
    setTimeout(() => {
      const select = $('#field-invoice');
      if (select) {
        select.value = invId;
        select.dispatchEvent(new Event('change'));
      }
    }, 50);
  };

  // ================= FORM CONFIGURATIONS & CRUD =================
  const CONFIGS = {
    subscriptions: {
      title: 'Subscription',
      prefix: 'SUB',
      fields: [
        { name: 'customer', label: 'Customer', type: 'select', source: 'customers', required: true },
        { name: 'plan', label: 'Plan', type: 'select', source: 'plans', required: true },
        { name: 'product', label: 'Product & Variant', type: 'select', source: 'products', required: true },
        { name: 'qty', label: 'Seat Quantity', type: 'number', required: true },
        { name: 'frequency', label: 'Billing Cycle', type: 'select', options: ['Monthly', 'Yearly', 'Weekly', 'Daily'], required: true },
        { name: 'paymentTerms', label: 'Payment Terms', type: 'select', options: ['Net 7 Days', 'Net 15 Days', 'Net 30 Days', 'Due on Receipt'], required: true },
        { name: 'status', label: 'Initial State', type: 'select', options: ['Draft', 'Quotation', 'Confirmed', 'Active'], required: true }
      ]
    },
    products: {
      title: 'Product',
      prefix: 'PRD',
      fields: [
        { name: 'name', label: 'Product Name', type: 'text', required: true },
        { name: 'type', label: 'Product Type', type: 'select', options: ['Software', 'Add-on', 'Service', 'Variant'], required: true },
        { name: 'variant', label: 'Variant (e.g. Odoo Brand +560)', type: 'select', options: ['Standard', 'Odoo Brand (+₹560)', 'Enterprise Dedicated'], required: true },
        { name: 'price', label: 'Sales Price (₹)', type: 'number', required: true },
        { name: 'cost', label: 'Cost Price (₹)', type: 'number', required: true },
        { name: 'notes', label: 'Notes', type: 'textarea', full: true }
      ]
    },
    plans: {
      title: 'Plan Frequency',
      prefix: 'PLN',
      fields: [
        { name: 'name', label: 'Plan Name', type: 'text', required: true },
        { name: 'frequency', label: 'Billing Frequency', type: 'select', options: ['Daily', 'Weekly', 'Monthly', 'Yearly'], required: true },
        { name: 'cost', label: 'Recurring Cost (₹)', type: 'number', required: true },
        { name: 'minQty', label: 'Minimum Quantity', type: 'number', required: true },
        { name: 'availableFrom', label: 'Available From', type: 'date', required: true },
        { name: 'availableTo', label: 'Available To', type: 'date', required: true },
        { name: 'autoCloseOnEnd', label: 'Lifecycle: Auto-close on expiry?', type: 'select', options: ['No', 'Yes'] }
      ]
    },
    customers: {
      title: 'Customer',
      prefix: 'CUS',
      fields: [
        { name: 'name', label: 'Customer / Business Name', type: 'text', required: true },
        { name: 'email', label: 'Email Address (Unique)', type: 'email', required: true },
        { name: 'company', label: 'Company Legal Name', type: 'text', required: true },
        { name: 'phone', label: 'Phone Number', type: 'tel' },
        { name: 'status', label: 'Status', type: 'select', options: ['Active', 'Inactive'], required: true }
      ]
    },
    staff: {
      title: 'Staff Member (Admin Only)',
      prefix: 'USR',
      fields: [
        { name: 'name', label: 'Staff Member Name', type: 'text', required: true },
        { name: 'email', label: 'Internal Work Email', type: 'email', required: true },
        { name: 'designation', label: 'Designation / Title', type: 'text', required: true },
        { name: 'role', label: 'Access Level', type: 'select', options: ['staff', 'admin'], required: true }
      ]
    },
    invoices: {
      title: 'Invoice',
      prefix: 'INV',
      fields: [
        { name: 'customer', label: 'Customer', type: 'select', source: 'customers', required: true },
        { name: 'date', label: 'Invoice Date', type: 'date', required: true },
        { name: 'due', label: 'Due Date', type: 'date', required: true },
        { name: 'amount', label: 'Total Amount (₹)', type: 'number', required: true },
        { name: 'status', label: 'Status', type: 'select', options: ['Draft', 'Confirmed', 'Paid'], required: true },
        { name: 'notes', label: 'Invoice Description', type: 'textarea', full: true }
      ]
    },
    payments: {
      title: 'Payment Record',
      prefix: 'PAY',
      fields: [
        { name: 'invoice', label: 'Invoice', type: 'select', source: 'invoices', required: true },
        { name: 'method', label: 'Payment Method', type: 'select', options: ['UPI', 'Credit/Debit Card', 'Bank Transfer', 'Cash'], required: true },
        { name: 'date', label: 'Date', type: 'date', required: true },
        { name: 'amount', label: 'Amount Paid (₹)', type: 'number', required: true },
        { name: 'note', label: 'Payment Reference / Note', type: 'text', full: true }
      ]
    },
    discounts: {
      title: 'Discount Rule (Admin Only)',
      prefix: 'DSC',
      fields: [
        { name: 'name', label: 'Rule Name', type: 'text', required: true },
        { name: 'code', label: 'Promo Code', type: 'text', required: true },
        { name: 'type', label: 'Type', type: 'select', options: ['Fixed amount', 'Percentage'], required: true },
        { name: 'value', label: 'Value (₹ or %)', type: 'number', required: true },
        { name: 'scope', label: 'Scope', type: 'select', options: ['Whole subscription', 'Specific product'], required: true },
        { name: 'minQty', label: 'Minimum Seats / Qty', type: 'number' },
        { name: 'minPurchase', label: 'Minimum Order Value (₹)', type: 'number' },
        { name: 'maxUses', label: 'Usage Limit (Max Times)', type: 'number', required: true },
        { name: 'starts', label: 'Start Date', type: 'date', required: true },
        { name: 'ends', label: 'End Date', type: 'date', required: true }
      ]
    }
  };

  let activeDialogPage = '';
  let editingRecordId = null;

  function openAdd(page) {
    // RBAC Guard: Problem statement Page 2: "Only the admin can add a new member of staff"
    // and Page 4: "Only the admin can create discount rules"
    if (page === 'staff' && currentUser?.role !== 'admin') {
      showToast('Permission Denied: Only Admin can add staff members', 'error');
      return;
    }
    if (page === 'discounts' && currentUser?.role !== 'admin') {
      showToast('Permission Denied: Only Admin can create discount rules', 'error');
      return;
    }

    activeDialogPage = page;
    editingRecordId = null;
    const conf = CONFIGS[page];
    if (!conf) return;

    $('#dialog-eyebrow').textContent = 'NEW RECORD';
    $('#dialog-title').textContent = `Add ${conf.title}`;
    $('#save-dialog-btn').textContent = 'Create Record';

    renderFormFields(conf, null);
    $('#entry-dialog').showModal();
  }

  function openEdit(page, id) {
    if ((page === 'staff' || page === 'discounts') && currentUser?.role !== 'admin') {
      showToast('Permission Denied: Admin action only', 'error');
      return;
    }

    activeDialogPage = page;
    editingRecordId = id;
    const conf = CONFIGS[page];
    const record = db[page].find(x => x.id === id);
    if (!conf || !record) return;

    $('#dialog-eyebrow').textContent = 'EDIT RECORD';
    $('#dialog-title').textContent = `Edit ${conf.title} (${id})`;
    $('#save-dialog-btn').textContent = 'Save Changes';

    renderFormFields(conf, record);
    $('#entry-dialog').showModal();
  }

  function renderFormFields(conf, existing) {
    let html = '';
    conf.fields.forEach(f => {
      const full = f.full ? ' full' : '';
      let val = existing ? existing[f.name] : '';

      if (!val && f.type === 'date') {
        if (f.name === 'starts' || f.name === 'date' || f.name === 'availableFrom') val = getTodayISO();
        if (f.name === 'ends' || f.name === 'availableTo') val = addMonthsISO(getTodayISO(), 6);
        if (f.name === 'due') val = addDaysISO(getTodayISO(), 7);
      }

      let input = '';
      if (f.type === 'select') {
        let options = f.options || (db[f.source] ? db[f.source].map(x => x.name || x.id) : []);
        input = `<select name="${f.name}" id="field-${f.name}" ${f.required ? 'required' : ''}>
          ${options.map(o => `<option value="${escapeHtml(o)}" ${String(val) === String(o) ? 'selected' : ''}>${escapeHtml(o)}</option>`).join('')}
        </select>`;
      } else if (f.type === 'textarea') {
        input = `<textarea name="${f.name}" id="field-${f.name}">${escapeHtml(val || '')}</textarea>`;
      } else {
        input = `<input type="${f.type}" name="${f.name}" id="field-${f.name}" value="${escapeHtml(val || '')}" ${f.required ? 'required' : ''}>`;
      }

      html += `<div class="field${full}"><label>${f.label} ${f.required ? '<span class="required">*</span>' : ''}</label>${input}</div>`;
    });

    $('#form-fields').innerHTML = html;
  }

  $('#entry-form').addEventListener('submit', (e) => {
    e.preventDefault();
    if (!activeDialogPage || !CONFIGS[activeDialogPage]) return;

    const conf = CONFIGS[activeDialogPage];
    const formData = new FormData(e.target);
    const item = {};

    formData.forEach((v, k) => {
      item[k] = ['price', 'cost', 'amount', 'qty', 'value', 'minQty', 'minPurchase', 'maxUses'].includes(k)
        ? Number(v || 0)
        : v.trim();
    });

    if (editingRecordId) {
      const idx = db[activeDialogPage].findIndex(x => x.id === editingRecordId);
      if (idx !== -1) {
        db[activeDialogPage][idx] = { ...db[activeDialogPage][idx], ...item };
        showToast(`${conf.title} updated`);
      }
    } else {
      item.id = generateId(conf.prefix);

      // Auto-calculations for subscriptions
      if (activeDialogPage === 'subscriptions') {
        const prod = db.products.find(p => p.name === item.product) || { price: 1499 };
        item.unitPrice = prod.price;
        item.taxRate = 18;
        const subtotal = item.unitPrice * (item.qty || 1);
        item.amount = subtotal + Math.round(subtotal * 0.18);
        item.start = getTodayISO();
        item.expiry = item.frequency === 'Yearly' ? addMonthsISO(getTodayISO(), 12) : addMonthsISO(getTodayISO(), 1);
      }

      if (activeDialogPage === 'discounts') {
        item.usedCount = 0;
        item.status = 'Active';
      }

      // Payments invoice sync
      if (activeDialogPage === 'payments') {
        const inv = db.invoices.find(i => i.id === item.invoice);
        if (inv) {
          inv.paidAmount = Number(inv.paidAmount || 0) + Number(item.amount);
          if (inv.paidAmount >= inv.amount) inv.status = 'Paid';
          item.customer = inv.customer;
        }
      }

      db[activeDialogPage].unshift(item);
      logActivity(activeDialogPage.slice(0, 3), `New ${conf.title}`, `${item.name || item.customer || item.id} created`);
      showToast(`${conf.title} created successfully`);
    }

    saveDatabase();
    $('#entry-dialog').close();
    render();
  });

  $('#close-dialog').onclick = $('#cancel-dialog').onclick = () => $('#entry-dialog').close();

  window.deleteRecord = (page, id) => {
    confirmAction(
      'Delete Record?',
      `Delete ${id} from ${page}?`,
      () => {
        db[page] = db[page].filter(x => x.id !== id);
        saveDatabase();
        showToast('Record deleted');
        render();
      }
    );
  };

  // ================= EXPORT DATA ENGINE =================
  window.exportTableToCSV = (page) => {
    const records = db[page] || [];
    if (!records.length) {
      showToast('No records to export', 'error');
      return;
    }

    const headers = Object.keys(records[0]);
    const csv = [headers.join(',')];
    records.forEach(r => {
      csv.push(headers.map(h => `"${String(r[h] ?? '').replace(/"/g, '""')}"`).join(','));
    });

    const blob = new Blob([csv.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `brightloop_${page}_${getTodayISO()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Exported ${records.length} records to CSV`);
  };

  window.openDataToolsModal = () => $('#data-dialog').showModal();
  $('#btn-data-tools').onclick = window.openDataToolsModal;

  window.exportDatabaseJSON = () => {
    const data = JSON.stringify({ version: 'Odoo-Brightloop-v2', timestamp: new Date(), data: db }, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `brightloop_odoo_backup_${getTodayISO()}.json`;
    a.click();
    showToast('Database exported as JSON');
  };

  window.importDatabaseJSON = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const r = new FileReader();
    r.onload = ev => {
      try {
        const parsed = JSON.parse(ev.target.result);
        const data = parsed.data || parsed;
        STORAGE_KEYS.forEach(k => { if (Array.isArray(data[k])) db[k] = data[k]; });
        saveDatabase();
        $('#data-dialog').close();
        showToast('Database restored successfully');
        render();
      } catch {
        showToast('Invalid backup file', 'error');
      }
    };
    r.readAsText(file);
  };

  window.resetToDemoData = () => {
    confirmAction(
      'Reset All Data?',
      'Restore the default Odoo Brightloop dataset from the challenge specification?',
      () => {
        STORAGE_KEYS.forEach(k => {
          db[k] = JSON.parse(JSON.stringify(SEED_DATA[k] || []));
        });
        saveDatabase();
        $('#data-dialog').close();
        showToast('Reset to demo dataset completed');
        render();
      }
    );
  };

  // Quick Action in Topbar
  $('#btn-quick-new').onclick = () => {
    if (currentPage === 'my-subscriptions' || currentPage === 'my-invoices') {
      showToast('In Customer Portal mode. Explore plans in catalog.');
      return;
    }
    const target = ['dashboard', 'reports'].includes(currentPage) ? 'subscriptions' : currentPage;
    openAdd(target);
  };

  // ================= PAGE RENDERERS =================

  // Executive Dashboard & Finance Lead Overview (Problem Statement Page 4)
  function renderDashboard() {
    const activeSubs = db.subscriptions.filter(s => s.status === 'Active');
    const revenue = db.payments.reduce((s, p) => s + Number(p.amount), 0);
    const owed = db.invoices.filter(i => i.status !== 'Paid').reduce((s, i) => s + Math.max(0, Number(i.amount) - Number(i.paidAmount || 0)), 0);
    const overdue = db.invoices.filter(i => i.due < getTodayISO() && i.status !== 'Paid');

    return `
      <div class="welcome-card">
        <div class="welcome-info">
          <h2>Executive Subscription Overview</h2>
          <p class="muted">Live status of active plans, billing day realization, and monthly cash flow.</p>
        </div>
        <div class="welcome-actions">
          <button class="btn btn-odoo btn-sm" onclick="openBillingDayModal()">⚡ Run Billing Day</button>
          <button class="btn btn-secondary btn-sm" onclick="exportTableToCSV('subscriptions')">Export CSV</button>
        </div>
      </div>

      <!-- Problem Statement Page 4: "How many subscriptions are active? How much revenue came in? How much owed? Overdue?" -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-title">ACTIVE SUBSCRIPTIONS</span>
            <span>▤</span>
          </div>
          <div class="stat-value" style="color:var(--odoo-purple)">${activeSubs.length}</div>
          <div class="stat-footer">${db.subscriptions.length} total across all stages</div>
        </div>

        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-title">REVENUE COLLECTED</span>
            <span>₹</span>
          </div>
          <div class="stat-value" style="color:var(--success)">${formatCurrency(revenue)}</div>
          <div class="stat-footer">Recorded across all payment methods</div>
        </div>

        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-title">OUTSTANDING AMOUNT</span>
            <span>◷</span>
          </div>
          <div class="stat-value" style="color:var(--warning)">${formatCurrency(owed)}</div>
          <div class="stat-footer">Awaiting client payment</div>
        </div>

        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-title">OVERDUE INVOICES</span>
            <span>!</span>
          </div>
          <div class="stat-value" style="color:var(--danger)">${overdue.length}</div>
          <div class="stat-footer">Past payment terms</div>
        </div>
      </div>

      <div class="dashboard-grid">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>Monthly Cash Flow</h3>
              <p class="muted">Payments collected over last 6 billing cycles</p>
            </div>
            <span class="badge badge-active">Live Calculated</span>
          </div>
          <div class="chart-bars">
            ${[
              { m: 'May', a: 11148 },
              { m: 'Jun', a: 2430 },
              { m: 'Jul', a: 1414 },
              { m: 'Aug', a: 4199 },
              { m: 'Sep', a: 4199 },
              { m: 'Oct', a: 4860 }
            ].map(b => `
              <div class="chart-bar-column">
                <div class="chart-bar" style="height:${Math.round((b.a / 12000) * 90)}%" data-tooltip="${formatCurrency(b.a)}"></div>
                <span class="chart-month-label">${b.m}</span>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>System Event Log</h3>
              <p class="muted">Recent billing and subscription events</p>
            </div>
          </div>
          <div class="activity-feed">
            ${db.activities.slice(0, 5).map(act => `
              <div class="activity-item">
                <div class="activity-icon-badge ${act.type}">
                  ${act.type === 'pay' ? '₹' : (act.type === 'sub' ? '★' : '▧')}
                </div>
                <div class="activity-content">
                  <span class="activity-title">${escapeHtml(act.title)}</span>
                  <span class="activity-detail">${escapeHtml(act.desc)}</span>
                  <span class="activity-time">${timeAgo(act.time)}</span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>

      <!-- Quick Subscriptions View -->
      ${renderTableTemplate('subscriptions', db.subscriptions.slice(0, 5), 'Recent Subscriptions')}
    `;
  }

  // Customer Portal View (Problem Statement Page 2)
  function renderCustomerPortal(view) {
    const custName = currentUser.customerName || currentUser.name;
    const custSubs = db.subscriptions.filter(s => s.customer.toLowerCase().includes(custName.toLowerCase()) || custName.toLowerCase().includes(s.customer.toLowerCase()));
    const custInvs = db.invoices.filter(i => i.customer.toLowerCase().includes(custName.toLowerCase()) || custName.toLowerCase().includes(i.customer.toLowerCase()));

    if (view === 'my-invoices') {
      return `
        <div class="welcome-card">
          <div class="welcome-info">
            <h2>My Billing Statements</h2>
            <p class="muted">View, download, and pay your Brightloop invoices online.</p>
          </div>
        </div>
        ${renderTableTemplate('invoices', custInvs, 'My Invoices')}
      `;
    }

    if (view === 'my-payments') {
      const custPayments = db.payments.filter(p => p.customer.toLowerCase().includes(custName.toLowerCase()));
      return `
        <div class="welcome-card">
          <div class="welcome-info">
            <h2>Payment Transactions</h2>
            <p class="muted">History of settled payments and receipts.</p>
          </div>
        </div>
        ${renderTableTemplate('payments', custPayments, 'Payment History')}
      `;
    }

    if (view === 'my-profile') {
      const custRecord = db.customers.find(c => c.name.toLowerCase().includes(custName.toLowerCase())) || {
        name: custName,
        email: currentUser.email,
        company: custName,
        status: 'Active'
      };
      return `
        <div class="panel" style="max-width:600px">
          <h2>My Account Profile</h2>
          <p class="muted">Your company billing information registered on Brightloop.</p>
          <div style="display:flex;flex-direction:column;gap:12px;margin-top:16px">
            <div><strong>Company:</strong> ${escapeHtml(custRecord.company || custRecord.name)}</div>
            <div><strong>Contact:</strong> ${escapeHtml(custRecord.name)}</div>
            <div><strong>Email:</strong> ${escapeHtml(custRecord.email)}</div>
            <div><strong>Status:</strong> <span class="badge badge-active">${custRecord.status}</span></div>
          </div>
        </div>
      `;
    }

    // Default: my-subscriptions
    return `
      <div class="welcome-card">
        <div class="welcome-info">
          <h2>Welcome, ${escapeHtml(custName)} 👋</h2>
          <p class="muted">Manage your active software subscriptions and plans without having to email anyone.</p>
        </div>
      </div>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-title">MY ACTIVE PLANS</div>
          <div class="stat-value" style="color:var(--odoo-purple)">${custSubs.filter(s => s.status === 'Active').length}</div>
        </div>
        <div class="stat-card">
          <div class="stat-title">TOTAL INVOICED</div>
          <div class="stat-value">${formatCurrency(custInvs.reduce((s, i) => s + Number(i.amount), 0))}</div>
        </div>
        <div class="stat-card">
          <div class="stat-title">PENDING BALANCE</div>
          <div class="stat-value" style="color:var(--warning)">${formatCurrency(custInvs.filter(i => i.status !== 'Paid').reduce((s, i) => s + Math.max(0, i.amount - (i.paidAmount || 0)), 0))}</div>
        </div>
      </div>
      ${renderTableTemplate('subscriptions', custSubs, 'My Current Subscriptions')}
    `;
  }

  // Quotation Templates List (Problem Statement Page 3)
  function renderTemplatesView() {
    return `
      <div class="welcome-card">
        <div class="welcome-info">
          <h2>Quotation Templates</h2>
          <p class="muted">Prepared offer templates for sales reps to build offers in seconds without starting from scratch.</p>
        </div>
        <button class="btn btn-odoo btn-sm" onclick="openAdd('templates')">+ New Template</button>
      </div>

      <div class="table-panel">
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Template Name</th>
                <th>Plan Preset</th>
                <th>Product Line</th>
                <th>Qty</th>
                <th>Validity</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${db.templates.map(t => `
                <tr>
                  <td><strong>${escapeHtml(t.name)}</strong><br><small class="muted">${escapeHtml(t.notes || '')}</small></td>
                  <td>${escapeHtml(t.plan)}</td>
                  <td><strong>${escapeHtml(t.product)}</strong></td>
                  <td>${t.defaultQty}</td>
                  <td>${t.validityDays} Days</td>
                  <td>
                    <button class="btn btn-odoo btn-sm" onclick="createSubFromTemplate('${t.id}')">
                      ⚡ Create Quotation
                    </button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  // Finance Reports (Problem Statement Page 4)
  function renderReportsView() {
    const active = db.subscriptions.filter(s => s.status === 'Active').length;
    const rev = db.payments.reduce((s, p) => s + Number(p.amount), 0);
    const owed = db.invoices.filter(i => i.status !== 'Paid').reduce((s, i) => s + Math.max(0, i.amount - (i.paidAmount || 0)), 0);
    const overdue = db.invoices.filter(i => i.due < getTodayISO() && i.status !== 'Paid').length;

    return `
      <div class="welcome-card">
        <div class="welcome-info">
          <h2>Finance Lead Month-End Report</h2>
          <p class="muted">Instant summary responding in &lt; 200ms across all subscriptions and ledgers.</p>
        </div>
        <div class="welcome-actions">
          <button class="btn btn-secondary btn-sm" onclick="window.print()">Print Report</button>
          <button class="btn btn-odoo btn-sm" onclick="exportTableToCSV('invoices')">Export Invoices</button>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-title">ACTIVE CONTRACTS</div>
          <div class="stat-value" style="color:var(--odoo-purple)">${active}</div>
          <div class="stat-footer">Monthly recurring clients</div>
        </div>
        <div class="stat-card">
          <div class="stat-title">CASH INFLOW</div>
          <div class="stat-value" style="color:var(--success)">${formatCurrency(rev)}</div>
          <div class="stat-footer">Settled via UPI, Card & NEFT</div>
        </div>
        <div class="stat-card">
          <div class="stat-title">OUTSTANDING RECEIVABLES</div>
          <div class="stat-value" style="color:var(--warning)">${formatCurrency(owed)}</div>
          <div class="stat-footer">Pending collection</div>
        </div>
        <div class="stat-card">
          <div class="stat-title">OVERDUE COUNT</div>
          <div class="stat-value" style="color:var(--danger)">${overdue}</div>
          <div class="stat-footer">Chase before lost revenue</div>
        </div>
      </div>

      <div class="panel" style="margin-top:16px">
        <h3>Overdue Invoices Requiring Attention</h3>
        <p class="muted">Invoices that have passed payment terms and need follow-up</p>
        <div class="table-responsive" style="margin-top:12px">
          <table class="data-table">
            <thead>
              <tr><th>Invoice</th><th>Customer</th><th>Due Date</th><th>Amount</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              ${db.invoices.filter(i => i.due < getTodayISO() && i.status !== 'Paid').map(i => `
                <tr>
                  <td class="code-cell">${i.id}</td>
                  <td><strong>${escapeHtml(i.customer)}</strong></td>
                  <td style="color:var(--danger)">${i.due}</td>
                  <td><strong>${formatCurrency(i.amount)}</strong></td>
                  <td><span class="badge badge-overdue">Overdue</span></td>
                  <td>
                    <button class="action-btn primary" onclick="viewInvoiceDoc('${i.id}')">View</button>
                    <button class="action-btn teal" onclick="recordPaymentForInvoice('${i.id}')">Collect Pay</button>
                  </td>
                </tr>
              `).join('') || '<tr><td colspan="6" class="muted">No overdue invoices! All payments are up to date.</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  // Generic Dynamic Table Renderer for All Collections
  function renderTableTemplate(page, customDataset, customTitle) {
    let dataset = [...(customDataset || db[page] || [])];
    const title = customTitle || CONFIGS[page]?.title || page.toUpperCase();

    // Filters
    const statuses = ['All'];
    db[page]?.forEach(item => {
      if (item.status && !statuses.includes(item.status)) statuses.push(item.status);
    });

    if (activeFilter && activeFilter !== 'All') {
      dataset = dataset.filter(x => x.status === activeFilter);
    }

    // Column Definitions
    const colDefs = {
      subscriptions: [
        { key: 'id', label: 'Subscription #', class: 'code-cell' },
        { key: 'customer', label: 'Customer' },
        { key: 'plan', label: 'Plan & Product', render: r => `<strong>${escapeHtml(r.plan)}</strong><br><small class="muted">${escapeHtml(r.product || '')} (${r.frequency || 'Monthly'})</small>` },
        { key: 'amount', label: 'Recurring Total', render: r => `<span class="amount-cell">${formatCurrency(r.amount)}</span>` },
        { key: 'expiry', label: 'Renewal Date' },
        { key: 'status', label: 'Lifecycle State', render: r => `<span class="badge badge-${(r.status||'').toLowerCase()}">${r.status}</span>` },
        { key: 'actions', label: 'Lifecycle Actions', render: r => `
          <div class="row-actions">
            ${r.status === 'Draft' ? `<button class="action-btn primary" onclick="advanceSubscriptionState('${r.id}', 'Quotation')">Send Quote</button>` : ''}
            ${r.status === 'Quotation' ? `<button class="action-btn teal" onclick="advanceSubscriptionState('${r.id}', 'Confirmed')">Confirm Quote</button>` : ''}
            ${r.status === 'Confirmed' ? `<button class="action-btn primary" onclick="advanceSubscriptionState('${r.id}', 'Active')">Activate</button>` : ''}
            ${r.status === 'Active' ? `
              <button class="action-btn teal" onclick="renewSubscription('${r.id}')">Renew</button>
              <button class="action-btn" onclick="advanceSubscriptionState('${r.id}', 'Paused')">Pause</button>
              <button class="action-btn danger" onclick="advanceSubscriptionState('${r.id}', 'Closed')">Close Early</button>
            ` : ''}
            ${r.status === 'Paused' ? `<button class="action-btn primary" onclick="advanceSubscriptionState('${r.id}', 'Active')">Resume</button>` : ''}
            ${currentUser?.role === 'admin' ? `<button class="action-btn danger" onclick="deleteRecord('subscriptions', '${r.id}')">×</button>` : ''}
          </div>
        `}
      ],
      products: [
        { key: 'id', label: 'Product ID', class: 'code-cell' },
        { key: 'name', label: 'Product Name', render: r => `<strong>${escapeHtml(r.name)}</strong><br><small class="muted">${escapeHtml(r.notes || '')}</small>` },
        { key: 'type', label: 'Type' },
        { key: 'variant', label: 'Variant', render: r => `<span class="badge badge-active">${escapeHtml(r.variant || 'Standard')}</span>` },
        { key: 'price', label: 'Sales Price', render: r => `<span class="amount-cell">${formatCurrency(r.price)}</span>` },
        { key: 'cost', label: 'Cost', render: r => formatCurrency(r.cost) },
        { key: 'actions', label: 'Actions', render: r => `
          <div class="row-actions">
            <button class="action-btn" onclick="openEdit('products', '${r.id}')">Edit</button>
            ${currentUser?.role === 'admin' ? `<button class="action-btn danger" onclick="deleteRecord('products', '${r.id}')">×</button>` : ''}
          </div>
        `}
      ],
      plans: [
        { key: 'id', label: 'Plan ID', class: 'code-cell' },
        { key: 'name', label: 'Plan Name' },
        { key: 'frequency', label: 'Frequency', render: r => `<span class="badge badge-quotation">${r.frequency}</span>` },
        { key: 'cost', label: 'Cost', render: r => `<span class="amount-cell">${formatCurrency(r.cost)}</span>` },
        { key: 'minQty', label: 'Min Qty' },
        { key: 'autoCloseOnEnd', label: 'Auto-Close', render: r => r.autoCloseOnEnd ? 'Yes' : 'No' },
        { key: 'actions', label: 'Actions', render: r => `
          <div class="row-actions">
            <button class="action-btn" onclick="openEdit('plans', '${r.id}')">Edit</button>
            ${currentUser?.role === 'admin' ? `<button class="action-btn danger" onclick="deleteRecord('plans', '${r.id}')">×</button>` : ''}
          </div>
        `}
      ],
      customers: [
        { key: 'id', label: 'Customer ID', class: 'code-cell' },
        { key: 'name', label: 'Customer', render: r => `<strong>${escapeHtml(r.name)}</strong>` },
        { key: 'email', label: 'Billing Email' },
        { key: 'company', label: 'Company' },
        { key: 'status', label: 'Status', render: r => `<span class="badge badge-${r.status === 'Active' ? 'active' : 'draft'}">${r.status}</span>` },
        { key: 'actions', label: 'Actions', render: r => `
          <div class="row-actions">
            <button class="action-btn" onclick="openEdit('customers', '${r.id}')">Edit</button>
            ${currentUser?.role === 'admin' ? `<button class="action-btn danger" onclick="deleteRecord('customers', '${r.id}')">×</button>` : ''}
          </div>
        `}
      ],
      staff: [
        { key: 'id', label: 'Staff ID', class: 'code-cell' },
        { key: 'name', label: 'Staff Name', render: r => `<strong>${escapeHtml(r.name)}</strong>` },
        { key: 'email', label: 'Work Email' },
        { key: 'designation', label: 'Designation' },
        { key: 'role', label: 'Role Access', render: r => `<span class="badge badge-active">${r.role.toUpperCase()}</span>` },
        { key: 'actions', label: 'Actions', render: r => `
          <div class="row-actions">
            <button class="action-btn" onclick="openEdit('staff', '${r.id}')">Edit</button>
            <button class="action-btn danger" onclick="deleteRecord('users', '${r.id}')">×</button>
          </div>
        `}
      ],
      invoices: [
        { key: 'id', label: 'Invoice #', class: 'code-cell' },
        { key: 'customer', label: 'Customer' },
        { key: 'date', label: 'Invoice Date' },
        { key: 'due', label: 'Due Date' },
        { key: 'amount', label: 'Total', render: r => `<span class="amount-cell">${formatCurrency(r.amount)}</span>` },
        { key: 'status', label: 'Status', render: r => `<span class="badge badge-${(r.status||'').toLowerCase()}">${r.status}</span>` },
        { key: 'actions', label: 'Actions', render: r => `
          <div class="row-actions">
            <button class="action-btn primary" onclick="viewInvoiceDoc('${r.id}')">View</button>
            ${r.status === 'Draft' ? `<button class="action-btn teal" onclick="confirmInvoice('${r.id}')">Confirm</button>` : ''}
            ${r.status !== 'Paid' ? `<button class="action-btn teal" onclick="recordPaymentForInvoice('${r.id}')">Pay</button>` : ''}
            ${r.status !== 'Paid' ? `<button class="action-btn" onclick="cancelInvoice('${r.id}')">Cancel</button>` : ''}
          </div>
        `}
      ],
      payments: [
        { key: 'id', label: 'Receipt #', class: 'code-cell' },
        { key: 'invoice', label: 'Invoice' },
        { key: 'customer', label: 'Customer' },
        { key: 'method', label: 'Method' },
        { key: 'date', label: 'Date' },
        { key: 'amount', label: 'Amount Paid', render: r => `<span class="amount-cell" style="color:var(--success)">${formatCurrency(r.amount)}</span>` },
        { key: 'actions', label: 'Actions', render: r => `
          <div class="row-actions">
            <button class="action-btn" onclick="openEdit('payments', '${r.id}')">Edit</button>
          </div>
        `}
      ],
      discounts: [
        { key: 'id', label: 'ID', class: 'code-cell' },
        { key: 'name', label: 'Discount Rule' },
        { key: 'code', label: 'Promo Code', render: r => `<code>${escapeHtml(r.code)}</code>` },
        { key: 'type', label: 'Type' },
        { key: 'value', label: 'Value', render: r => r.type === 'Percentage' ? `${r.value}%` : formatCurrency(r.value) },
        { key: 'scope', label: 'Scope' },
        { key: 'maxUses', label: 'Usage Count', render: r => `<strong>${r.usedCount || 0} / ${r.maxUses} uses</strong>` },
        { key: 'ends', label: 'Expires' },
        { key: 'status', label: 'Status', render: r => `<span class="badge badge-active">${r.status}</span>` },
        { key: 'actions', label: 'Actions', render: r => `
          <div class="row-actions">
            <button class="action-btn" onclick="openEdit('discounts', '${r.id}')">Edit</button>
            <button class="action-btn danger" onclick="deleteRecord('discounts', '${r.id}')">×</button>
          </div>
        `}
      ],
      taxes: [
        { key: 'id', label: 'Tax ID', class: 'code-cell' },
        { key: 'name', label: 'Tax Rule' },
        { key: 'rate', label: 'Rate', render: r => `<strong>${r.rate}%</strong>` },
        { key: 'description', label: 'Description' },
        { key: 'isDefault', label: 'Default', render: r => r.isDefault ? '✓ Standard' : '—' }
      ]
    }[page] || [];

    return `
      <div class="table-panel">
        <div class="table-panel-header">
          <div>
            <h3>${title}</h3>
            ${statuses.length > 2 ? `
              <div class="table-filter-tabs" style="margin-top:8px">
                ${statuses.map(st => `
                  <button class="filter-tab ${activeFilter === st ? 'active' : ''}" onclick="window.setTableFilter('${st}')">${st}</button>
                `).join('')}
              </div>
            ` : ''}
          </div>

          <div class="table-actions-bar">
            <input type="text" class="table-search" id="table-search-input" placeholder="Search ${title.toLowerCase()}...">
            <button class="btn btn-secondary btn-sm" onclick="exportTableToCSV('${page}')">Export CSV</button>
            ${currentUser?.role !== 'customer' && CONFIGS[page] ? `
              <button class="btn btn-odoo btn-sm" onclick="openAdd('${page}')">+ Add New</button>
            ` : ''}
          </div>
        </div>

        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>${colDefs.map(c => `<th>${c.label}</th>`).join('')}</tr>
            </thead>
            <tbody id="table-body">
              ${dataset.length ? dataset.map(row => `
                <tr>${colDefs.map(c => `<td class="${c.class || ''}">${c.render ? c.render(row) : escapeHtml(row[c.key] || '—')}</td>`).join('')}</tr>
              `).join('') : '<tr><td colspan="8" class="muted" style="text-align:center;padding:32px">No records found.</td></tr>'}
            </tbody>
          </table>
        </div>

        <div class="table-panel-footer">
          <span>Showing <strong>${dataset.length}</strong> records</span>
          <span>Response latency &lt; 200ms</span>
        </div>
      </div>
    `;
  }

  window.setTableFilter = (filterName) => {
    activeFilter = filterName;
    render();
  };

  function setPage(page) {
    currentPage = page;
    activeFilter = 'All';

    $$('.nav-link').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.page === page);
    });

    const titles = {
      dashboard: 'Executive Dashboard',
      subscriptions: 'Subscription Contracts',
      templates: 'Quotation Templates',
      customers: 'Customer Directory',
      products: 'Products & Variants',
      plans: 'Plan Frequencies',
      staff: 'Staff Directory',
      invoices: 'Billing & Invoices',
      payments: 'Payment Ledger',
      discounts: 'Discount Rules',
      taxes: 'Tax Configuration',
      reports: 'Finance Lead Reports',
      'my-subscriptions': 'My Subscriptions',
      'my-invoices': 'My Invoices',
      'my-payments': 'My Payments',
      'my-profile': 'Account Profile'
    };

    $('#page-title').textContent = titles[page] || 'Dashboard';
    $('#page-eyebrow').textContent = `ODOO · BRIGHTLOOP / ${page.toUpperCase()}`;

    // Close mobile drawer
    $('#sidebar').classList.remove('open');
    $('#sidebar-overlay').classList.remove('active');

    render();
  }

  function render() {
    if (!currentUser) return;

    let content = '';
    if (currentUser.role === 'customer') {
      content = renderCustomerPortal(currentPage);
    } else if (currentPage === 'dashboard') {
      content = renderDashboard();
    } else if (currentPage === 'templates') {
      content = renderTemplatesView();
    } else if (currentPage === 'reports') {
      content = renderReportsView();
    } else if (currentPage === 'staff') {
      content = renderTableTemplate('staff', db.users.filter(u => u.role !== 'customer'), 'Staff Directory');
    } else {
      content = renderTableTemplate(currentPage);
    }

    $('#page-content').innerHTML = content;

    // Search filter
    const search = $('#table-search-input');
    if (search) {
      search.addEventListener('input', () => {
        const q = search.value.toLowerCase().trim();
        const tbody = $('#table-body');
        if (!tbody) return;
        tbody.querySelectorAll('tr').forEach(r => {
          r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
      });
    }
  }

  // --- Mobile Drawer ---
  $('#mobile-toggle').onclick = () => {
    $('#sidebar').classList.add('open');
    $('#sidebar-overlay').classList.add('active');
  };
  $('#sidebar-overlay').onclick = () => {
    $('#sidebar').classList.remove('open');
    $('#sidebar-overlay').classList.remove('active');
  };

  $('#theme-toggle').onclick = toggleTheme;
  $('#btn-logout').onclick = window.handleLogout;

  // --- Application Bootloader ---
  function init() {
    initTheme();
    loadDatabase();

    // Check saved session
    try {
      const savedSession = localStorage.getItem('bl_odoo_session');
      if (savedSession) {
        setSession(JSON.parse(savedSession));
      } else {
        // Starts on authentication screen as requested!
        $('#auth-screen').style.display = 'flex';
        $('#app-layout').style.display = 'none';
      }
    } catch {
      $('#auth-screen').style.display = 'flex';
      $('#app-layout').style.display = 'none';
    }
  }

  window.openAdd = openAdd;
  window.openEdit = openEdit;
  window.setPage = setPage;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();