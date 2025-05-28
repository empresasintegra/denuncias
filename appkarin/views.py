from django.shortcuts import render
from .models import Item, Categoria
from django.http import HttpResponse



# Create your views here.
def home(request):
    return render(request, 'index.html')

def itemsDenuncia(request):
    
  
    categorias = Categoria.objects.all().prefetch_related('item_set')
    
    context = {
        'categorias': categorias
    }

    
    return render(request, 'pageItemsDenuncia.html', context)