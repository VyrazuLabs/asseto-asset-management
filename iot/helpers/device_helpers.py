import uuid
def generate_topic(organization_id:uuid.uuid4, attachment_name:str):
    return f"{organization_id}/attachment/{attachment_name}"