
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    barcode = Column(String(50), unique=True, index=True, nullable=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    purchase_price = Column(Float, default=0.0)#آخرین قیمت خرید (یا میانگین موزون قیمت خرید
    sale_price = Column(Float, default=0.0)#قیمت فروش پایه
    min_sale_price = Column(Float, default=0.0)#حداقل قیمت مجاز برای تخفیف (جلوگیری از فروش زیر قیمت
    stock = Column(Integer, default=0)
    min_stock_alert = Column(Integer, default=5)#حداقل موجودی هشدار (نمایش پیام کمبود کالا در پنل
    unit = Column(String(30), default="عدد")#واحد سنجش (عدد، کیلوگرم، بسته، کارتن
    is_active = Column(Boolean, default=True)#فعال/غیرفعال بودن محصول
    image_path = Column(String(255), nullable=True)#آدرس تصویر محصول
    created_at = Column(DateTime, default=datetime.now)#تاریخ ایجاد محصول
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)#تاریخ آخرین ویرایش

    sale_items = relationship("SaleItem", back_populates="product")
    purchase_items = relationship("PurchaseItem", back_populates="product")


#برای باشگاه مشتریان، دسته‌بندی و پیگیری مطالبات نسیه.
class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    address = Column(Text, nullable=True)
    balance = Column(Float, default=0.0)#مانده حساب (مثبت: بدهکار، منفی: بستانکار) |
    credit_limit = Column(Float, default=0.0)#سقف مجاز خرید نسیه/اعتباری |
    loyalty_points = Column(Integer, default=0)#امتیاز باشگاه مشتریان |
    notes = Column(Text, nullable=True)#یادداشت‌های اختصاصی درباره مشتری |
    created_at = Column(DateTime, default=datetime.now)#تاریخ ثبت مشتری

    sales = relationship("SaleInvoice", back_populates="customer")

#جدول تأمین‌کننده / خریدار عمده
#برای اینکه خریدهای انبار از حالت دستی خارج شده و طرف حساب مشخص باشد
class Supplier(Base):
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)#نام شخص یا شرکت تأمین‌کننده
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    balance = Column(Float, default=0.0)#تراز حساب (بستانکاری/بدهکاری به تأمین‌کننده
    created_at = Column(DateTime, default=datetime.now)#تاریخ ثبت

    purchases = relationship("PurchaseInvoice", back_populates="supplier")

#جدول فاکتور خرید / ورود به انبار
#برای ثبت دقیق خریدهایی که موجودی را افزایش می‌دهند و هزینه ایجاد می‌کنند.
class PurchaseInvoice(Base):
    __tablename__ = 'purchase_invoices'

    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), nullable=True)#شماره فاکتور خرید (دستی یا سیستمی) |
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)#ارجاع به تأمین‌کننده (اختیاری) |
    total_amount = Column(Float, default=0.0)#جمع کل فاکتور خرید
    paid_amount = Column(Float, default=0.0)#مبلغ پرداخت‌شده به تأمین‌کننده |
    payment_status = Column(String(20), default="paid")  # paid, partial, creditوضعیت پرداخت
    invoice_date = Column(DateTime, default=datetime.now)#تاریخ خرید
    notes = Column(Text, nullable=True)#توضیحات خرید

    supplier = relationship("Supplier", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase_invoice", cascade="all, delete-orphan")

#جدول اقلام فاکتور خرید
#
class PurchaseItem(Base):
    __tablename__ = 'purchase_items'

    id = Column(Integer, primary_key=True)
    purchase_id = Column(Integer, ForeignKey('purchase_invoices.id'))#شناسه فاکتور خرید |
    product_id = Column(Integer, ForeignKey('products.id'))#شناسه محصول
    quantity = Column(Integer, default=1)#تعداد خریداری‌شده
    unit_price = Column(Float, default=0.0)#قیمت خرید واحد در زمان این فاکتور |
    total_price = Column(Float, default=0.0)#جمع سطر (`quantity * unit_price`) |

    purchase_invoice = relationship("PurchaseInvoice", back_populates="items")
    product = relationship("Product", back_populates="purchase_items")

#. جدول فاکتور فروش
class SaleInvoice(Base):
    __tablename__ = 'sale_invoices'

    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), unique=True, index=True)#شماره فاکتور رسمی (مانند `INV-1403-001`) |
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)#ارجاع به مشتری (می‌تواند برای مشتری گذری `Null` باشد) |
    subtotal = Column(Float, default=0.0)#جمع اقلام قبل از تخفیف و مالیات |
    discount_amount = Column(Float, default=0.0)#مبلغ تخفیف کل
    tax_amount = Column(Float, default=0.0)#| `tax_amount` | `Float` (Default: 0) | مالیات یا ارزش افزوده (در صورت نیاز) |
    total_amount = Column(Float, default=0.0)#مبلغ نهایی پرداختی مشتری (`subtotal - discount + tax`) |
    total_cost = Column(Float, default=0.0)#بهای تمام‌شده کل اقلام (برای محاسبه دقیق و لحظه‌ای سود
    net_profit = Column(Float, default=0.0)#سود خالص این فاکتور (`total_amount - total_cost`) |
    paid_amount = Column(Float, default=0.0)#مبلغ پرداخت‌شده توسط مشتری |
    payment_method = Column(String(30), default="cash")  # cash, card, credit, etc. روش پرداخت
    status = Column(String(20), default="completed")  #  وضعیت فاکتور (`completed`, `cancelled`, `refunded`) |
    created_at = Column(DateTime, default=datetime.now)#تاریخ و زمان دقیق ثبت فاکتور |
    notes = Column(Text, nullable=True)#توضیحات یا شروط فاکتور

    customer = relationship("Customer", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale_invoice", cascade="all, delete-orphan")

#جدول اقلام فاکتور فروش
class SaleItem(Base):
    __tablename__ = 'sale_items'

    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sale_invoices.id'))#ارجاع به فاکتور فروش |
    product_id = Column(Integer, ForeignKey('products.id'))#ارجاع به محصول |
    quantity = Column(Integer, default=1)#تعداد فروخته‌شده
    unit_purchase_price = Column(Float, default=0.0)  # قیمت خرید زمان فروش برای ثبت سود دقیق
    unit_sale_price = Column(Float, default=0.0)#قیمت فروش واحد
    unit_discount = Column(Float, default=0.0)#تخفیف روی این قلم کالا
    total_price = Column(Float, default=0.0)#جمع مبلغ سطر (`quantity * (unit_sale_price - unit_discount)`) |
    profit = Column(Float, default=0.0)#سود این سطر

    sale_invoice = relationship("SaleInvoice", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

#جدول هزینه‌های جاری / متفرقه
#برای اینکه سود و زیان شما **واقعی** باشد، باید هزینه‌های جانبی (اجاره، بسته‌بندی، پیک، آب و برق و...) از سود ناخالص کسر شود.
class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)#عنوان هزینه (مثلاً: بسته بندی، کرایه پیک، شارژ مغازه)
    category = Column(String(50), default="عمومی")#دسته‌بندی هزینه |

    amount = Column(Float, default=0.0)#مبلغ هزینه
    expense_date = Column(DateTime, default=datetime.now)#تاریخ پرداخت
    notes = Column(Text, nullable=True)#توضیحات
