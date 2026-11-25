# Universal Billing Software — Local MVP

A local-first sales billing starter for different business types (restaurant, saree shop, grocery, electronics, services, etc.). Owners register, select a business type, add their own products/services, and create invoices.

## Run on macOS

Requirements: Python 3.10+, Node.js 18+, npm.

```bash
chmod +x start.sh
./start.sh
```

Open http://localhost:5173. Backend API: http://127.0.0.1:8000/docs.

The SQLite database is created at `backend/billing.db` and remains on this computer.

## MVP scope
- Single local business profile and business-type selection
- Custom product/service catalogue (SKU, category, unit, price, GST rate)
- Customer details and sales invoices
- GST / non-GST tax mode
- Invoice history and browser print/PDF

## Important
This is a development MVP, not production-ready accounting or statutory GST software. It does not yet include authentication, multi-business isolation, inventory accounting, GST filing, e-invoicing, e-way bills, or cloud sync. Verify applicable tax rates and invoice requirements before commercial use. Back up `backend/billing.db`.