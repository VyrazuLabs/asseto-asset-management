from configurations.models import TagConfiguration,LocalizationConfiguration

def get_tag_configurations(request):
    get_tag_configurations_data=TagConfiguration.objects.filter(organization=request.user.organization).first()
    obj=[]
    if get_tag_configurations_data is not None:
        dict = {
            'id': get_tag_configurations_data.id,
            'prefix': get_tag_configurations_data.prefix,
            'number_suffix': get_tag_configurations_data.number_suffix,
            # 'use_default_settings': get_tag_configurations_data.use_default_settings,
        }
        print(dict)
    else:
        dict = {
            'id': None,
            'prefix': None,
            'number_suffix': None,
            # 'use_default_settings': None,
        }
    obj.append(dict)
    return obj

def get_localization_configurations(request):
    get_localization_configurations_data=LocalizationConfiguration.objects.filter(organization=request.user.organization).first()
    obj=[]
    if get_localization_configurations_data is not None:
        dict = {
            # 'id': get_localization_configurations_data.id,
            'date_format': get_localization_configurations_data.date_format,
            'time_format': get_localization_configurations_data.time_format,
            'timezone': get_localization_configurations_data.timezone,
            'currency': get_localization_configurations_data.currency,
            'name_display_format': get_localization_configurations_data.name_display_format
            # 'use_default_settings': get_tag_configurations_data.use_default_settings,
        }
        print(dict)
    else:
        dict = {
            'id': None,
            'prefix': None,
            'number_suffix': None,
            # 'use_default_settings': None,
        }
    obj.append(dict)
    return obj