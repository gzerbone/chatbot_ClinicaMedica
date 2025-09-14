from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
#ViewSet é uma classe que agrupa múltiplas operações em uma única classe. É como ter várias views em uma só.
router.register(r'medicos', views.MedicoViewSet)

urlpatterns = [
    # URLs do router
    path('api/', include(router.urls)),
    
    # URLs específicas
    path('api/especialidades/', views.EspecialidadeListView.as_view(), name='especialidades-list'),
    path('api/clinica/', views.ClinicaInfoView.as_view(), name='clinica-info'),
    path('api/convenios/', views.ConvenioListView.as_view(), name='convenios-list'),
    path('api/exames/', views.ExameListView.as_view(), name='exames-list'),
    path('api/especialidades/<int:especialidade_id>/medicos/', 
         views.medicos_por_especialidade, name='medicos-por-especialidade'),
    path('api/search/', views.search_info, name='search-info'),
]
