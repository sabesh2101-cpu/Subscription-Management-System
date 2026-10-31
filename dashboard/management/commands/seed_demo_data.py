import random
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from accounts.models import User
from catalog.models import Product, SubscriptionPlan
from billing.models import Discount, Invoice, Payment
from subscriptions.models import Subscription, compute_next_billing_date
from dashboard.models import MSMEStatistic


class Command(BaseCommand):
    help = 'Seeds realistic demo data for the Subscription Management System prototype.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("==> Clearing existing prototype data..."))
        Payment.objects.all().delete()
        Invoice.objects.all().delete()
        Subscription.objects.all().delete()
        Discount.objects.all().delete()
        SubscriptionPlan.objects.all().delete()
        Product.objects.all().delete()
        MSMEStatistic.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        User.objects.filter(username='admin').delete()

        self.stdout.write(self.style.NOTICE("==> Creating demo users..."))
        # 1 Admin
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@subtrack.internal',
            password='admin123',
            first_name='System',
            last_name='Administrator',
            role=User.ROLE_ADMIN,
            company_name='SubTrack HQ'
        )

        # 1 Staff
        staff = User.objects.create_user(
            username='staff_priya',
            email='priya@subtrack.internal',
            password='staff123',
            first_name='Priya',
            last_name='Sharma',
            role=User.ROLE_STAFF,
            is_staff=True,
            company_name='Customer Operations'
        )

        # 3 Customers
        c1 = User.objects.create_user(
            username='cust_arun',
            email='arun@apexretail.com',
            password='cust123',
            first_name='Arun',
            last_name='Kumar',
            role=User.ROLE_CUSTOMER,
            company_name='Apex Retail Enterprises',
            phone='+91-9876543210',
            address='Suite 402, Commercial Towers, Bengaluru, KA'
        )

        c2 = User.objects.create_user(
            username='cust_meera',
            email='meera@zenithcloud.io',
            password='cust123',
            first_name='Meera',
            last_name='Nair',
            role=User.ROLE_CUSTOMER,
            company_name='Zenith Cloud Logistics',
            phone='+91-9811223344',
            address='Unit 12, Export Hub, Chennai, TN'
        )

        c3 = User.objects.create_user(
            username='cust_karan',
            email='karan@horizonmfg.in',
            password='cust123',
            first_name='Karan',
            last_name='Patel',
            role=User.ROLE_CUSTOMER,
            company_name='Horizon Manufacturing Ltd',
            phone='+91-9922334455',
            address='GIDC Industrial Estate, Ahmedabad, GJ'
        )

        customers = [c1, c2, c3]

        self.stdout.write(self.style.NOTICE("==> Creating 5 catalog products..."))
        p1 = Product.objects.create(
            sku='ODOO-INV-01',
            name='Odoo Invoicing Pro',
            description='Automated billing, quote-to-cash workflows, tax compliance and invoice tracking.',
            price=Decimal('49.00'),
            is_active=True
        )
        p2 = Product.objects.create(
            sku='ERP-SUITE-X',
            name='Cloud ERP Suite',
            description='Comprehensive ERP module integrating inventory, sales, procurement and financial accounting.',
            price=Decimal('199.00'),
            is_active=True
        )
        p3 = Product.objects.create(
            sku='INV-MSME-02',
            name='MSME Inventory Manager',
            description='Lightweight barcode, stock replenishment and multi-warehouse software for growing SMEs.',
            price=Decimal('29.00'),
            is_active=True
        )
        p4 = Product.objects.create(
            sku='HR-AUTO-05',
            name='Payroll & HR Automator',
            description='End-to-end payroll computation, attendance tracking and regulatory filings.',
            price=Decimal('79.00'),
            is_active=True
        )
        p5 = Product.objects.create(
            sku='CRM-HELP-08',
            name='Customer CRM & Helpdesk',
            description='Omnichannel support ticketing, customer communication log and SLA monitoring.',
            price=Decimal('59.00'),
            is_active=True
        )

        self.stdout.write(self.style.NOTICE("==> Creating 8 subscription plans..."))
        plan1 = SubscriptionPlan.objects.create(
            product=p1,
            name='Invoicing Starter Monthly',
            billing_cycle=SubscriptionPlan.CYCLE_MONTHLY,
            price=Decimal('19.00'),
            trial_days=14,
            is_active=True
        )
        plan2 = SubscriptionPlan.objects.create(
            product=p1,
            name='Invoicing Growth Quarterly',
            billing_cycle=SubscriptionPlan.CYCLE_QUARTERLY,
            price=Decimal('49.00'),
            trial_days=0,
            is_active=True
        )
        plan3 = SubscriptionPlan.objects.create(
            product=p1,
            name='Invoicing Enterprise Annual',
            billing_cycle=SubscriptionPlan.CYCLE_YEARLY,
            price=Decimal('180.00'),
            trial_days=30,
            is_active=True
        )
        plan4 = SubscriptionPlan.objects.create(
            product=p2,
            name='Cloud ERP Professional Monthly',
            billing_cycle=SubscriptionPlan.CYCLE_MONTHLY,
            price=Decimal('99.00'),
            trial_days=14,
            is_active=True
        )
        plan5 = SubscriptionPlan.objects.create(
            product=p2,
            name='Cloud ERP Annual Corporate',
            billing_cycle=SubscriptionPlan.CYCLE_YEARLY,
            price=Decimal('990.00'),
            trial_days=30,
            is_active=True
        )
        plan6 = SubscriptionPlan.objects.create(
            product=p3,
            name='MSME Inventory Standard Monthly',
            billing_cycle=SubscriptionPlan.CYCLE_MONTHLY,
            price=Decimal('25.00'),
            trial_days=7,
            is_active=True
        )
        plan7 = SubscriptionPlan.objects.create(
            product=p4,
            name='HR Automator Monthly',
            billing_cycle=SubscriptionPlan.CYCLE_MONTHLY,
            price=Decimal('45.00'),
            trial_days=14,
            is_active=True
        )
        plan8 = SubscriptionPlan.objects.create(
            product=p5,
            name='CRM Pro Annual',
            billing_cycle=SubscriptionPlan.CYCLE_YEARLY,
            price=Decimal('499.00'),
            trial_days=14,
            is_active=True
        )

        all_plans = [plan1, plan2, plan3, plan4, plan5, plan6, plan7, plan8]

        self.stdout.write(self.style.NOTICE("==> Creating 6 discount vouchers..."))
        today = timezone.now().date()
        d1 = Discount.objects.create(
            code='WELCOME10',
            type=Discount.TYPE_PERCENT,
            value=Decimal('10.00'),
            valid_from=today - timedelta(days=180),
            valid_to=today + timedelta(days=180),
            usage_limit=100,
            times_used=8,
            is_active=True
        )
        d2 = Discount.objects.create(
            code='MSME25',
            type=Discount.TYPE_PERCENT,
            value=Decimal('25.00'),
            valid_from=today - timedelta(days=120),
            valid_to=today + timedelta(days=120),
            usage_limit=50,
            times_used=12,
            is_active=True
        )
        d3 = Discount.objects.create(
            code='STARTUP50',
            type=Discount.TYPE_FIXED,
            value=Decimal('50.00'),
            valid_from=today - timedelta(days=90),
            valid_to=today + timedelta(days=90),
            usage_limit=20,
            times_used=4,
            is_active=True
        )
        d4 = Discount.objects.create(
            code='ANNUALSAVE',
            type=Discount.TYPE_PERCENT,
            value=Decimal('15.00'),
            valid_from=today - timedelta(days=180),
            valid_to=today + timedelta(days=180),
            usage_limit=200,
            times_used=6,
            is_active=True
        )
        d5 = Discount.objects.create(
            code='FLAT15',
            type=Discount.TYPE_FIXED,
            value=Decimal('15.00'),
            valid_from=today - timedelta(days=60),
            valid_to=today + timedelta(days=180),
            usage_limit=100,
            times_used=3,
            is_active=True
        )
        d6 = Discount.objects.create(
            code='EXPIRED20',
            type=Discount.TYPE_PERCENT,
            value=Decimal('20.00'),
            valid_from=today - timedelta(days=400),
            valid_to=today - timedelta(days=200),
            usage_limit=30,
            times_used=30,
            is_active=False
        )

        active_discounts = [d1, d2, d3, d4, d5, None, None, None]

        self.stdout.write(self.style.NOTICE("==> Creating 15 subscriptions..."))
        subscriptions = []
        statuses = [
            Subscription.STATUS_ACTIVE,
            Subscription.STATUS_ACTIVE,
            Subscription.STATUS_ACTIVE,
            Subscription.STATUS_ACTIVE,
            Subscription.STATUS_ACTIVE,
            Subscription.STATUS_ACTIVE,
            Subscription.STATUS_ACTIVE,
            Subscription.STATUS_ACTIVE,
            Subscription.STATUS_ACTIVE,
            Subscription.STATUS_ACTIVE,
            Subscription.STATUS_PAUSED,
            Subscription.STATUS_PAUSED,
            Subscription.STATUS_CANCELLED,
            Subscription.STATUS_CANCELLED,
            Subscription.STATUS_DRAFT,
        ]

        for i in range(15):
            customer = customers[i % len(customers)]
            plan = all_plans[i % len(all_plans)]
            status = statuses[i]
            discount = active_discounts[i % len(active_discounts)]

            # Stagger start dates across the last 6 months
            days_ago = (15 - i) * 12
            start_dt = today - timedelta(days=days_ago)
            next_bill = compute_next_billing_date(start_dt, plan.billing_cycle)

            sub = Subscription.objects.create(
                customer=customer,
                plan=plan,
                start_date=start_dt,
                next_billing_date=next_bill,
                status=status,
                discount=discount,
                notes=f"Demo subscription contract #{i+1} for {customer.company_name}."
            )
            subscriptions.append(sub)

        self.stdout.write(self.style.NOTICE("==> Generating invoices and payments across the last 6 months..."))
        payment_methods = [
            Payment.METHOD_CARD,
            Payment.METHOD_UPI,
            Payment.METHOD_BANK_TRANSFER,
            Payment.METHOD_CASH
        ]

        inv_count = 1
        current_year = today.year

        # Create realistic billing cycles over months 5 down to 0 (current)
        for month_offset in range(5, -1, -1):
            cycle_date = today - timedelta(days=month_offset * 30)

            # Generate invoices for each customer for active/paused subs
            for idx, sub in enumerate(subscriptions[:12]):
                if sub.start_date <= cycle_date:
                    subtotal = sub.plan.price
                    discount_amount = Decimal('0.00')
                    if sub.discount:
                        discount_amount = sub.discount.calculate_discount_amount(subtotal)
                    total = max(Decimal('0.00'), subtotal - discount_amount)

                    inv_num = f"INV-{current_year}-{inv_count:04d}"
                    inv_count += 1
                    due_date = cycle_date + timedelta(days=15)

                    # Historical invoices: paid; recent ones: some unpaid or overdue
                    if month_offset >= 2:
                        inv_status = Invoice.STATUS_PAID
                    elif month_offset == 1:
                        inv_status = Invoice.STATUS_PAID if idx % 2 == 0 else Invoice.STATUS_OVERDUE
                    else:
                        inv_status = Invoice.STATUS_SENT if idx % 2 == 1 else Invoice.STATUS_PAID

                    invoice = Invoice.objects.create(
                        invoice_number=inv_num,
                        subscription=sub,
                        issue_date=cycle_date,
                        due_date=due_date,
                        subtotal=subtotal,
                        discount_amount=discount_amount,
                        tax_amount=Decimal('0.00'),
                        total=total,
                        status=inv_status,
                        notes=f"Billing cycle invoice for {sub.plan.name}"
                    )

                    # If paid, record payment
                    if inv_status == Invoice.STATUS_PAID:
                        paid_time = timezone.make_aware(
                            timezone.datetime.combine(cycle_date + timedelta(days=random.randint(1, 10)), timezone.datetime.min.time())
                        )
                        Payment.objects.create(
                            invoice=invoice,
                            amount=total,
                            method=payment_methods[idx % len(payment_methods)],
                            reference=f"TXN-{current_year}-{random.randint(100000, 999999)}",
                            paid_on=paid_time,
                            status=Payment.STATUS_SUCCESS,
                            notes="Automated demo reconciliation"
                        )
                    elif inv_status == Invoice.STATUS_OVERDUE and total > Decimal('20.00'):
                        # Partial payment on overdue invoice
                        partial = (total / Decimal('2.0')).quantize(Decimal('0.01'))
                        Payment.objects.create(
                            invoice=invoice,
                            amount=partial,
                            method=Payment.METHOD_UPI,
                            reference=f"UPI-PARTIAL-{random.randint(10000, 99999)}",
                            paid_on=timezone.make_aware(timezone.datetime.combine(cycle_date + timedelta(days=5), timezone.datetime.min.time())),
                            status=Payment.STATUS_SUCCESS,
                            notes="Partial settlement"
                        )

        self.stdout.write(self.style.NOTICE("==> Seeding MSME Economic Reference Data..."))
        msme_samples = [
            ("Maharashtra", "Manufacturing", 450200, 2026, "Auto component, textiles and metal fabrication units"),
            ("Maharashtra", "IT & Software Services", 310500, 2026, "Pune and Mumbai tech park registered service units"),
            ("Tamil Nadu", "Automotive & Engineering", 398000, 2026, "Chennai auto cluster and Coimbatore precision engineering"),
            ("Tamil Nadu", "Textiles & Apparel", 285400, 2026, "Tirupur and Erode export garment hubs"),
            ("Karnataka", "IT & Cloud Software", 345000, 2026, "Bengaluru tech corridor startups and MSME service providers"),
            ("Karnataka", "Electronics & Hardware", 182300, 2026, "Hardware prototyping and assembly clusters"),
            ("Gujarat", "Chemicals & Petrochemicals", 312000, 2026, "Ankleshwar and Vapi industrial belts"),
            ("Gujarat", "Retail & E-commerce", 267400, 2026, "Surat and Ahmedabad trading enterprises"),
            ("Telangana", "Pharma & Life Sciences", 215000, 2026, "Genome Valley biotechnology and formulation units"),
            ("Delhi NCR", "Retail & E-commerce", 298000, 2026, "B2B distribution networks and online merchants"),
            ("Uttar Pradesh", "Handicrafts & Leather", 230400, 2026, "Kanpur leather and Moradabad brassware units"),
            ("West Bengal", "Food Processing", 192000, 2026, "Agro processing and cold-chain clusters"),
            ("Maharashtra", "Manufacturing", 420000, 2025, "Annual baseline census 2025"),
            ("Tamil Nadu", "Automotive & Engineering", 375000, 2025, "Annual baseline census 2025"),
            ("Karnataka", "IT & Cloud Software", 310000, 2025, "Annual baseline census 2025"),
        ]

        for state, sector, units, yr, notes in msme_samples:
            MSMEStatistic.objects.create(
                state=state,
                sector=sector,
                registered_units=units,
                year=yr,
                notes=notes
            )

        self.stdout.write(self.style.SUCCESS("\n" + "="*70))
        self.stdout.write(self.style.SUCCESS("  SUBSCRIPTION MANAGEMENT SYSTEM DEMO SEED COMPLETED"))
        self.stdout.write(self.style.SUCCESS("="*70))
        self.stdout.write(self.style.SUCCESS("Demo User Accounts:"))
        self.stdout.write(self.style.SUCCESS("  [ADMIN]    Username: admin        | Password: admin123"))
        self.stdout.write(self.style.SUCCESS("  [STAFF]    Username: staff_priya  | Password: staff123"))
        self.stdout.write(self.style.SUCCESS("  [CUSTOMER] Username: cust_arun    | Password: cust123"))
        self.stdout.write(self.style.SUCCESS("  [CUSTOMER] Username: cust_meera   | Password: cust123"))
        self.stdout.write(self.style.SUCCESS("  [CUSTOMER] Username: cust_karan   | Password: cust123"))
        self.stdout.write(self.style.SUCCESS("="*70 + "\n"))
