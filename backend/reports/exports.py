"""CSV streaming and paginated PDF output over canonical report data."""

import csv
from tempfile import SpooledTemporaryFile
from threading import Lock

from django.http import FileResponse, StreamingHttpResponse
from django.db.models import Q
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas
from rest_framework.exceptions import NotFound, ValidationError

from operations.models import ParkingRecord
from parking_slots.models import ParkingZone
from .revenue import revenue_report
from .serializers import REPORT_TIMEZONE
from .services import occupancy_report

PDF_LOCK = Lock()
LOG_FIELDS = ('id', 'registration_number', 'slot_number', 'zone_name',
              'check_in_time', 'check_out_time', 'status', 'fee_amount', 'payment_status')


def report_rows(query):
    kind = query['report']
    if kind != 'logs':
        fields = ('start', 'end', 'interval', 'zone') if kind == 'occupancy' else (
            'start', 'end', 'interval', 'payment_method', 'vehicle_type')
        report = (occupancy_report if kind == 'occupancy' else revenue_report)(
            **{key: query[key] for key in fields if key in query})
        headers = tuple(report['results'][0]) if report['results'] else (
            ('zone_id', 'zone_name', 'start', 'end', 'slot_count', 'observed_minutes',
             'occupied_slot_minutes', 'utilization_percent', 'entries') if kind == 'occupancy'
            else ('start', 'end', 'receipt_count', 'revenue'))
        return headers, (tuple(row[key] for key in headers) for row in report['results'])

    records = ParkingRecord.objects.filter(
        check_in_time__gte=query['start'], check_in_time__lt=query['end'],
    ).order_by('check_in_time', 'pk')
    if 'zone' in query:
        if not ParkingZone.objects.filter(pk=query['zone']).exists():
            raise NotFound('Zone not found.')
        records = records.filter(slot__zone_id=query['zone'])
    if 'status' in query:
        records = records.filter(status=query['status'])
    if 'vehicle_type' in query:
        records = records.filter(
            Q(vehicle_type_at_checkin_snapshot=query['vehicle_type'])
            | (Q(vehicle_type_at_checkin_snapshot__isnull=True) | Q(vehicle_type_at_checkin_snapshot=''))
            & Q(vehicle__vehicle_type=query['vehicle_type']))

    def rows():
        values = records.values_list(
            'pk', 'registration_number_snapshot', 'vehicle__registration_number',
            'slot_number_snapshot', 'slot__slot_number', 'zone_name_snapshot', 'slot__zone__name',
            'check_in_time', 'check_out_time', 'status', 'fee_amount', 'payment_status')
        for pk, plate, current_plate, slot, current_slot, zone, current_zone, entered, exited, status, fee, payment in values.iterator(chunk_size=1000):
            yield (pk, plate or current_plate, slot or current_slot, zone or current_zone,
                   entered.astimezone(REPORT_TIMEZONE).isoformat(),
                   exited.astimezone(REPORT_TIMEZONE).isoformat() if exited else '', status, fee, payment)
    return LOG_FIELDS, rows()


class Echo:
    def write(self, value):
        return value


def safe_cell(value):
    if value is None:
        return ''
    text = str(value)
    # Quoting alone does not stop spreadsheets from evaluating formulas.
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r', '\n')) else text


def export_response(query):
    headers, rows = report_rows(query)
    filename = f"{query['report']}-{query['start']:%Y%m%d}-{query['end']:%Y%m%d}.{query['export_format']}"
    if query['export_format'] == 'csv':
        writer = csv.writer(Echo())

        def content():
            yield '\ufeff' + writer.writerow(headers)
            for row in rows:
                yield writer.writerow([safe_cell(value) for value in row])
        response = StreamingHttpResponse(content(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    # Bound printable reports; CSV remains available for unrestricted row counts.
    printable = []
    for row in rows:
        if len(printable) == 10000:
            raise ValidationError({'end': 'PDF supports at most 10000 rows. Narrow filters or use CSV.'})
        printable.append(row)
    buffer = SpooledTemporaryFile(max_size=1024 * 1024)
    try:
        # ReportLab documents process-global font state as not thread-safe.
        with PDF_LOCK:
            pdf = Canvas(buffer, pagesize=landscape(A4))
            width, height = landscape(A4)
            cell_width = (width - 48) / len(headers)
            page = 0

            def new_page():
                nonlocal page
                page += 1
                pdf.setFont('Helvetica-Bold', 14)
                pdf.drawString(24, height - 28, f"BAY | {query['report'].title()} report | Page {page}")
                pdf.setFont('Helvetica', 8)
                pdf.drawString(24, height - 44, f"{query['start'].isoformat()} to {query['end'].isoformat()} | Asia/Kolkata | INR")
                pdf.drawString(24, height - 57, 'Dates: inclusive start, exclusive end. Logs: check-in time; revenue: paid receipts by payment time.')
                pdf.drawString(24, height - 70, 'Occupancy uses current inventory and zone. Long cells wrap onto additional lines.')
                filters = ', '.join(f'{key}={value}' for key, value in query.items()
                                    if key not in ('report', 'export_format', 'start', 'end'))
                pdf.drawString(24, height - 83, f'Filters: {filters or "none"}')
                return height - 107

            def lines(value):
                text = '' if value is None else str(value)
                result = ['']
                for char in text.replace('\n', ' ').replace('\r', ' '):
                    if stringWidth(result[-1] + char, 'Helvetica', 7) > cell_width - 6:
                        result.append('')
                    result[-1] += char
                return result

            def draw_row(row, y):
                cells = [lines(value) for value in row]
                pdf.setFont('Helvetica', 7)
                for col, cell in enumerate(cells):
                    for line, text in enumerate(cell):
                        pdf.drawString(24 + col * cell_width, y - line * 9, text)
                return y - max(map(len, cells)) * 9 - 8

            y = draw_row(headers, new_page())
            for row in printable:
                needed = max(len(lines(value)) for value in row) * 9 + 8
                if y - needed < 24:
                    pdf.showPage()
                    y = draw_row(headers, new_page())
                y = draw_row(row, y)
            if not printable:
                pdf.drawString(24, y, 'No matching records.')
            pdf.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')
    except Exception:
        buffer.close()
        raise
