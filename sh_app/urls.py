from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('record/<int:pk>', views.sheep_record, name='record'),
    path('delete_record/<int:pk>', views.delete_record, name='delete_record'),
    path('add_record/', views.add_record, name='add_record'),
    path('update_record/<int:pk>', views.update_record, name='update_record'),
    
    path('selection/', views.breeding_selection, name='breeding_selection'),
    path('flash-rams/', views.flash_rams_state, name='flash_rams_state'),
    path('flash-ewes/', views.flash_ewes_state, name='flash_ewes_state'),

    path('breed-rams/', views.breed_rams_state, name='breed_rams_state'),
    # path('breed-ewes/', views.breed_ewes_state, name='breed_ewes_state'),
    # path('flash-rams/', views.flash_rams, name='flash_rams'),
    path('breed-rams/', views.breed_rams_state, name='breed_rams_state'),

    # Add the test URL temporarily
    # path('test_ram_selection/', views.test_ram_selection, name='test_ram_selection'),
    path('debug_breeding/', views.debug_breeding_flow, name='debug_breeding'),

    # path('selection/breeding_task', views.breeding_task, name='breeding_task'),
    path('breeding/create-cycle/', views.create_breeding_cycle, name='create_breeding_cycle'),
    # path('compatible-ewes/<str:ram_id>/', views.get_compatible_ewes_ajax, name='get_compatible_ewes'),

    # path('breeding/', views.BreedingCycleListView.as_view(), name='breeding_cycle_list'),
    # path('breeding/<str:pk>/', views.BreedingCycleDetailView.as_view(), name='breeding_cycle_detail'),
    # path('breeding/create/', views.BreedingCycleCreateView.as_view(), name='breeding_cycle_create'),
    # path('breeding/<str:pk>/update/', views.BreedingCycleUpdateView.as_view(), name='breeding_cycle_update'),
    # path('dashboard/', views.BreedingDashboardView.as_view(), name='breeding_dashboard'),
    
    # API endpoints for automation
    # path('api/update-statuses/', views.update_cycle_statuses_api, name='update_cycle_statuses_api'),
    # path('api/upcoming-births/', views.upcoming_births_api, name='upcoming_births_api'),
    
    # path('breeding/', views.BreedingHomeView.as_view(), name='breeding_home'),
    # path('breeding_task/', views.breeding_task, name='breeding_task'),
    # path('breeding_task/breeding_info/', views.breeding_info, name='breeding_info'),
    # path('create-cycle/', views.create_breeding_cycle, name='create_breeding_cycle'),
    # path('breeding/', views.BreedingHomeView.as_view(), name='breeding_home'),
    # path('breeding/breeding_task/', views.BreedingTaskView.as_view(), name='breeding_task'),
    path('breeding/breeding_info/', views.BreedingInfoView.as_view(), name='breeding_info'), 
    # urls.py example
    path('breeding/process-selection/', views.process_ram_selection, name='process_ram_selection'),
    path('breeding/task/', views.BreedingTaskView.as_view(), name='breeding_task'),
    # path('import_sheep_csv/', views.import_sheep_csv, name='import_sheep_csv'),
    # path('download_csv_template/', views.download_csv_template, name='download_csv_template'),
    # path('export_sheep_csv/', views.export_sheep_csv, name='export_sheep_csv'),
    
    # path('sheep/import/', views.import_sheep_csv, name='import_sheep_csv'),
    # path('sheep/import/sample/', views.download_sample_csv, name='download_sample_csv'),
    # path('sheep/', views.sheep_list, name='sheep_list'),

    path('import-csv/', views.import_sheep_csv, name='import_sheep_csv'),
]
