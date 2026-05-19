from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta, datetime
import csv
import pandas as pd
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa

from apps.farmers.models import FarmerProfile
from apps.deliveries.models import CoffeeBatch
from .models import ReportTemplate, ReportExport, DashboardWidget

# ========== REPORTS INDEX / DASHBOARD ==========

@staff_member_required
def reports_index(request):
    """Reports dashboard/index page"""
    return render(request, 'reports/index.html')

# ========== MAIN DASHBOARD ==========

@staff_member_required
def dashboard(request):
    widgets = DashboardWidget.objects.filter(user=request.user, is_visible=True)
    if not widgets.exists():
        create_default_widgets(request.user)
        widgets = DashboardWidget.objects.filter(user=request.user, is_visible=True)
    
    # Get today's date
    today = timezone.now().date()
    current_year = timezone.now().year
    
    context = {
        'widgets': widgets,
        'total_farmers': FarmerProfile.objects.count(),
        'total_deliveries': CoffeeBatch.objects.count(),
        'total_kgs': CoffeeBatch.objects.aggregate(total=Sum('cherry_weight_kg'))['total'] or 0,
        'total_payments': 0,
        # Today's stats
        'today_kgs': CoffeeBatch.objects.filter(delivery_date=today).aggregate(total=Sum('cherry_weight_kg'))['total'] or 0,
        'today_count': CoffeeBatch.objects.filter(delivery_date=today).count(),
        # Season stats (current year)
        'season_kgs': CoffeeBatch.objects.filter(delivery_date__year=current_year).aggregate(total=Sum('cherry_weight_kg'))['total'] or 0,
        'season_count': CoffeeBatch.objects.filter(delivery_date__year=current_year).count(),
        # Gender stats
        'male_farmers': FarmerProfile.objects.filter(gender='M').count(),
        'female_farmers': FarmerProfile.objects.filter(gender='F').count(),
    }
    return render(request, 'reports/dashboard.html', context)

def create_default_widgets(user):
    widgets = [
        {'title': 'Deliveries Over Time', 'widget_type': 'chart', 'row': 1, 'column': 1, 'width': 6},
        {'title': 'Quality Distribution', 'widget_type': 'chart', 'row': 1, 'column': 2, 'width': 6},
        {'title': 'Top Farmers', 'widget_type': 'table', 'row': 2, 'column': 1, 'width': 12},
        {'title': 'Payment Summary', 'widget_type': 'metric', 'row': 3, 'column': 1, 'width': 4},
    ]
    for widget_data in widgets:
        DashboardWidget.objects.create(user=user, **widget_data)

# ========== API ENDPOINTS ==========

@staff_member_required
def stats_api(request):
    today = timezone.now().date()
    current_year = timezone.now().year
    
    return JsonResponse({
        'total_farmers': FarmerProfile.objects.count(),
        'total_deliveries': CoffeeBatch.objects.count(),
        'total_kgs': float(CoffeeBatch.objects.aggregate(total=Sum('cherry_weight_kg'))['total'] or 0),
        'total_payments': 0,
        # Today's stats
        'today_kgs': float(CoffeeBatch.objects.filter(delivery_date=today).aggregate(total=Sum('cherry_weight_kg'))['total'] or 0),
        'today_count': CoffeeBatch.objects.filter(delivery_date=today).count(),
        # Season stats
        'season_kgs': float(CoffeeBatch.objects.filter(delivery_date__year=current_year).aggregate(total=Sum('cherry_weight_kg'))['total'] or 0),
        'season_count': CoffeeBatch.objects.filter(delivery_date__year=current_year).count(),
        # Gender stats
        'male_farmers': FarmerProfile.objects.filter(gender='M').count(),
        'female_farmers': FarmerProfile.objects.filter(gender='F').count(),
    })

@staff_member_required
def delivery_summary_chart(request):
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    deliveries = CoffeeBatch.objects.filter(
        delivery_date__gte=start_date,
        delivery_date__lte=end_date
    ).values('delivery_date').annotate(
        total_kgs=Sum('cherry_weight_kg'),
        count=Count('id')
    ).order_by('delivery_date')
    labels = []
    kgs_data = []
    count_data = []
    for day in deliveries:
        labels.append(day['delivery_date'].strftime('%Y-%m-%d'))
        kgs_data.append(float(day['total_kgs']))
        count_data.append(day['count'])
    return JsonResponse({
        'labels': labels,
        'datasets': [
            {'label': 'Kgs Delivered', 'data': kgs_data, 'borderColor': '#8B5A2B', 'backgroundColor': 'rgba(139, 90, 43, 0.1)'},
            {'label': 'Number of Deliveries', 'data': count_data, 'borderColor': '#C4A35A', 'backgroundColor': 'rgba(196, 163, 90, 0.1)'}
        ]
    })

@staff_member_required
def quality_distribution_chart(request):
    grades = CoffeeBatch.objects.values('quality_grade').annotate(
        total_kgs=Sum('cherry_weight_kg')
    ).order_by('-total_kgs')
    labels = []
    data = []
    colors = {'specialty': '#2E7D32', 'premium': '#4CAF50', 'standard': '#FFC107', 'commercial': '#F57C00'}
    for grade in grades:
        labels.append(grade['quality_grade'].capitalize())
        data.append(float(grade['total_kgs'] or 0))
    bg_colors = [colors.get(g['quality_grade'], '#8B5A2B') for g in grades]
    return JsonResponse({
        'labels': labels,
        'datasets': [{'data': data, 'backgroundColor': bg_colors}]
    })

@staff_member_required
def top_farmers_table(request):
    farmers = FarmerProfile.objects.annotate(
        total_kgs=Sum('coffee_batches__cherry_weight_kg'),
        total_deliveries=Count('coffee_batches')
    ).order_by('-total_kgs')[:10]
    data = []
    for farmer in farmers:
        data.append({
            'name': farmer.full_name(),
            'farm': farmer.farm_name,
            'total_kgs': float(farmer.total_kgs or 0),
            'deliveries': farmer.total_deliveries,
            'payments': 0
        })
    return JsonResponse({'data': data})

# ========== DIRECT EXPORT FUNCTIONS ==========

@staff_member_required
def export_farmers(request):
    """Export farmers data directly"""
    file_format = request.GET.get('format', 'excel')
    data = export_farmers_report()
    
    if file_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="farmers_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        writer = csv.writer(response)
        writer.writerow(data['headers'])
        for row in data['rows']:
            writer.writerow(row)
        return response
    else:  # excel
        df = pd.DataFrame(data['rows'], columns=data['headers'])
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Farmers', index=False)
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="farmers_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        return response


@staff_member_required
def export_deliveries(request):
    """Export deliveries data directly"""
    file_format = request.GET.get('format', 'excel')
    data = export_deliveries_report()
    
    if file_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="deliveries_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        writer = csv.writer(response)
        writer.writerow(data['headers'])
        for row in data['rows']:
            writer.writerow(row)
        return response
    else:  # excel
        df = pd.DataFrame(data['rows'], columns=data['headers'])
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Deliveries', index=False)
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="deliveries_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        return response


@staff_member_required
def export_report(request, report_type):
    file_format = request.GET.get('format', 'csv')
    if report_type == 'deliveries':
        data = export_deliveries_report()
    elif report_type == 'farmers':
        data = export_farmers_report()
    else:
        return HttpResponse('Invalid report type', status=400)
    if file_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_{timezone.now().strftime("%Y%m%d")}.csv"'
        writer = csv.writer(response)
        writer.writerow(data['headers'])
        for row in data['rows']:
            writer.writerow(row)
        return response
    elif file_format == 'excel':
        df = pd.DataFrame(data['rows'], columns=data['headers'])
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=report_type, index=False)
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_{timezone.now().strftime("%Y%m%d")}.xlsx"'
        return response

def export_deliveries_report():
    deliveries = CoffeeBatch.objects.select_related('farmer').all().order_by('-delivery_date')[:1000]
    headers = ['Batch Code', 'Farmer', 'Delivery Date', 'Cherry (kg)', 'Dry (kg)', 'Quality Grade', 'Price/kg', 'Total Amount', 'Payment Status']
    rows = []
    for d in deliveries:
        rows.append([
            d.batch_code,
            d.farmer.full_name(),
            d.delivery_date.strftime('%Y-%m-%d'),
            float(d.cherry_weight_kg),
            float(d.dry_weight_kg),
            d.get_quality_grade_display(),
            float(d.price_per_kg),
            float(d.total_amount),
            d.get_payment_status_display(),
        ])
    return {'headers': headers, 'rows': rows}

def export_farmers_report():
    farmers = FarmerProfile.objects.all()
    headers = ['Farmer ID', 'Name', 'Phone', 'Farm Name', 'Gender', 'Region', 'District', 'Total Deliveries', 'Total Kgs', 'SMS Opt-in']
    rows = []
    for f in farmers:
        rows.append([
            f.id,
            f.full_name(),
            f.phone_number,
            f.farm_name,
            f.get_gender_display() if hasattr(f, 'get_gender_display') else 'Not specified',
            f.get_region_display(),
            f.district,
            f.total_deliveries(),
            float(f.total_kgs_delivered()),
            'Yes' if f.sms_notifications else 'No',
        ])
    return {'headers': headers, 'rows': rows}

# ========== HARVEST PREDICTION ==========

@staff_member_required
def harvest_prediction(request):
    historical = CoffeeBatch.objects.filter(
        delivery_date__gte=timezone.now() - timedelta(days=365*3)
    ).values('delivery_date').annotate(
        total_kgs=Sum('cherry_weight_kg')
    ).order_by('delivery_date')
    predictions = []
    if historical.count() > 30:
        recent = list(historical)[-30:]
        avg_daily = sum(d['total_kgs'] for d in recent) / 30
        for i in range(1, 31):
            pred_date = timezone.now().date() + timedelta(days=i)
            predictions.append({
                'date': pred_date.strftime('%Y-%m-%d'),
                'predicted_kgs': round(float(avg_daily * (0.9 + (i % 10) / 20)), 2)
            })
    by_month = CoffeeBatch.objects.extra(
        select={'month': "strftime('%%m', delivery_date)"}
    ).values('month').annotate(
        avg_kgs=Avg('cherry_weight_kg')
    ).order_by('month')
    seasonality = []
    for m in by_month:
        month_name = datetime.strptime(m['month'], '%m').strftime('%B')
        seasonality.append({
            'month': month_name,
            'avg_kgs': float(m['avg_kgs'] or 0)
        })
    return JsonResponse({
        'predictions': predictions,
        'seasonality': seasonality
    })

# ========== COLLECTION REPORT ==========
@staff_member_required
def collection_report(request):
    """Daily/Weekly/Monthly coffee collection report with PDF export"""
    
    # Get date range from request
    period = request.GET.get('period', 'month')  # day, week, month
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    # Default to current month if no dates provided
    today = timezone.now().date()
    
    if period == 'day':
        if not start_date_str:
            start_date = today
            end_date = today
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = start_date if not end_date_str else datetime.strptime(end_date_str, '%Y-%m-%d').date()
    elif period == 'week':
        if not start_date_str:
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else start_date + timedelta(days=6)
    else:  # month
        if not start_date_str:
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else start_date.replace(day=28)
    
    # Filter batches by date range (delivery_date is a DateField)
    batches = CoffeeBatch.objects.filter(
        delivery_date__gte=start_date,
        delivery_date__lte=end_date
    ).select_related('farmer')
    
    # Summary statistics
    total_weight = batches.aggregate(Sum('cherry_weight_kg'))['cherry_weight_kg__sum'] or 0
    total_batches = batches.count()
    total_farmers = batches.values('farmer').distinct().count()
    avg_weight = batches.aggregate(Avg('cherry_weight_kg'))['cherry_weight_kg__avg'] or 0
    
    # Grade distribution
    grade_distribution = batches.values('quality_grade').annotate(
        count=Count('id'),
        total_weight=Sum('cherry_weight_kg')
    ).order_by('quality_grade')
    
    # Daily breakdown - using Python to group by date
    daily_dict = {}
    for batch in batches:
        # delivery_date is already a date object
        date_key = batch.delivery_date
        if date_key not in daily_dict:
            daily_dict[date_key] = {'batches': 0, 'weight': 0, 'farmers': set()}
        daily_dict[date_key]['batches'] += 1
        daily_dict[date_key]['weight'] += float(batch.cherry_weight_kg)
        daily_dict[date_key]['farmers'].add(batch.farmer.id)
    
    # Convert to list of dictionaries
    daily_breakdown = []
    for date, data in sorted(daily_dict.items()):
        daily_breakdown.append({
            'delivery_date_only': date,
            'batches': data['batches'],
            'weight': data['weight'],
            'farmers': len(data['farmers'])
        })
    
    # Prepare context
    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_weight': total_weight,
        'total_batches': total_batches,
        'total_farmers': total_farmers,
        'avg_weight': avg_weight,
        'grade_distribution': grade_distribution,
        'daily_breakdown': daily_breakdown,
        'batches': batches[:100],
        'generated_at': timezone.now(),
    }
    
    # Check if PDF download requested
    if request.GET.get('download') == 'pdf':
        return render_to_pdf(request, 'reports/collection_report_pdf.html', context)
    
    return render(request, 'reports/collection_report.html', context)


def render_to_pdf(request, template_src, context_dict):
    """Helper function to generate PDF from HTML template using xhtml2pdf"""
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="collection_report.pdf"'
        return response
    return HttpResponse('Error generating PDF', status=400)