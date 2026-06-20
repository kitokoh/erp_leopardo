from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@login_required
def dashboard_view(request):
    # Pour l'instant, une simple réponse pour que l'URL fonctionne
    # Plus tard, on rendra un vrai template avec des données.
    active_company_name = request.session.get('active_company_name', 'N/A')
    return HttpResponse(f"<h1>Dashboard Principal</h1><p>Société active: {active_company_name}</p><p><a href=\"{% url 'users:logout' %}\">Déconnexion</a></p>")
    # context = {
    #     'page_title': 'Tableau de Bord',
    #     'active_company_name': active_company_name,
    # }
    # return render(request, 'dashboard/main_dashboard.html', context)
