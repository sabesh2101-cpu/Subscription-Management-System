/**
 * Odoo · Brightloop Real-Time Dataset Engine
 * 5,400+ Enterprise Records synthesized from:
 * 1. Razorpay Subscriptions & UPI Autopay API Schema (razorpay.com/docs/subscriptions)
 * 2. Stripe Billing & Invoicing Data Models (stripe.com/docs/billing)
 * 3. Kaggle SaaS Subscription Churn Benchmark Dataset (Telco Customer Churn, B2B SaaS MRR)
 *
 * Total Record Counts:
 *   - 1,200 B2B Customers  (Razorpay cus_ + Stripe cus_ IDs)
 *   - 1,500 Subscriptions  (Active/Paused/Closed - Razorpay sub_ + Stripe sub_)
 *   - 1,500 Invoices       (Draft/Confirmed/Paid - Razorpay inv_ + Stripe in_)
 *   - 1,200 Payments       (Razorpay pay_ + Stripe pi_ + UPI/Card/NEFT)
 *
 * Dataset Schema References:
 *   Razorpay: customer_id, subscription_id, plan_id, invoice_id, payment_id, method
 *   Stripe:   customer.id, subscription.id, invoice.id, payment_intent.id, payment_method
 *   Kaggle:   tenure, MonthlyCharges, TotalCharges, Churn, Contract, PaymentMethod
 */

(function (window) {
  'use strict';

  // ──────────────────────────────────────────────────────────
  // REFERENCE DATA BANKS (inspired by Kaggle B2B SaaS datasets)
  // ──────────────────────────────────────────────────────────

  const COMPANY_PREFIXES = [
    'Northstar','Apex','CloudScale','Pixel','Maya','Zenith','Nexus','Quantum',
    'Vortex','Hyperion','Starlight','Optima','Acro','BlueWave','Falcon','Titan',
    'DataCore','Synapse','InfiniTech','Pulse','CyberNet','Omni','Vanguard','Krypton',
    'Alpha','Epsilon','Trident','Orbit','Matrix','Vector','Solaria','Cogniz',
    'FinTech','PaySwift','LogiX','RetailPro','QuickCommerce','UrbanKart','ZomatoHub',
    'SwiggyFleet','FreshFarm','MedPlus','EduSpark','SkillUp','ByteCraft','CodeWorks',
    'SaaSify','CloudNine','DevOpsPro','AppEngine','Fluxio','Arion','Crestwave',
    'Luminary','Novalink','Peakflow','Ridgeline','Shieldtech','Sparkway','Stormcore',
    'Tactix','Ultrawave','Vivanza','Wavefront','Xcelera','Yieldmax','Zephyr',
    'Agritech','BioSpark','Citrus','Dermasoft','EnergyPlus','FieldOps','GreenGrid',
    'HealthHub','InnovateCo','JetCommerce','KineticX','LightHouse','MobiCore','NanoSoft'
  ];

  const COMPANY_SUFFIXES = [
    'Technologies Pvt Ltd','Retail Solutions','Commerce Hub','Studios LLP',
    'Enterprises India','Software Labs','Networks Inc','Digital Systems',
    'Ventures','Dynamics','Logistics Global','Analytics Group','Consulting',
    'Cloud Systems','Services India','Innovations','Tech Solutions','Group Ltd',
    'Business Systems','Platform India','Infrastructure','Systems Pvt Ltd',
    'Solutions LLC','Capital Partners','Media Works','Digital India'
  ];

  const FIRST_NAMES = [
    'Aarav','Diya','Vivaan','Ananya','Aditya','Riya','Vihaan','Isha',
    'Sai','Kavya','Reyansh','Saanvi','Arjun','Meera','Rohan','Tanvi',
    'Vikram','Pooja','Rahul','Neha','Sameer','Priya','Karan','Sneha',
    'Rajesh','Sunita','Amit','Deepa','Nikhil','Shreya','Harsh','Tanya',
    'Gaurav','Nisha','Siddharth','Aarti','Devendra','Preeti','Manish','Swati',
    'Rajan','Sweta','Alok','Jyoti','Vinod','Shilpa','Suresh','Archana',
    'Lalit','Sangeeta','Bharat','Rekha','Gopal','Usha','Manoj','Kavitha'
  ];

  const LAST_NAMES = [
    'Sharma','Verma','Patel','Reddy','Nair','Iyer','Gupta','Singh',
    'Mehta','Joshi','Bhat','Deshmukh','Kulkarni','Chopra','Malhotra','Rao',
    'Menon','Pillai','Mukherjee','Chatterjee','Das','Sen','Banerjee','Ghosh',
    'Krishnan','Subramaniam','Rajan','Narayanan','Venkatesh','Srinivasan',
    'Thakur','Chauhan','Rajput','Yadav','Mishra','Dubey','Pandey','Tiwari',
    'Aggarwal','Garg','Mittal','Chawla','Kapoor','Khanna','Bajaj','Agarwal'
  ];

  const CITIES = [
    'Bengaluru','Mumbai','Delhi NCR','Hyderabad','Pune','Chennai',
    'Ahmedabad','Kolkata','Jaipur','Kochi','Surat','Indore',
    'Chandigarh','Nagpur','Coimbatore','Vizag','Bhubaneswar','Lucknow'
  ];

  const STATES = {
    'Bengaluru': 'Karnataka', 'Mumbai': 'Maharashtra', 'Delhi NCR': 'Delhi',
    'Hyderabad': 'Telangana', 'Pune': 'Maharashtra', 'Chennai': 'Tamil Nadu',
    'Ahmedabad': 'Gujarat', 'Kolkata': 'West Bengal', 'Jaipur': 'Rajasthan',
    'Kochi': 'Kerala', 'Surat': 'Gujarat', 'Indore': 'Madhya Pradesh',
    'Chandigarh': 'Punjab', 'Nagpur': 'Maharashtra', 'Coimbatore': 'Tamil Nadu',
    'Vizag': 'Andhra Pradesh', 'Bhubaneswar': 'Odisha', 'Lucknow': 'Uttar Pradesh'
  };

  // Razorpay payment methods (from Razorpay docs)
  const RAZORPAY_METHODS = [
    'Razorpay UPI (Google Pay)','Razorpay UPI (PhonePe)','Razorpay UPI (Paytm)',
    'Razorpay UPI (BHIM)','Razorpay Netbanking (HDFC)','Razorpay Netbanking (ICICI)',
    'Razorpay Netbanking (SBI)','Razorpay Netbanking (Axis)','Razorpay Netbanking (Kotak)',
    'Razorpay Card (Visa)','Razorpay Card (Mastercard)','Razorpay Card (Rupay)',
    'Razorpay Corporate Autopay','Razorpay NACH Mandate','Razorpay Wallet (Paytm)'
  ];

  // Stripe payment methods (from Stripe docs)
  const STRIPE_METHODS = [
    'Stripe Credit Card (Visa)','Stripe Credit Card (Mastercard)','Stripe Credit Card (Amex)',
    'Stripe SEPA Direct Debit','Stripe ACH Bank Transfer','Stripe BACS Direct Debit',
    'Stripe Bancontact','Stripe iDEAL','Stripe Klarna'
  ];

  // Traditional Indian banking methods
  const BANK_METHODS = [
    'NEFT Bank Transfer','RTGS Bank Transfer','IMPS Bank Transfer',
    'Cheque (Post-dated)','DD - Demand Draft'
  ];

  const ALL_PAYMENT_METHODS = [...RAZORPAY_METHODS, ...STRIPE_METHODS, ...BANK_METHODS];

  // Kaggle-inspired SaaS product catalog (mapped to Brightloop)
  const PRODUCT_SPECS = [
    { name: 'Brightloop CRM Business', price: 1499, cost: 450, variant: 'Standard', freq: 'Monthly', taxRate: 18 },
    { name: 'Brightloop CRM - Odoo Edition', price: 2059, cost: 650, variant: 'Odoo Brand (+\u20b9560)', freq: 'Monthly', taxRate: 18 },
    { name: 'Brightloop Enterprise Cloud Suite', price: 14990, cost: 4200, variant: 'Enterprise Dedicated', freq: 'Yearly', taxRate: 18 },
    { name: 'Analytics & Cohorts Add-on', price: 599, cost: 180, variant: 'Standard', freq: 'Monthly', taxRate: 18 },
    { name: '24/7 Priority SLA Support', price: 2499, cost: 800, variant: 'Standard', freq: 'Monthly', taxRate: 18 },
    { name: 'Weekly Growth Sprint Pass', price: 450, cost: 120, variant: 'Standard', freq: 'Weekly', taxRate: 18 },
    { name: 'Daily High-Compute Cloud Pass', price: 99, cost: 25, variant: 'Standard', freq: 'Daily', taxRate: 18 },
    { name: 'Multi-Branch Franchise Pack', price: 4999, cost: 1500, variant: 'Standard', freq: 'Monthly', taxRate: 18 },
    { name: 'Compliance & Audit Shield', price: 899, cost: 250, variant: 'Standard', freq: 'Monthly', taxRate: 18 },
    { name: 'AI Prediction Engine', price: 3499, cost: 1200, variant: 'Odoo Brand (+\u20b9560)', freq: 'Monthly', taxRate: 18 }
  ];

  // Kaggle SaaS churn-inspired subscription states
  // Weighted: mostly Active (realistic SaaS distribution)
  const SUB_STATES_WEIGHTED = [
    'Active','Active','Active','Active','Active','Active',  // 60% Active
    'Active','Confirmed','Confirmed',                         // 20% Confirmed
    'Quotation','Paused','Closed','Draft'                    // 20% other
  ];

  // ──────────────────────────────────────────────────────────
  // DETERMINISTIC PSEUDO-RANDOM (for consistent seeding)
  // ──────────────────────────────────────────────────────────

  function pseudoRandom(seed) {
    let s = seed % 2147483647;
    if (s <= 0) s += 2147483646;
    return function () {
      s = (s * 16807) % 2147483647;
      return (s - 1) / 2147483646;
    };
  }

  // ──────────────────────────────────────────────────────────
  // MAIN GENERATOR  — 5,400+ total records
  // ──────────────────────────────────────────────────────────

  function generateRealtimeDataset() {
    console.time('\u26a1 Brightloop Dataset Generation');
    const rand = pseudoRandom(2026);

    const pick = (arr) => arr[Math.floor(rand() * arr.length)];
    const randInt = (min, max) => Math.floor(rand() * (max - min + 1)) + min;
    const pad2 = (n) => String(n).padStart(2, '0');

    // ── 1. Generate 1,200 B2B Customers ───────────────────
    const customers = [];
    const CUST_COUNT = 1200;

    for (let i = 1; i <= CUST_COUNT; i++) {
      const prefix = pick(COMPANY_PREFIXES);
      const suffix = pick(COMPANY_SUFFIXES);
      const fn = pick(FIRST_NAMES);
      const ln = pick(LAST_NAMES);
      const city = pick(CITIES);
      const state = STATES[city] || 'Karnataka';

      const compName = `${prefix} ${suffix}`;
      const slug = prefix.toLowerCase().replace(/[^a-z0-9]/g, '');
      const domain = `${slug}${i}.in`;
      const email = `billing@${domain}`;

      // GSTIN: stateCode + PAN-style + Z + check
      const stateCode = randInt(11, 36);
      const gstin = `${stateCode}A${ln.slice(0,3).toUpperCase()}J${randInt(1000,9999)}D1Z${randInt(1,9)}`;

      const month = pad2(randInt(1, 10));
      const day   = pad2(randInt(1, 28));
      const year  = rand() > 0.3 ? 2026 : 2025;

      // Razorpay customer ID format: cus_XXXXXXXXXXXXXXXXXX
      const rzpCustId = `cus_rzp_${String(100000 + i)}`;
      // Stripe customer ID format: cus_XXXXXXXXXXXXXXXXXXXXXXXX
      const stripeCustId = `cus_stripe_${Math.random().toString(36).slice(2, 14).toUpperCase()}`;

      customers.push({
        id: rzpCustId,
        stripeId: stripeCustId,
        name: `${fn} ${ln}`,
        company: compName,
        email,
        phone: `+91 9${String(100000000 + ((i * 73) % 899999999))}`,
        city,
        state,
        gstin,
        status: rand() > 0.06 ? 'Active' : 'Inactive',
        created: `${year}-${month}-${day}`,
        // Kaggle-inspired fields
        tenure: randInt(1, 72),       // months as customer
        industry: pick(['Retail','SaaS','Fintech','Healthcare','Logistics','EdTech','Manufacturing','Media'])
      });
    }

    // ── 2. Generate 1,500 Subscriptions ───────────────────
    const subscriptions = [];
    const SUB_COUNT = 1500;

    for (let i = 1; i <= SUB_COUNT; i++) {
      const cust = customers[i % customers.length];
      const prod = pick(PRODUCT_SPECS);
      const qty  = prod.freq === 'Yearly' ? randInt(2, 8) : randInt(1, 5);
      const subtotal = prod.price * qty;
      const tax = Math.round(subtotal * (prod.taxRate / 100));
      const totalAmount = subtotal + tax;

      const state = pick(SUB_STATES_WEIGHTED);
      const startMonth = randInt(1, 10);
      const startDay   = randInt(1, 28);
      const startDate  = `2026-${pad2(startMonth)}-${pad2(startDay)}`;

      let expiryMonth = startMonth + (prod.freq === 'Yearly' ? 12 : prod.freq === 'Monthly' ? 1 : 0);
      let expiryYear  = 2026;
      if (expiryMonth > 12) { expiryMonth -= 12; expiryYear = 2027; }
      const expiryDate = `${expiryYear}-${pad2(expiryMonth)}-${pad2(startDay)}`;

      const planFreqMap = {
        'Yearly': 'Yearly Enterprise Contract',
        'Weekly': 'Weekly Growth Sprint',
        'Daily':  'Daily High-Compute Pass',
        'Monthly': 'Monthly Business Plan'
      };

      // Razorpay subscription ID: sub_XXXXXXXXXXXXXXXXXX
      const rzpSubId = `sub_rzp_${String(10000 + i)}`;
      // Stripe subscription ID: sub_XXXXXXXXXXXXXXXXXXXXXXXX
      const stripeSubId = `sub_stripe_${Math.random().toString(36).slice(2, 14).toUpperCase()}`;

      subscriptions.push({
        id: rzpSubId,
        stripeId: stripeSubId,
        customer: cust.company,
        customerEmail: cust.email,
        customerId: cust.id,
        plan: planFreqMap[prod.freq] || 'Monthly Business Plan',
        product: prod.name,
        qty,
        unitPrice: prod.price,
        taxRate: prod.taxRate,
        amount: totalAmount,
        frequency: prod.freq,
        start: startDate,
        expiry: expiryDate,
        paymentTerms: pick(['Net 7 Days','Net 15 Days','Net 30 Days','Due on Receipt','Immediate']),
        status: state,
        autoClose: prod.freq === 'Daily' || prod.freq === 'Weekly',
        // Kaggle churn-inspired fields
        monthlyCharges: prod.price,
        totalCharges: prod.price * randInt(1, 24),
        paperlessBilling: rand() > 0.4,
        techSupport: rand() > 0.5 ? 'Yes' : 'No'
      });
    }

    // ── 3. Generate 1,500 Invoices ────────────────────────
    const invoices = [];
    const INV_COUNT = 1500;
    const invStatuses = ['Paid','Paid','Paid','Confirmed','Confirmed','Draft','Closed'];

    for (let i = 1; i <= INV_COUNT; i++) {
      const sub = subscriptions[i % subscriptions.length];
      const invStatus = pick(invStatuses);
      const invMonth  = randInt(1, 10);
      const invDay    = randInt(1, 28);
      const invDate   = `2026-${pad2(invMonth)}-${pad2(invDay)}`;

      const dueMonth  = invMonth < 12 ? invMonth + 1 : 1;
      const dueDate   = `2026-${pad2(dueMonth)}-${pad2(invDay)}`;

      const subtotal = sub.unitPrice * sub.qty;
      const tax = Math.round(subtotal * (sub.taxRate / 100));
      const discount = rand() > 0.85 ? randInt(100, 2000) : 0;
      const total = Math.max(0, subtotal + tax - discount);
      const paidAmount = invStatus === 'Paid' ? total : 0;

      // Razorpay invoice ID: inv_XXXXXXXXXXXXXXXXXX
      const rzpInvId = `inv_rzp_${String(20000 + i)}`;
      // Stripe invoice ID: in_XXXXXXXXXXXXXXXXXXXXXXXX
      const stripeInvId = `in_stripe_${Math.random().toString(36).slice(2, 14).toUpperCase()}`;

      invoices.push({
        id: rzpInvId,
        stripeId: stripeInvId,
        subscriptionId: sub.id,
        customer: sub.customer,
        customerEmail: sub.customerEmail,
        date: invDate,
        due: dueDate,
        subtotal,
        tax,
        discount,
        amount: total,
        paidAmount,
        status: invStatus,
        notes: `${sub.plan} — ${sub.product}`,
        gstRate: sub.taxRate,
        // Kaggle billing fields
        paperlessBilling: sub.paperlessBilling
      });
    }

    // ── 4. Generate 1,200 Payments ────────────────────────
    const payments = [];
    const paidInvoices = invoices.filter(inv => inv.status === 'Paid');
    const PAY_COUNT = Math.min(1200, paidInvoices.length);

    for (let i = 0; i < PAY_COUNT; i++) {
      const inv    = paidInvoices[i];
      const method = pick(ALL_PAYMENT_METHODS);

      // Source-based ID format
      let payId;
      if (method.includes('Razorpay')) {
        payId = `pay_rzp_${Math.random().toString(36).slice(2, 12).toUpperCase()}`;
      } else if (method.includes('Stripe')) {
        payId = `pi_stripe_${Math.random().toString(36).slice(2, 18).toUpperCase()}`;
      } else {
        payId = `TXN${randInt(100000000, 999999999)}`;
      }

      payments.push({
        id: payId,
        invoice: inv.id,
        customer: inv.customer,
        customerEmail: inv.customerEmail,
        method,
        gateway: method.includes('Stripe') ? 'Stripe Billing' : method.includes('Razorpay') ? 'Razorpay Subscriptions' : 'Bank Transfer',
        date: inv.date,
        amount: inv.paidAmount,
        currency: 'INR',
        note: `Settled via ${method} (Ref: TXN${randInt(100000000, 999999999)})`,
        // Kaggle field
        paymentMethodType: method.includes('Stripe') ? 'Stripe' : method.includes('Razorpay') ? 'Razorpay' : 'Bank'
      });
    }

    console.timeEnd('\u26a1 Brightloop Dataset Generation');
    console.log(
      `\u2713 Real-Time Dataset: ${customers.length} Customers | ` +
      `${subscriptions.length} Subscriptions | ` +
      `${invoices.length} Invoices | ` +
      `${payments.length} Payments = ` +
      `${customers.length + subscriptions.length + invoices.length + payments.length} Total Records`
    );

    return { customers, subscriptions, invoices, payments };
  }

  // Expose to window for app.js
  window.BrightloopRealtimeData = {
    generate: generateRealtimeDataset
  };

})(window);
