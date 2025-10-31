# views.py
import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
logger = logging.getLogger(__name__) #tambahkan ini untuk multi database.
import json
from ....models.selling_blending import BlendingResult,BlendingDetail

def generate_blend_code():
    prefix = "BLND-"
    latest_code = (
        BlendingResult.objects
        .filter(blend_code__startswith=prefix)
        .order_by('-blend_code')
        .values_list('blend_code', flat=True)
        .first()
    )

    if latest_code:
        latest_number = int(latest_code.replace(prefix, ''))
    else:
        latest_number = 0

    next_number = latest_number + 1
    return f"{prefix}{str(next_number).zfill(5)}"

def get_next_blend_code(request):
    code = generate_blend_code()
    return JsonResponse({'blend_code': code})

@csrf_exempt
def create_blending_sale(request):
    if request.method == 'POST':
        payload = json.loads(request.body)

        # Ambil data dari POST
        target_tonase   = payload.get("target_tonase")
        target_ni       = payload.get("target_ni")
        final_grade     = payload.get("final_grade", {})
        result_details  = payload.get("result", [])
        user_id = request.user.id if request.user.is_authenticated else None

        # Generate blend_code
        blend_code = generate_blend_code()

        # Simpan ke BlendingResult
        result = BlendingResult.objects.create(
            blend_code=blend_code,
            target_tonase=target_tonase,
            target_ni=target_ni,
            final_ni=final_grade.get('ni', 0),
            final_fe=final_grade.get('fe'),
            final_co=final_grade.get('co'),
            final_mgo=final_grade.get('mgo'),
            final_al2o3=final_grade.get('al2o3'),
            final_sio2=final_grade.get('sio2'),
            final_sm=final_grade.get('sm'),
            total_used=payload.get("total_used"),
            id_user=user_id,
            created_at=timezone.now()
        )

        # Simpan ke BlendingDetail
        for item in result_details:
            BlendingDetail.objects.create(
                blending=result,
                pile_id=item['pile_id'],
                used_tonase=item['used_tonase'],
                ni=item.get('ni'),
                fe=item.get('fe'),
                co=item.get('co'),
                mgo=item.get('mgo'),
                al2o3=item.get('al2o3'),
                sio2=item.get('sio2'),
                sm=item.get('sm'),
                balance=item.get('balance')
            )

    return JsonResponse({'success': True, 'blend_code': blend_code})