from math import ceil

def add_pagination(list_data, page=1,page_size=10):
    total_length=len(list_data)
    start_index=(page-1)*page_size
    end_index=start_index+page_size
    paginated_data=list_data[start_index:end_index]
    total_pages=ceil(total_length/page_size)

    return{
        'data': paginated_data,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_count': total_length,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1,
            'next_page': page + 1 if page < total_pages else None,
            'previous_page': page - 1 if page > 1 else None
        }
    }