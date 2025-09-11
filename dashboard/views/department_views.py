from django.shortcuts import render
from django.contrib import messages
from dashboard.models import Department
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from dashboard.forms import DepartmentForm
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q


PAGE_SIZE = 10
ORPHANS = 1


def check_admin(user):
    return user.is_superuser


def manage_access(user):
    permissions_list = [
        'authentication.edit_department',
        'authentication.add_department',
        'authentication.delete_department',
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False


@login_required
@user_passes_test(manage_access)
def departments(request):
    department_list = Department.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    deleted_department_count=Department.deleted_objects.count()
    paginator = Paginator(department_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    department_form = DepartmentForm()

    context = {
        'sidebar': 'admin',
        'submenu': 'department',
        'page_object': page_object,
        'department_form': department_form,
        'deleted_department_count':deleted_department_count,
        'title': 'Departments'
    }
    return render(request, 'dashboard/departments/list.html', context=context)


@login_required
@user_passes_test(check_admin)
def department_details(request, id):

    department = get_object_or_404(
        Department.undeleted_objects, pk=id, organization=request.user.organization)

    history_list = department.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {'sidebar': 'admin', 'page_object': page_object,
               'submenu': 'department', 'department': department, 'title': 'Department - Details'}
    return render(request, 'dashboard/departments/detail.html', context=context)


@login_required
@permission_required('authentication.add_department')
def add_department(request):

    form = DepartmentForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            department = form.save(commit=False)
            department.organization = request.user.organization
            department.save()
            messages.success(request, 'Department added successfully')
            return HttpResponse(status=204)

    context = {"form": form, "modal_title": "Add Department"}
    return render(request, 'dashboard/departments/department-modal.html', context=context)


@login_required
@permission_required('authentication.edit_department')
def update_department(request, id):

    department = get_object_or_404(
        Department.undeleted_objects, pk=id, organization=request.user.organization)
    form = DepartmentForm(
        request.POST or None, instance=department)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully')
            return HttpResponse(status=204)

    context = {"form": form, "modal_title": "Update Department"}
    return render(request, 'dashboard/departments/department-modal.html', context=context)


@login_required
@permission_required('authentication.delete_department')
def delete_department(request, id):

    if request.method == 'POST':
        department = get_object_or_404(
            Department.undeleted_objects, pk=id, organization=request.user.organization)
        department.status = False
        department.soft_delete()
        history_id = department.history.first().history_id
        department.history.filter(pk=history_id).update(history_type='-')
        messages.success(request, 'Department deleted successfully')
        return redirect(request.META.get('HTTP_REFERER'))

    return redirect('/')


@user_passes_test(check_admin)
def department_status(request, id):
    if request.method == "POST":
        department = get_object_or_404(
            Department.undeleted_objects, pk=id, organization=request.user.organization)
        department.status = False if department.status else True
        department.save()
    return HttpResponse(status=204)



@login_required
def search_department(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'dashboard/departments/departments-data.html', {
            'page_object': Department.undeleted_objects.filter(Q(organization=request.user.organization) & (Q(
                name__icontains=search_text) | Q(contact_person_name__icontains=search_text) | Q(contact_person_email__icontains=search_text) | Q(contact_person_phone__icontains=search_text)
            )).order_by('-created_at')[:10]
        })

    department_list = Department.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(department_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'dashboard/departments/departments-data.html', {'page_object': page_object})
