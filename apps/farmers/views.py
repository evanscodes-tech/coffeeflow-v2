from django.shortcuts import render, get_object_or_404 
from django.contrib.auth.decorators import login_required 
from django.contrib.admin.views.decorators import staff_member_required 
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from io import BytesIO
from xhtml2pdf import pisa
from apps.farmers.models import FarmerProfile
from apps.deliveries.models import CoffeeBatch
from django.db.models import Q
from django.shortcuts import render


@login_required 
def farmer_list(request): 
    farmers = FarmerProfile.objects.all() 
    return render(request, 'farmers/list.html', {'farmers': farmers}) 


@staff_member_required
def farmer_detail(request, farmer_id):
    """
    View a farmer's full profile + all deliveries + payment summary
    Uses farmer_id (e.g., F001) to identify the farmer
    """
    # Get the farmer by farmer_id (e.g., F001)
    farmer = get_object_or_404(FarmerProfile, farmer_id=farmer_id)
    
    # Get all deliveries for this farmer
    deliveries = CoffeeBatch.objects.filter(farmer=farmer).order_by('-delivery_date')
    
    # Calculate totals
    total_deliveries = deliveries.count()
    total_kgs = deliveries.aggregate(total=Sum('cherry_weight_kg'))['total'] or 0
    total_paid = deliveries.filter(payment_status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
    total_pending = deliveries.filter(payment_status='pending').aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'farmer': farmer,
        'deliveries': deliveries,
        'total_deliveries': total_deliveries,
        'total_kgs': total_kgs,
        'total_paid': total_paid,
        'total_pending': total_pending,
    }
    return render(request, 'farmers/farmer_detail.html', context)


def render_to_pdf(template_src, context_dict):
    """Helper function to generate PDF from HTML template using xhtml2pdf"""
    html = render_to_string(template_src, context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('Error generating PDF', status=400)


@staff_member_required
def farmer_statement_pdf(request, farmer_id):
    """
    Generate a PDF statement for a farmer with all deliveries and payment summary
    """
    farmer = get_object_or_404(FarmerProfile, farmer_id=farmer_id)
    deliveries = CoffeeBatch.objects.filter(farmer=farmer).order_by('-delivery_date')
    
    # Calculate totals
    total_deliveries = deliveries.count()
    total_kgs = deliveries.aggregate(total=Sum('cherry_weight_kg'))['total'] or 0
    total_paid = deliveries.filter(payment_status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
    total_pending = deliveries.filter(payment_status='pending').aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'farmer': farmer,
        'deliveries': deliveries,
        'total_deliveries': total_deliveries,
        'total_kgs': total_kgs,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'generated_date': timezone.now(),
    }
    return render_to_pdf('farmers/statement_pdf.html', context)


@staff_member_required
def search_farmer(request):
    query = request.GET.get('q', '').strip()
    farmers = []

    if query:
        farmers = FarmerProfile.objects.filter(
            Q(farmer_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query)
        ).order_by('farmer_id')

    context = {
        'query': query,
        'farmers': farmers,
        'count': farmers.count(),
    }
    return render(request, 'farmers/search_results.html', context)