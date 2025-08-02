"""
API views for service notifications
Ubuntu-compatible endpoints for automated notifications
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import permission_required
from django.core.management import call_command
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
@permission_required('warranty_and_services.can_send_notifications', raise_exception=True)
def api_send_service_notifications(request):
    """
    API endpoint to trigger service due notifications
    Can be called by external cron job or monitoring system
    """
    try:
        data = json.loads(request.body) if request.body else {}
        days_list = data.get('days', [15, 7, 3, 0])
        dry_run = data.get('dry_run', False)
        
        logger.info(f"API service notifications triggered - days: {days_list}, dry_run: {dry_run}")
        
        # Call the Django management command
        call_command('send_service_due_notifications', 
                    days=days_list, 
                    dry_run=dry_run)
        
        return JsonResponse({
            'success': True,
            'message': f'Service notifications triggered for {days_list} days',
            'dry_run': dry_run
        })
        
    except Exception as e:
        logger.error(f"Error in API service notifications: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt  
@require_http_methods(["GET"])
def api_service_notification_status(request):
    """
    API endpoint to check upcoming service due notifications
    """
    try:
        from datetime import timedelta
        from django.utils import timezone
        from .models import Installation
        
        today = timezone.now().date()
        
        # Count installations due for service in next 30 days
        upcoming_services = {}
        for days in [0, 1, 3, 7, 15, 30]:
            target_date = today + timedelta(days=days)
            count = Installation.objects.filter(
                service_followups__next_service_date=target_date,
                service_followups__is_completed=False
            ).distinct().count()
            
            upcoming_services[f'due_in_{days}_days'] = count
            
        return JsonResponse({
            'success': True,
            'today': today.isoformat(),
            'upcoming_services': upcoming_services,
            'total_due_in_30_days': sum(upcoming_services.values())
        })
        
    except Exception as e:
        logger.error(f"Error in service notification status: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

class ServiceNotificationWebhookView(View):
    """
    Webhook endpoint for external monitoring systems
    Supports authentication via API key
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        """Handle webhook POST requests"""
        try:
            # Check API key authentication
            api_key = request.headers.get('X-API-Key')
            expected_key = getattr(settings, 'SERVICE_NOTIFICATION_API_KEY', None)
            
            if not api_key or api_key != expected_key:
                return JsonResponse({'error': 'Unauthorized'}, status=401)
            
            data = json.loads(request.body) if request.body else {}
            action = data.get('action', 'send_notifications')
            
            if action == 'send_notifications':
                days_list = data.get('days', [15, 7, 3, 0])
                dry_run = data.get('dry_run', False)
                
                call_command('send_service_due_notifications', 
                           days=days_list, 
                           dry_run=dry_run)
                
                return JsonResponse({
                    'success': True,
                    'action': action,
                    'message': f'Notifications sent for {days_list} days'
                })
                
            elif action == 'status':
                # Return status information
                return api_service_notification_status(request)
                
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except Exception as e:
            logger.error(f"Error in webhook: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
