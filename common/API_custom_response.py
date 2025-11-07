from rest_framework.response import Response

def api_response(
        success=True,
        status=200,
        data=None,
        message=None,
        error_message=None,
        system_message=None,
        **kwargs
):
    response={
        "success": success,
        "status": status,
        "data": data,
        "message": message,
        "error_message": error_message,
        "system_message": system_message,
        
    }

    if status!=200:
        response['success']=False,

    if status == 500:
        response['error_message'] = "Somthing went wrong Please try again later."

    if kwargs:
        response.update(kwargs)

    custom_response_dict = {key: value for key, value in response.items() if value is not None}


    return Response(custom_response_dict, status=status)

