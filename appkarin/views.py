from django.shortcuts import render
from .models import Item, Categoria
from django.http import HttpResponse



# Create your views here.
def home(request):
    return render(request, 'index.html')

def itemsDenuncia(request):
    
    print("alo!!!!!?")
  
    categorias= Categoria.objects.all()
    print("TERMINE!!!")
    print("ESTO ES CATEGORIAS",Categoria.objects.all())


    
    count=1
    context={}

    for categoria in categorias:
        items= Item.objects.filter(categoria=categoria)
        print(items)
        context['items_categoria_{count}']= items
        print(context)
        count+=1

    
    return render(request, 'pageItemsDenuncia.html', context)