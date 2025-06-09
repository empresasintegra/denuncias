import codecs
        
models=['denuncias','item','relacion_empresa','tiempo','usuario','categoria']


for modelo in models:

    with codecs.open('${modelo}.json', 'r', encoding='utf-16') as f:
        content = f.read()
    with codecs.open('${modelo}utf8.json', 'w', encoding='utf-8') as f:
        f.write(content)