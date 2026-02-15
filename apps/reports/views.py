from django.shortcuts import render 
from django.http import JsonResponse, HttpResponse 
from django.contrib.admin.views.decorators import staff_member_required 
from django.db.models import Sum, Count, Avg 
from django.utils import timezone 
from datetime import timedelta, datetime 
import csv 
import pandas as pd 
from io import BytesIO 
 
from farmers.models import FarmerProfile 
from deliveries.models import CoffeeBatch 
from .models import ReportTemplate, ReportExport, DashboardWidget 
 
@staff_member_required 
def dashboard(request): 
    widgets = DashboardWidget.objects.filter(user=request.user, is_visible=True) 
    if not widgets.exists(): 
        create_default_widgets(request.user) 
        widgets = DashboardWidget.objects.filter(user=request.user, is_visible=True) 
    context = { 
        'widgets': widgets, 
        'total_farmers': FarmerProfile.objects.count(), 
        'total_deliveries': CoffeeBatch.objects.count(), 
        'total_kgs': CoffeeBatch.objects.aggregate(total=Sum('cherry_weight_kg'))['total'] or 0, 
        'total_payments': 0, 
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
 
@staff_member_required 
def stats_api(request): 
    return JsonResponse({ 
        'total_farmers': FarmerProfile.objects.count(), 
        'total_deliveries': CoffeeBatch.objects.count(), 
        'total_kgs': float(CoffeeBatch.objects.aggregate(total=Sum('cherry_weight_kg'))['total'] or 0), 
        'total_payments': 0, 
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
    headers = ['Farmer ID', 'Name', 'Phone', 'Farm Name', 'Region', 'District', 'Total Deliveries', 'Total Kgs', 'SMS Opt-in'] 
    rows = [] 
    for f in farmers: 
        rows.append([ 
            f.id, 
            f.full_name(), 
            f.phone_number, 
            f.farm_name, 
            f.get_region_display(), 
            f.district, 
            f.total_deliveries(), 
            float(f.total_kgs_delivered()), 
            'Yes' if f.sms_notifications else 'No', 
        ]) 
    return {'headers': headers, 'rows': rows} 
 
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
