from openpyxl import Workbook, load_workbook
from app.models import Order, Sample

def export_to_excel():
    workbook = Workbook()
    sheet = workbook.active

    # Write headers
    headers = ['User', 'Name', 'Billing Address']
    sheet.append(headers)

    # Write data from Order model
    orders = Order.objects.all()
    for order in orders:
        row = [order.user.username, order.name, order.billing_address]
        sheet.append(row)

    # Write data from Sample model
    samples = Sample.objects.all()
    for sample in samples:
        row = [sample.order.user.username, sample.sample_name, sample.concentration]
        sheet.append(row)

    workbook.save('output.xlsx')

def import_from_excel(file_path):
    workbook = load_workbook(file_path)
    sheet = workbook.active

    # Skip the header row
    rows = list(sheet.iter_rows(min_row=2, values_only=True))

    for row in rows:
        user = User.objects.get(username=row[0])
        order = Order(user=user, name=row[1], billing_address=row[2])
        order.save()

        sample = Sample(order=order, sample_name=row[10], concentration=row[11])
        sample.save()